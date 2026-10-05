"""Results data for the NOM-035 results page.

One assignment at a time, narrowed by a validated filter (see
apps/core/results_query.py), returned as frozen dataclasses. The small-group
rule is applied here, not in templates: a suppressed result carries no numbers.
See docs/platform/nom-035-results-dashboard.md.
"""

import statistics
from collections import Counter, defaultdict
from dataclasses import dataclass, replace

from django.db.models import Count, Max, Min, Q
from django.utils import timezone

from apps.accounts import demographics
from apps.accounts.models import CompanyArea, UserProfile
from apps.nom035 import _nom035_scoring as cfg
from apps.nom035 import constants as c
from apps.nom035.models import GroupScore, SubmissionScore
from apps.surveys.models import SurveyAssignment

NOM035_SURVEY_KEY = "nom035"
NO_DATA = "Sin dato"
NO_AREA = "Sin área"
FINAL = "final"
_PROFILE = "submission__user__profile__"

_MONTHS = (
    "ene",
    "feb",
    "mar",
    "abr",
    "may",
    "jun",
    "jul",
    "ago",
    "sep",
    "oct",
    "nov",
    "dic",
)


def _short(day, *, year=True) -> str:
    text = f"{day.day} {_MONTHS[day.month - 1]}"
    return f"{text} {day.year}" if year else text


def period_span(first, last) -> str:
    """The application span, "3 feb – 10 mar 2026"; "" when nothing was answered."""
    if first is None:
        return ""
    if first == last:
        return _short(first)
    if first.year == last.year:
        return f"{_short(first, year=False)} – {_short(last)}"
    return f"{_short(first)} – {_short(last)}"


def assignment_label(variant_label, first, last, created) -> str:
    if first is None:
        return f"{variant_label} · creada {_short(created)} · sin respuestas"
    return f"{variant_label} · aplicada {period_span(first, last)}"


@dataclass(frozen=True)
class AssignmentOption:
    assignment: SurveyAssignment
    label: str
    scored_count: int


def local_date(moment):
    return timezone.localtime(moment).date() if moment is not None else None


def assignment_options(company) -> list[AssignmentOption]:
    scored = Q(submissions__nom035_score__isnull=False)
    rows = (
        SurveyAssignment.objects.filter(company=company, survey__key=NOM035_SURVEY_KEY)
        .select_related("company")
        .annotate(
            first_answer=Min("submissions__completed_at", filter=scored),
            last_answer=Max("submissions__completed_at", filter=scored),
            scored_count=Count("submissions__nom035_score"),
        )
        .order_by("-created_at", "-pk")
    )
    return [
        AssignmentOption(
            assignment=a,
            label=assignment_label(
                a.get_variant_display(),
                local_date(a.first_answer),
                local_date(a.last_answer),
                local_date(a.created_at),
            ),
            scored_count=a.scored_count,
        )
        for a in rows
    ]


def select_assignment(options, requested_pk):
    if not options:
        return None
    for option in options:
        if option.assignment.pk == requested_pk:
            return option
    return next((o for o in options if o.scored_count), options[0])


def shows(size: int, base: int, *, suppress: bool) -> bool:
    """Whether `size` questionnaires out of `base` may be shown.

    Both the set and what it leaves out of its base must be empty or at least
    MIN_GROUP_SIZE, so no one is exposed directly or by subtraction.
    """
    if not suppress:
        return True
    rest = base - size
    return size >= c.MIN_GROUP_SIZE and (rest == 0 or rest >= c.MIN_GROUP_SIZE)


@dataclass(frozen=True)
class Slice:
    key: str
    label: str
    value: int
    color: str


# Color-key prefixes: the risk palette's two tiers. Categorías and the final
# score draw in "ndr-<level>"; dominios in the deeper "dom-<level>". The chart
# and badge palettes in apps/core map both.
PALETTE_NDR = "ndr"
PALETTE_DOMINIO = "dom"


def _ndr_slices(counts, palette=PALETTE_NDR) -> tuple[Slice, ...]:
    """Shared by DistributionRow and ParticipationRow: one Slice per (level, count)."""
    return tuple(
        Slice(level, c.NDR_LABELS[level], count, f"{palette}-{level}")
        for level, count in counts
    )


