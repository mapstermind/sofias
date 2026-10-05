"""The report's data: built live from the engine, frozen as JSON on publish.

`dump`/`load` round-trip exactly (tests/test_snapshot.py), so a published report
renders through the same dataclasses as a live draft.
"""

from dataclasses import asdict, dataclass, replace
from datetime import date

from django.db.models import Max, Min
from django.utils import timezone

from apps.nom035.results import (
    AreaResults,
    DimensionGroup,
    DistributionRow,
    Guia1,
    ParticipationRow,
    Slice,
    StatsRow,
    local_date,
    period_span,
    report_results,
)


@dataclass(frozen=True)
class CompanyFacts:
    name: str
    legal_name: str
    address: str
    rfc: str
    work_center: str
    industry: str
    reference_code: str


@dataclass(frozen=True)
class ReportData:
    company: CompanyFacts
    variant: str
    variant_label: str
    period_label: str
    registered: int
    responded: int
    participation_percent: int | None
    computed_on: date
    sex: tuple
    age: tuple
    participation: tuple
    final_distribution: DistributionRow | None
    final_stats: StatsRow | None
    categoria_distribution: tuple
    categoria_stats: tuple
    dimensions: tuple
    areas: tuple
    guia1: Guia1 | None


def _clamped(row):
    """StatsRow bands end at +inf, which JSON cannot hold; the strip clamps to
    scale_max anyway, so live and frozen data clamp alike."""
    if row is None:
        return None
    return replace(
        row,
        strip_bands=tuple(
            (min(upper, row.scale_max), color, label)
            for upper, color, label in row.strip_bands
        ),
        children=tuple(_clamped(ch) for ch in row.children),
    )


def build_report_data(assignment) -> ReportData:
    rr = report_results(assignment)
    r = rr.results
    company = assignment.company
    answered = assignment.submissions.filter(nom035_score__isnull=False).aggregate(
        first=Min("completed_at"), last=Max("completed_at")
    )
    return ReportData(
        company=CompanyFacts(
            name=company.name,
            legal_name=company.legal_name,
            address=company.address,
            rfc=company.rfc,
            work_center=company.work_center,
            industry=company.industry,
            reference_code=company.reference_code,
        ),
        variant=assignment.variant,
        variant_label=assignment.get_variant_display(),
        period_label=period_span(
            local_date(answered["first"]), local_date(answered["last"])
        ),
        registered=rr.registered,
        responded=r.size,
        participation_percent=round(r.size * 100 / rr.registered)
        if rr.registered
        else None,
        computed_on=timezone.localdate(),
        sex=r.sex,
        age=r.age,
        participation=r.participation,
        final_distribution=r.final_distribution,
        final_stats=_clamped(r.final_stats),
        categoria_distribution=r.categoria_distribution,
        categoria_stats=tuple(_clamped(s) for s in r.categoria_stats),
        dimensions=tuple(
            replace(g, rows=tuple(_clamped(row) for row in g.rows))
            for g in rr.dimensions
        ),
        areas=rr.areas,
        guia1=r.guia1,
    )


# ── JSON ─────────────────────────────────────────────────────────────────────


def dump(data: ReportData) -> dict:
    raw = asdict(data)
    raw["computed_on"] = data.computed_on.isoformat()
    return raw


def _tuples(value):
    return tuple(tuple(v) if isinstance(v, list) else v for v in value)


def _distribution(raw):
    if raw is None:
        return None
    return DistributionRow(
        key=raw["key"],
        label=raw["label"],
        n=raw["n"],
        counts=_tuples(raw["counts"]),
        children=tuple(_distribution(ch) for ch in raw["children"]),
    )


def _stats(raw):
    if raw is None:
        return None
    return StatsRow(
        **{
            k: raw[k]
            for k in (
                "key",
                "label",
                "n",
                "mean",
                "median",
                "minimum",
                "maximum",
                "scale_max",
            )
        },
        strip_bands=_tuples(raw["strip_bands"]),
        children=tuple(_stats(ch) for ch in raw["children"]),
    )


def _guia1(raw):
    return Guia1(**raw) if raw is not None else None


def load(raw: dict) -> ReportData:
    return ReportData(
        company=CompanyFacts(**raw["company"]),
        variant=raw["variant"],
        variant_label=raw["variant_label"],
        period_label=raw["period_label"],
        registered=raw["registered"],
        responded=raw["responded"],
        participation_percent=raw["participation_percent"],
        computed_on=date.fromisoformat(raw["computed_on"]),
        sex=tuple(Slice(**s) for s in raw["sex"]),
        age=tuple(Slice(**s) for s in raw["age"]),
        participation=tuple(
            ParticipationRow(**{**p, "counts": _tuples(p["counts"])})
            for p in raw["participation"]
        ),
        final_distribution=_distribution(raw["final_distribution"]),
        final_stats=_stats(raw["final_stats"]),
        categoria_distribution=tuple(
            _distribution(d) for d in raw["categoria_distribution"]
        ),
        categoria_stats=tuple(_stats(s) for s in raw["categoria_stats"]),
        dimensions=tuple(
            DimensionGroup(
                key=g["key"], label=g["label"], rows=tuple(_stats(r) for r in g["rows"])
            )
            for g in raw["dimensions"]
        ),
        areas=tuple(
            AreaResults(
                area_id=a["area_id"],
                label=a["label"],
                n=a["n"],
                suppressed=a["suppressed"],
                final=_distribution(a["final"]),
                categorias=tuple(_distribution(d) for d in a["categorias"]),
                guia1=_guia1(a["guia1"]),
            )
            for a in raw["areas"]
        ),
        guia1=_guia1(raw["guia1"]),
    )


def data_for(report) -> ReportData:
    if report.status == report.Status.PUBLISHED and report.snapshot is not None:
        return load(report.snapshot)
    return build_report_data(report.assignment)
