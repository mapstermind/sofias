# NOM-035 Results Report Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** An Administrador writes, previews and publishes one frozen Reporte de
resultados per closed NOM-035 assignment; the company's Ejecutivo principal reads
it on the platform and downloads it as a letter-size PDF.

**Architecture:** `apps/nom035/results.py` gains a `report_results(assignment)`
read that adds dimensión and per-área aggregates to the whole-assignment
`Results`, always under the small-group rule. `apps/reports` (registered by this
plan) turns that into a `ReportData` dataclass, serializes it to a JSON snapshot
on publish, and renders it through an ordered section registry into one set of
partials shared by the screen page and the WeasyPrint PDF. Report partials use
semantic classes from a plain stylesheet (`static/css/report.css`) so the PDF
does not depend on WeasyPrint parsing Tailwind; only the reused chart components
carry Tailwind classes, which Task 1's spike settles.

**Tech Stack:** Django 6.0, PostgreSQL 17, pytest + pytest-django, Tailwind v4
(screen), WeasyPrint (PDF), Source Serif 4 / Source Sans 3 (bundled).

**Spec:** [`docs/platform/nom-035-report.md`](../nom-035-report.md)

## Global Constraints

- Everything a user sees is Spanish; code, comments, identifiers English.
- Every model field has an explicit lowercase Spanish `verbose_name`; every model a Spanish `Meta.verbose_name`/`verbose_name_plural`; the `apps.reports` `AppConfig` a Spanish `verbose_name` (`assert_explicit_labels` enforces the model part).
- Risk is stated as distributions; never attach an NDR level to a mean, median or company.
- The small-group rule (`shows`, `_hide_until_safe`, `MIN_GROUP_SIZE = 5`) always applies to report data, whoever views it.
- Only a closed (`SurveyAssignment.Status.CLOSED`) assignment with at least one scored questionnaire can be published.
- Required to publish: `issued_in`, `activities_summary`, `evaluator_name`, `evaluator_license`, `conclusions`.
- Readers: Administrador needs `can_manage_surveys` + `can_view_insights`; Ejecutivo principal needs `can_view_insights` and sees only published reports of their own company; anything else is 404 (403 for a missing permission, as the results views do).
- Percents print as `N %` (number, non-breaking space, `%`), rounded by largest remainder within a row.
- Report partials use breakpoints up to `md:` only; layout written mobile-first; no horizontal scroll at 360 px.
- Never commit: each task ends at a green suite with an uncommitted diff, the list of touched files, and a proposed commit message, then waits for the user (CLAUDE.md, gate 4). This holds for subagents.
- Any change under `templates/` or Tailwind-bearing files ends with `npm run build:css`.
- Do not edit anything under `docs/adr/`.

## Review Focus

1. **A Guía II (`small`) assignment** — no Entorno organizacional categoría, fewer dominios; every section, the matrix lookup and the method annex must render without a `KeyError`. Pinned in Task 5 (`test_matrix_covers_every_dominio_of_both_variants`), Task 7 (`test_small_variant_report_renders`) and Task 10.
2. **Scores recomputed after publishing** — the published page must not change. Pinned in Task 9 (`test_published_report_ignores_later_scores`).
3. **Administrador text with line breaks or HTML** — paragraphs kept, markup escaped. Pinned in Task 7 (`test_admin_text_is_escaped_and_keeps_paragraphs`).
4. **Respondents with no área, or whose account was deleted** — counted in the company sections, grouped as "Sin área", never crash the snapshot. Pinned in Task 2 (`test_report_results_sin_area_and_deleted_user`).
5. **Double submit** — *Publicar* on a published report and *Despublicar* on a draft are no-ops with a message, never a 500 or a second snapshot. Pinned in Task 9 (`test_publish_and_unpublish_are_idempotent`).

---

### Task 1: WeasyPrint spike (throwaway) and dependency

Settles the spec's first open question. The spike code is deleted; only the
dependency, the setup note and the recorded outcome survive.

**Files:**
- Modify: `pyproject.toml`, `poetry.lock` (via `poetry add`)
- Modify: `.claude/CLAUDE.md` (setup section)
- Modify: this plan (record the outcome under Task 1)
- Scratch only: `$SCRATCH/spike_pdf.py` (the session scratchpad; never in the repo)

**Interfaces:**
- Produces: `weasyprint` importable; a recorded decision **CHARTS_CSS = "output.css"** or **CHARTS_CSS = "shim"**, and **FONT_FORMAT = "variable"** or **"static"**, used by Task 11.

- [ ] **Step 1: System libraries.** Ask the user to run (needs sudo): `! sudo apt install -y libpango-1.0-0 libpangoft2-1.0-0 libharfbuzz-subset0`
- [ ] **Step 2: Add the dependency.** Run: `poetry add weasyprint` — expect it in `[tool.poetry.dependencies]` (or `[project].dependencies`, whichever `pyproject.toml` uses).
- [ ] **Step 3: Fetch candidate fonts into scratch.**

```bash
mkdir -p "$SCRATCH/fonts" && cd "$SCRATCH/fonts"
curl -fsSLO "https://github.com/google/fonts/raw/main/ofl/sourceserif4/SourceSerif4%5Bopsz,wght%5D.ttf"
curl -fsSLO "https://github.com/google/fonts/raw/main/ofl/sourcesans3/SourceSans3%5Bwght%5D.ttf"
curl -fsSLO "https://github.com/google/fonts/raw/main/ofl/sourceserif4/OFL.txt"
```

- [ ] **Step 4: Write the spike.** `$SCRATCH/spike_pdf.py`:

```python
import os, sys
sys.path.insert(0, "/home/mapstermind/projects/sofias")
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
import django; django.setup()
from pathlib import Path
from django.template import Context, Template
from weasyprint import CSS, HTML
from apps.nom035.results import Slice

SCRATCH = Path(os.environ["SCRATCH"])
slices = [Slice(k, k.title(), v, f"ndr-{k}") for k, v in
          [("nulo", 5), ("bajo", 7), ("medio", 3), ("alto", 2), ("muy_alto", 1)]]
html = Template("""{% load charts %}<html><body>
<h1 style="font-family:'Serif'; font-weight:600">Título con acentos: ñ á é</h1>
<p style="font-family:'Sans'">Texto sans 400</p><p style="font-family:'Sans'; font-weight:700">Sans 700</p>
{% stacked_bar slices legend=True %}{% level_columns slices size="lg" %}
{% range_strip bands 100 points %}</body></html>""").render(Context({
    "slices": slices,
    "bands": [(20, "ndr-nulo", "Nulo"), (45, "ndr-bajo", "Bajo"), (70, "ndr-medio", "Medio"),
              (90, "ndr-alto", "Alto"), (100, "ndr-muy_alto", "Muy alto")],
    "points": [("min", "Mín", 10), ("median", "Mediana", 40), ("mean", "Prom.", 42.5), ("max", "Máx", 95)],
}))
fonts = CSS(string=f"""
@font-face {{ font-family: 'Serif'; src: url('file://{SCRATCH}/fonts/SourceSerif4[opsz,wght].ttf'); font-weight: 200 900; }}
@font-face {{ font-family: 'Sans'; src: url('file://{SCRATCH}/fonts/SourceSans3[wght].ttf'); font-weight: 200 900; }}
@page {{ size: letter; margin: 2cm }}""")
HTML(string=html).write_pdf(
    SCRATCH / "spike.pdf",
    stylesheets=["/home/mapstermind/projects/sofias/static/css/output.css", fonts],
)
print("ok")
```

- [ ] **Step 5: Run and look.** Run: `SCRATCH=<scratchpad> python "$SCRATCH/spike_pdf.py" && pdftoppm -r 80 -png "$SCRATCH/spike.pdf" "$SCRATCH/spike"`; open the PNG with the Read tool. Check: (a) chart segments are colored green/amber/orange/red, not black or missing; (b) the column chart's bars have heights; (c) the strip's bands and labels show; (d) the serif heading is bold (600) and differs visibly from the sans 400 line; (e) accents render; (f) WeasyPrint's stderr warnings (record any `Ignored` lines about `@layer`, `oklch`, `@property`).
- [ ] **Step 6: Record the outcome** directly below this checklist in this plan, e.g. `Outcome: CHARTS_CSS = "output.css" (colors and layers render); FONT_FORMAT = "variable" (600 renders bold).` If charts are uncolored → `CHARTS_CSS = "shim"`. If weight 600 renders like 400 → `FONT_FORMAT = "static"` and note the static font source used (Adobe releases: `adobe-fonts/source-serif`, `adobe-fonts/source-sans` release zips, `TTF/` folder).
- [ ] **Step 7: Setup note.** In `.claude/CLAUDE.md`, under `## PostgreSQL Setup`'s code block, add a sibling section:

```markdown
## PDF rendering setup

The report PDF is rendered by WeasyPrint, which needs Pango:

```bash
sudo apt install -y libpango-1.0-0 libpangoft2-1.0-0 libharfbuzz-subset0
```
```

- [ ] **Step 8: Verify and hand back.** Run: `pytest && ruff check . && ruff format --check .` — expect green. Delete nothing in the repo (the spike lived in scratch). Stop; list files (`pyproject.toml`, `poetry.lock`, `.claude/CLAUDE.md`, this plan); propose: `build: add WeasyPrint for the NOM-035 report PDF`.

Outcome: _(filled by Step 6)_

---

### Task 2: Report aggregates in `apps/nom035`

**Files:**
- Create: `apps/nom035/tests/factories.py`
- Modify: `apps/nom035/tests/test_results.py` (import `make_assignment`, `make_score` from factories; delete the local copies)
- Modify: `conftest.py` (add `nom035_survey` fixture; delete it from `test_results.py`)
- Modify: `apps/nom035/results.py`
- Test: `apps/nom035/tests/test_report_results.py`

**Interfaces:**
- Produces (in `apps/nom035/results.py`):
  - `WHOLE_ASSIGNMENT` — a query object accepted by `results_for` with no filters.
  - `@dataclass(frozen=True) class DimensionGroup: key: str; label: str; rows: tuple[StatsRow, ...]` — one per dominio, rows are its dimensiones.
  - `@dataclass(frozen=True) class AreaResults: area_id: int | None; label: str; n: int; suppressed: bool; final: DistributionRow | None; categorias: tuple[DistributionRow, ...]; guia1: Guia1 | None`
  - `@dataclass(frozen=True) class ReportResults: results: Results; registered: int; dimensions: tuple[DimensionGroup, ...]; areas: tuple[AreaResults, ...]`
  - `def report_results(assignment) -> ReportResults`
  - `NEUTRAL_BAND_LABEL = "Sin umbral oficial"`

- [ ] **Step 1: Move the test helpers.** Create `apps/nom035/tests/factories.py` holding `make_assignment` and `make_score` exactly as they are in `test_results.py` (lines 30–73, with their imports). In `test_results.py` replace them with `from apps.nom035.tests.factories import make_assignment, make_score`. Move the `nom035_survey` fixture to root `conftest.py` under the survey fixture chain:

```python
@pytest.fixture
def nom035_survey(db):
    """The NOM-035 survey row (key "nom035"), without modules — scores are made directly."""
    from apps.surveys.models import Survey

    return Survey.objects.create(
        key="nom035", title="NOM-035", status=Survey.Status.PUBLISHED
    )
```

Run: `pytest apps/nom035` — expect PASS (pure move).

- [ ] **Step 2: Write the failing tests.** `apps/nom035/tests/test_report_results.py`:

```python
import pytest

from apps.nom035 import _nom035_scoring as cfg
from apps.nom035 import constants as c
from apps.nom035.results import NEUTRAL_BAND_LABEL, report_results
from apps.nom035.tests.factories import make_assignment, make_score

pytestmark = pytest.mark.django_db


def _cat(key, score, ndr):
    return (c.LEVEL_CATEGORIA, key, score, ndr)


@pytest.fixture
def two_areas(make_company, make_user_with_profile, make_area, nom035_survey):
    """Ops: 6 respondents (3 Alto in Ambiente, 1 Guía I positive); Dirección: 2."""
    company = make_company()
    ops = make_area(company, name="Operaciones")
    dir_ = make_area(company, name="Dirección")
    assignment = make_assignment(company, nom035_survey, variant="large")
    for i in range(6):
        user = make_user_with_profile(email=f"o{i}@x.mx", company=company, area=ops)
        ndr = c.NDR_ALTO if i < 3 else c.NDR_NULO
        make_score(
            assignment,
            user,
            final_ndr=ndr,
            guia1_event=i == 0,
            guia1_positive=i == 0,
            groups=[_cat(cfg.CAT_AMBIENTE, 12 if i < 3 else 2, ndr)],
        )
    for i in range(2):
        user = make_user_with_profile(email=f"d{i}@x.mx", company=company, area=dir_)
        make_score(assignment, user, groups=[_cat(cfg.CAT_AMBIENTE, 2, c.NDR_NULO)])
    return {"assignment": assignment, "ops": ops, "dir": dir_}


def test_report_results_is_the_whole_assignment_suppressed(two_areas):
    data = report_results(two_areas["assignment"])
    assert data.results.size == 8
    assert data.results.filtered is False
    assert data.registered == 8


def test_area_results_follow_participation_visibility(two_areas):
    data = report_results(two_areas["assignment"])
    by_label = {a.label: a for a in data.areas}
    # Dirección (2) is hidden; hiding it leaves 2 hidden, so Operaciones hides too.
    assert by_label["Dirección"].suppressed is True
    assert by_label["Operaciones"].suppressed is True
    assert by_label["Dirección"].final is None
    assert by_label["Dirección"].categorias == ()
    assert by_label["Dirección"].guia1 is None


def test_area_results_numbers_when_visible(
    make_company, make_user_with_profile, make_area, nom035_survey
):
    company = make_company()
    a = make_area(company, name="A")
    b = make_area(company, name="B")
    assignment = make_assignment(company, nom035_survey, variant="large")
    for area, prefix in ((a, "a"), (b, "b")):
        for i in range(5):
            user = make_user_with_profile(
                email=f"{prefix}{i}@x.mx", company=company, area=area
            )
            make_score(
                assignment,
                user,
                final_ndr=c.NDR_MEDIO if prefix == "a" else c.NDR_BAJO,
                guia1_event=prefix == "a" and i == 0,
                groups=[_cat(cfg.CAT_AMBIENTE, 9, c.NDR_MEDIO)],
            )
    data = report_results(assignment)
    row = next(x for x in data.areas if x.label == "A")
    assert row.suppressed is False
    assert row.n == 5
    assert dict(row.final.counts)[c.NDR_MEDIO] == 5
    assert [cat.key for cat in row.categorias][0] == cfg.CAT_AMBIENTE
    assert dict(row.categorias[0].counts)[c.NDR_MEDIO] == 5
    assert (row.guia1.none, row.guia1.event, row.guia1.positive) == (4, 1, 0)


def test_dimension_groups_follow_the_variant(two_areas):
    data = report_results(two_areas["assignment"])
    dominios = [g.key for g in data.dimensions]
    assert dominios[0] == cfg.DOM_CONDICIONES
    assert cfg.DOM_PERTENENCIA in dominios  # large variant has Entorno


def test_dimension_rows_use_one_neutral_band(make_company, nom035_survey):
    company = make_company()
    assignment = make_assignment(company, nom035_survey, variant="large")
    dim = cfg.dimensions_for_dominio(cfg.DOM_CONDICIONES, "large")[0]
    for value in (1, 3, 8):
        make_score(assignment, groups=[(c.LEVEL_DIMENSION, dim, value, "")])
    data = report_results(assignment)
    row = data.dimensions[0].rows[0]
    assert row.key == dim
    assert (row.n, row.minimum, row.median, row.maximum) == (3, 1, 3, 8)
    assert row.mean == 4.0
    assert row.strip_bands == ((row.scale_max, "none", NEUTRAL_BAND_LABEL),)
    items = sum(
        1 for _c, _d, d in cfg.taxonomy_for_variant("large").values() if d == dim
    )
    assert row.scale_max == items * 4


def test_small_variant_has_no_entorno_dimensions(make_company, nom035_survey):
    company = make_company()
    assignment = make_assignment(company, nom035_survey, variant="small")
    make_score(assignment)
    keys = [g.key for g in report_results(assignment).dimensions]
    assert cfg.DOM_RECONOCIMIENTO not in keys
    assert cfg.DOM_PERTENENCIA not in keys


def test_report_results_sin_area_and_deleted_user(
    make_company, make_user_with_profile, nom035_survey
):
    company = make_company()
    assignment = make_assignment(company, nom035_survey)
    for i in range(5):
        make_score(
            assignment, make_user_with_profile(email=f"n{i}@x.mx", company=company)
        )
    make_score(assignment, user=None)  # deleted account
    data = report_results(assignment)
    assert data.results.size == 6
    assert [a.label for a in data.areas] == ["Sin área"]
    assert data.areas[0].n == 6


def test_report_results_query_count_does_not_grow(
    two_areas, make_user_with_profile, django_assert_max_num_queries
):
    with django_assert_max_num_queries(20):
        report_results(two_areas["assignment"])
```