@dataclass(frozen=True)
class DistributionRow:
    key: str
    label: str
    n: int
    counts: tuple[tuple[str, int], ...]
    palette: str = PALETTE_NDR
    children: tuple["DistributionRow", ...] = ()

    @property
    def slices(self) -> tuple[Slice, ...]:
        return _ndr_slices(self.counts, self.palette)


@dataclass(frozen=True)
class StatsRow:
    key: str
    label: str
    n: int
    mean: float | None
    median: float | None
    minimum: int | None
    maximum: int | None
    scale_max: int
    strip_bands: tuple[tuple[float, str, str], ...]
    children: tuple["StatsRow", ...] = ()

    @property
    def strip_points(self) -> list[tuple[str, str, float]]:
        if not self.n:
            return []
        return [
            ("min", "Mín", self.minimum),
            ("median", "Mediana", self.median),
            ("mean", "Prom.", self.mean),
            ("max", "Máx", self.maximum),
        ]


@dataclass(frozen=True)
class Guia1:
    none: int
    event: int
    positive: int

    @property
    def slices(self) -> tuple[Slice, ...]:
        return (
            Slice("none", "Sin acontecimiento", self.none, "guia1-none"),
            Slice(
                "event",
                "Acontecimiento sin requerir valoración",
                self.event,
                "guia1-event",
            ),
            Slice(
                "positive",
                "Requiere valoración clínica",
                self.positive,
                "guia1-positive",
            ),
        )


@dataclass(frozen=True)
class ParticipationRow:
    area_id: int | None
    label: str
    registered: int | None
    responded: int
    participation: int | None
    counts: tuple[tuple[str, int], ...]
    suppressed: bool

    @property
    def slices(self) -> tuple[Slice, ...]:
        return _ndr_slices(self.counts)


def _area_of(profile, company):
    """The respondent's área, but only if it belongs to `company` (else "Sin área")."""
    area = profile.area if profile is not None else None
    if area is not None and area.company_id != company.pk:
        return None
    return area


def _participation(assignment, query, scores, today, *, group_suppressed, suppress):
    company = assignment.company
    registered = dict(
        narrow(
            UserProfile.objects.filter(company=company, is_activated=True),
            query,
            today,
            prefix="",
        )
        .values("area_id")
        .annotate(n=Count("pk"))
        .values_list("area_id", "n")
    )
    by_area = defaultdict(list)
    for score in scores:
        area = _area_of(_profile(score), company)
        by_area[area.pk if area else None].append(score.final_ndr)

    group_size = len(scores)
    areas = CompanyArea.objects.filter(company=company).order_by("name")
    if query.area_ids:
        areas = areas.filter(pk__in=query.area_ids)
    entries = [
        (area.pk, area.name, registered.get(area.pk, 0))
        for area in areas
        if area.is_active or registered.get(area.pk) or by_area.get(area.pk)
    ]
    if by_area.get(None):
        entries.append((None, NO_AREA, None))

    visible = {
        area_id
        for area_id, _label, _registered in entries
        if by_area.get(area_id)
        and not group_suppressed
        and shows(len(by_area[area_id]), group_size, suppress=suppress)
    }
    if suppress:
        _hide_until_safe(entries, by_area, visible)

    def row(area_id, label, registered_count):
        ndrs = by_area.get(area_id, [])
        counted = Counter(ndrs)
        shown = area_id in visible
        return ParticipationRow(
            area_id=area_id,
            label=label,
            registered=registered_count,
            responded=len(ndrs),
            participation=round(len(ndrs) * 100 / registered_count)
            if registered_count
            else None,
            counts=tuple((lvl, counted[lvl]) for lvl in c.NDR_ORDER) if shown else (),
            suppressed=bool(ndrs) and not shown,
        )

    return tuple(row(*entry) for entry in entries)


def _hide_until_safe(entries, by_area, visible):
    """Hide the smallest visible rows until the hidden respondents number 0 or >= 5.

    The group's final distribution is always shown, so a hidden total of 1-4
    would be recoverable by subtracting the visible rows from it. Mutates
    `visible`; ties go to the label that sorts first.
    """
    answered = [(len(by_area.get(a, [])), label, a) for a, label, _r in entries]
    answered = [entry for entry in answered if entry[0]]
    hidden = sum(n for n, _label, a in answered if a not in visible)
    candidates = sorted(
        (entry for entry in answered if entry[2] in visible),
        key=lambda entry: (entry[0], entry[1]),
    )
    for n, _label, area_id in candidates:
        if hidden == 0 or hidden >= c.MIN_GROUP_SIZE:
            break
        visible.discard(area_id)
        hidden += n


def _distribution(
    key, label, ndrs, children=(), palette=PALETTE_NDR
) -> DistributionRow:
    counted = Counter(ndrs)
    return DistributionRow(
        key=key,
        label=label,
        n=len(ndrs),
        counts=tuple((level, counted[level]) for level in c.NDR_ORDER),
        palette=palette,
        children=tuple(children),
    )


def _stats(key, label, values, *, level, variant, scale_max, children=()) -> StatsRow:
    palette = PALETTE_DOMINIO if level == c.LEVEL_DOMINIO else PALETTE_NDR
    bands = tuple(
        (upper, f"{palette}-{ndr}", c.NDR_LABELS[ndr])
        for upper, ndr in cfg.thresholds_for(level, key, variant)
    )
    return StatsRow(
        key=key,
        label=label,
        n=len(values),
        mean=round(statistics.fmean(values), 1) if values else None,
        median=statistics.median(values) if values else None,
        minimum=min(values) if values else None,
        maximum=max(values) if values else None,
        scale_max=scale_max,
        strip_bands=bands,
        children=tuple(children),
    )


def _structure(variant):
    """(categorías in order, {categoría: [dominios]}, {key: item count}) for a variant."""
    taxonomy = cfg.taxonomy_for_variant(variant)
    items = Counter()
    for cat_key, dom_key, _dim in taxonomy.values():
        items[cat_key] += 1
        items[dom_key] += 1
    categorias = [k for k in cfg.CATEGORIA_ORDER if k in items]
    dominios = {
        k: [d for d in cfg.dominios_for_categoria(k) if d in items] for k in categorias
    }
    return categorias, dominios, items, len(taxonomy)


def _valuation(assignment, scores):
    variant = assignment.variant
    categorias, dominios, items, total_items = _structure(variant)
    rows = defaultdict(list)  # (level, key) -> [(score, ndr)]
    for level, key, value, ndr in GroupScore.objects.filter(
        submission_score_id__in=[s.pk for s in scores],
        level__in=(c.LEVEL_CATEGORIA, c.LEVEL_DOMINIO),
    ).values_list("level", "key", "score", "ndr"):
        rows[(level, key)].append((value, ndr))

    def ndrs(level, key):
        return [ndr for _v, ndr in rows[(level, key)]]

    def values(level, key):
        return [v for v, _ndr in rows[(level, key)]]

    distribution, stats = [], []
    for cat in categorias:
        doms = dominios[cat]
        distribution.append(
            _distribution(
                cat,
                cfg.group_label(cat),
                ndrs(c.LEVEL_CATEGORIA, cat),
                [
                    _distribution(
                        d,
                        cfg.group_label(d),
                        ndrs(c.LEVEL_DOMINIO, d),
                        palette=PALETTE_DOMINIO,
                    )
                    for d in doms
                ],
            )
        )
        stats.append(
            _stats(
                cat,
                cfg.group_label(cat),
                values(c.LEVEL_CATEGORIA, cat),
                level=c.LEVEL_CATEGORIA,
                variant=variant,
                scale_max=items[cat] * 4,
                children=[
                    _stats(
                        d,
                        cfg.group_label(d),
                        values(c.LEVEL_DOMINIO, d),
                        level=c.LEVEL_DOMINIO,
                        variant=variant,
                        scale_max=items[d] * 4,
                    )
                    for d in doms
                ],
            )
        )
    final_distribution = _distribution(
        FINAL, "Calificación final", [s.final_ndr for s in scores]
    )
    final_stats = _stats(
        FINAL,
        "Calificación final",
        [s.final_score for s in scores],
        level=FINAL,
        variant=variant,
        scale_max=total_items * 4,
    )
    guia1 = _guia1(scores)
    return final_distribution, tuple(distribution), final_stats, tuple(stats), guia1


@dataclass(frozen=True)
class Results:
    assignment: SurveyAssignment
    size: int
    whole_size: int
    filtered: bool
    suppressed: bool
    sex: tuple[Slice, ...] = ()
    age: tuple[Slice, ...] = ()
    participation: tuple = ()
    final_distribution: object = None
    categoria_distribution: tuple = ()
    final_stats: object = None
    categoria_stats: tuple = ()
    guia1: object = None

    @property
    def empty(self) -> bool:
        return self.size == 0