- [ ] **Step 3: Run to verify it fails.** Run: `pytest apps/nom035/tests/test_report_results.py -v` — expect FAIL: `ImportError: cannot import name 'NEUTRAL_BAND_LABEL'`.

- [ ] **Step 4: Implement.** Append to `apps/nom035/results.py`:

```python
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
    dim_items = Counter(dim for _c, _d, dim in cfg.taxonomy_for_variant(variant).values())
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
```

Also refactor `_valuation` to use `_guia1(scores)` instead of its inline `Guia1(...)` (same values; keeps one definition).

- [ ] **Step 5: Run to verify it passes.** Run: `pytest apps/nom035 -v` — expect PASS. If `test_area_results_follow_participation_visibility` fails because Operaciones is visible, re-check: Dirección (2) hidden → hidden total 2 → `_hide_until_safe` hides Operaciones (6). The assertion is correct; fix the code, not the test.
- [ ] **Step 6: Verify and hand back.** Run: `pytest && ruff check . && ruff format .` — expect green. Stop; list files; propose: `feat(nom035): dimensión and per-área aggregates for the report`.

---

### Task 3: `apps.reports` registration, models and `Company` fields

**Files:**
- Modify: `apps/reports/apps.py`, `config/settings.py` (`INSTALLED_APPS`)
- Modify: `apps/reports/models.py`, `apps/reports/admin.py`
- Create: `apps/reports/migrations/0001_initial.py` (generated)
- Modify: `apps/accounts/models.py` (`Company`), `apps/accounts/admin.py` (`CompanyAdmin`)
- Create: `apps/accounts/migrations/00NN_company_industry_work_center.py` (generated)
- Create: `apps/reports/tests/__init__.py`, `apps/reports/tests/test_models.py`

**Interfaces:**
- Produces: `Report` (fields per spec Schema plus `created_at`, `updated_at`), `Report.Status.DRAFT/PUBLISHED`, `Report.signatories` (related name), `ReportSignatory(report, title, name, order)`, `Company.industry`, `Company.work_center`, `Report.headcount_total` property (sum of the non-null headcounts, or `None` when all are null).

- [ ] **Step 1: Write the failing tests.** `apps/reports/tests/test_models.py`:

```python
import pytest

from apps.reports.models import Report, ReportSignatory
from apps.surveys.models import SurveyAssignment

pytestmark = pytest.mark.django_db


@pytest.fixture
def assignment(company, nom035_survey):
    return SurveyAssignment.objects.create(
        company=company, survey=nom035_survey, variant="large"
    )


def test_reports_app_labels_are_spanish(assert_explicit_labels):
    assert_explicit_labels("reports")


def test_company_report_fields_have_labels(assert_explicit_labels):
    assert_explicit_labels("accounts")


def test_report_defaults_to_draft_without_snapshot(assignment):
    report = Report.objects.create(assignment=assignment)
    assert report.status == Report.Status.DRAFT
    assert report.snapshot is None
    assert report.published_at is None


def test_headcount_total(assignment):
    report = Report(assignment=assignment)
    assert report.headcount_total is None
    report.headcount_in_person = 10
    report.headcount_hybrid = 4
    assert report.headcount_total == 14


def test_signatories_are_ordered(assignment):
    report = Report.objects.create(assignment=assignment)
    ReportSignatory.objects.create(report=report, title="B", name="Y", order=2)
    ReportSignatory.objects.create(report=report, title="A", name="X", order=1)
    assert [s.title for s in report.signatories.all()] == ["A", "B"]


def test_app_verbose_name():
    from django.apps import apps

    assert apps.get_app_config("reports").verbose_name == "Reportes"
```

- [ ] **Step 2: Run to verify it fails.** Run: `pytest apps/reports -v` — expect FAIL (app not installed / import error).
- [ ] **Step 3: Register the app.** `apps/reports/apps.py`:

```python
from django.apps import AppConfig


class ReportsConfig(AppConfig):
    name = "apps.reports"
    label = "reports"
    verbose_name = "Reportes"
    default_auto_field = "django.db.models.BigAutoField"
```

Add `"apps.reports",` after `"apps.nom035",` in `INSTALLED_APPS`.

- [ ] **Step 4: Models.** `apps/reports/models.py`:

```python
from django.conf import settings
from django.db import models


class Report(models.Model):
    class Status(models.TextChoices):
        DRAFT = "draft", "Borrador"
        PUBLISHED = "published", "Publicado"

    assignment = models.OneToOneField(
        "surveys.SurveyAssignment",
        on_delete=models.CASCADE,
        related_name="report",
        verbose_name="asignación",
    )
    status = models.CharField(
        "estado", max_length=10, choices=Status.choices, default=Status.DRAFT
    )
    snapshot = models.JSONField("datos publicados", null=True, blank=True)
    published_at = models.DateTimeField("fecha de publicación", null=True, blank=True)
    published_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="+",
        verbose_name="publicado por",
    )
    issued_in = models.CharField("lugar de emisión", max_length=120, blank=True)
    activities_summary = models.TextField("principales actividades", blank=True)
    headcount_in_person = models.PositiveIntegerField(
        "personal presencial", null=True, blank=True
    )
    headcount_home_office = models.PositiveIntegerField(
        "personal en home office", null=True, blank=True
    )
    headcount_hybrid = models.PositiveIntegerField(
        "personal híbrido", null=True, blank=True
    )
    evaluator_name = models.CharField(
        "responsable de la evaluación", max_length=200, blank=True
    )
    evaluator_license = models.CharField(
        "cédula profesional", max_length=40, blank=True
    )
    additional_recommendations = models.TextField(
        "recomendaciones adicionales", blank=True
    )
    conclusions = models.TextField("conclusiones", blank=True)
    created_at = models.DateTimeField("fecha de alta", auto_now_add=True)
    updated_at = models.DateTimeField("última actualización", auto_now=True)

    class Meta:
        verbose_name = "reporte"
        verbose_name_plural = "reportes"

    def __str__(self):
        return f"Reporte de {self.assignment}"

    @property
    def headcount_total(self):
        counts = [
            n
            for n in (
                self.headcount_in_person,
                self.headcount_home_office,
                self.headcount_hybrid,
            )
            if n is not None
        ]
        return sum(counts) if counts else None


class ReportSignatory(models.Model):
    report = models.ForeignKey(
        Report,
        on_delete=models.CASCADE,
        related_name="signatories",
        verbose_name="reporte",
    )
    title = models.CharField("cargo", max_length=200)
    name = models.CharField("nombre", max_length=200)
    order = models.PositiveSmallIntegerField("orden", default=0)

    class Meta:
        verbose_name = "responsable de la empresa"
        verbose_name_plural = "responsables de la empresa"
        ordering = ("order", "pk")

    def __str__(self):
        return f"{self.title}: {self.name}"
```

`apps/reports/admin.py` — read-only inspection for operators:

```python
from django.contrib import admin

from apps.reports.models import Report, ReportSignatory


class ReportSignatoryInline(admin.TabularInline):
    model = ReportSignatory
    extra = 0


@admin.register(Report)
class ReportAdmin(admin.ModelAdmin):
    list_display = ("assignment", "status", "published_at")
    list_filter = ("status",)
    readonly_fields = ("snapshot", "published_at", "published_by")
    inlines = [ReportSignatoryInline]
```

- [ ] **Step 5: Company fields.** In `Company`, after `address`:

```python
    industry = models.CharField("actividad principal", max_length=255, blank=True)
    work_center = models.CharField("centro de trabajo", max_length=255, blank=True)
```

In `CompanyAdmin` nothing else is needed: with no `fields`/`fieldsets` declared, the change form shows every editable field. Confirm by opening `/admin/accounts/company/<id>/change/` in Task 12's manual pass.

- [ ] **Step 6: Migrations.** Run: `python manage.py makemigrations accounts reports` then `python manage.py migrate`. Expect `0001_initial` for reports and one accounts migration.
- [ ] **Step 7: Run tests.** Run: `pytest apps/reports apps/accounts apps/core/tests/test_localization.py -v` — expect PASS. `test_every_project_app_is_covered_by_the_label_guard` must pass now that `reports` is registered; if it lists `reports`, the guard expects an explicit label test — add `"reports"` wherever that test enumerates covered apps.
- [ ] **Step 8: Verify and hand back.** Run: `pytest && ruff check . && ruff format . && python manage.py check` — green. Stop; list files; propose: `feat(reports): register apps.reports with Report and ReportSignatory`.

---

### Task 4: Fixed content and the norm's action criteria

**Files:**
- Move (git): `docs/temporal/Ejemplo Reporte Resultados.md` and `docs/temporal/Interpretación de Riesgo.md` → `docs/internal/report-references/` (only if the user approved — see the handoff question; otherwise read them from `docs/temporal/` and leave the files untouched)
- Modify: `apps/nom035/_nom035_scoring.py` (`_ACTION_TEXT`, its comment)
- Create: `apps/reports/content.py`
- Test: `apps/reports/tests/test_content.py`, `apps/nom035/tests/test_config.py` (add one test)

**Interfaces:**
- Produces (in `apps/reports/content.py`):
  - `PROVIDER_NAME: str`, `CONFIDENTIALITY_NOTICE: str`, `OBJECTIVE_PLACEHOLDER: str`
  - `RECOMMENDATIONS: dict[str, dict[str, str]]` — `{dominio_key: {ndr_level: text}}` for levels `medio`, `alto`, `muy_alto`
  - `GLOSSARY: tuple[tuple[str, str], ...]` — `(term, definition)`
  - `LFT_ARTICLES: tuple[tuple[str, str], ...]` — `(heading, text)`; article 43's fractions joined with `\n`
- Changes: `cfg.action_text(ndr)` returns the norm's verbatim "Necesidad de acción" text.

- [ ] **Step 1: Write the failing tests.** In `apps/nom035/tests/test_config.py` add:

```python
def test_action_text_is_the_norms_wording():
    # Guias de Referencia.md, "Tabla - Criterios para la toma de acciones".
    assert cfg.action_text(c.NDR_NULO) == (
        "El riesgo resulta despreciable por lo que no se requieren medidas adicionales."
    )
    assert cfg.action_text(c.NDR_MEDIO).startswith(
        "Se requiere revisar la política de prevención de riesgos psicosociales"
    )
    assert "área" not in " ".join(cfg.action_text(n) for n in c.NDR_ORDER)
```