def narrow(queryset, query, today, prefix=_PROFILE):
    """Apply the query's respondent filters to a queryset reaching UserProfile at `prefix`."""
    q = Q()
    if query.sex:
        q &= Q(**{f"{prefix}sex": query.sex})
    if query.area_ids:
        q &= Q(**{f"{prefix}area_id__in": query.area_ids})
    if query.location_ids:
        q &= Q(**{f"{prefix}location_id__in": query.location_ids})
    if query.age_slugs:
        ages = Q()
        for slug in query.age_slugs:
            earliest, latest = demographics.birth_date_range(
                demographics.band_by_slug(slug), today
            )
            band = Q(**{f"{prefix}date_of_birth__lte": latest})
            if earliest is not None:
                band &= Q(**{f"{prefix}date_of_birth__gte": earliest})
            ages |= band
        q &= ages
    return queryset.filter(q)


def _profile(score):
    user = score.submission.user
    return getattr(user, "profile", None) if user is not None else None


_SEXES = ((UserProfile.Sex.FEMALE, "sex-female"), (UserProfile.Sex.MALE, "sex-male"))


def _sex_slices(sexes) -> tuple[Slice, ...]:
    counts = {value: 0 for value, _ in _SEXES}
    missing = 0
    for sex in sexes:
        if sex in counts:
            counts[sex] += 1
        else:
            missing += 1
    slices = [
        Slice(value, UserProfile.Sex(value).label, counts[value], color)
        for value, color in _SEXES
    ]
    return (*slices, Slice("none", NO_DATA, missing, "none"))


def _age_slices(birth_dates, today) -> tuple[Slice, ...]:
    counts = {band.slug: 0 for band in demographics.AGE_BANDS}
    missing = 0
    for dob in birth_dates:
        band = demographics.age_band(demographics.age_on(dob, today)) if dob else None
        if band is None:
            missing += 1
        else:
            counts[band.slug] += 1
    slices = [
        Slice(b.slug, b.label, counts[b.slug], "age") for b in demographics.AGE_BANDS
    ]
    return (*slices, Slice("none", NO_DATA, missing, "none"))


def results_for(assignment, query, *, suppress_small_groups: bool) -> Results:
    today = timezone.localdate()
    base = SubmissionScore.objects.filter(submission__assignment=assignment)
    whole_size = base.count()
    scores = list(
        narrow(base, query, today)
        .select_related(f"{_PROFILE}area", f"{_PROFILE}location")
        .order_by("pk")
    )
    size = len(scores)
    filtered = query.is_filtered
    suppressed = (
        filtered
        and size > 0
        and not shows(size, whole_size, suppress=suppress_small_groups)
    )

    profiles = [_profile(s) for s in scores]
    if query.sex:
        sexes = narrow(base, replace(query, sex="", sex_slug=""), today).values_list(
            f"{_PROFILE}sex", flat=True
        )
    else:
        sexes = [p.sex if p else "" for p in profiles]
    if query.age_slugs:
        dobs = narrow(base, replace(query, age_slugs=()), today).values_list(
            f"{_PROFILE}date_of_birth", flat=True
        )
    else:
        dobs = [p.date_of_birth if p else None for p in profiles]

    participation = _participation(
        assignment,
        query,
        scores,
        today,
        group_suppressed=suppressed,
        suppress=suppress_small_groups,
    )

    valuation = {}
    if size and not suppressed:
        (
            final_distribution,
            categoria_distribution,
            final_stats,
            categoria_stats,
            guia1,
        ) = _valuation(assignment, scores)
        valuation = dict(
            final_distribution=final_distribution,
            categoria_distribution=categoria_distribution,
            final_stats=final_stats,
            categoria_stats=categoria_stats,
            guia1=guia1,
        )

    return Results(
        assignment=assignment,
        size=size,
        whole_size=whole_size,
        filtered=filtered,
        suppressed=suppressed,
        sex=_sex_slices(sexes),
        age=_age_slices(dobs, today),
        participation=participation,
        **valuation,
    )


NEUTRAL_BAND_LABEL = "Sin umbral oficial"


@dataclass(frozen=True)
class _WholeAssignment:
    """A results query with no filters: what the report always reads."""

    sex: str = ""
    age_slugs: tuple = ()
    area_ids: tuple = ()
    location_ids: tuple = ()
    is_filtered: bool = False


WHOLE_ASSIGNMENT = _WholeAssignment()


@dataclass(frozen=True)
class DimensionGroup:
    key: str
    label: str
    rows: tuple[StatsRow, ...]


@dataclass(frozen=True)
class AreaResults:
    area_id: int | None
    label: str
    n: int
    suppressed: bool
    final: DistributionRow | None = None
    categorias: tuple[DistributionRow, ...] = ()
    guia1: Guia1 | None = None


@dataclass(frozen=True)
class ReportResults:
    results: Results
    registered: int
    dimensions: tuple[DimensionGroup, ...]
    areas: tuple[AreaResults, ...]


def _guia1(scores) -> Guia1:
    return Guia1(
        none=sum(1 for s in scores if not s.guia1_event),
        event=sum(1 for s in scores if s.guia1_event and not s.guia1_positive),
        positive=sum(1 for s in scores if s.guia1_positive),
    )


def _dimensions(assignment, scores) -> tuple[DimensionGroup, ...]:
    variant = assignment.variant
    categorias, dominios, _items, _total = _structure(variant)
    dim_items = Counter(
        dim for _c, _d, dim in cfg.taxonomy_for_variant(variant).values()
    )
    values = defaultdict(list)
    for key, value in GroupScore.objects.filter(
        submission_score_id__in=[s.pk for s in scores], level=c.LEVEL_DIMENSION
    ).values_list("key", "score"):
        values[key].append(value)

    def row(dim):
        scale_max = dim_items[dim] * 4
        vals = values[dim]
        return StatsRow(
            key=dim,
            label=cfg.group_label(dim),
            n=len(vals),
            mean=round(statistics.fmean(vals), 1) if vals else None,
            median=statistics.median(vals) if vals else None,
            minimum=min(vals) if vals else None,
            maximum=max(vals) if vals else None,
            scale_max=scale_max,
            strip_bands=((scale_max, "none", NEUTRAL_BAND_LABEL),),
        )

    return tuple(
        DimensionGroup(
            key=dom,
            label=cfg.group_label(dom),
            rows=tuple(row(d) for d in cfg.dimensions_for_dominio(dom, variant)),
        )
        for cat in categorias
        for dom in dominios[cat]
    )


def _areas(assignment, scores, participation) -> tuple[AreaResults, ...]:
    company = assignment.company
    categorias, _dominios, _items, _total = _structure(assignment.variant)
    by_area = defaultdict(list)
    for score in scores:
        area = _area_of(_profile(score), company)
        by_area[area.pk if area else None].append(score)
    cat_ndrs = defaultdict(list)  # (submission_score_id, key) -> ndr
    for score_id, key, ndr in GroupScore.objects.filter(
        submission_score_id__in=[s.pk for s in scores], level=c.LEVEL_CATEGORIA
    ).values_list("submission_score_id", "key", "ndr"):
        cat_ndrs[(score_id, key)].append(ndr)

    rows = []
    for p in participation:
        area_scores = by_area.get(p.area_id, [])
        if not area_scores:
            continue
        if p.suppressed:
            rows.append(AreaResults(p.area_id, p.label, len(area_scores), True))
            continue
        ids = [s.pk for s in area_scores]
        rows.append(
            AreaResults(
                area_id=p.area_id,
                label=p.label,
                n=len(area_scores),
                suppressed=False,
                final=_distribution(
                    FINAL, "Calificación final", [s.final_ndr for s in area_scores]
                ),
                categorias=tuple(
                    _distribution(
                        cat,
                        cfg.group_label(cat),
                        [n for i in ids for n in cat_ndrs[(i, cat)]],
                    )
                    for cat in categorias
                ),
                guia1=_guia1(area_scores),
            )
        )
    return tuple(rows)


def report_results(assignment) -> ReportResults:
    """Everything the report reads: the whole assignment, small groups always hidden."""
    results = results_for(assignment, WHOLE_ASSIGNMENT, suppress_small_groups=True)
    scores = list(
        SubmissionScore.objects.filter(submission__assignment=assignment)
        .select_related(f"{_PROFILE}area")
        .order_by("pk")
    )
    registered = UserProfile.objects.filter(
        company=assignment.company, is_activated=True
    ).count()
    return ReportResults(
        results=results,
        registered=registered,
        dimensions=_dimensions(assignment, scores) if scores else (),
        areas=_areas(assignment, scores, results.participation),
    )