(Use the module's existing `cfg`/`c` import names.) `apps/reports/tests/test_content.py`:

```python
from apps.nom035 import _nom035_scoring as cfg
from apps.nom035 import constants as c
from apps.reports import content


def test_matrix_covers_every_dominio_of_both_variants():
    for variant in ("small", "large"):
        dominios = {d for _c, d, _dim in cfg.taxonomy_for_variant(variant).values()}
        for dominio in dominios:
            assert set(content.RECOMMENDATIONS[dominio]) == {
                c.NDR_MEDIO,
                c.NDR_ALTO,
                c.NDR_MUY_ALTO,
            }, dominio
            assert all(content.RECOMMENDATIONS[dominio].values())


def test_fixed_text_is_present():
    assert content.PROVIDER_NAME
    assert content.PROVIDER_NAME in content.CONFIDENTIALITY_NOTICE
    assert content.OBJECTIVE_PLACEHOLDER
    terms = [term for term, _ in content.GLOSSARY]
    assert "Violencia laboral" in terms
    assert [h for h, _ in content.LFT_ARTICLES] == [
        "Artículo 43",
        "Artículo 473",
        "Artículo 474",
        "Artículo 475",
    ]
```

- [ ] **Step 2: Run to verify it fails.** Run: `pytest apps/reports/tests/test_content.py apps/nom035/tests/test_config.py -v` — expect FAIL (`ModuleNotFoundError: apps.reports.content`; action-text assertion).
- [ ] **Step 3: Action criteria.** In `_nom035_scoring.py` replace `_ACTION_TEXT` with the five rows of `Guias de Referencia.md` lines 242–246, verbatim (Muy alto … Nulo), and replace the comment above it with:

```python
# ── "Necesidad de acción" per NDR level ─────────────────────────────────────
# Verbatim from Guias de Referencia.md, "Tabla - Criterios para la toma de
# acciones" (identical in Guía II and Guía III). The report prints the row of
# every level at least one worker reached; see docs/platform/nom-035-report.md.
```

Then `grep -rn "action_text\|_ACTION_TEXT" apps templates docs/platform` and update any test or doc sentence still describing the área-framed wording (`nom-035-analytics.md` may mention it; fix the sentence, keep the doc's present tense).

- [ ] **Step 4: Content module.** Create `apps/reports/content.py`. Transcribe verbatim from `Ejemplo Reporte Resultados.md` (path per the Files note):
  - `RECOMMENDATIONS` — the table *"Recomendaciones según Riesgo Identificado"*: one entry per row, keyed by the engine's dominio constant (`cfg.DOM_CONDICIONES`, `cfg.DOM_CARGA`, `cfg.DOM_CONTROL`, `cfg.DOM_JORNADA`, `cfg.DOM_INTERFERENCIA`, `cfg.DOM_LIDERAZGO`, `cfg.DOM_RELACIONES`, `cfg.DOM_VIOLENCIA`, `cfg.DOM_RECONOCIMIENTO`, `cfg.DOM_PERTENENCIA`); column 3 → `c.NDR_MEDIO`, column 4 → `c.NDR_ALTO`, column 5 → `c.NDR_MUY_ALTO`. Fix only evident typos (`trabajo‑familia` non-breaking hyphen → `trabajo-familia`) and keep the wording otherwise.
  - `GLOSSARY` — every bold term from *"Acontecimiento traumático severo"* through *"Violencia laboral"*, in document order, term without the trailing colon.
  - `LFT_ARTICLES` — articles 43 (intro + fractions I–VI, one per line), 473, 474, 475.
  - `CONFIDENTIALITY_NOTICE` — the paragraph under *"Política de Confidencialidad/Manejo de Datos y Aviso de Privacidad"* plus the following paragraph about the STPS procedures, with `NOMBRE NEGOCIO` replaced by `{PROVIDER_NAME}` via an f-string.
  - `PROVIDER_NAME = "SOFIA-S"` — confirm with the user at handoff (Open item A).
  - `OBJECTIVE_PLACEHOLDER = "Texto del objetivo pendiente de definir por la persona responsable de la evaluación."`

Module docstring:

```python
"""Fixed report content: consultancy text shared by every report.

Transcribed from the report template in docs/internal/report-references/. The
recommendations matrix is consultancy content, not part of the norm; the norm's
own action criteria live in apps/nom035 (`action_text`).
"""
```

- [ ] **Step 5: Run to verify it passes.** Run: `pytest apps/reports apps/nom035 -v` — PASS.
- [ ] **Step 6: Verify and hand back.** `pytest && ruff check . && ruff format .` — green. Stop; list files; propose: `feat(reports): fixed report content and the norm's action criteria`.

---

### Task 5: `ReportData` and the snapshot

**Files:**
- Create: `apps/reports/snapshot.py`
- Test: `apps/reports/tests/test_snapshot.py`
- Create: `apps/reports/tests/conftest.py` (shared report fixtures)

**Interfaces:**
- Consumes: `report_results(assignment) -> ReportResults`, the nom035 dataclasses, `assignment_options` (for the period label).
- Produces (in `apps/reports/snapshot.py`):

```python
@dataclass(frozen=True)
class CompanyFacts:
    legal_name: str
    address: str
    rfc: str
    work_center: str
    industry: str
    reference_code: str

@dataclass(frozen=True)
class ReportData:
    company: CompanyFacts
    variant: str            # "small" | "large"
    variant_label: str      # "Guía II" | "Guía III"
    period_label: str       # assignment_label(...) text
    registered: int
    responded: int
    participation_percent: int | None
    computed_on: date
    sex: tuple[Slice, ...]
    age: tuple[Slice, ...]
    participation: tuple[ParticipationRow, ...]
    final_distribution: DistributionRow | None
    final_stats: StatsRow | None
    categoria_distribution: tuple[DistributionRow, ...]
    categoria_stats: tuple[StatsRow, ...]
    dimensions: tuple[DimensionGroup, ...]
    areas: tuple[AreaResults, ...]
    guia1: Guia1 | None

def build_report_data(assignment) -> ReportData
def dump(data: ReportData) -> dict      # JSON-safe
def load(raw: dict) -> ReportData
def data_for(report) -> ReportData      # snapshot when published, else live
```

- [ ] **Step 1: Shared fixtures.** `apps/reports/tests/conftest.py`:

```python
import pytest

from apps.nom035 import _nom035_scoring as cfg
from apps.nom035 import constants as c
from apps.nom035.tests.factories import make_assignment, make_score
from apps.surveys.models import SurveyAssignment


@pytest.fixture
def scored_assignment(company, make_user_with_profile, make_area, nom035_survey):
    """A closed Guía III assignment: 6 in Operaciones, 5 in Ventas, 1 with no área."""
    company.industry = "Manufactura"
    company.work_center = "Planta Norte"
    company.save()
    assignment = make_assignment(company, nom035_survey, variant="large")
    specs = [("Operaciones", 6, c.NDR_ALTO), ("Ventas", 5, c.NDR_BAJO)]
    for name, count, ndr in specs:
        area = make_area(company, name=name)
        for i in range(count):
            user = make_user_with_profile(
                email=f"{name[:3].lower()}{i}@x.mx", company=company, area=area
            )
            make_score(
                assignment,
                user,
                final_score=90,
                final_ndr=ndr,
                groups=[
                    (c.LEVEL_CATEGORIA, cfg.CAT_AMBIENTE, 12, ndr),
                    (c.LEVEL_DOMINIO, cfg.DOM_CONDICIONES, 12, ndr),
                    (c.LEVEL_DOMINIO, cfg.DOM_LIDERAZGO, 18, c.NDR_MUY_ALTO),
                ],
            )
    make_score(
        assignment,
        make_user_with_profile(email="solo@x.mx", company=company),
        final_ndr=c.NDR_NULO,
    )
    assignment.status = SurveyAssignment.Status.CLOSED
    assignment.save()
    return assignment
```

- [ ] **Step 2: Write the failing tests.** `apps/reports/tests/test_snapshot.py`:

```python
import json

import pytest

from apps.nom035 import constants as c
from apps.reports.models import Report
from apps.reports.snapshot import build_report_data, data_for, dump, load

pytestmark = pytest.mark.django_db


def test_build_report_data_facts(scored_assignment):
    data = build_report_data(scored_assignment)
    assert data.company.industry == "Manufactura"
    assert data.company.work_center == "Planta Norte"
    assert data.variant == "large"
    assert data.variant_label == "Guía III"
    assert data.responded == 12
    assert data.registered == 12
    assert data.participation_percent == 100
    assert data.final_distribution.n == 12


def test_round_trip_is_lossless(scored_assignment):
    data = build_report_data(scored_assignment)
    raw = json.loads(json.dumps(dump(data)))  # what a JSONField stores
    assert load(raw) == data


def test_infinite_band_is_clamped_for_json(scored_assignment):
    raw = dump(build_report_data(scored_assignment))
    text = json.dumps(raw, allow_nan=False)  # raises on inf
    assert "Infinity" not in text


def test_empty_assignment(company, nom035_survey):
    from apps.nom035.tests.factories import make_assignment

    data = build_report_data(make_assignment(company, nom035_survey))
    assert data.responded == 0
    assert data.final_distribution is None
    assert data.participation_percent is None or data.participation_percent == 0
    assert load(json.loads(json.dumps(dump(data)))) == data


def test_data_for_reads_snapshot_when_published(scored_assignment):
    report = Report.objects.create(assignment=scored_assignment)
    live = data_for(report)
    report.snapshot = dump(live)
    report.status = Report.Status.PUBLISHED
    report.save()
    from apps.nom035.models import SubmissionScore

    SubmissionScore.objects.update(final_ndr=c.NDR_MUY_ALTO)
    assert data_for(report) == live
    report.status = Report.Status.DRAFT
    assert data_for(report) != live
```

- [ ] **Step 3: Run to verify it fails.** Run: `pytest apps/reports/tests/test_snapshot.py -v` — FAIL (`ModuleNotFoundError`).
- [ ] **Step 4: Implement** `apps/reports/snapshot.py`:

```python
"""The report's data: built live from the engine, frozen as JSON on publish.

`dump`/`load` round-trip exactly (tests/test_snapshot.py), so a published report
renders through the same dataclasses as a live draft.
"""

from dataclasses import asdict, dataclass, replace
from datetime import date

from django.utils import timezone

from apps.nom035.results import (
    AreaResults,
    DimensionGroup,
    DistributionRow,
    Guia1,
    ParticipationRow,
    Slice,
    StatsRow,
    assignment_options,
    report_results,
)


@dataclass(frozen=True)
class CompanyFacts:
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
    label = next(
        o.label for o in assignment_options(company) if o.assignment.pk == assignment.pk
    )
    return ReportData(
        company=CompanyFacts(
            legal_name=company.legal_name,
            address=company.address,
            rfc=company.rfc,
            work_center=company.work_center,
            industry=company.industry,
            reference_code=company.reference_code,
        ),
        variant=assignment.variant,
        variant_label=assignment.get_variant_display(),
        period_label=label,
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
        **{k: raw[k] for k in ("key", "label", "n", "mean", "median", "minimum", "maximum", "scale_max")},
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
        categoria_distribution=tuple(_distribution(d) for d in raw["categoria_distribution"]),
        categoria_stats=tuple(_stats(s) for s in raw["categoria_stats"]),
        dimensions=tuple(
            DimensionGroup(key=g["key"], label=g["label"], rows=tuple(_stats(r) for r in g["rows"]))
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
```

Bands are clamped when the live data is built (`_clamped`), so `dump` needs no special case and `load(dump(x)) == x` holds exactly.

- [ ] **Step 5: Run to verify it passes.** `pytest apps/reports -v` — PASS.
- [ ] **Step 6: Verify and hand back.** `pytest && ruff check . && ruff format .` — green. Stop; list files; propose: `feat(reports): report data and its JSON snapshot`.

---

### Task 6: Generated sentences, levels present and recommendations

**Files:**
- Create: `apps/reports/text.py`
- Test: `apps/reports/tests/test_text.py`

**Interfaces:**
- Consumes: `DistributionRow`, `largest_remainder` (`apps/core/charts.py`), `RECOMMENDATIONS`, `cfg.action_text`, `cfg.categoria_of`.
- Produces (in `apps/reports/text.py`):

```python
def percent(count: int, n: int) -> str            # "12 %" with U+00A0
def final_sentence(row: DistributionRow) -> str
def categoria_sentence(rows: Sequence[DistributionRow]) -> str
def dominio_sentence(rows: Sequence[DistributionRow]) -> str   # dominio rows (flattened children)
def levels_present(data: ReportData) -> list[str]             # NDR keys in NDR_ORDER
def action_criteria(data: ReportData) -> list[tuple[str, str, str]]  # (level, label, text)
@dataclass(frozen=True)
class Recommendation:
    categoria_label: str
    dominio_key: str
    dominio_label: str
    level: str
    level_label: str
    share: str          # "12 %"
    text: str
def recommendations(data: ReportData) -> list[Recommendation]
```

- [ ] **Step 1: Write the failing tests.** `apps/reports/tests/test_text.py`:

```python
from apps.nom035 import _nom035_scoring as cfg
from apps.nom035 import constants as c
from apps.nom035.results import DistributionRow
from apps.reports import text

NB = " "


def row(key, counts, children=()):
    full = {lvl: 0 for lvl in c.NDR_ORDER} | counts
    return DistributionRow(
        key=key,
        label=cfg.group_label(key),
        n=sum(full.values()),
        counts=tuple((lvl, full[lvl]) for lvl in c.NDR_ORDER),
        children=tuple(children),
    )


def test_percent_uses_a_non_breaking_space():
    assert text.percent(1, 4) == f"25{NB}%"
    assert text.percent(0, 0) == f"0{NB}%"


def test_final_sentence():
    r = row("final", {c.NDR_NULO: 120, c.NDR_BAJO: 70, c.NDR_MEDIO: 35, c.NDR_ALTO: 20, c.NDR_MUY_ALTO: 5})
    assert text.final_sentence(r) == (
        f"De los 250 colaboradores evaluados, el 76{NB}% presentó niveles de riesgo "
        f"Nulo o Bajo; el 24{NB}% restante, Medio, Alto o Muy alto."
    )


def test_final_sentence_one_person():
    r = row("final", {c.NDR_BAJO: 1})
    assert text.final_sentence(r).startswith("De 1 colaborador evaluado, el 100")


def test_categoria_sentence_single_leader():
    rows = [
        row(cfg.CAT_AMBIENTE, {c.NDR_NULO: 9, c.NDR_ALTO: 1}),
        row(cfg.CAT_LIDERAZGO, {c.NDR_NULO: 6, c.NDR_ALTO: 2, c.NDR_MUY_ALTO: 2}),
    ]
    assert text.categoria_sentence(rows) == (
        "La categoría «Liderazgo y relaciones en el trabajo» concentra la mayor "
        f"proporción de trabajadores en niveles Alto o Muy alto: 40{NB}%."
    )


def test_categoria_sentence_tie_names_both():
    rows = [
        row(cfg.CAT_AMBIENTE, {c.NDR_NULO: 3, c.NDR_ALTO: 1}),
        row(cfg.CAT_TIEMPO, {c.NDR_NULO: 6, c.NDR_MUY_ALTO: 2}),
    ]
    sentence = text.categoria_sentence(rows)
    assert sentence.startswith("Las categorías «")
    assert f"25{NB}% cada una" in sentence


def test_categoria_sentence_none():
    rows = [row(cfg.CAT_AMBIENTE, {c.NDR_NULO: 3, c.NDR_MEDIO: 2})]
    assert text.categoria_sentence(rows) == (
        "Ninguna categoría tiene trabajadores en niveles Alto o Muy alto."
    )


def test_dominio_sentence_top_three_skipping_zero():
    rows = [
        row(cfg.DOM_CARGA, {c.NDR_NULO: 6, c.NDR_ALTO: 4}),
        row(cfg.DOM_LIDERAZGO, {c.NDR_NULO: 5, c.NDR_MUY_ALTO: 5}),
        row(cfg.DOM_JORNADA, {c.NDR_NULO: 9, c.NDR_ALTO: 1}),
        row(cfg.DOM_VIOLENCIA, {c.NDR_NULO: 8, c.NDR_ALTO: 2}),
        row(cfg.DOM_CONTROL, {c.NDR_NULO: 10}),
    ]
    assert text.dominio_sentence(rows) == (
        "Los dominios con mayor proporción de trabajadores en niveles Alto o Muy "
        f"alto son «Liderazgo» (50{NB}%), «Carga de trabajo» (40{NB}%) y "
        f"«Violencia» (20{NB}%)."
    )


def test_dominio_sentence_tie_at_cutoff_included():
    rows = [
        row(cfg.DOM_CARGA, {c.NDR_NULO: 1, c.NDR_ALTO: 1}),
        row(cfg.DOM_LIDERAZGO, {c.NDR_NULO: 1, c.NDR_ALTO: 1}),
        row(cfg.DOM_JORNADA, {c.NDR_NULO: 1, c.NDR_ALTO: 1}),
        row(cfg.DOM_VIOLENCIA, {c.NDR_NULO: 1, c.NDR_ALTO: 1}),
    ]
    assert text.dominio_sentence(rows).count("«") == 4


def test_dominio_sentence_single_and_none():
    one = [row(cfg.DOM_CARGA, {c.NDR_NULO: 3, c.NDR_ALTO: 1}), row(cfg.DOM_JORNADA, {c.NDR_NULO: 4})]
    assert text.dominio_sentence(one) == (
        "El dominio con mayor proporción de trabajadores en niveles Alto o Muy alto "
        f"es «Carga de trabajo» (25{NB}%)."
    )
    assert text.dominio_sentence([row(cfg.DOM_JORNADA, {c.NDR_NULO: 4})]) == (
        "Ningún dominio tiene trabajadores en niveles Alto o Muy alto."
    )
```

Add, using the `scored_assignment` fixture (marked `django_db`):

```python
import pytest

from apps.reports.snapshot import build_report_data


@pytest.mark.django_db
def test_levels_present_and_criteria(scored_assignment):
    data = build_report_data(scored_assignment)
    # Final: nulo, bajo, alto; categoría/dominio add muy_alto (Liderazgo).
    assert text.levels_present(data) == [c.NDR_NULO, c.NDR_BAJO, c.NDR_ALTO, c.NDR_MUY_ALTO]
    levels = [lvl for lvl, _label, _text in text.action_criteria(data)]
    assert levels == text.levels_present(data)


@pytest.mark.django_db
def test_recommendations_one_per_dominio_level_reached(scored_assignment):
    data = build_report_data(scored_assignment)
    recs = [(r.dominio_key, r.level, r.share) for r in text.recommendations(data)]
    assert (cfg.DOM_CONDICIONES, c.NDR_ALTO, f"55{NB}%") in recs  # 6 of 11
    assert (cfg.DOM_LIDERAZGO, c.NDR_MUY_ALTO, f"100{NB}%") in recs
    assert all(level != c.NDR_BAJO for _d, level, _s in recs)
```

- [ ] **Step 2: Run to verify it fails.** `pytest apps/reports/tests/test_text.py -v` — FAIL (`ModuleNotFoundError`).
- [ ] **Step 3: Implement** `apps/reports/text.py`:

```python
"""Sentences and lists the report generates from its data. Pure functions."""

from dataclasses import dataclass
from fractions import Fraction

from apps.core.charts import largest_remainder
from apps.nom035 import _nom035_scoring as cfg
from apps.nom035 import constants as c
from apps.reports.content import RECOMMENDATIONS

NBSP = " "
HIGH = (c.NDR_ALTO, c.NDR_MUY_ALTO)
LOW = (c.NDR_NULO, c.NDR_BAJO)
RECOMMENDED = (c.NDR_MEDIO, c.NDR_ALTO, c.NDR_MUY_ALTO)


def percent(count: int, n: int) -> str:
    return f"{round(count * 100 / n) if n else 0}{NBSP}%"


def _join(items: list[str]) -> str:
    return items[0] if len(items) == 1 else f"{', '.join(items[:-1])} y {items[-1]}"


def _row_percents(row) -> dict[str, int]:
    """Largest-remainder percents for a row, as the charts print them."""
    levels = [lvl for lvl, _n in row.counts]
    return dict(zip(levels, largest_remainder([n for _l, n in row.counts])))


def _high_share(row) -> Fraction:
    counts = dict(row.counts)
    return Fraction(sum(counts[lvl] for lvl in HIGH), row.n) if row.n else Fraction(0)


def final_sentence(row) -> str:
    pct = _row_percents(row)
    low = sum(pct[lvl] for lvl in LOW)
    noun = "colaborador evaluado" if row.n == 1 else "colaboradores evaluados"
    lead = "De" if row.n == 1 else "De los"
    return (
        f"{lead} {row.n} {noun}, el {low}{NBSP}% presentó niveles de riesgo Nulo o "
        f"Bajo; el {100 - low}{NBSP}% restante, Medio, Alto o Muy alto."
    )


def _share_text(row) -> str:
    return f"{round(_high_share(row) * 100)}{NBSP}%"


def categoria_sentence(rows) -> str:
    ranked = [r for r in rows if _high_share(r) > 0]
    if not ranked:
        return "Ninguna categoría tiene trabajadores en niveles Alto o Muy alto."
    top = max(_high_share(r) for r in ranked)
    leaders = [r for r in ranked if _high_share(r) == top]
    names = _join([f"«{r.label}»" for r in leaders])
    share = _share_text(leaders[0])
    if len(leaders) == 1:
        return (
            f"La categoría {names} concentra la mayor proporción de trabajadores en "
            f"niveles Alto o Muy alto: {share}."
        )
    return (
        f"Las categorías {names} concentran la mayor proporción de trabajadores en "
        f"niveles Alto o Muy alto: {share} cada una."
    )


def dominio_sentence(rows) -> str:
    ranked = sorted(
        (r for r in rows if _high_share(r) > 0), key=lambda r: -_high_share(r)
    )
    if not ranked:
        return "Ningún dominio tiene trabajadores en niveles Alto o Muy alto."
    cutoff = _high_share(ranked[min(2, len(ranked) - 1)])
    chosen = [r for r in ranked if _high_share(r) >= cutoff]
    names = _join([f"«{r.label}» ({_share_text(r)})" for r in chosen])
    if len(chosen) == 1:
        return (
            "El dominio con mayor proporción de trabajadores en niveles Alto o Muy "
            f"alto es {names}."
        )
    return (
        "Los dominios con mayor proporción de trabajadores en niveles Alto o Muy "
        f"alto son {names}."
    )


def _dominio_rows(data):
    return [d for cat in data.categoria_distribution for d in cat.children]


def levels_present(data) -> list[str]:
    rows = [*filter(None, [data.final_distribution]), *data.categoria_distribution, *_dominio_rows(data)]
    reached = {lvl for r in rows for lvl, n in r.counts if n}
    return [lvl for lvl in c.NDR_ORDER if lvl in reached]


def action_criteria(data) -> list[tuple[str, str, str]]:
    return [(lvl, c.NDR_LABELS[lvl], cfg.action_text(lvl)) for lvl in levels_present(data)]


@dataclass(frozen=True)
class Recommendation:
    categoria_label: str
    dominio_key: str
    dominio_label: str
    level: str
    level_label: str
    share: str
    text: str


def recommendations(data) -> list[Recommendation]:
    out = []
    for cat in data.categoria_distribution:
        for dom in cat.children:
            pct = _row_percents(dom)
            for lvl, n in dom.counts:
                if lvl in RECOMMENDED and n:
                    out.append(
                        Recommendation(
                            categoria_label=cat.label,
                            dominio_key=dom.key,
                            dominio_label=dom.label,
                            level=lvl,
                            level_label=c.NDR_LABELS[lvl],
                            share=f"{pct[lvl]}{NBSP}%",
                            text=RECOMMENDATIONS[dom.key][lvl],
                        )
                    )
    return out
```

Note: `test_recommendations_one_per_dominio_level_reached` expects 6 of 11 → `55 %`. With largest remainder on Condiciones `{alto: 6, bajo: 5}` of the 11 respondents who have that dominio: 54.5 → 55, 45.5 → 45 (tie broken by index: alto's remainder .545 vs bajo's .4545) — 55. If the fixture's `n` differs (the no-área respondent has no dominio rows), recompute and fix the expected value only if the arithmetic, not the code, was wrong.

- [ ] **Step 4: Run to verify it passes.** `pytest apps/reports -v` — PASS.
- [ ] **Step 5: Verify and hand back.** `pytest && ruff check . && ruff format .` — green. Stop; list files; propose: `feat(reports): generated sentences, action criteria and recommendations`.

---

### Task 7: Section registry, report stylesheet and the non-chart sections

**Files:**
- Create: `apps/reports/sections.py`
- Create: `templates/reports/_document.html`, `templates/reports/sections/_portada.html`, `_datos.html`, `_objetivo.html`, `_actividades.html`, `_poblacion.html`, `_resultados.html` (heading only; children filled in Task 8), `_criterios.html`, `_recomendaciones.html`, `_conclusiones.html`, `_responsables.html`, `_anexo.html`, `_toc.html`
- Create: `static/css/report.css`
- Test: `apps/reports/tests/test_sections.py`

**Interfaces:**
- Consumes: `ReportData`, `data_for`, `text.*`, `content.*`, `Report`.
- Produces:

```python
@dataclass(frozen=True)
class ReportContext:
    report: Report                 # may be unsaved (assignment set, fields empty)
    data: ReportData
    draft: bool
    issued_on: date                # published_at date, else today
    signatories: list[ReportSignatory]

@dataclass(frozen=True)
class Section:
    key: str
    title: str                     # "" → not numbered, not in the TOC (portada)
    template: str
    build: Callable[[ReportContext], dict]
    children: tuple["Section", ...] = ()

@dataclass(frozen=True)
class RenderedSection:
    key: str
    number: str                    # "1", "5.3"; "" for the portada
    title: str
    template: str
    context: dict
    children: tuple["RenderedSection", ...]

REGISTRY: tuple[Section, ...]
def context_for(report) -> ReportContext
def render_sections(ctx: ReportContext, registry=REGISTRY) -> list[RenderedSection]
```

- [ ] **Step 1: Write the failing tests.** `apps/reports/tests/test_sections.py`:

```python
import pytest
from django.template.loader import render_to_string

from apps.reports.models import Report, ReportSignatory
from apps.reports.sections import REGISTRY, context_for, render_sections

pytestmark = pytest.mark.django_db


def _render(report):
    ctx = context_for(report)
    return render_to_string(
        "reports/_document.html", {"sections": render_sections(ctx), "ctx": ctx}
    )


@pytest.fixture
def report(scored_assignment):
    report = Report.objects.create(
        assignment=scored_assignment,
        issued_in="Ciudad de México",
        activities_summary="Compras\nAlmacén",
        evaluator_name="Sofía Santana Arciniega",
        evaluator_license="1234567",
        conclusions="Primera.\n\nSegunda.",
    )
    ReportSignatory.objects.create(report=report, title="Dirección de RH", name="Lic. Ana", order=1)
    return report


def _flatten(sections):
    for s in sections:
        yield s
        yield from _flatten(s.children)


def test_numbering_skips_the_portada_and_nests_results():
    from apps.reports.sections import number_sections

    numbers = [(s.key, s.number) for s in _flatten(number_sections(REGISTRY))]
    assert numbers[0] == ("portada", "")
    assert ("datos", "1") in numbers
    assert ("resultados.final", "5.3") in numbers


def test_document_renders_every_section(report):
    html = _render(report)
    for heading in (
        "Datos del centro de trabajo",
        "Objetivo",
        "Principales actividades",
        "Selección de la población",
        "Resultados",
        "Criterios de acción",
        "Recomendaciones según riesgo identificado",
        "Conclusiones",
        "Responsables",
        "Anexo",
    ):
        assert heading in html, heading
    assert "Planta Norte" in html and "Manufactura" in html
    assert "Lic. Ana" in html and "1234567" in html


def test_admin_text_is_escaped_and_keeps_paragraphs(report):
    report.conclusions = "<script>x</script>\n\nSegundo párrafo."
    report.save()
    html = _render(report)
    assert "<script>x</script>" not in html
    assert "&lt;script&gt;" in html
    assert html.count("<p") >= 2


def test_optional_blocks_are_left_out(report):
    report.signatories.all().delete()
    html = _render(report)
    assert "Responsables de la empresa" not in html
    assert "Número de trabajadores" not in html  # no headcounts entered
    assert "Recomendaciones adicionales" not in html


def test_unsaved_report_previews(scored_assignment):
    html = _render(Report(assignment=scored_assignment))
    assert "Datos del centro de trabajo" in html


def test_small_variant_report_renders(company, nom035_survey):
    from apps.nom035.tests.factories import make_assignment, make_score

    assignment = make_assignment(company, nom035_survey, variant="small")
    make_score(assignment)
    html = _render(Report(assignment=assignment))
    assert "Guía II" in html
    assert "Entorno organizacional" not in html.split("Anexo")[0]


def test_reordering_the_registry_renumbers():
    from apps.reports.sections import number_sections

    swapped = (REGISTRY[0], REGISTRY[2], REGISTRY[1], *REGISTRY[3:])
    numbers = {s.key: s.number for s in number_sections(swapped)}
    assert numbers["objetivo"] == "1"
    assert numbers["datos"] == "2"
```


- [ ] **Step 2: Run to verify it fails.** `pytest apps/reports/tests/test_sections.py -v` — FAIL (`ModuleNotFoundError`).
- [ ] **Step 3: Registry.** `apps/reports/sections.py`:

```python
"""The report, declared as one ordered list of sections.

Screen, PDF and table of contents all iterate REGISTRY; reorder, drop or add a
section here (plus its partial). Numbers are derived from position.
"""

from dataclasses import dataclass, field
from datetime import date
from typing import Callable

from django.utils import timezone

from apps.nom035 import _nom035_scoring as cfg
from apps.nom035 import constants as c
from apps.reports import content, text
from apps.reports.snapshot import ReportData, data_for

_T = "reports/sections/"


@dataclass(frozen=True)
class ReportContext:
    report: object
    data: ReportData
    draft: bool
    issued_on: date
    signatories: list


@dataclass(frozen=True)
class Section:
    key: str
    title: str
    template: str
    build: Callable = lambda ctx: {}
    children: tuple = ()


@dataclass(frozen=True)
class RenderedSection:
    key: str
    number: str
    title: str
    template: str
    context: dict = field(default_factory=dict)
    children: tuple = ()


def context_for(report) -> ReportContext:
    published = report.status == report.Status.PUBLISHED and report.snapshot
    return ReportContext(
        report=report,
        data=data_for(report),
        draft=not published,
        issued_on=timezone.localdate(report.published_at)
        if published and report.published_at
        else timezone.localdate(),
        signatories=list(report.signatories.all()) if report.pk else [],
    )


def number_sections(registry, prefix="") -> list[RenderedSection]:
    out, n = [], 0
    for s in registry:
        number = ""
        if s.title:
            n += 1
            number = f"{prefix}{n}"
        out.append(
            RenderedSection(
                key=s.key,
                number=number,
                title=s.title,
                template=s.template,
                children=tuple(number_sections(s.children, f"{number}.")),
            )
        )
    return out


# REGISTRY (below) is defined before render_sections is first called.


def _render(registry, ctx, prefix=""):
    out, n = [], 0
    for s in registry:
        number = ""
        if s.title:
            n += 1
            number = f"{prefix}{n}"
        out.append(
            RenderedSection(
                key=s.key,
                number=number,
                title=s.title,
                template=s.template,
                context={"data": ctx.data, "ctx": ctx, **s.build(ctx)},
                children=tuple(_render(s.children, ctx, f"{number}.")),
            )
        )
    return out


def render_sections(ctx, registry=None) -> list[RenderedSection]:
    return _render(REGISTRY if registry is None else registry, ctx)
```

`number_sections` numbers without building contexts (used by the numbering tests); `_render` numbers the same way and builds each section's context.

Builders and the registry (in the same module):

```python
def _actividades(ctx):
    r = ctx.report
    return {
        "headcounts": [
            (label, value)
            for label, value in (
                ("Presencial", r.headcount_in_person),
                ("Home office", r.headcount_home_office),
                ("Híbrido", r.headcount_hybrid),
            )
            if value is not None
        ],
        "headcount_total": r.headcount_total,
    }


def _poblacion(ctx):
    guide = "Guía II" if ctx.data.variant == "small" else "Guía III"
    return {"guides": f"Guía I y {guide}"}


def _anexo(ctx):
    variant = ctx.data.variant
    taxonomy = cfg.taxonomy_for_variant(variant)
    return {
        "glossary": content.GLOSSARY,
        "lft": content.LFT_ARTICLES,
        "method": method_tables(variant, taxonomy),
    }


REGISTRY = (
    Section("portada", "", _T + "_portada.html",
            lambda ctx: {"provider": content.PROVIDER_NAME}),
    Section("datos", "Datos del centro de trabajo", _T + "_datos.html"),
    Section("objetivo", "Objetivo", _T + "_objetivo.html",
            lambda ctx: {"objective": content.OBJECTIVE_PLACEHOLDER}),
    Section("actividades", "Principales actividades", _T + "_actividades.html", _actividades),
    Section("poblacion", "Selección de la población", _T + "_poblacion.html", _poblacion),
    Section("resultados", "Resultados", _T + "_resultados.html", children=RESULTS_CHILDREN),
    Section("criterios", "Criterios de acción", _T + "_criterios.html",
            lambda ctx: {"criteria": text.action_criteria(ctx.data)}),
    Section("recomendaciones", "Recomendaciones según riesgo identificado",
            _T + "_recomendaciones.html",
            lambda ctx: {"recommendations": text.recommendations(ctx.data)}),
    Section("conclusiones", "Conclusiones", _T + "_conclusiones.html"),
    Section("responsables", "Responsables", _T + "_responsables.html",
            lambda ctx: {"provider": content.PROVIDER_NAME,
                         "notice": content.CONFIDENTIALITY_NOTICE}),
    Section("anexo", "Anexo", _T + "_anexo.html", _anexo),
)
```

For this task `RESULTS_CHILDREN` is a tuple of eight `Section`s with keys `resultados.perfil`, `resultados.participacion`, `resultados.final`, `resultados.categoria`, `resultados.dominio`, `resultados.dimension`, `resultados.area`, `resultados.guia1`, titles *Perfil de quienes respondieron*, *Participación por área*, *Calificación final*, *Resultados por categoría*, *Resultados por dominio*, *Resultados por dimensión*, *Resultados por área*, *Guía I*, each pointing to `_T + "results/_<suffix>.html"`; create those eight partials as a heading-only stub (`<h3>{{ number }} {{ title }}</h3>`) — Task 8 fills them. Define `RESULTS_CHILDREN` above `REGISTRY`.

`method_tables(variant, taxonomy)` returns:

```python
def method_tables(variant, taxonomy):
    """Rows for the annex: taxonomy, scoring direction, thresholds — this variant only."""
    by_dim = {}
    for code, (cat, dom, dim) in taxonomy.items():
        by_dim.setdefault((cat, dom, dim), []).append(int(code.split("-")[1]))
    taxonomy_rows = [
        {
            "categoria": cfg.group_label(cat),
            "dominio": cfg.group_label(dom),
            "dimension": cfg.group_label(dim),
            "items": ", ".join(str(n) for n in sorted(items)),
        }
        for (cat, dom, dim), items in sorted(
            by_dim.items(),
            key=lambda kv: (cfg.CATEGORIA_ORDER.index(kv[0][0]), min(kv[1])),
        )
    ]
    numbers = sorted(int(code.split("-")[1]) for code in taxonomy)
    prefix = next(iter(taxonomy)).split("-")[0]
    direct = [n for n in numbers if not cfg.is_inverted(f"{prefix}-{n}")]
    inverted = [n for n in numbers if cfg.is_inverted(f"{prefix}-{n}")]

    def bands(level, key):
        uppers = [u for u, _ndr in cfg.thresholds_for(level, key, variant)]
        lows = [0, *uppers[:-1]]
        cells = []
        for (lo, hi), (_u, ndr) in zip(zip(lows, uppers), cfg.thresholds_for(level, key, variant)):
            if hi == float("inf"):
                cells.append((ndr, f"≥ {lo:g}"))
            elif lo == 0:
                cells.append((ndr, f"< {hi:g}"))
            else:
                cells.append((ndr, f"{lo:g} a < {hi:g}"))
        return cells

    categorias = [k for k in cfg.CATEGORIA_ORDER if any(t[0] == k for t in taxonomy.values())]
    dominios = [d for k in categorias for d in cfg.dominios_for_categoria(k)
                if any(t[1] == d for t in taxonomy.values())]
    return {
        "taxonomy": taxonomy_rows,
        "direct": ", ".join(map(str, direct)),
        "inverted": ", ".join(map(str, inverted)),
        "final": bands("final", "final"),
        "categorias": [(cfg.group_label(k), bands(c.LEVEL_CATEGORIA, k)) for k in categorias],
        "dominios": [(cfg.group_label(d), bands(c.LEVEL_DOMINIO, d)) for d in dominios],
        "levels": [(lvl, c.NDR_LABELS[lvl]) for lvl in c.NDR_ORDER],
    }
```

Add to `test_sections.py`:

```python
def test_method_tables_match_the_engine():
    from apps.nom035 import _nom035_scoring as cfg
    from apps.reports.sections import method_tables

    large = method_tables("large", cfg.taxonomy_for_variant("large"))
    assert large["final"][0][1] == "< 50"
    assert large["final"][-1][1] == "≥ 140"
    assert large["final"][2][1] == "75 a < 99"
    small = method_tables("small", cfg.taxonomy_for_variant("small"))
    assert len(small["categorias"]) == 4
    assert "1" in small["inverted"].split(", ")  # Guía II item 1 scores 4→0
```

- [ ] **Step 4: Templates.** `templates/reports/_document.html` — iterates sections and children:

```django
{% for s in sections %}
  <section id="sec-{{ s.key|slugify }}" class="report-section report-section--{{ s.key|slugify }}">
    {% include s.template with s=s data=s.context.data ctx=s.context.ctx c=s.context %}
    {% for child in s.children %}
      <section id="sec-{{ child.key|slugify }}" class="report-subsection">
        {% include child.template with s=child data=child.context.data ctx=child.context.ctx c=child.context %}
      </section>
    {% endfor %}
  </section>
{% endfor %}
```

Each partial starts with its heading `<h2 class="report-h2"><span class="report-num">{{ s.number }}</span> {{ s.title }}</h2>` (portada: none; children use `report-h3`). Prose uses `report-prose`; tables `report-table`; admin free text always through `{{ value|linebreaks }}` (auto-escapes, makes `<p>`). Write each partial with Spanish copy exactly as the spec's *Report contents* lists, e.g. `_poblacion.html`:

```django
<h2 class="report-h2"><span class="report-num">{{ s.number }}</span> {{ s.title }}</h2>
<div class="report-prose">
  <p>Se aplicaron la {{ c.guides }} de la NOM-035-STPS-2018 mediante la plataforma, en el periodo {{ data.period_label }}.</p>
  <p>Colaboradores registrados y activos: <strong>{{ data.registered }}</strong>. Cuestionarios respondidos: <strong>{{ data.responded }}</strong>{% if data.participation_percent is not None %} ({{ data.participation_percent }}&nbsp;% de participación){% endif %}.</p>
</div>
```

Optional blocks are wrapped in `{% if %}`: headcounts in `_actividades.html` (`{% if c.headcounts %}` with heading text *Número de trabajadores*), signatories in `_responsables.html` (`{% if ctx.signatories %}` with sub-heading *Responsables de la empresa*), additional recommendations in `_recomendaciones.html` (`{% if ctx.report.additional_recommendations %}` with sub-heading *Recomendaciones adicionales*). `_criterios.html` prints each `(level, label, text)` as a `report-criterion report-criterion--{{ level }}` block with `{% ndr_badge level %}`-style markup (load `valuation_extras`; use whichever badge filter that module exposes). `_recomendaciones.html` groups by `categoria_label` then `dominio_label` (`{% regroup %}`), each entry: badge, *"{{ share }} en {{ level_label }}"*, matrix text, and a line *"Ver la sección de resultados por dominio."* `_anexo.html` prints glossary (`<dl>`), LFT articles (`linebreaks`), then *Método utilizado*: taxonomy table, scoring-direction table (two rows: *Siempre 0 … Nunca 4* for `direct`, *Siempre 4 … Nunca 0* for `inverted`), and threshold tables with header cells `report-level report-level--{{ level }}`. `_toc.html` lists numbered sections and children as links `#sec-<key>` with a `report-toc-page` span (filled by CSS in the PDF).

- [ ] **Step 5: Stylesheet.** `static/css/report.css` — plain CSS, hex colors, no Tailwind. It defines `@font-face` for `Source Serif 4` and `Source Sans 3` (files from Task 1, copied in Task 11 — reference `../fonts/...` now), and the classes the partials use: `.report-sheet` (white, max-width 52rem, padding 1rem; `@media (min-width: 768px)` padding 3rem), `.report-prose` (serif, 1.0625rem/1.65, max-width 65ch), `.report-finding` (serif, 1.25rem/1.45, weight 600), `.report-h2`/`.report-h3` (sans, weights 700/600, `#111827`), `.report-num` (`#4338CA`, tabular numerals), `.report-table` (sans, 0.875rem, `border-collapse: collapse`, rules `#E5E7EB`, `thead` repeated via `display: table-header-group`), `.report-small` (`#4B5563`, 0.8125rem), `.report-level--nulo|bajo|medio|alto|muy_alto` and `.report-criterion--*` (the NDR hexes: gray `#D1D5DB`, green `#22C55E`, amber `#F59E0B`, orange `#F97316`, red `#EF4444` — the Tailwind 300/500 values `valuation_extras` uses), and phone stacking: under 768 px `.report-table--stack tr { display: block }` etc. Keep selectors single-class to avoid specificity fights.
- [ ] **Step 6: Run to verify it passes.** `pytest apps/reports -v` — PASS.
- [ ] **Step 7: Verify and hand back.** `pytest && ruff check . && ruff format . && npm run build:css` — green. Stop; list files; propose: `feat(reports): section registry and the report's text sections`.

---

### Task 8: Results sections with the dashboard's charts

**Files:**
- Modify: `templates/reports/sections/results/_perfil.html`, `_participacion.html`, `_final.html`, `_categoria.html`, `_dominio.html`, `_dimension.html`, `_area.html`, `_guia1.html`
- Create: `templates/reports/sections/results/_stats.html` (the report's stats row) and `_suppressed.html`
- Modify: `apps/reports/sections.py` (builders for the results children)
- Test: `apps/reports/tests/test_results_sections.py`

**Interfaces:**
- Consumes: chart tags `stacked_bar(items, unit, legend)`, `column_chart(items, unit)`, `level_columns(items, unit, names, size)`, `range_strip(bands, scale_max, points)` from `{% load charts %}`; `text.final_sentence`, `categoria_sentence`, `dominio_sentence`.
- Produces: builders returning `{"finding": str}` for final/categoría/dominio (empty string when `data.final_distribution is None`) and `{"dominio_rows": [...]}` for dominio.

- [ ] **Step 1: Write the failing tests.** `apps/reports/tests/test_results_sections.py`:

```python
import pytest
from django.template.loader import render_to_string

from apps.reports.models import Report
from apps.reports.sections import context_for, render_sections

pytestmark = pytest.mark.django_db
SUPPRESSED = "Grupo demasiado pequeño"


def _html(report):
    ctx = context_for(report)
    return render_to_string("reports/_document.html", {"sections": render_sections(ctx), "ctx": ctx})


def test_results_use_the_dashboard_charts(scored_assignment):
    html = _html(Report(assignment=scored_assignment))
    assert html.count("<svg") >= 10
    assert "De los 12 colaboradores evaluados" in html
    assert "concentra la mayor proporción" in html
    assert "Los dominios con mayor proporción" in html or "El dominio con mayor" in html


def test_dominios_are_always_expanded(scored_assignment):
    html = _html(Report(assignment=scored_assignment))
    assert "<details" not in html
    assert "Condiciones en el ambiente de trabajo" in html


def test_dimension_strip_is_neutral(scored_assignment):
    html = _html(Report(assignment=scored_assignment))
    assert "Sin umbral oficial" in html


def test_area_sections_hide_small_groups(scored_assignment):
    html = _html(Report(assignment=scored_assignment))
    area = html.split('id="sec-resultadosarea"')[1].split("</section>")[0]
    assert "Operaciones" in area and "Ventas" in area
    assert SUPPRESSED in html  # "Sin área" (1 respondent) is hidden


def test_empty_assignment_shows_empty_states(company, nom035_survey):
    from apps.nom035.tests.factories import make_assignment

    html = _html(Report(assignment=make_assignment(company, nom035_survey)))
    assert "Aún no hay cuestionarios valorados" in html
    assert "<svg" not in html
```

(`slugify("resultados.area")` is `resultadosarea`; adjust the id in the test if the document template slugifies differently.)

- [ ] **Step 2: Run to verify it fails.** `pytest apps/reports/tests/test_results_sections.py -v` — FAIL.
- [ ] **Step 3: Builders.** In `sections.py` give the result children builders:

```python
def _finding(fn, rows):
    return {"finding": fn(rows) if rows else ""}

RESULTS_CHILDREN = (
    Section("resultados.perfil", "Perfil de quienes respondieron", _T + "results/_perfil.html"),
    Section("resultados.participacion", "Participación por área", _T + "results/_participacion.html"),
    Section("resultados.final", "Calificación final", _T + "results/_final.html",
            lambda ctx: _finding(text.final_sentence, ctx.data.final_distribution)),
    Section("resultados.categoria", "Resultados por categoría", _T + "results/_categoria.html",
            lambda ctx: _finding(text.categoria_sentence, ctx.data.categoria_distribution)),
    Section("resultados.dominio", "Resultados por dominio", _T + "results/_dominio.html", _dominio),
    Section("resultados.dimension", "Resultados por dimensión", _T + "results/_dimension.html"),
    Section("resultados.area", "Resultados por área", _T + "results/_area.html"),
    Section("resultados.guia1", "Guía I", _T + "results/_guia1.html"),
)


def _dominio(ctx):
    stats = {s.key: s for cat in ctx.data.categoria_stats for s in cat.children}
    groups = [
        {
            "label": cat.label,
            "rows": [{"dist": d, "stats": stats.get(d.key)} for d in cat.children],
        }
        for cat in ctx.data.categoria_distribution
    ]
    rows = [d for cat in ctx.data.categoria_distribution for d in cat.children]
    return {"groups": groups, **_finding(text.dominio_sentence, rows)}
```

- [ ] **Step 4: Partials.** Pattern for every results partial: heading → `{% if not data.final_distribution %}<p class="report-small">Aún no hay cuestionarios valorados en esta encuesta.</p>{% else %}` → `<p class="report-finding">{{ c.finding }}</p>` (when present) → chart(s) → `<p class="report-small">n = …</p>` → `{% endif %}`. Mapping (from the spec's chart table):
  - `_perfil.html`: `{% stacked_bar data.sex unit="persona" legend=True %}` then `{% column_chart data.age unit="persona" %}`, each under a `report-h4` label *Sexo* / *Edad*.
  - `_participacion.html`: `report-table report-table--stack` with columns Área / Registrados / Respondieron / Participación / Distribución; the last cell `{% if row.suppressed %}{% include "reports/sections/results/_suppressed.html" %}{% elif row.counts %}{% level_columns row.slices size="sm" %}{% endif %}`.
  - `_final.html`: `{% level_columns data.final_distribution.slices size="lg" %}` then `{% include "reports/sections/results/_stats.html" with row=data.final_stats %}`.
  - `_categoria.html`: per categoría (zip distributions with `data.categoria_stats` by index — pass a pre-zipped list from a builder instead if the template gets awkward), label, `{% level_columns row.slices %}`, `_stats.html`.
  - `_dominio.html`: per group `c.groups`, `report-h4` with the categoría label, then each dominio: label, `{% level_columns r.dist.slices size="sm" %}`, `_stats.html` with `row=r.stats`.
  - `_dimension.html`: per `data.dimensions` group, `report-h4` dominio label, each row through `_stats.html` (its single neutral band carries the "Sin umbral oficial" label).
  - `_area.html`: first a table with one row per área: label, *n*, `{% stacked_bar a.final.slices %}` or the suppressed include; then for each visible área a block with its categoría rows as `{% level_columns cat.slices size="sm" %}`.
  - `_guia1.html`: `{% stacked_bar data.guia1.slices legend=True %}`, then a count table per área (Área / Sin acontecimiento / Acontecimiento sin requerir valoración / Requiere valoración clínica), suppressed rows through the include.
  - `_stats.html`: like `templates/core/results/_stats_row.html` but with report classes and **no** `md:grid-cols` beyond `md:`: label, `<dl>` n / Prom. / Mediana / Mín / Máx, `{% if row.n %}{% range_strip row.strip_bands row.scale_max row.strip_points %}{% endif %}`.
  - `_suppressed.html`: `<span class="report-small">Grupo demasiado pequeño para mostrar resultados sin identificar a las personas (mínimo 5)</span>` — the dashboard's wording.
  - An NDR legend (the five levels with their colors) closes 5.3, 5.4 and 5.5: reuse `{% include "core/results/_ndr_legend.html" %}` only if it has no breakpoint above `md:`; otherwise write `results/_legend.html` with report classes.
- [ ] **Step 5: Run to verify it passes.** `pytest apps/reports -v` — PASS.
- [ ] **Step 6: Verify and hand back.** `pytest && ruff check . && ruff format . && npm run build:css` — green. Stop; list files; propose: `feat(reports): results sections drawn with the dashboard's charts`.

---

### Task 9: Administrador pages — list, preview, edit, publish

**Files:**
- Create: `apps/reports/publishing.py`, `apps/reports/forms.py`, `apps/reports/views.py`, `apps/reports/urls.py`
- Modify: `config/urls.py`
- Create: `templates/reports/report_list.html`, `templates/reports/report_detail.html`, `templates/reports/report_form.html`
- Modify: `templates/core/company_dashboard.html` (admin link), `templates/core/company_results.html` (admin link)
- Test: `apps/reports/tests/test_publishing.py`, `apps/reports/tests/test_admin_views.py`

**Interfaces:**
- Produces:
  - `publishing.blockers(report) -> list[str]` — Spanish messages, empty when publishable.
  - `publishing.publish(report, user) -> list[str]` — blockers (nothing changed) or `[]` after storing the snapshot.
  - `publishing.unpublish(report) -> None`
  - `forms.ReportForm` (ModelForm, all Administrador fields), `forms.SignatoryFormSet` (inline formset, `extra=1`, `can_delete=True`, ordering by position).
  - URL names (namespace `reports`): `admin_list`, `admin_detail`, `admin_edit`, `admin_publish`, `admin_unpublish`, `admin_pdf` (the last wired in Task 11).

- [ ] **Step 1: Write the failing tests.** `apps/reports/tests/test_publishing.py`:

```python
import pytest

from apps.nom035.models import SubmissionScore
from apps.reports import publishing
from apps.reports.models import Report
from apps.surveys.models import SurveyAssignment

pytestmark = pytest.mark.django_db

READY = dict(
    issued_in="CDMX",
    activities_summary="Compras",
    evaluator_name="Sofía",
    evaluator_license="123",
    conclusions="Ok",
)


def test_blockers_list_every_unmet_condition(scored_assignment):
    scored_assignment.status = SurveyAssignment.Status.ACTIVE
    scored_assignment.save()
    report = Report.objects.create(assignment=scored_assignment)
    messages = publishing.blockers(report)
    assert "La encuesta sigue activa; ciérrala antes de publicar el reporte." in messages
    assert any("Lugar de emisión" in m for m in messages)
    assert any("Conclusiones" in m for m in messages)


def test_no_scores_blocks(company, nom035_survey):
    from apps.nom035.tests.factories import make_assignment

    a = make_assignment(company, nom035_survey)
    a.status = SurveyAssignment.Status.CLOSED
    a.save()
    report = Report.objects.create(assignment=a, **READY)
    assert publishing.blockers(report) == [
        "La encuesta no tiene cuestionarios valorados."
    ]


def test_publish_stores_snapshot(scored_assignment, make_user):
    report = Report.objects.create(assignment=scored_assignment, **READY)
    assert publishing.publish(report, make_user(email="a@x.mx")) == []
    report.refresh_from_db()
    assert report.status == Report.Status.PUBLISHED
    assert report.snapshot["responded"] == 12
    assert report.published_by.email == "a@x.mx"


def test_published_report_ignores_later_scores(scored_assignment, make_user):
    from apps.reports.snapshot import data_for

    report = Report.objects.create(assignment=scored_assignment, **READY)
    publishing.publish(report, make_user(email="a@x.mx"))
    before = data_for(report)
    SubmissionScore.objects.update(final_ndr="muy_alto")
    report.refresh_from_db()
    assert data_for(report) == before


def test_publish_and_unpublish_are_idempotent(scored_assignment, make_user):
    report = Report.objects.create(assignment=scored_assignment, **READY)
    user = make_user(email="a@x.mx")
    publishing.publish(report, user)
    first = report.published_at
    assert publishing.publish(report, user) == ["El reporte ya está publicado."]
    report.refresh_from_db()
    assert report.published_at == first
    publishing.unpublish(report)
    publishing.unpublish(report)
    report.refresh_from_db()
    assert report.status == Report.Status.DRAFT and report.snapshot is None
```

`apps/reports/tests/test_admin_views.py`:

```python
import pytest
from django.urls import reverse

from apps.accounts.roles import ROLES
from apps.reports.models import Report, ReportSignatory

pytestmark = pytest.mark.django_db


@pytest.fixture
def admin_client(client, make_user, bootstrap_groups):
    user = make_user(email="op@x.mx")
    user.groups.add(bootstrap_groups[ROLES[0].name])
    client.force_login(user)
    return client


@pytest.fixture
def urls(scored_assignment):
    ref = scored_assignment.company.reference_code
    pk = scored_assignment.pk
    return {
        "list": reverse("reports:admin_list", args=[ref]),
        "detail": reverse("reports:admin_detail", args=[ref, pk]),
        "edit": reverse("reports:admin_edit", args=[ref, pk]),
        "publish": reverse("reports:admin_publish", args=[ref, pk]),
        "unpublish": reverse("reports:admin_unpublish", args=[ref, pk]),
    }


def _form_data(**overrides):
    data = {
        "issued_in": "CDMX",
        "activities_summary": "Compras",
        "headcount_in_person": "10",
        "headcount_home_office": "",
        "headcount_hybrid": "",
        "evaluator_name": "Sofía",
        "evaluator_license": "123",
        "additional_recommendations": "",
        "conclusions": "Ok",
        "signatories-TOTAL_FORMS": "1",
        "signatories-INITIAL_FORMS": "0",
        "signatories-MIN_NUM_FORMS": "0",
        "signatories-MAX_NUM_FORMS": "1000",
        "signatories-0-title": "Dirección de RH",
        "signatories-0-name": "Lic. Ana",
        "signatories-0-ORDER": "1",
    }
    return data | overrides


def test_list_shows_states(admin_client, urls):
    body = admin_client.get(urls["list"]).content.decode()
    assert "Sin iniciar" in body


def test_detail_previews_without_creating(admin_client, urls):
    resp = admin_client.get(urls["detail"])
    assert resp.status_code == 200
    assert "Datos del centro de trabajo" in resp.content.decode()
    assert Report.objects.count() == 0


def test_edit_creates_report_and_signatories(admin_client, urls):
    resp = admin_client.post(urls["edit"], _form_data())
    assert resp.status_code == 302
    report = Report.objects.get()
    assert report.signatories.get().name == "Lic. Ana"


def test_edit_prefills_from_previous_report(admin_client, urls, scored_assignment, nom035_survey):
    from apps.nom035.tests.factories import make_assignment

    older = make_assignment(scored_assignment.company, nom035_survey)
    prev = Report.objects.create(assignment=older, evaluator_name="Sofía", evaluator_license="999")
    ReportSignatory.objects.create(report=prev, title="RH", name="Ana", order=1)
    body = admin_client.get(urls["edit"]).content.decode()
    assert 'value="999"' in body and 'value="Ana"' in body


def test_publish_flow_and_edit_lock(admin_client, urls):
    admin_client.post(urls["edit"], _form_data())
    resp = admin_client.post(urls["publish"], follow=True)
    assert "Reporte publicado." in resp.content.decode()
    resp = admin_client.get(urls["edit"], follow=True)
    assert "Despublica el reporte para editarlo." in resp.content.decode()
    resp = admin_client.post(urls["unpublish"], follow=True)
    assert "Reporte despublicado." in resp.content.decode()


def test_publish_refusal_names_the_reasons(admin_client, urls, scored_assignment):
    scored_assignment.status = "active"
    scored_assignment.save()
    resp = admin_client.post(urls["publish"], follow=True)
    assert "La encuesta sigue activa" in resp.content.decode()


def test_publish_is_post_only(admin_client, urls):
    assert admin_client.get(urls["publish"]).status_code == 405


def test_executive_cannot_use_admin_routes(client, urls, make_user_with_profile, bootstrap_groups, scored_assignment):
    user = make_user_with_profile(email="e@x.mx", company=scored_assignment.company)
    user.groups.add(bootstrap_groups[ROLES[1].name])
    client.force_login(user)
    assert client.get(urls["detail"]).status_code == 403


def test_foreign_or_non_nom035_assignment_is_404(admin_client, scored_assignment, make_company, survey):
    from apps.surveys.models import SurveyAssignment

    other = make_company(name="Otra", legal_name="Otra SA")
    url = reverse("reports:admin_detail", args=[other.reference_code, scored_assignment.pk])
    assert admin_client.get(url).status_code == 404
    plain = SurveyAssignment.objects.create(company=scored_assignment.company, survey=survey, variant="large")
    url = reverse("reports:admin_detail", args=[scored_assignment.company.reference_code, plain.pk])
    assert admin_client.get(url).status_code == 404
```

- [ ] **Step 2: Run to verify it fails.** `pytest apps/reports/tests/test_publishing.py apps/reports/tests/test_admin_views.py -v` — FAIL.
- [ ] **Step 3: Publishing.** `apps/reports/publishing.py`:

```python
"""Publishing freezes the report's data; unpublishing discards it."""

from django.db import transaction
from django.utils import timezone

from apps.nom035.models import SubmissionScore
from apps.reports.models import Report
from apps.reports.snapshot import build_report_data, dump
from apps.surveys.models import SurveyAssignment

REQUIRED = (
    ("issued_in", "Lugar de emisión"),
    ("activities_summary", "Principales actividades"),
    ("evaluator_name", "Responsable de la evaluación"),
    ("evaluator_license", "Cédula profesional"),
    ("conclusions", "Conclusiones"),
)


def blockers(report) -> list[str]:
    out = []
    assignment = report.assignment
    if assignment.status == SurveyAssignment.Status.ACTIVE:
        out.append("La encuesta sigue activa; ciérrala antes de publicar el reporte.")
    if not SubmissionScore.objects.filter(submission__assignment=assignment).exists():
        out.append("La encuesta no tiene cuestionarios valorados.")
    out += [
        f"Falta completar: {label}."
        for name, label in REQUIRED
        if not getattr(report, name).strip()
    ]
    return out


def publish(report, user) -> list[str]:
    if report.status == Report.Status.PUBLISHED:
        return ["El reporte ya está publicado."]
    problems = blockers(report)
    if problems:
        return problems
    with transaction.atomic():
        report.snapshot = dump(build_report_data(report.assignment))
        report.status = Report.Status.PUBLISHED
        report.published_at = timezone.now()
        report.published_by = user
        report.save()
    return []


def unpublish(report) -> None:
    if report.status == Report.Status.DRAFT:
        return
    report.snapshot = None
    report.status = Report.Status.DRAFT
    report.published_at = None
    report.published_by = None
    report.save()
```

- [ ] **Step 4: Forms.** `apps/reports/forms.py`: `ReportForm(ModelForm)` over the Administrador fields with widget `attrs` carrying the same input classes the app's other forms use (copy the class string from `apps/accounts/forms.py`'s text inputs); `textarea` rows 5. `SignatoryFormSet = inlineformset_factory(Report, ReportSignatory, fields=("title", "name"), extra=1, can_delete=True, can_order=True)` with prefix `signatories`; on save, set each kept form's `order` from `ORDER`. Blank extra rows are ignored by the formset (`empty_permitted`).
- [ ] **Step 5: Views.** `apps/reports/views.py`:

```python
"""Report pages: Administrador (any company) and Ejecutivo principal (own company)."""

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views import View

from apps.accounts.models import Company
from apps.nom035.results import NOM035_SURVEY_KEY, assignment_options
from apps.reports import publishing
from apps.reports.forms import ReportForm, SignatoryFormSet
from apps.reports.models import Report
from apps.reports.sections import context_for, render_sections
from apps.surveys.models import SurveyAssignment


class AdminMixin(LoginRequiredMixin):
    def dispatch(self, request, *args, **kwargs):
        user = request.user
        if user.is_authenticated and not (
            user.has_perm("accounts.can_manage_surveys")
            and user.has_perm("accounts.can_view_insights")
        ):
            raise PermissionDenied
        return super().dispatch(request, *args, **kwargs)

    def company(self):
        return get_object_or_404(Company, reference_code=self.kwargs["reference_code"])

    def assignment(self):
        return get_object_or_404(
            SurveyAssignment.objects.select_related("company"),
            pk=self.kwargs["assignment_id"],
            company__reference_code=self.kwargs["reference_code"],
            survey__key=NOM035_SURVEY_KEY,
        )

    def report(self, assignment):
        return Report.objects.filter(assignment=assignment).first() or Report(
            assignment=assignment
        )


class AdminReportListView(AdminMixin, View):
    def get(self, request, reference_code):
        company = self.company()
        reports = {r.assignment_id: r for r in Report.objects.filter(assignment__company=company)}
        rows = [
            {"option": o, "report": reports.get(o.assignment.pk)}
            for o in assignment_options(company)
        ]
        return render(request, "reports/report_list.html", {"company": company, "rows": rows, "is_admin_view": True})


class AdminReportDetailView(AdminMixin, View):
    def get(self, request, reference_code, assignment_id):
        assignment = self.assignment()
        report = self.report(assignment)
        ctx = context_for(report)
        return render(
            request,
            "reports/report_detail.html",
            {
                "company": assignment.company,
                "report": report,
                "ctx": ctx,
                "sections": render_sections(ctx),
                "blockers": publishing.blockers(report) if report.status == Report.Status.DRAFT else [],
                "is_admin_view": True,
            },
        )


class AdminReportEditView(AdminMixin, View):
    template_name = "reports/report_form.html"

    def _locked(self, report):
        if report.status == Report.Status.PUBLISHED:
            messages.error(self.request, "Despublica el reporte para editarlo.")
            return redirect(self._detail_url())
        return None

    def _detail_url(self):
        return reverse("reports:admin_detail", args=[self.kwargs["reference_code"], self.kwargs["assignment_id"]])

    def _previous(self, assignment):
        return (
            Report.objects.filter(assignment__company=assignment.company)
            .exclude(assignment=assignment)
            .order_by("-created_at")
            .first()
        )

    def get(self, request, reference_code, assignment_id):
        assignment = self.assignment()
        report = self.report(assignment)
        if (locked := self._locked(report)) is not None:
            return locked
        initial, sig_initial = {}, []
        if report.pk is None and (prev := self._previous(assignment)) is not None:
            initial = {"evaluator_name": prev.evaluator_name, "evaluator_license": prev.evaluator_license}
            sig_initial = [{"title": s.title, "name": s.name} for s in prev.signatories.all()]
        form = ReportForm(instance=report, initial=initial)
        formset = SignatoryFormSet(instance=report, prefix="signatories", initial=sig_initial)
        formset.extra = max(len(sig_initial), 1)
        return render(request, self.template_name, {"form": form, "formset": formset, "company": assignment.company, "report": report, "is_admin_view": True})

    def post(self, request, reference_code, assignment_id):
        assignment = self.assignment()
        report = self.report(assignment)
        if (locked := self._locked(report)) is not None:
            return locked
        form = ReportForm(request.POST, instance=report)
        formset = SignatoryFormSet(request.POST, instance=report, prefix="signatories")
        if form.is_valid() and formset.is_valid():
            report = form.save()
            formset.instance = report
            formset.save()  # see forms.py for ORDER → order
            messages.success(request, "Reporte guardado.")
            return redirect(self._detail_url())
        return render(request, self.template_name, {"form": form, "formset": formset, "company": assignment.company, "report": report, "is_admin_view": True})


class AdminPublishView(AdminMixin, View):
    def post(self, request, reference_code, assignment_id):
        report = self.report(self.assignment())
        if report.pk is None:
            problems = publishing.blockers(report)
        else:
            problems = publishing.publish(report, request.user)
        if problems:
            for p in problems:
                messages.error(request, p)
        else:
            messages.success(request, "Reporte publicado.")
        return redirect("reports:admin_detail", reference_code, assignment_id)


class AdminUnpublishView(AdminMixin, View):
    def post(self, request, reference_code, assignment_id):
        report = self.report(self.assignment())
        if report.pk is not None and report.status == Report.Status.PUBLISHED:
            publishing.unpublish(report)
            messages.success(request, "Reporte despublicado.")
        return redirect("reports:admin_detail", reference_code, assignment_id)
```

(`View` returns 405 for methods without a handler, so GET on publish is 405.)

`apps/reports/urls.py`:

```python
from django.urls import path

from . import views

app_name = "reports"

_ADMIN = "empresas/<str:reference_code>/reportes/"

urlpatterns = [
    path(_ADMIN, views.AdminReportListView.as_view(), name="admin_list"),
    path(f"{_ADMIN}<int:assignment_id>/", views.AdminReportDetailView.as_view(), name="admin_detail"),
    path(f"{_ADMIN}<int:assignment_id>/editar/", views.AdminReportEditView.as_view(), name="admin_edit"),
    path(f"{_ADMIN}<int:assignment_id>/publicar/", views.AdminPublishView.as_view(), name="admin_publish"),
    path(f"{_ADMIN}<int:assignment_id>/despublicar/", views.AdminUnpublishView.as_view(), name="admin_unpublish"),
]
```

`config/urls.py`: add `path("", include(("apps.reports.urls", "reports"))),` after the core include. Check `core`'s `empresas/<str:reference_code>/` pattern does not shadow `empresas/<ref>/reportes/` — it doesn't (Django matches the full path).

- [ ] **Step 6: Templates.** `report_detail.html` extends `base_app.html` (`container_width` `max-w-5xl`), links `{% static 'css/report.css' %}` in a `{% block extra_head %}` if `base.html` has one (else add the `<link>` at the top of `content` — check `templates/base.html`), shows a back link to the company dashboard, the messages, the action bar (sticky top, `flex flex-wrap gap-2`): *Editar* (hidden when published), *Publicar* / *Despublicar* as POST forms with `{% csrf_token %}`, *Descargar PDF* (href added in Task 11), the state badge (*Borrador* / *Publicado el …*), the blockers list for drafts under *"Para publicar falta:"*, then `<article class="report-sheet">{% include "reports/_toc.html" %}{% include "reports/_document.html" %}</article>`. `report_list.html`: table/stack of `rows` with the option label, state (*Sin iniciar* / *Borrador* / *Publicado*), link *Abrir*. `report_form.html`: the form, the formset rows (title + name + *Eliminar* checkbox + a hidden ORDER field set by position), a note that new rows can be added by saving (one blank row always shown), *Guardar* / *Cancelar*.
- [ ] **Step 7: Entry links.** In `company_dashboard.html` inside the `can_view_insights` section, for `is_admin_view` add a link *Reporte de resultados* to `reports:admin_list`; in `company_results.html` next to the back link, `{% if is_admin_view %}` a link *Reporte* to `reports:admin_list`.
- [ ] **Step 8: Run to verify it passes.** `pytest apps/reports -v` — PASS.
- [ ] **Step 9: Verify and hand back.** `pytest && ruff check . && ruff format . && npm run build:css` — green. Stop; list files; propose: `feat(reports): Administrador pages to edit and publish the report`.

---

### Task 10: Ejecutivo principal pages and the dashboard card

**Files:**
- Modify: `apps/reports/views.py`, `apps/reports/urls.py`
- Modify: `templates/reports/report_list.html`, `templates/reports/report_detail.html` (reader mode: no action bar except *Descargar PDF*)
- Modify: `templates/core/company_dashboard.html` (card)
- Test: `apps/reports/tests/test_executive_views.py`

**Interfaces:**
- Produces URL names `exec_list`, `exec_detail`, `exec_pdf` (pdf wired in Task 11).

- [ ] **Step 1: Write the failing tests.** `apps/reports/tests/test_executive_views.py`:

```python
import pytest
from django.urls import reverse

from apps.accounts.roles import ROLES
from apps.reports import publishing
from apps.reports.models import Report

pytestmark = pytest.mark.django_db
READY = dict(issued_in="CDMX", activities_summary="A", evaluator_name="S", evaluator_license="1", conclusions="C")


@pytest.fixture
def exec_client(client, make_user_with_profile, bootstrap_groups, scored_assignment):
    user = make_user_with_profile(email="e@x.mx", company=scored_assignment.company)
    user.groups.add(bootstrap_groups[ROLES[1].name])
    client.force_login(user)
    return client


def _detail(a):
    return reverse("reports:exec_detail", args=[a.pk])


def test_draft_is_404(exec_client, scored_assignment):
    Report.objects.create(assignment=scored_assignment, **READY)
    assert exec_client.get(_detail(scored_assignment)).status_code == 404


def test_published_is_readable_and_listed(exec_client, scored_assignment, make_user):
    report = Report.objects.create(assignment=scored_assignment, **READY)
    publishing.publish(report, make_user(email="op@x.mx"))
    body = exec_client.get(reverse("reports:exec_list")).content.decode()
    assert "Abrir" in body
    resp = exec_client.get(_detail(scored_assignment))
    assert resp.status_code == 200
    html = resp.content.decode()
    assert "Despublicar" not in html and "Editar" not in html


def test_other_company_is_404(client, make_user_with_profile, bootstrap_groups, make_company, scored_assignment, make_user):
    report = Report.objects.create(assignment=scored_assignment, **READY)
    publishing.publish(report, make_user(email="op@x.mx"))
    other = make_company(name="Otra", legal_name="Otra SA")
    user = make_user_with_profile(email="o@x.mx", company=other)
    user.groups.add(bootstrap_groups[ROLES[1].name])
    client.force_login(user)
    assert client.get(_detail(scored_assignment)).status_code == 404


def test_secondary_exec_is_403(client, make_user_with_profile, bootstrap_groups, scored_assignment):
    user = make_user_with_profile(email="s@x.mx", company=scored_assignment.company)
    user.groups.add(bootstrap_groups[ROLES[2].name])
    client.force_login(user)
    assert client.get(reverse("reports:exec_list")).status_code == 403


def test_dashboard_card_links_to_reports(exec_client):
    body = exec_client.get(reverse("core:company_dashboard")).content.decode()
    assert reverse("reports:exec_list") in body
    assert "Reporte de resultados" in body
```

- [ ] **Step 2: Run to verify it fails.** `pytest apps/reports/tests/test_executive_views.py -v` — FAIL.
- [ ] **Step 3: Views and URLs.**

```python
class ExecutiveMixin(LoginRequiredMixin):
    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated and not request.user.has_perm("accounts.can_view_insights"):
            raise PermissionDenied
        return super().dispatch(request, *args, **kwargs)

    def own_company(self):
        profile = getattr(self.request.user, "profile", None)
        return profile.company if profile is not None and profile.company_id else None

    def published(self, company):
        return get_object_or_404(
            Report.objects.select_related("assignment__company"),
            assignment_id=self.kwargs["assignment_id"],
            assignment__company=company,
            assignment__survey__key=NOM035_SURVEY_KEY,
            status=Report.Status.PUBLISHED,
        )


class ExecutiveReportListView(ExecutiveMixin, View):
    def get(self, request):
        company = self.own_company()
        if company is None:
            return redirect("accounts:setup_profile")
        published = {
            r.assignment_id: r
            for r in Report.objects.filter(assignment__company=company, status=Report.Status.PUBLISHED)
        }
        rows = [
            {"option": o, "report": published[o.assignment.pk]}
            for o in assignment_options(company)
            if o.assignment.pk in published
        ]
        return render(request, "reports/report_list.html", {"company": company, "rows": rows, "is_admin_view": False})


class ExecutiveReportDetailView(ExecutiveMixin, View):
    def get(self, request, assignment_id):
        company = self.own_company()
        if company is None:
            return redirect("accounts:setup_profile")
        report = self.published(company)
        ctx = context_for(report)
        return render(request, "reports/report_detail.html", {
            "company": company, "report": report, "ctx": ctx,
            "sections": render_sections(ctx), "blockers": [], "is_admin_view": False,
        })
```

URLs: `path("tablero-empresa/reportes/", ..., name="exec_list")`, `path("tablero-empresa/reportes/<int:assignment_id>/", ..., name="exec_detail")`.

- [ ] **Step 4: Templates.** `report_detail.html`: wrap *Editar/Publicar/Despublicar* and the blockers in `{% if is_admin_view %}`. `report_list.html`: for executives, empty state *"Aún no hay reportes publicados."*; links to `exec_detail`. Dashboard card: below the *Valoración de resultados* section, `{% if perms.accounts.can_view_insights and not is_admin_view %}` a second card *Reporte de resultados* linking to `reports:exec_list` with the copy *"Consulta y descarga los reportes publicados."* and *"Ver reportes"* — same card classes as the results card.
- [ ] **Step 5: Run to verify it passes.** `pytest apps/reports apps/core -v` — PASS.
- [ ] **Step 6: Verify and hand back.** `pytest && ruff check . && ruff format . && npm run build:css` — green. Stop; list files; propose: `feat(reports): Ejecutivo principal reads published reports`.

---

### Task 11: PDF rendering

**Files:**
- Create: `apps/reports/pdf.py`
- Create: `templates/reports/base_report.html`, `templates/reports/report_pdf.html`
- Create: `static/css/report-print.css`; if Task 1 recorded `CHARTS_CSS = "shim"`, also `static/css/report-charts.css`
- Create: `static/fonts/` — the Source Serif 4 and Source Sans 3 files chosen in Task 1, plus `static/fonts/OFL.txt`
- Modify: `apps/reports/views.py`, `apps/reports/urls.py`, `templates/reports/report_detail.html` (PDF button href)
- Test: `apps/reports/tests/test_pdf.py`

**Interfaces:**
- Produces: `pdf.render_report_pdf(report) -> bytes`, `pdf.static_fetcher(url) -> dict`, `pdf.filename(report) -> str`; URL names `admin_pdf`, `exec_pdf`.

- [ ] **Step 1: Write the failing tests.** `apps/reports/tests/test_pdf.py`:

```python
import pytest
from django.urls import reverse

from apps.accounts.roles import ROLES
from apps.reports import pdf, publishing
from apps.reports.models import Report

pytestmark = pytest.mark.django_db
READY = dict(issued_in="CDMX", activities_summary="A", evaluator_name="S", evaluator_license="1", conclusions="C")


def test_render_report_pdf_produces_pages(scored_assignment):
    data = pdf.render_report_pdf(Report(assignment=scored_assignment))
    assert data.startswith(b"%PDF")
    assert len(data) > 10_000


def test_static_fetcher_refuses_non_static_urls():
    with pytest.raises(ValueError):
        pdf.static_fetcher("https://example.com/x.css")


def test_static_fetcher_serves_static_files():
    result = pdf.static_fetcher(f"{pdf.BASE_URL}static/css/report.css")
    assert result["mime_type"] == "text/css"
    assert b"report-sheet" in result["string"]


def test_filename(scored_assignment):
    report = Report(assignment=scored_assignment)
    name = pdf.filename(report)
    assert name.startswith(f"reporte-nom035-{scored_assignment.company.reference_code}-")
    assert name.endswith(".pdf")


def test_admin_pdf_draft_has_watermark_html(client, make_user, bootstrap_groups, scored_assignment, monkeypatch):
    captured = {}
    monkeypatch.setattr(pdf, "_write_pdf", lambda html: captured.setdefault("html", html) and b"%PDF-1.7")
    user = make_user(email="op@x.mx")
    user.groups.add(bootstrap_groups[ROLES[0].name])
    client.force_login(user)
    url = reverse("reports:admin_pdf", args=[scored_assignment.company.reference_code, scored_assignment.pk])
    resp = client.get(url)
    assert resp["Content-Type"] == "application/pdf"
    assert "attachment;" in resp["Content-Disposition"]
    assert "BORRADOR" in captured["html"]


def test_exec_pdf_only_when_published(client, make_user_with_profile, make_user, bootstrap_groups, scored_assignment, monkeypatch):
    monkeypatch.setattr(pdf, "_write_pdf", lambda html: b"%PDF-1.7")
    user = make_user_with_profile(email="e@x.mx", company=scored_assignment.company)
    user.groups.add(bootstrap_groups[ROLES[1].name])
    client.force_login(user)
    url = reverse("reports:exec_pdf", args=[scored_assignment.pk])
    report = Report.objects.create(assignment=scored_assignment, **READY)
    assert client.get(url).status_code == 404
    publishing.publish(report, make_user(email="op@x.mx"))
    assert client.get(url).status_code == 200
```

- [ ] **Step 2: Run to verify it fails.** `pytest apps/reports/tests/test_pdf.py -v` — FAIL.
- [ ] **Step 3: Fonts.** Copy the font files Task 1 settled on into `static/fonts/` with `OFL.txt`. Update the `@font-face` rules at the top of `static/css/report.css` to their real filenames (`font-weight: 200 900` for variable files; one rule per weight for static files).
- [ ] **Step 4: `pdf.py`.**

```python
"""The report as a letter-size PDF, rendered by WeasyPrint from the screen partials."""

import mimetypes

from django.contrib.staticfiles import finders
from django.template.loader import render_to_string
from django.utils import timezone

from apps.reports.sections import context_for, render_sections

BASE_URL = "https://reporte.sofias.invalid/"
_STATIC = f"{BASE_URL}static/"


def static_fetcher(url):
    """Resolve the report's fonts, CSS and images from static files; nothing else."""
    if not url.startswith(_STATIC):
        raise ValueError(f"El PDF solo carga archivos estáticos: {url}")
    path = finders.find(url[len(_STATIC):])
    if path is None:
        raise ValueError(f"Archivo estático no encontrado: {url}")
    with open(path, "rb") as fh:
        data = fh.read()
    return {"string": data, "mime_type": mimetypes.guess_type(path)[0] or "application/octet-stream"}


def _write_pdf(html: str) -> bytes:
    from weasyprint import HTML

    return HTML(string=html, base_url=BASE_URL, url_fetcher=static_fetcher).write_pdf()


def render_report_pdf(report) -> bytes:
    ctx = context_for(report)
    html = render_to_string(
        "reports/report_pdf.html",
        {"ctx": ctx, "sections": render_sections(ctx), "report": report},
    )
    return _write_pdf(html)


def filename(report) -> str:
    day = timezone.localdate(report.published_at) if report.published_at else timezone.localdate()
    code = report.assignment.company.reference_code
    return f"reporte-nom035-{code}-{day:%Y-%m}.pdf"
```

If Task 1 showed the installed WeasyPrint requires a `URLFetcher` object rather than a function, wrap `static_fetcher` accordingly and keep the function as the testable unit.

- [ ] **Step 5: Templates.** `base_report.html` — standalone document (no `{% static %}` host: links are relative to `BASE_URL`):

```django
<!doctype html>
<html lang="es">
<head>
  <meta charset="utf-8">
  <title>Reporte de resultados — {{ ctx.data.company.legal_name }}</title>
  <link rel="stylesheet" href="static/css/output.css">   {# omit when CHARTS_CSS = "shim"; use static/css/report-charts.css instead #}
  <link rel="stylesheet" href="static/css/report.css">
  <link rel="stylesheet" href="static/css/report-print.css">
</head>
<body class="report-print">
  {% if ctx.draft %}<div class="report-watermark" aria-hidden="true">BORRADOR</div>{% endif %}
  <div class="report-running-name">{{ ctx.data.company.legal_name }}</div>
  {% block document %}{% endblock %}
</body>
</html>
```

`report_pdf.html` extends it and fills `document` with `{% include "reports/_toc.html" %}{% include "reports/_document.html" %}`.

`static/css/report-print.css`:

```css
@page {
  size: letter;
  margin: 2.2cm 2cm 2cm;
  @top-center { content: string(company); font: 9pt "Source Sans 3"; color: #4B5563; }
  @bottom-right { content: "Página " counter(page) " de " counter(pages); font: 9pt "Source Sans 3"; color: #4B5563; }
}
@page :first { @top-center { content: none; } @bottom-right { content: none; } }
.report-running-name { string-set: company content(); display: none; }
.report-watermark {
  position: fixed; top: 45%; left: 0; right: 0; text-align: center;
  transform: rotate(-30deg); font: 700 72pt "Source Sans 3"; color: rgba(239, 68, 68, 0.12);
}
.report-section--portada { break-after: page; }
.report-section--resultados, .report-section--anexo { break-before: page; }
.report-finding, .report-chart, .report-table tr, .report-criterion { break-inside: avoid; }
.report-table thead { display: table-header-group; }
.report-toc a::after { content: leader(".") target-counter(attr(href), page); }
.report-sheet { max-width: none; padding: 0; box-shadow: none; }
```

Name the portada's wrapper so `report-section--portada` matches the `_document.html` class (`report-section--{{ s.key|slugify }}`). If `CHARTS_CSS = "shim"`, `report-charts.css` defines the classes the four chart component templates use (grep `templates/components/charts/*.html` and `apps/core/templatetags/charts.py` `_COLORS` for the exact list) with hex values.

- [ ] **Step 6: Views and URLs.**

```python
def _pdf_response(report):
    from django.http import HttpResponse

    from apps.reports import pdf

    response = HttpResponse(pdf.render_report_pdf(report), content_type="application/pdf")
    response["Content-Disposition"] = f'attachment; filename="{pdf.filename(report)}"'
    return response


class AdminReportPdfView(AdminMixin, View):
    def get(self, request, reference_code, assignment_id):
        return _pdf_response(self.report(self.assignment()))


class ExecutiveReportPdfView(ExecutiveMixin, View):
    def get(self, request, assignment_id):
        company = self.own_company()
        if company is None:
            return redirect("accounts:setup_profile")
        return _pdf_response(self.published(company))
```

URLs: `f"{_ADMIN}<int:assignment_id>/pdf/"` → `admin_pdf`; `"tablero-empresa/reportes/<int:assignment_id>/pdf/"` → `exec_pdf`. Point the *Descargar PDF* button at the matching name in `report_detail.html`.

- [ ] **Step 7: Run to verify it passes.** `pytest apps/reports -v` — PASS (the first test really runs WeasyPrint).
- [ ] **Step 8: Look at it.** Render a PDF from `python manage.py shell` for a seeded company (or the test fixture data), `pdftoppm -r 60 -png` a cover, a results page and an annex page into scratch, and read them. Check: cover alone on page 1, running header from page 2, *Página N de M*, TOC page numbers, charts colored, no split finding blocks, watermark on a draft. Fix CSS until it holds.
- [ ] **Step 9: Verify and hand back.** `pytest && ruff check . && ruff format . && npm run build:css` — green. Stop; list files; propose: `feat(reports): letter-size PDF with WeasyPrint`.

---

### Task 12: Phone layout, build and manual verification

**Files:**
- Modify: report templates / `static/css/report.css` as the checks require
- Modify: `static/css/output.css` (rebuilt)

- [ ] **Step 1: Build.** `npm run build:css`.
- [ ] **Step 2: Automated floor.** `pytest apps/core/tests/test_responsive.py -v` — PASS.
- [ ] **Step 3: Manual checklist for the user** (the user eyeballs browser changes themselves — do not install browser tooling). Write it into the PR description draft:
  - 360 px: report detail (admin draft and executive), list pages, edit form — no horizontal scroll; tables stacked one block per row; action bar wraps; charts scale.
  - Desktop: TOC links jump to sections; *Publicar* refusal lists reasons; publish → executive sees it on the dashboard card; unpublish → executive gets 404.
  - Django admin: `Company` change form shows *actividad principal* and *centro de trabajo*.
  - PDF (draft and published): cover, running header, *Página N de M*, TOC numbers, watermark only on drafts, chart colors, no split blocks, Guía II report shows only Guía II tables in the annex.
- [ ] **Step 4: Full suite.** `pytest && ruff check . && ruff format --check . && python manage.py check && python manage.py makemigrations --check --dry-run` — all green.
- [ ] **Step 5: Hand back.** Stop; list files; propose: `chore(reports): phone layout pass and rebuilt CSS`.

---

### Task 13: Documentation (always last)

**Files:**
- Modify: `docs/platform/nom-035-report.md` (post-ship form)
- Modify: `apps/reports/CLAUDE.md`, `apps/nom035/CLAUDE.md`, `.claude/CLAUDE.md` (Architecture block, registered apps, Cross-cutting survey data flow)
- Modify: `docs/platform/overview.md` (`reports` row and the paragraph at lines 63–64)
- Modify: `docs/platform/nom-035-results-dashboard.md` (out-of-scope bullet: link to the report doc instead of "the downloadable/PDF report itself")
- Modify: `docs/platform/nom-035-analytics.md` (out-of-scope "downloadable/static PDF report (Iniciativa 2)" → link to the report doc; any sentence about `action_text` wording)

- [ ] **Step 1: Feature doc.** Rewrite `nom-035-report.md` in present tense as the shipped feature: `Status: Current — implemented in apps/reports, aggregates in apps/nom035/results.py`; replace *Where the code will live* with *Where the code lives* (actual paths); move the WeasyPrint open question out (record the Task 1 outcome as a *Key decision*: which CSS the PDF loads, which font files); keep the expert points under *Open questions* as links to `nom-035-valoracion-supuestos.md`; resolve the reference-material question with where the files ended up. No migration commentary.
- [ ] **Step 2: App docs.** `apps/reports/CLAUDE.md` — replace the placeholder text with: what lives in each module (`models`, `snapshot`, `text`, `content`, `sections`, `publishing`, `pdf`, `views`), the registry as the place to change the report's structure, `report.css` being plain CSS on purpose, the snapshot shape rule (change → republish), and the PDF static-only fetcher. `apps/nom035/CLAUDE.md` — add `report_results` and its dataclasses to the `results.py` bullet; describe `action_text` as the norm's verbatim action criteria.
- [ ] **Step 3: Project docs.** `.claude/CLAUDE.md`: in *Architecture* change the `reports/` line to `# NOM-035 results report: draft/publish, snapshot, PDF  → apps/reports/CLAUDE.md`; add `apps.reports` to the registered-apps sentence and drop the "empty stub" sentence; in *Survey data flow* append `→ apps/reports freezes a published report per closed assignment`. `overview.md`: `reports` row → implemented. Dashboard and analytics docs: the link edits above.
- [ ] **Step 4: Scaffolding check.** `docs/platform/wip/` will be cleaned after merge (README only); `docs/temporal/` must be empty or gone if its files were moved in Task 4.
- [ ] **Step 5: Verify and hand back.** `pytest && ruff check .` — green; `grep -rn "placeholder\|not yet implemented\|stub" apps/reports/CLAUDE.md docs/platform/overview.md` — nothing stale. Stop; list files; propose: `docs: NOM-035 report feature doc and app docs`.
