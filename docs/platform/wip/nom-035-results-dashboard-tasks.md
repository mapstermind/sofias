# NOM-035 Results Dashboard Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** A per-company NOM-035 results page — one assignment at a time, one global filter bar, server-rendered SVG charts swapped in place — replacing the dashboard's "Valoración de resultados" section.

**Architecture:** `apps/nom035/results.py` turns one assignment plus a validated filter into a tree of frozen dataclasses, applying the small-group rule itself. `apps/core` parses the query string (`results_query.py`), computes instrument-agnostic chart geometry (`charts.py`), renders it through three inclusion tags, and serves a page plus a fragment URL that `static/ts/results_dashboard.ts` swaps into `#results-body`.

**Tech Stack:** Django 6.0, PostgreSQL 17, pytest + pytest-django, Tailwind v4 (`npm run build:css`), TypeScript via `tsc` (`npm run build:js`). No new dependency.

**Spec:** [`docs/platform/nom-035-results-dashboard.md`](../nom-035-results-dashboard.md) — read it before starting any task; this plan argues from it.

## Global Constraints

- User-facing copy is Spanish; code, comments, identifiers and test names are English.
- Every new model field has an explicit lowercase Spanish `verbose_name` (`assert_explicit_labels` enforces it).
- No new Python or npm dependency.
- `MIN_GROUP_SIZE = 5`. A set *S* out of base *B* shows only when `|S| >= 5` and `|B| - |S|` is `0` or `>= 5`, for viewers without `accounts.can_view_small_groups`.
- The suppression message is exactly: `Grupo demasiado pequeño para mostrar resultados sin identificar a las personas (mínimo 5)`.
- Any number written into an SVG attribute renders inside `{% localize off %}`.
- Tailwind classes live only in `templates/`, `apps/**/templatetags/*.py`, `apps/**/forms.py`, `static/ts/` — nowhere else compiles.
- `<fieldset>`/`<legend>` carry `m-0 p-0 border-0 min-w-0`.
- Every page works at 360px with no horizontal scroll; mobile-first classes (`flex-col md:flex-row`).
- Colors: NDR from `valuation_extras.py`; Femenino `violet-600`, Masculino `sky-600`, Sin dato `gray-300`, age columns `indigo-500`, Guía I none/event/positive `gray-300`/`amber-500`/`red-500`.
- Views authorize on permission codenames, never group names.
- Run `ruff format .` and `ruff check .` before each commit; `pytest` stays green after every task.
- All work happens on branch `feat/nom-035-results-dashboard`; never commit to `main`.

---

### Task 1: Store `guia1_event` on `SubmissionScore`

**Files:**
- Modify: `apps/nom035/scoring.py` (`ScoreResult`, `score_submission`)
- Modify: `apps/nom035/services.py` (`materialize`)
- Modify: `apps/nom035/models.py` (`SubmissionScore`)
- Create: `apps/nom035/migrations/0003_submissionscore_guia1_event.py` (via `makemigrations`)
- Test: `apps/nom035/tests/test_score_submission.py`, `apps/nom035/tests/test_materialize.py`

**Interfaces:**
- Produces: `ScoreResult.guia1_event: bool`; `SubmissionScore.guia1_event: BooleanField`.

- [ ] **Step 1: Write the failing tests**

Append to `apps/nom035/tests/test_score_submission.py`:

```python
def test_guia1_event_true_when_trigger_answered_yes(nom035_assignment):
    sub = SurveySubmission.objects.create(
        assignment=nom035_assignment, status=SurveySubmission.Status.COMPLETED
    )
    codes = {
        q.code: q for q in Question.objects.filter(survey=nom035_assignment.survey)
    }
    # Event, but below every section threshold: an event without a referral.
    _answer_guia1(sub, codes, event=True, yes_codes=["g1-4"])

    result = score_submission(sub)
    assert result.guia1_event is True
    assert result.guia1_positive is False


def test_guia1_event_false_without_trigger(nom035_assignment):
    sub = SurveySubmission.objects.create(
        assignment=nom035_assignment, status=SurveySubmission.Status.COMPLETED
    )
    codes = {
        q.code: q for q in Question.objects.filter(survey=nom035_assignment.survey)
    }
    _answer_guia1(sub, codes, event=False, yes_codes=["g1-2"])

    assert score_submission(sub).guia1_event is False


def test_guia1_positive_implies_event(nom035_assignment):
    sub = SurveySubmission.objects.create(
        assignment=nom035_assignment, status=SurveySubmission.Status.COMPLETED
    )
    codes = {
        q.code: q for q in Question.objects.filter(survey=nom035_assignment.survey)
    }
    _answer_guia1(sub, codes, event=True, yes_codes=["g1-2"])

    result = score_submission(sub)
    assert result.guia1_positive is True
    assert result.guia1_event is True
```

Read `apps/nom035/tests/test_materialize.py` for its fixtures, then append a test that completes a submission answering `g1-1` "Sí" and asserts `SubmissionScore.objects.get(submission=sub).guia1_event is True`, using the same setup that file already uses to create a completed NOM-035 submission.

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest apps/nom035/tests/test_score_submission.py apps/nom035/tests/test_materialize.py -v`
Expected: FAIL — `AttributeError: 'ScoreResult' object has no attribute 'guia1_event'`.

- [ ] **Step 3: Implement**

`apps/nom035/scoring.py` — add the field and return it:

```python
@dataclass(frozen=True)
class ScoreResult:
    final_score: int
    final_ndr: str
    groups: list[GroupResult]
    guia1_positive: bool
    guia1_event: bool
```

and in `score_submission` change the return to:

```python
    return ScoreResult(
        final_score=final,
        final_ndr=final_ndr,
        groups=groups,
        guia1_positive=positive,
        guia1_event=event,
    )
```

`apps/nom035/models.py` — below `guia1_positive`:

```python
    # Guía I Sección I answered "Sí": a severe traumatic event occurred. Always
    # true when guia1_positive is; see scoring.score_submission.
    guia1_event = models.BooleanField(
        "acontecimiento traumático severo", default=False
    )
```

`apps/nom035/services.py` — add `"guia1_event": result.guia1_event,` to `defaults`.

Run: `python manage.py makemigrations nom035 --name submissionscore_guia1_event`

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest apps/nom035 -v`
Expected: PASS (including `test_recompute_command.py`, which now backfills the column through `materialize`).

- [ ] **Step 5: Commit**

```bash
git add apps/nom035
git commit -m "feat(nom035): store the Guía I traumatic-event flag"
```

---

### Task 2: `can_view_small_groups` permission

**Files:**
- Modify: `apps/accounts/models.py` (`Role.Meta.permissions`)
- Modify: `apps/accounts/management/commands/bootstrap_groups.py` (`GROUP_PERMISSIONS`)
- Create: the next `apps/accounts/migrations/0009_*.py` (via `makemigrations`; Django names it)
- Test: `apps/accounts/tests/test_roles.py`

**Interfaces:**
- Produces: permission `accounts.can_view_small_groups`, held by the `Admins` group only.

- [ ] **Step 1: Write the failing test**

Append to `apps/accounts/tests/test_roles.py`:

```python
def test_only_admins_may_view_small_groups():
    from apps.accounts.management.commands.bootstrap_groups import GROUP_PERMISSIONS

    holders = {
        name for name, codenames in GROUP_PERMISSIONS.items()
        if "can_view_small_groups" in codenames
    }
    assert holders == {"Admins"}


@pytest.mark.django_db
def test_small_groups_permission_exists():
    from django.contrib.auth.models import Permission

    perm = Permission.objects.get(codename="can_view_small_groups")
    assert perm.content_type.app_label == "accounts"
```

(Add `import pytest` at the top if the file lacks it.)

- [ ] **Step 2: Run to verify failure**

Run: `pytest apps/accounts/tests/test_roles.py -v`
Expected: FAIL — `holders == set()` and `Permission.DoesNotExist`.

- [ ] **Step 3: Implement**

In `Role.Meta.permissions` append:

```python
            ("can_view_small_groups", "Puede ver resultados de grupos pequeños"),
```

In `GROUP_PERMISSIONS`, Administrador list, append `"can_view_small_groups",`.

Run: `python manage.py makemigrations accounts`

- [ ] **Step 4: Run to verify pass**

Run: `pytest apps/accounts apps/core/tests/test_localization.py -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add apps/accounts
git commit -m "feat(accounts): add can_view_small_groups for Administrador"
```

---

### Task 3: Age bands (`apps/accounts/demographics.py`)

**Files:**
- Create: `apps/accounts/demographics.py`
- Modify: `apps/accounts/models.py` (`UserProfile.age` delegates to `age_on`)
- Test: `apps/accounts/tests/test_demographics.py`

**Interfaces:**
- Produces:
  - `AgeBand(slug: str, label: str, lower: int, upper: int | None)` (frozen dataclass)
  - `AGE_BANDS: tuple[AgeBand, ...]` — `15-19` … `55-59`, `60-mas`
  - `band_by_slug(slug: str) -> AgeBand | None`
  - `age_on(date_of_birth: date, today: date) -> int`
  - `age_band(age: int | None) -> AgeBand | None`
  - `birth_date_range(band: AgeBand, today: date) -> tuple[date | None, date]` — inclusive `(earliest, latest)`

- [ ] **Step 1: Write the failing tests**

```python
from datetime import date, timedelta

import pytest

from apps.accounts.demographics import (
    AGE_BANDS,
    age_band,
    age_on,
    band_by_slug,
    birth_date_range,
)


def test_bands_are_contiguous_five_year_steps_then_sixty_plus():
    assert [b.slug for b in AGE_BANDS] == [
        "15-19", "20-24", "25-29", "30-34", "35-39",
        "40-44", "45-49", "50-54", "55-59", "60-mas",
    ]
    assert AGE_BANDS[0].label == "15–19"
    assert AGE_BANDS[-1].label == "60 o más"
    assert AGE_BANDS[-1].upper is None


@pytest.mark.parametrize(
    ("age", "slug"),
    [(15, "15-19"), (19, "15-19"), (20, "20-24"), (59, "55-59"), (60, "60-mas"), (99, "60-mas")],
)
def test_age_band_edges(age, slug):
    assert age_band(age).slug == slug


def test_age_band_outside_or_missing():
    assert age_band(14) is None
    assert age_band(None) is None


def test_band_by_slug():
    assert band_by_slug("25-29").lower == 25
    assert band_by_slug("nonsense") is None


def test_age_on_counts_completed_years():
    assert age_on(date(2000, 9, 21), date(2026, 9, 21)) == 26
    assert age_on(date(2000, 9, 22), date(2026, 9, 21)) == 25


@pytest.mark.parametrize("today", [date(2026, 9, 21), date(2028, 2, 29), date(2027, 2, 28)])
def test_birth_date_range_agrees_with_age_band(today):
    """Every date of birth inside a band's range has an age in that band, and
    every date just outside does not — including around 29 February."""
    for band in AGE_BANDS:
        earliest, latest = birth_date_range(band, today)
        assert age_band(age_on(latest, today)) == band
        assert age_band(age_on(latest + timedelta(days=1), today)) != band
        if earliest is not None:
            assert age_band(age_on(earliest, today)) == band
            assert age_band(age_on(earliest - timedelta(days=1), today)) != band
```

- [ ] **Step 2: Run to verify failure**

Run: `pytest apps/accounts/tests/test_demographics.py -v`
Expected: FAIL — `ModuleNotFoundError: apps.accounts.demographics`.

- [ ] **Step 3: Implement `apps/accounts/demographics.py`**

```python
"""Age bands for demographic breakdowns.

Instrument-agnostic: it describes `UserProfile`, so any results page or roster
may group by it. Age is derived as of a given day (ADR-0005), never stored.
"""

from dataclasses import dataclass
from datetime import date, timedelta


@dataclass(frozen=True)
class AgeBand:
    slug: str
    label: str
    lower: int
    upper: int | None  # inclusive; None for the open-ended last band


AGE_BANDS: tuple[AgeBand, ...] = (
    *(AgeBand(f"{lo}-{lo + 4}", f"{lo}–{lo + 4}", lo, lo + 4) for lo in range(15, 60, 5)),
    AgeBand("60-mas", "60 o más", 60, None),
)

_BY_SLUG = {band.slug: band for band in AGE_BANDS}


def band_by_slug(slug: str) -> AgeBand | None:
    return _BY_SLUG.get(slug)


def age_on(date_of_birth: date, today: date) -> int:
    """Completed years on `today`."""
    birthday_passed = (today.month, today.day) >= (date_of_birth.month, date_of_birth.day)
    return today.year - date_of_birth.year - (0 if birthday_passed else 1)


def age_band(age: int | None) -> AgeBand | None:
    if age is None:
        return None
    for band in AGE_BANDS:
        if age >= band.lower and (band.upper is None or age <= band.upper):
            return band
    return None


def _years_before(day: date, years: int) -> date:
    try:
        return day.replace(year=day.year - years)
    except ValueError:  # 29 February in a non-leap target year
        return day.replace(year=day.year - years, day=28)


def birth_date_range(band: AgeBand, today: date) -> tuple[date | None, date]:
    """Inclusive (earliest, latest) date of birth whose age on `today` is in `band`.

    `earliest` is None for the open-ended band. Filtering by this range in the
    database gives the same answer as `age_band(age_on(dob, today))`.
    """
    latest = _years_before(today, band.lower)
    if band.upper is None:
        return None, latest
    earliest = _years_before(today, band.upper + 1) + timedelta(days=1)
    return earliest, latest
```

If the 29-February case fails the agreement test, fix `_years_before` so that `birth_date_range` and `age_on` agree — the test is the contract, not this sketch.

Then make `UserProfile.age` in `apps/accounts/models.py` delegate (keep its docstring):

```python
        if self.date_of_birth is None:
            return None
        return age_on(self.date_of_birth, timezone.localdate())
```

with `from apps.accounts.demographics import age_on` at the top of `models.py`.

- [ ] **Step 4: Run to verify pass**

Run: `pytest apps/accounts -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add apps/accounts
git commit -m "feat(accounts): add five-year age bands"
```

---

### Task 4: Shared query readers and `ResultsQuery`

**Files:**
- Create: `apps/core/query_params.py`
- Modify: `apps/core/roster.py` (import the shared readers; keep behavior)
- Create: `apps/core/results_query.py`
- Test: `apps/core/tests/test_results_query.py`; existing `apps/core/tests/test_roster.py` must stay green unchanged except for imports of moved names

**Interfaces:**
- Produces in `query_params.py`: `values(params, key) -> list[str]`, `valid_pks(raw_values, valid_ids: set[int]) -> tuple[int, ...]`, `SEX_SLUGS: dict[str, str]`, `SEX_SLUGS_TO_LABELS: dict[str, str]`, `first_sex(params) -> tuple[str, str]` (stored value, slug; `("", "")` when none).
- Produces in `results_query.py`:
  - `ResultsQuery(assignment_id: int | None, sex: str, sex_slug: str, age_slugs: tuple[str, ...], area_ids: tuple[int, ...], location_ids: tuple[int, ...])`, frozen, with `is_filtered: bool` property and `params() -> list[tuple[str, str]]`
  - `parse_results_query(params, *, assignment_ids: set[int], area_ids: set[int], location_ids: set[int]) -> ResultsQuery`
  - `results_url(base: str, query: ResultsQuery, *, drop: tuple[str, str] | None = None, add: tuple[str, str] | None = None) -> str`
  - `Pill(label: str, remove_url: str)`; `filter_pills(query, base, *, area_names: dict[int, str], location_names: dict[int, str]) -> list[Pill]`

- [ ] **Step 1: Move the readers (refactor, no behavior change)**

Create `apps/core/query_params.py` holding `_values` → `values`, `_valid_pk`, `_valid_pks` → `valid_pks`, `SEX_SLUGS`, `SEX_SLUGS_TO_LABELS`, moved verbatim from `roster.py` with their docstrings, plus:

```python
def first_sex(params) -> tuple[str, str]:
    """The first `sexo` value that names a sex we know, as (stored, slug).

    `QueryDict.get()` returns the LAST value, which would let an unrecognized
    value shadow a valid one before it.
    """
    for candidate in values(params, "sexo"):
        stored = SEX_SLUGS.get(candidate.strip())
        if stored:
            return stored, candidate.strip()
    return "", ""
```

In `roster.py`, import `SEX_SLUGS`, `SEX_SLUGS_TO_LABELS`, `first_sex`, `valid_pks`, `values` from `apps.core.query_params`, replace the inline sex loop in `parse_roster_query` with `sex, sex_slug = first_sex(params)`, and replace `_values`/`_valid_pks` calls. Keep `roster.SEX_SLUGS` and `roster.SEX_SLUGS_TO_LABELS` importable (they are now re-exported names) so templates and tests that use them keep working. Grep for `roster._values`, `roster._valid_pks`, `roster.SEX_SLUGS` across `apps/` and `templates/` and update any reference.

Run: `pytest apps/core/tests/test_roster.py apps/core/tests/test_views.py -v`
Expected: PASS, unchanged.

- [ ] **Step 2: Write the failing `ResultsQuery` tests** (`apps/core/tests/test_results_query.py`)

```python
from apps.core.results_query import (
    ResultsQuery,
    filter_pills,
    parse_results_query,
    results_url,
)


def _parse(params, **ids):
    return parse_results_query(
        params,
        assignment_ids=ids.get("assignment_ids", {7}),
        area_ids=ids.get("area_ids", {1, 2}),
        location_ids=ids.get("location_ids", {5}),
    )


def test_empty_query_is_unfiltered():
    query = _parse({})
    assert query == ResultsQuery()
    assert not query.is_filtered


def test_parses_every_dimension():
    query = _parse(
        {"encuesta": "7", "sexo": "femenino", "edad": ["25-29", "20-24"],
         "area": ["2", "1"], "localidad": "5"}
    )
    assert query.assignment_id == 7
    assert (query.sex, query.sex_slug) == ("female", "femenino")
    assert query.age_slugs == ("20-24", "25-29")  # band order, not URL order
    assert query.area_ids == (2, 1)
    assert query.location_ids == (5,)
    assert query.is_filtered


def test_ignores_foreign_and_malformed_values():
    query = _parse(
        {"encuesta": "99", "sexo": "otro", "edad": ["abc", "25-29", "25-29"],
         "area": ["3", "x", "1"], "localidad": "6"}
    )
    assert query.assignment_id is None
    assert query.sex == ""
    assert query.age_slugs == ("25-29",)
    assert query.area_ids == (1,)
    assert query.location_ids == ()


def test_assignment_alone_is_not_a_filter():
    assert not _parse({"encuesta": "7"}).is_filtered


def test_results_url_round_trips_and_edits():
    query = _parse({"encuesta": "7", "sexo": "femenino", "area": ["1", "2"]})
    base = "/tablero-empresa/resultados/"
    assert results_url(base, query) == base + "?encuesta=7&sexo=femenino&area=1&area=2"
    assert results_url(base, query, drop=("area", "1")) == base + "?encuesta=7&sexo=femenino&area=2"
    assert results_url(base, query, add=("localidad", "5")).endswith("&localidad=5")
    assert results_url(base, query, add=("area", "1")).count("area=1") == 1
    assert results_url(base, ResultsQuery()) == base


def test_filter_pills_label_and_remove_one_value():
    query = _parse({"encuesta": "7", "sexo": "masculino", "edad": "30-34", "area": "1", "localidad": "5"})
    pills = filter_pills(query, "/r/", area_names={1: "Operaciones"}, location_names={5: "Matriz"})
    assert [p.label for p in pills] == ["Masculino", "30–34", "Operaciones", "Matriz"]
    assert pills[2].remove_url == "/r/?encuesta=7&sexo=masculino&edad=30-34&localidad=5"
```

- [ ] **Step 3: Run to verify failure**

Run: `pytest apps/core/tests/test_results_query.py -v`
Expected: FAIL — `ModuleNotFoundError`.

- [ ] **Step 4: Implement `apps/core/results_query.py`**

```python
"""Query-string parsing for the NOM-035 results page.

Same rule as the roster: an absent, empty, unrecognized or foreign-company
value is ignored, never an error. Spanish slugs in, English values out.
"""

from dataclasses import dataclass
from urllib.parse import urlencode

from apps.accounts.demographics import AGE_BANDS, band_by_slug
from apps.core.query_params import SEX_SLUGS_TO_LABELS, first_sex, valid_pks, values


@dataclass(frozen=True)
class ResultsQuery:
    assignment_id: int | None = None
    sex: str = ""
    sex_slug: str = ""
    age_slugs: tuple[str, ...] = ()
    area_ids: tuple[int, ...] = ()
    location_ids: tuple[int, ...] = ()

    @property
    def is_filtered(self) -> bool:
        """Whether the group is narrower than the whole assignment."""
        return bool(self.sex or self.age_slugs or self.area_ids or self.location_ids)

    def params(self) -> list[tuple[str, str]]:
        pairs = []
        if self.assignment_id is not None:
            pairs.append(("encuesta", str(self.assignment_id)))
        if self.sex_slug:
            pairs.append(("sexo", self.sex_slug))
        pairs += [("edad", slug) for slug in self.age_slugs]
        pairs += [("area", str(pk)) for pk in self.area_ids]
        pairs += [("localidad", str(pk)) for pk in self.location_ids]
        return pairs


def parse_results_query(params, *, assignment_ids, area_ids, location_ids) -> ResultsQuery:
    assignment = valid_pks(values(params, "encuesta")[:1], assignment_ids)
    sex, sex_slug = first_sex(params)
    wanted = {raw.strip() for raw in values(params, "edad")}
    return ResultsQuery(
        assignment_id=assignment[0] if assignment else None,
        sex=sex,
        sex_slug=sex_slug,
        age_slugs=tuple(band.slug for band in AGE_BANDS if band.slug in wanted),
        area_ids=valid_pks(values(params, "area"), area_ids),
        location_ids=valid_pks(values(params, "localidad"), location_ids),
    )


def results_url(base, query, *, drop=None, add=None) -> str:
    pairs = [pair for pair in query.params() if pair != drop]
    if add is not None and add not in pairs:
        pairs.append(add)
    return f"{base}?{urlencode(pairs)}" if pairs else base


@dataclass(frozen=True)
class Pill:
    label: str
    remove_url: str


def filter_pills(query, base, *, area_names, location_names) -> list[Pill]:
    entries = []
    if query.sex_slug:
        entries.append((SEX_SLUGS_TO_LABELS[query.sex_slug], ("sexo", query.sex_slug)))
    entries += [(band_by_slug(s).label, ("edad", s)) for s in query.age_slugs]
    entries += [(area_names[pk], ("area", str(pk))) for pk in query.area_ids]
    entries += [(location_names[pk], ("localidad", str(pk))) for pk in query.location_ids]
    return [Pill(label, results_url(base, query, drop=pair)) for label, pair in entries]
```

- [ ] **Step 5: Run to verify pass, then commit**

Run: `pytest apps/core -v`
Expected: PASS.

```bash
git add apps/core
git commit -m "feat(core): parse results-page filters; share query readers with the roster"
```

---

### Task 5: Chart geometry (`apps/core/charts.py`)

**Files:**
- Create: `apps/core/charts.py`
- Test: `apps/core/tests/test_charts.py`

**Interfaces:**
- Consumes: any item with attributes `key: str`, `label: str`, `value: int`, `color: str`.
- Produces:
  - `largest_remainder(values: list[int]) -> list[int]` (sums to 100 when any value > 0)
  - `Segment(key, label, value, percent, x, width, color, tooltip)`; `stacked_segments(items, unit: tuple[str, str]) -> list[Segment]`
  - `Column(key, label, value, x, width, center, y, height, color, tooltip)`; `columns(items, unit) -> list[Column]`
  - `StripBand(color, label, x, width)`, `Marker(key, label, value, display, x, lane, anchor, band_label, tooltip)`, `Strip(bands, markers, scale_max)`; `range_strip(bands: list[tuple[float, str, str]], scale_max: int, points: list[tuple[str, str, float]]) -> Strip | None` — `bands` are `(upper_exclusive, color_key, label)`, `points` are `(key, label, value)`.
  - `format_number(value: float) -> str` — whole numbers without decimals, others to one decimal with `.`.

- [ ] **Step 1: Write the failing tests**

```python
from dataclasses import dataclass

from apps.core.charts import (
    columns,
    format_number,
    largest_remainder,
    range_strip,
    stacked_segments,
)

UNIT = ("cuestionario", "cuestionarios")


@dataclass
class Item:
    key: str
    label: str
    value: int
    color: str = "c"


def test_largest_remainder_sums_to_100():
    assert largest_remainder([1, 1, 1]) == [34, 33, 33]
    assert sum(largest_remainder([7, 13, 29, 2, 0])) == 100
    assert largest_remainder([0, 0]) == [0, 0]
    assert largest_remainder([0, 5]) == [0, 100]


def test_stacked_segments_positions_and_omits_empty():
    segs = stacked_segments([Item("a", "Bajo", 1), Item("b", "Medio", 0), Item("c", "Alto", 3)], UNIT)
    assert [s.key for s in segs] == ["a", "c"]
    assert (segs[0].x, segs[0].width) == (0.0, 25.0)
    assert (segs[1].x, segs[1].width) == (25.0, 75.0)
    assert segs[0].tooltip == "Bajo · 1 cuestionario · 25 %"
    assert segs[1].tooltip == "Alto · 3 cuestionarios · 75 %"


def test_stacked_segments_empty_when_total_zero():
    assert stacked_segments([Item("a", "A", 0)], UNIT) == []


def test_columns_scale_to_the_tallest_with_headroom():
    cols = columns([Item("a", "15–19", 2), Item("b", "20–24", 4), Item("c", "Sin dato", 0)], UNIT)
    assert [c.height for c in cols] == [44.0, 88.0, 0.0]
    assert cols[1].y == 12.0
    assert cols[0].x < cols[0].center < cols[1].x
    assert cols[2].tooltip == "Sin dato · 0 cuestionarios"


BANDS = [(50, "ndr-nulo", "Nulo"), (75, "ndr-bajo", "Bajo"), (99, "ndr-medio", "Medio"),
         (140, "ndr-alto", "Alto"), (float("inf"), "ndr-muy_alto", "Muy alto")]


def test_range_strip_bands_clip_to_scale():
    strip = range_strip(BANDS, 200, [])
    assert [b.label for b in strip.bands] == ["Nulo", "Bajo", "Medio", "Alto", "Muy alto"]
    assert strip.bands[0].x == 0.0 and strip.bands[0].width == 25.0
    assert strip.bands[-1].x == 70.0 and strip.bands[-1].width == 30.0


def test_range_strip_markers_band_and_lanes():
    points = [("min", "Mín", 20), ("median", "Mediana", 80), ("mean", "Prom.", 84.3), ("max", "Máx", 180)]
    strip = range_strip(BANDS, 200, points)
    by_key = {m.key: m for m in strip.markers}
    assert by_key["min"].band_label == "Nulo"
    assert by_key["mean"].band_label == "Medio"
    assert by_key["mean"].display == "84.3"
    assert by_key["median"].display == "80"
    # Median (40%) and mean (42.15%) are too close to share a lane.
    assert by_key["median"].lane != by_key["mean"].lane
    assert by_key["min"].lane == "above"
    assert by_key["mean"].tooltip == "Prom.: 84.3 · Medio"


def test_range_strip_anchors_labels_at_the_edges():
    strip = range_strip(BANDS, 200, [("min", "Mín", 0), ("max", "Máx", 200)])
    anchors = {m.key: m.anchor for m in strip.markers}
    assert anchors == {"min": "start", "max": "end"}


def test_range_strip_none_for_empty_scale():
    assert range_strip(BANDS, 0, []) is None


def test_format_number():
    assert format_number(81.0) == "81"
    assert format_number(81.5) == "81.5"
    assert format_number(84.25) == "84.2"
```

- [ ] **Step 2: Run to verify failure**

Run: `pytest apps/core/tests/test_charts.py -v`
Expected: FAIL — `ModuleNotFoundError`.

- [ ] **Step 3: Implement `apps/core/charts.py`**

```python
"""Chart geometry: pure functions from plain data to positions.

Knows nothing about NOM-035 or about Tailwind. Items carry a `color` *key*;
`templatetags/charts.py` turns keys into classes. Every position is a percent
of the chart's width (or height, for columns), so an SVG scales to any width.
"""

from dataclasses import dataclass

COLUMN_HEADROOM = 88.0  # tallest column's height, leaving room for its count
LABEL_GAP = 9.0  # minimum % between two marker labels sharing a lane
EDGE = 6.0  # % from either end where a label anchors to the edge


def format_number(value: float) -> str:
    rounded = round(value, 1)
    return str(int(rounded)) if rounded == int(rounded) else f"{rounded:.1f}"


def _count(value: int, unit: tuple[str, str]) -> str:
    return f"{value} {unit[0] if value == 1 else unit[1]}"


def largest_remainder(values: list[int]) -> list[int]:
    """Whole percents that always add up to 100 (or all 0 when nothing counted)."""
    total = sum(values)
    if not total:
        return [0] * len(values)
    raw = [v * 100 / total for v in values]
    floors = [int(r) for r in raw]
    short = 100 - sum(floors)
    order = sorted(range(len(values)), key=lambda i: (-(raw[i] - floors[i]), i))
    for i in order[:short]:
        floors[i] += 1
    return floors


@dataclass(frozen=True)
class Segment:
    key: str
    label: str
    value: int
    percent: int
    x: float
    width: float
    color: str
    tooltip: str


def stacked_segments(items, unit) -> list[Segment]:
    items = list(items)
    total = sum(item.value for item in items)
    if not total:
        return []
    percents = largest_remainder([item.value for item in items])
    segments, x = [], 0.0
    for item, percent in zip(items, percents):
        width = item.value * 100 / total
        if item.value:
            segments.append(
                Segment(
                    key=item.key,
                    label=item.label,
                    value=item.value,
                    percent=percent,
                    x=round(x, 3),
                    width=round(width, 3),
                    color=item.color,
                    tooltip=f"{item.label} · {_count(item.value, unit)} · {percent} %",
                )
            )
        x += width
    return segments


@dataclass(frozen=True)
class Column:
    key: str
    label: str
    value: int
    x: float
    width: float
    center: float
    y: float
    height: float
    color: str
    tooltip: str


def columns(items, unit) -> list[Column]:
    items = list(items)
    peak = max((item.value for item in items), default=0)
    slot = 100 / len(items) if items else 0
    out = []
    for i, item in enumerate(items):
        height = round(item.value * COLUMN_HEADROOM / peak, 3) if peak else 0.0
        out.append(
            Column(
                key=item.key,
                label=item.label,
                value=item.value,
                x=round(i * slot + slot * 0.15, 3),
                width=round(slot * 0.7, 3),
                center=round(i * slot + slot / 2, 3),
                y=round(100 - height, 3),
                height=height,
                color=item.color,
                tooltip=f"{item.label} · {_count(item.value, unit)}",
            )
        )
    return out


@dataclass(frozen=True)
class StripBand:
    color: str
    label: str
    x: float
    width: float


@dataclass(frozen=True)
class Marker:
    key: str
    label: str
    value: float
    display: str
    x: float
    lane: str  # "above" | "below"
    anchor: str  # SVG text-anchor: "start" | "middle" | "end"
    band_label: str
    tooltip: str


@dataclass(frozen=True)
class Strip:
    bands: tuple[StripBand, ...]
    markers: tuple[Marker, ...]
    scale_max: int


def _band_label(bands, value) -> str:
    for upper, _color, label in bands:
        if value < upper:
            return label
    return bands[-1][2]


def range_strip(bands, scale_max, points) -> Strip | None:
    """Bands as (upper_exclusive, color, label), ascending; points as (key, label, value)."""
    if scale_max <= 0:
        return None
    drawn, lower = [], 0.0
    for upper, color, label in bands:
        upper = min(upper, scale_max)
        if upper > lower:
            drawn.append(
                StripBand(
                    color=color,
                    label=label,
                    x=round(lower * 100 / scale_max, 3),
                    width=round((upper - lower) * 100 / scale_max, 3),
                )
            )
            lower = upper

    last = {"above": None, "below": None}
    markers = []
    for key, label, value in sorted(points, key=lambda p: p[2]):
        x = round(min(max(value, 0), scale_max) * 100 / scale_max, 3)
        if last["above"] is None or x - last["above"] >= LABEL_GAP:
            lane = "above"
        elif last["below"] is None or x - last["below"] >= LABEL_GAP:
            lane = "below"
        else:
            lane = "above" if x - last["above"] >= x - last["below"] else "below"
        last[lane] = x
        display = format_number(value)
        band_label = _band_label(bands, value)
        markers.append(
            Marker(
                key=key,
                label=label,
                value=value,
                display=display,
                x=x,
                lane=lane,
                anchor="start" if x < EDGE else "end" if x > 100 - EDGE else "middle",
                band_label=band_label,
                tooltip=f"{label}: {display} · {band_label}",
            )
        )
    return Strip(bands=tuple(drawn), markers=tuple(markers), scale_max=scale_max)
```

- [ ] **Step 4: Run to verify pass, then commit**

Run: `pytest apps/core/tests/test_charts.py -v`
Expected: PASS.

```bash
git add apps/core/charts.py apps/core/tests/test_charts.py
git commit -m "feat(core): pure geometry for stacked bars, columns and range strips"
```

---

### Task 6: Chart components (tags, templates, colors)

**Files:**
- Modify: `apps/core/templatetags/valuation_extras.py` (add `_FILL`, `ndr_fill`)
- Create: `apps/core/templatetags/charts.py`
- Create: `templates/components/charts/stacked_bar.html`, `column_chart.html`, `range_strip.html`
- Test: `apps/core/tests/test_chart_components.py`, `apps/core/tests/test_valuation_extras.py`

**Interfaces:**
- Consumes: Task 5 geometry.
- Produces template tags (`{% load charts %}`):
  - `{% stacked_bar items unit="cuestionario" legend=False label="" %}`
  - `{% column_chart items unit="persona" label="" %}`
  - `{% range_strip bands scale_max points label="" %}`
  - Color keys understood: `ndr-<level>` for every NDR level, `sex-female`, `sex-male`, `age`, `none`, `guia1-none`, `guia1-event`, `guia1-positive`. Units: `cuestionario`, `persona`.

- [ ] **Step 1: Write the failing tests**

Append to `apps/core/tests/test_valuation_extras.py`:

```python
def test_ndr_fill_maps_every_level():
    from apps.core.templatetags.valuation_extras import ndr_fill
    from apps.nom035 import constants as c

    assert ndr_fill(c.NDR_BAJO) == "fill-green-500"
    assert ndr_fill(c.NDR_MUY_ALTO) == "fill-red-500"
    assert ndr_fill("nonsense") == "fill-gray-200"
```

`apps/core/tests/test_chart_components.py`:

```python
from dataclasses import dataclass

from django.template import Context, Template
from django.test import override_settings


@dataclass
class Item:
    key: str
    label: str
    value: int
    color: str


def _render(source, **context):
    return Template("{% load charts %}" + source).render(Context(context))


def test_stacked_bar_renders_segments_with_tooltip_and_fill():
    html = _render(
        "{% stacked_bar items legend=True label='Distribución' %}",
        items=[Item("bajo", "Bajo", 1, "ndr-bajo"), Item("alto", "Alto", 3, "ndr-alto")],
    )
    assert 'data-tooltip="Alto · 3 cuestionarios · 75 %"' in html
    assert "fill-orange-500" in html
    assert 'x="25.0%"' in html
    assert "<title>" not in html
    assert "75 %" in html  # legend


@override_settings(USE_THOUSAND_SEPARATOR=True)
def test_svg_numbers_never_localized():
    html = _render(
        "{% stacked_bar items %}",
        items=[Item("a", "A", 1, "none"), Item("b", "B", 2, "none")],
    )
    assert 'width="33.333%"' in html


def test_column_chart_labels_every_column():
    html = _render(
        "{% column_chart items %}",
        items=[Item("15-19", "15–19", 2, "age"), Item("none", "Sin dato", 0, "none")],
    )
    assert "15–19" in html and "Sin dato" in html
    assert "fill-indigo-500" in html
    assert 'data-tooltip="15–19 · 2 personas"' in html


def test_range_strip_renders_bands_and_labelled_markers():
    html = _render(
        "{% range_strip bands 200 points %}",
        bands=[(100, "ndr-nulo", "Nulo"), (float("inf"), "ndr-muy_alto", "Muy alto")],
        points=[("mean", "Prom.", 84.3)],
    )
    assert "Prom. 84.3" in html
    assert 'data-tooltip="Prom.: 84.3 · Nulo"' in html
    assert "fill-red-500" in html
    assert ">200<" in html


def test_unknown_color_key_falls_back_to_gray():
    html = _render("{% stacked_bar items %}", items=[Item("a", "A", 1, "mystery")])
    assert "fill-gray-300" in html
```

- [ ] **Step 2: Run to verify failure**

Run: `pytest apps/core/tests/test_chart_components.py apps/core/tests/test_valuation_extras.py -v`
Expected: FAIL — `'charts' is not a registered tag library` and missing `ndr_fill`.

- [ ] **Step 3: Implement**

`valuation_extras.py` — beside `_BAR`:

```python
_FILL = {
    c.NDR_NULO: "fill-gray-300",
    c.NDR_BAJO: "fill-green-500",
    c.NDR_MEDIO: "fill-amber-500",
    c.NDR_ALTO: "fill-orange-500",
    c.NDR_MUY_ALTO: "fill-red-500",
}
_NEUTRAL_FILL = "fill-gray-200"


@register.filter
def ndr_fill(ndr):
    """Tailwind SVG fill class for an NDR chart mark."""
    return _FILL.get(ndr, _NEUTRAL_FILL)
```

`apps/core/templatetags/charts.py`:

```python
"""Inclusion tags for the chart components in templates/components/charts/.

This module is the chart palette: a color key from the data layer becomes a
pair of Tailwind classes here (an SVG fill, and a background for legend
swatches). NDR entries come from valuation_extras so the risk ramp has one
source. Classes are spelled out in full so Tailwind's scan of templatetags/
compiles them.
"""

from dataclasses import asdict

from django import template

from apps.core import charts
from apps.core.templatetags.valuation_extras import ndr_bar, ndr_fill
from apps.nom035 import constants as c

register = template.Library()

_COLORS = {
    **{f"ndr-{level}": (ndr_fill(level), ndr_bar(level)) for level in c.NDR_ORDER},
    "sex-female": ("fill-violet-600", "bg-violet-600"),
    "sex-male": ("fill-sky-600", "bg-sky-600"),
    "age": ("fill-indigo-500", "bg-indigo-500"),
    "none": ("fill-gray-300", "bg-gray-300"),
    "guia1-none": ("fill-gray-300", "bg-gray-300"),
    "guia1-event": ("fill-amber-500", "bg-amber-500"),
    "guia1-positive": ("fill-red-500", "bg-red-500"),
}
_FALLBACK = ("fill-gray-300", "bg-gray-300")

UNITS = {
    "cuestionario": ("cuestionario", "cuestionarios"),
    "persona": ("persona", "personas"),
}


def _paint(mark) -> dict:
    fill, swatch = _COLORS.get(mark.color, _FALLBACK)
    return {**asdict(mark), "fill": fill, "swatch": swatch}


@register.inclusion_tag("components/charts/stacked_bar.html")
def stacked_bar(items, unit="cuestionario", legend=False, label=""):
    segments = [_paint(s) for s in charts.stacked_segments(items, UNITS[unit])]
    return {
        "segments": segments,
        "legend": legend,
        "aria_label": label or "; ".join(s["tooltip"] for s in segments),
    }


@register.inclusion_tag("components/charts/column_chart.html")
def column_chart(items, unit="persona", label=""):
    cols = [_paint(col) for col in charts.columns(items, UNITS[unit])]
    return {
        "cols": cols,
        "aria_label": label or "; ".join(col["tooltip"] for col in cols),
    }


@register.inclusion_tag("components/charts/range_strip.html")
def range_strip(bands, scale_max, points, label=""):
    strip = charts.range_strip(bands, scale_max, points)
    if strip is None:
        return {"strip": None}
    return {
        "strip": {
            "bands": [_paint(b) for b in strip.bands],
            "markers": [asdict(m) for m in strip.markers],
            "scale_max": strip.scale_max,
        },
        "aria_label": label or "; ".join(m.tooltip for m in strip.markers),
    }
```

`templates/components/charts/stacked_bar.html`:

```django
{% load l10n %}{% localize off %}
<figure class="m-0 w-full min-w-0">
  {% if segments %}
    <div class="overflow-hidden rounded-full">
      <svg class="block h-3 w-full" role="img" aria-label="{{ aria_label }}">
        {% for s in segments %}
          <rect x="{{ s.x }}%" y="0" width="{{ s.width }}%" height="100%"
                class="{{ s.fill }} stroke-white outline-none hover:opacity-80 focus:opacity-80"
                stroke-width="2" tabindex="0" aria-label="{{ s.tooltip }}" data-tooltip="{{ s.tooltip }}"></rect>
        {% endfor %}
      </svg>
    </div>
  {% else %}
    <div class="h-3 w-full rounded-full bg-gray-100"></div>
  {% endif %}
  {% if legend and segments %}
    <ul class="mt-2 flex flex-wrap gap-x-4 gap-y-1 text-xs text-gray-600">
      {% for s in segments %}
        <li class="flex items-center gap-1.5">
          <span class="size-2.5 shrink-0 rounded-sm {{ s.swatch }}" aria-hidden="true"></span>
          {{ s.label }} <span class="text-gray-500">{{ s.percent }} % ({{ s.value }})</span>
        </li>
      {% endfor %}
    </ul>
  {% endif %}
</figure>
{% endlocalize %}
```

`templates/components/charts/column_chart.html`:

```django
{% load l10n %}{% localize off %}
<figure class="m-0 w-full min-w-0 pt-4">
  <svg class="block h-36 w-full overflow-visible" role="img" aria-label="{{ aria_label }}">
    {% for col in cols %}
      <rect x="{{ col.x }}%" y="{{ col.y }}%" width="{{ col.width }}%" height="{{ col.height }}%" rx="3"
            class="{{ col.fill }} outline-none hover:opacity-80 focus:opacity-80"
            tabindex="0" aria-label="{{ col.tooltip }}" data-tooltip="{{ col.tooltip }}"></rect>
      {% if col.value %}
        <text x="{{ col.center }}%" y="{{ col.y }}%" dy="-4" text-anchor="middle" class="fill-gray-700 text-[10px]">{{ col.value }}</text>
      {% endif %}
    {% endfor %}
  </svg>
  <div class="mt-1 grid gap-0.5 text-center text-[10px] leading-tight text-gray-500"
       style="grid-template-columns: repeat({{ cols|length }}, minmax(0, 1fr))">
    {% for col in cols %}<span>{{ col.label }}</span>{% endfor %}
  </div>
</figure>
{% endlocalize %}
```

`templates/components/charts/range_strip.html`:

```django
{% load l10n %}{% localize off %}
{% if strip %}
<figure class="m-0 w-full min-w-0">
  <svg class="block h-16 w-full overflow-visible" role="img" aria-label="{{ aria_label }}">
    {% for b in strip.bands %}
      <rect x="{{ b.x }}%" y="24" width="{{ b.width }}%" height="10" class="{{ b.fill }} opacity-60"></rect>
    {% endfor %}
    {% for m in strip.markers %}
      {% if m.lane == "above" %}
        <line x1="{{ m.x }}%" x2="{{ m.x }}%" y1="15" y2="24" class="stroke-gray-400" stroke-width="1"></line>
        <text x="{{ m.x }}%" y="11" text-anchor="{{ m.anchor }}" class="fill-gray-700 text-[10px]">{{ m.label }} {{ m.display }}</text>
      {% else %}
        <line x1="{{ m.x }}%" x2="{{ m.x }}%" y1="34" y2="43" class="stroke-gray-400" stroke-width="1"></line>
        <text x="{{ m.x }}%" y="55" text-anchor="{{ m.anchor }}" class="fill-gray-700 text-[10px]">{{ m.label }} {{ m.display }}</text>
      {% endif %}
      <circle cx="{{ m.x }}%" cy="29" r="5" class="fill-gray-900 stroke-white outline-none" stroke-width="2"
              tabindex="0" aria-label="{{ m.tooltip }}" data-tooltip="{{ m.tooltip }}"></circle>
    {% endfor %}
  </svg>
  <div class="flex justify-between text-[10px] text-gray-400"><span>0</span><span>{{ strip.scale_max }}</span></div>
</figure>
{% endif %}
{% endlocalize %}
```

- [ ] **Step 4: Run to verify pass, then commit**

Run: `pytest apps/core -v`
Expected: PASS.

```bash
git add apps/core templates/components
git commit -m "feat(core): SVG chart components — stacked bar, columns, range strip"
```

---

### Task 7: Results data — assignment options and labels

**Files:**
- Create: `apps/nom035/results.py`
- Test: `apps/nom035/tests/test_results.py`

**Interfaces:**
- Produces:
  - `NOM035_SURVEY_KEY = "nom035"`
  - `AssignmentOption(assignment: SurveyAssignment, label: str, scored_count: int)`
  - `assignment_label(variant_label: str, first: date | None, last: date | None, created: date) -> str`
  - `assignment_options(company) -> list[AssignmentOption]` — newest first, `assignment.company` preloaded
  - `select_assignment(options, requested_pk: int | None) -> AssignmentOption | None`

- [ ] **Step 1: Write the failing tests** — create `apps/nom035/tests/test_results.py`:

```python
from datetime import date, datetime

import pytest
from django.utils import timezone

from apps.nom035 import constants as c
from apps.nom035.models import GroupScore, SubmissionScore
from apps.nom035.results import (
    assignment_label,
    assignment_options,
    select_assignment,
)
from apps.responses.models import SurveySubmission
from apps.surveys.models import Survey, SurveyAssignment

pytestmark = pytest.mark.django_db


@pytest.fixture
def nom035_survey(db):
    return Survey.objects.create(key="nom035", title="NOM-035", status=Survey.Status.PUBLISHED)


def make_assignment(company, survey, variant="large"):
    return SurveyAssignment.objects.create(
        company=company, survey=survey, variant=variant,
        status=SurveyAssignment.Status.ACTIVE,
    )


def make_score(assignment, user=None, *, final_score=10, final_ndr=c.NDR_BAJO,
               groups=(), guia1_event=False, guia1_positive=False, completed_at=None):
    """A scored submission without running the engine.

    Created IN_PROGRESS so the completion signal does not overwrite the
    explicit score; `completed_at` is set directly for label tests.
    `groups` is an iterable of (level, key, score, ndr).
    """
    sub = SurveySubmission.objects.create(
        assignment=assignment, user=user,
        status=SurveySubmission.Status.IN_PROGRESS, completed_at=completed_at,
    )
    score = SubmissionScore.objects.create(
        submission=sub, final_score=final_score, final_ndr=final_ndr,
        guia1_event=guia1_event, guia1_positive=guia1_positive,
    )
    GroupScore.objects.bulk_create(
        GroupScore(submission_score=score, level=level, key=key, score=value, ndr=ndr)
        for level, key, value, ndr in groups
    )
    return score


def test_assignment_label_forms():
    created = date(2026, 1, 12)
    assert assignment_label("Guía III", None, None, created) == "Guía III · creada 12 ene 2026 · sin respuestas"
    assert assignment_label("Guía III", date(2026, 1, 12), date(2026, 2, 28), created) == "Guía III · aplicada 12 ene – 28 feb 2026"
    assert assignment_label("Guía II", date(2025, 12, 1), date(2026, 1, 5), created) == "Guía II · aplicada 1 dic 2025 – 5 ene 2026"
    assert assignment_label("Guía II", date(2026, 3, 4), date(2026, 3, 4), created) == "Guía II · aplicada 4 mar 2026"


def test_assignment_options_only_nom035_newest_first(make_company, survey, nom035_survey):
    company = make_company()
    make_assignment(company, survey)  # another instrument — excluded
    older = make_assignment(company, nom035_survey)
    newer = make_assignment(company, nom035_survey, variant="small")
    tz = timezone.get_current_timezone()
    make_score(older, completed_at=datetime(2026, 1, 12, 18, tzinfo=tz))
    make_score(older, completed_at=datetime(2026, 2, 28, 9, tzinfo=tz))

    options = assignment_options(company)

    assert [o.assignment for o in options] == [newer, older]
    assert options[1].label == "Guía III · aplicada 12 ene – 28 feb 2026"
    assert options[1].scored_count == 2
    assert options[0].scored_count == 0
    assert options[0].label.endswith("sin respuestas")


def test_select_assignment_prefers_request_then_latest_scored(make_company, nom035_survey):
    company = make_company()
    scored = make_assignment(company, nom035_survey)
    make_score(scored)
    make_assignment(company, nom035_survey)  # newest, unscored
    options = assignment_options(company)

    assert select_assignment(options, None).assignment == scored
    assert select_assignment(options, options[0].assignment.pk) == options[0]
    assert select_assignment([], None) is None
```

- [ ] **Step 2: Run to verify failure**

Run: `pytest apps/nom035/tests/test_results.py -v`
Expected: FAIL — `ModuleNotFoundError: apps.nom035.results`.

- [ ] **Step 3: Implement the top of `apps/nom035/results.py`**

```python
"""Results data for the NOM-035 results page.

One assignment at a time, narrowed by a validated filter (see
apps/core/results_query.py), returned as frozen dataclasses. The small-group
rule is applied here, not in templates: a suppressed result carries no numbers.
See docs/platform/nom-035-results-dashboard.md.
"""

from dataclasses import dataclass

from django.db.models import Count, Max, Min, Q
from django.utils import timezone

from apps.surveys.models import SurveyAssignment

NOM035_SURVEY_KEY = "nom035"

_MONTHS = ("ene", "feb", "mar", "abr", "may", "jun", "jul", "ago", "sep", "oct", "nov", "dic")


def _short(day, *, year=True) -> str:
    text = f"{day.day} {_MONTHS[day.month - 1]}"
    return f"{text} {day.year}" if year else text


def assignment_label(variant_label, first, last, created) -> str:
    if first is None:
        return f"{variant_label} · creada {_short(created)} · sin respuestas"
    if first == last:
        span = _short(first)
    elif first.year == last.year:
        span = f"{_short(first, year=False)} – {_short(last)}"
    else:
        span = f"{_short(first)} – {_short(last)}"
    return f"{variant_label} · aplicada {span}"


@dataclass(frozen=True)
class AssignmentOption:
    assignment: SurveyAssignment
    label: str
    scored_count: int


def _local_date(moment):
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
                _local_date(a.first_answer),
                _local_date(a.last_answer),
                _local_date(a.created_at),
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
```

- [ ] **Step 4: Run to verify pass, then commit**

Run: `pytest apps/nom035/tests/test_results.py -v`
Expected: PASS.

```bash
git add apps/nom035/results.py apps/nom035/tests/test_results.py
git commit -m "feat(nom035): list and label NOM-035 assignments for the results page"
```

---

### Task 8: Results data — the group, respondent profile, suppression

**Files:**
- Modify: `apps/nom035/results.py`
- Modify: `apps/nom035/constants.py` (`MIN_GROUP_SIZE = 5`)
- Test: `apps/nom035/tests/test_results.py`

**Interfaces:**
- Consumes: `ResultsQuery` (Task 4) — duck-typed: `sex`, `age_slugs`, `area_ids`, `location_ids`, `is_filtered`; `dataclasses.replace` works on it. `demographics` (Task 3).
- Produces:
  - `shows(size: int, base: int, *, suppress: bool) -> bool`
  - `Slice(key: str, label: str, value: int, color: str)`
  - `Results` with fields `assignment`, `size: int`, `whole_size: int`, `filtered: bool`, `suppressed: bool`, `sex: tuple[Slice, ...]`, `age: tuple[Slice, ...]`, `participation`, `final_distribution`, `categoria_distribution`, `final_stats`, `categoria_stats`, `guia1` (the last five filled in Tasks 9–10; default to empty/None here) and property `empty: bool`
  - `results_for(assignment, query, *, suppress_small_groups: bool) -> Results`
  - `narrow(queryset, query, today, prefix: str)` — applies sex/age/área/localidad to any queryset whose `UserProfile` sits at `prefix` (`"submission__user__profile__"` or `""`)

- [ ] **Step 1: Write the failing tests** — append to `test_results.py`:

```python
from datetime import timedelta

from apps.core.results_query import ResultsQuery
from apps.nom035.results import results_for, shows


def test_shows_rule():
    assert shows(3, 20, suppress=False)
    assert not shows(4, 20, suppress=True)
    assert shows(5, 20, suppress=True)
    assert not shows(17, 20, suppress=True)  # complement of 3
    assert shows(15, 20, suppress=True)
    assert shows(20, 20, suppress=True)      # complement of 0


def _years_ago(years):
    today = timezone.localdate()
    return today.replace(year=today.year - years) - timedelta(days=1)


@pytest.fixture
def people(make_company, make_user_with_profile, make_area, make_location, nom035_survey):
    """Six respondents in Operaciones plus two in Ventas, one with no sex/dob."""
    company = make_company()
    ops = make_area(company, name="Operaciones")
    ventas = make_area(company, name="Ventas")
    matriz = make_location(company, name="Matriz")
    assignment = make_assignment(company, nom035_survey)
    specs = [
        ("female", 22, ops), ("female", 27, ops), ("female", 27, ops),
        ("male", 33, ops), ("male", 45, ops), ("male", 61, ops),
        ("female", 27, ventas), ("", None, ventas),
    ]
    for i, (sex, age, area) in enumerate(specs):
        user = make_user_with_profile(
            email=f"p{i}@x.mx", company=company, area=area, location=matriz
        )
        user.profile.sex = sex
        user.profile.date_of_birth = _years_ago(age) if age else None
        user.profile.save()
        make_score(assignment, user)
    return {"company": company, "assignment": assignment, "ops": ops, "ventas": ventas}


def test_unfiltered_group_is_the_whole_assignment(people):
    results = results_for(people["assignment"], ResultsQuery(), suppress_small_groups=True)
    assert (results.size, results.whole_size) == (8, 8)
    assert not results.filtered and not results.suppressed


def test_sex_and_age_profile(people):
    results = results_for(people["assignment"], ResultsQuery(), suppress_small_groups=True)
    assert [(s.label, s.value, s.color) for s in results.sex] == [
        ("Femenino", 4, "sex-female"), ("Masculino", 3, "sex-male"), ("Sin dato", 1, "none"),
    ]
    ages = {s.key: s.value for s in results.age}
    assert ages["20-24"] == 1 and ages["25-29"] == 3 and ages["60-mas"] == 1
    assert ages["none"] == 1
    assert [s.key for s in results.age][-1] == "none"


def test_filters_narrow_the_group(people):
    query = ResultsQuery(sex="female", sex_slug="femenino", age_slugs=("25-29",),
                         area_ids=(people["ops"].pk,))
    results = results_for(people["assignment"], query, suppress_small_groups=False)
    assert results.size == 2
    assert results.filtered


def test_profile_ignores_its_own_dimension(people):
    query = ResultsQuery(sex="female", sex_slug="femenino")
    results = results_for(people["assignment"], query, suppress_small_groups=False)
    assert results.size == 4
    assert sum(s.value for s in results.sex) == 8  # sex chart ignores the sex filter


def test_small_filtered_group_is_suppressed_for_executives_only(people):
    query = ResultsQuery(area_ids=(people["ventas"].pk,))
    locked = results_for(people["assignment"], query, suppress_small_groups=True)
    free = results_for(people["assignment"], query, suppress_small_groups=False)
    assert locked.suppressed and not free.suppressed
    assert locked.final_distribution is None
    assert sum(s.value for s in locked.sex) == 2  # people counts stay visible


def test_complement_rule_suppresses_all_but_a_few(people):
    # Operaciones = 6 of 8: the 2 left out would be exposed by subtraction.
    query = ResultsQuery(area_ids=(people["ops"].pk,))
    assert results_for(people["assignment"], query, suppress_small_groups=True).suppressed


def test_empty_group(people):
    query = ResultsQuery(age_slugs=("50-54",))
    results = results_for(people["assignment"], query, suppress_small_groups=True)
    assert results.empty and not results.suppressed


def test_deleted_respondent_counts_unfiltered_but_drops_when_filtered(people):
    make_score(people["assignment"], None)
    whole = results_for(people["assignment"], ResultsQuery(), suppress_small_groups=False)
    assert whole.size == 9
    assert {s.key: s.value for s in whole.sex}["none"] == 2
    filtered = results_for(people["assignment"], ResultsQuery(sex="male", sex_slug="masculino"),
                           suppress_small_groups=False)
    assert filtered.size == 3
```

- [ ] **Step 2: Run to verify failure**

Run: `pytest apps/nom035/tests/test_results.py -v`
Expected: FAIL — `ImportError: cannot import name 'results_for'`.

- [ ] **Step 3: Implement**

`apps/nom035/constants.py`:

```python
# Smallest group of questionnaires shown to viewers without
# can_view_small_groups — and the smallest group they may subtract to.
MIN_GROUP_SIZE = 5
```

In `results.py` add (imports merged at top):

```python
from dataclasses import dataclass, replace

from apps.accounts import demographics
from apps.accounts.models import UserProfile
from apps.nom035 import constants as c
from apps.nom035.models import SubmissionScore

NO_DATA = "Sin dato"
_PROFILE = "submission__user__profile__"


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
            earliest, latest = demographics.birth_date_range(demographics.band_by_slug(slug), today)
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
    slices = [Slice(value, UserProfile.Sex(value).label, counts[value], color) for value, color in _SEXES]
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
    slices = [Slice(b.slug, b.label, counts[b.slug], "age") for b in demographics.AGE_BANDS]
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
    suppressed = filtered and size > 0 and not shows(size, whole_size, suppress=suppress_small_groups)

    profiles = [_profile(s) for s in scores]
    if query.sex:
        sexes = narrow(base, replace(query, sex="", sex_slug=""), today).values_list(f"{_PROFILE}sex", flat=True)
    else:
        sexes = [p.sex if p else "" for p in profiles]
    if query.age_slugs:
        dobs = narrow(base, replace(query, age_slugs=()), today).values_list(f"{_PROFILE}date_of_birth", flat=True)
    else:
        dobs = [p.date_of_birth if p else None for p in profiles]

    return Results(
        assignment=assignment,
        size=size,
        whole_size=whole_size,
        filtered=filtered,
        suppressed=suppressed,
        sex=_sex_slices(sexes),
        age=_age_slices(dobs, today),
    )
```

Note `values_list` over a deleted user yields `None` — `_sex_slices` counts it as Sin dato, as the spec requires.

- [ ] **Step 4: Run to verify pass, then commit**

Run: `pytest apps/nom035 -v`
Expected: PASS.

```bash
git add apps/nom035
git commit -m "feat(nom035): results group, respondent profile and small-group rule"
```

---

### Task 9: Results data — distribution, statistics, Guía I

**Files:**
- Modify: `apps/nom035/results.py`
- Test: `apps/nom035/tests/test_results.py`

**Interfaces:**
- Produces:
  - `DistributionRow(key: str, label: str, n: int, counts: tuple[tuple[str, int], ...], children: tuple[DistributionRow, ...])` with property `slices -> tuple[Slice, ...]` (color `ndr-<level>`)
  - `StatsRow(key, label, n, mean: float | None, median: float | None, minimum: int | None, maximum: int | None, scale_max: int, strip_bands: tuple[tuple[float, str, str], ...], children: tuple[StatsRow, ...])` with property `strip_points -> list[tuple[str, str, float]]` (empty when `n == 0`)
  - `Guia1(none: int, event: int, positive: int)` with property `slices`
  - `Results.final_distribution`, `categoria_distribution`, `final_stats`, `categoria_stats`, `guia1` filled whenever the group is neither empty nor suppressed

- [ ] **Step 1: Write the failing tests** — append:

```python
from apps.nom035 import _nom035_scoring as cfg


@pytest.fixture
def scored_large(make_company, nom035_survey):
    company = make_company()
    assignment = make_assignment(company, nom035_survey, variant="large")
    amb = cfg.CAT_AMBIENTE
    cond = cfg.DOM_CONDICIONES
    rows = [
        (40, c.NDR_NULO, 3, c.NDR_NULO, False, False),
        (60, c.NDR_BAJO, 6, c.NDR_BAJO, True, False),
        (80, c.NDR_MEDIO, 10, c.NDR_MEDIO, True, True),
        (160, c.NDR_MUY_ALTO, 14, c.NDR_MUY_ALTO, False, False),
    ]
    for final, final_ndr, cat_score, cat_ndr, event, positive in rows:
        make_score(
            assignment, final_score=final, final_ndr=final_ndr,
            guia1_event=event, guia1_positive=positive,
            groups=[
                (c.LEVEL_CATEGORIA, amb, cat_score, cat_ndr),
                (c.LEVEL_DOMINIO, cond, cat_score, cat_ndr),
            ],
        )
    return assignment


def test_final_distribution_counts_every_level(scored_large):
    results = results_for(scored_large, ResultsQuery(), suppress_small_groups=True)
    row = results.final_distribution
    assert row.n == 4
    assert dict(row.counts) == {c.NDR_NULO: 1, c.NDR_BAJO: 1, c.NDR_MEDIO: 1, c.NDR_ALTO: 0, c.NDR_MUY_ALTO: 1}
    assert [s.color for s in row.slices] == [f"ndr-{lvl}" for lvl in c.NDR_ORDER]


def test_categoria_rows_follow_the_variant(scored_large):
    results = results_for(scored_large, ResultsQuery(), suppress_small_groups=True)
    keys = [row.key for row in results.categoria_distribution]
    assert keys == [k for k in cfg.CATEGORIA_ORDER]  # Guía III has all five
    ambiente = results.categoria_distribution[0]
    assert ambiente.n == 4
    assert [d.key for d in ambiente.children][0] == cfg.DOM_CONDICIONES
    tiempo = results.categoria_distribution[2]
    assert tiempo.n == 0  # no rows stored for it in this fixture


def test_small_variant_has_no_entorno(make_company, nom035_survey):
    assignment = make_assignment(make_company(), nom035_survey, variant="small")
    make_score(assignment)
    results = results_for(assignment, ResultsQuery(), suppress_small_groups=False)
    assert cfg.CAT_ENTORNO not in [row.key for row in results.categoria_distribution]
    assert len(results.categoria_distribution) == 4


def test_statistics_final_and_categoria(scored_large):
    results = results_for(scored_large, ResultsQuery(), suppress_small_groups=True)
    final = results.final_stats
    assert (final.n, final.mean, final.median, final.minimum, final.maximum) == (4, 85.0, 70, 40, 160)
    assert final.scale_max == len(cfg.taxonomy_for_variant("large")) * 4
    assert final.strip_bands[0] == (50, "ndr-nulo", "Nulo")
    assert [p[0] for p in final.strip_points] == ["min", "median", "mean", "max"]
    ambiente = results.categoria_stats[0]
    assert (ambiente.mean, ambiente.median) == (8.2, 8.0)
    tiempo = results.categoria_stats[2]
    assert tiempo.n == 0 and tiempo.mean is None and tiempo.strip_points == []


def test_guia1_outcomes(scored_large):
    results = results_for(scored_large, ResultsQuery(), suppress_small_groups=True)
    assert (results.guia1.none, results.guia1.event, results.guia1.positive) == (2, 1, 1)
    assert [s.color for s in results.guia1.slices] == ["guia1-none", "guia1-event", "guia1-positive"]


def test_group_rows_query_count_does_not_grow(scored_large, django_assert_max_num_queries):
    with django_assert_max_num_queries(3):
        results_for(scored_large, ResultsQuery(), suppress_small_groups=True)
```

Mean of 3, 6, 10, 14 is 8.25; `round(8.25, 1)` in Python is `8.2` (banker's rounding on the binary value) — the assertion pins the implementation's `round(fmean, 1)`. Median of 3, 6, 10, 14 is 8.0.

The query budget above covers: count, scores, group rows. Task 10 raises it for the participation queries.

- [ ] **Step 2: Run to verify failure**

Run: `pytest apps/nom035/tests/test_results.py -v`
Expected: FAIL — `AttributeError: 'NoneType' object has no attribute 'n'`.

- [ ] **Step 3: Implement** — add to `results.py`:

```python
import statistics
from collections import Counter, defaultdict

from apps.nom035 import _nom035_scoring as cfg
from apps.nom035.models import GroupScore

FINAL = "final"


@dataclass(frozen=True)
class DistributionRow:
    key: str
    label: str
    n: int
    counts: tuple[tuple[str, int], ...]
    children: tuple["DistributionRow", ...] = ()

    @property
    def slices(self) -> tuple[Slice, ...]:
        return tuple(Slice(level, c.NDR_LABELS[level], count, f"ndr-{level}") for level, count in self.counts)


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
            Slice("event", "Acontecimiento sin requerir valoración", self.event, "guia1-event"),
            Slice("positive", "Requiere valoración clínica", self.positive, "guia1-positive"),
        )


def _distribution(key, label, ndrs, children=()) -> DistributionRow:
    counted = Counter(ndrs)
    return DistributionRow(
        key=key, label=label, n=len(ndrs),
        counts=tuple((level, counted[level]) for level in c.NDR_ORDER),
        children=tuple(children),
    )


def _stats(key, label, values, *, level, variant, scale_max, children=()) -> StatsRow:
    bands = tuple(
        (upper, f"ndr-{ndr}", c.NDR_LABELS[ndr]) for upper, ndr in cfg.thresholds_for(level, key, variant)
    )
    return StatsRow(
        key=key, label=label, n=len(values),
        mean=round(statistics.fmean(values), 1) if values else None,
        median=statistics.median(values) if values else None,
        minimum=min(values) if values else None,
        maximum=max(values) if values else None,
        scale_max=scale_max, strip_bands=bands, children=tuple(children),
    )


def _structure(variant):
    """(categorías in order, {categoría: [dominios]}, {key: item count}) for a variant."""
    taxonomy = cfg.taxonomy_for_variant(variant)
    items = Counter()
    for cat_key, dom_key, _dim in taxonomy.values():
        items[cat_key] += 1
        items[dom_key] += 1
    categorias = [k for k in cfg.CATEGORIA_ORDER if k in items]
    dominios = {k: [d for d in cfg.dominios_for_categoria(k) if d in items] for k in categorias}
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
        distribution.append(_distribution(
            cat, cfg.group_label(cat), ndrs(c.LEVEL_CATEGORIA, cat),
            [_distribution(d, cfg.group_label(d), ndrs(c.LEVEL_DOMINIO, d)) for d in doms],
        ))
        stats.append(_stats(
            cat, cfg.group_label(cat), values(c.LEVEL_CATEGORIA, cat),
            level=c.LEVEL_CATEGORIA, variant=variant, scale_max=items[cat] * 4,
            children=[
                _stats(d, cfg.group_label(d), values(c.LEVEL_DOMINIO, d),
                       level=c.LEVEL_DOMINIO, variant=variant, scale_max=items[d] * 4)
                for d in doms
            ],
        ))
    final_distribution = _distribution(FINAL, "Calificación final", [s.final_ndr for s in scores])
    final_stats = _stats(FINAL, "Calificación final", [s.final_score for s in scores],
                         level=FINAL, variant=variant, scale_max=total_items * 4)
    guia1 = Guia1(
        none=sum(1 for s in scores if not s.guia1_event),
        event=sum(1 for s in scores if s.guia1_event and not s.guia1_positive),
        positive=sum(1 for s in scores if s.guia1_positive),
    )
    return final_distribution, tuple(distribution), final_stats, tuple(stats), guia1
```

`thresholds_for("final", "final", variant)` is how the engine already reads the final table — `level=FINAL, key=FINAL`.

In `results_for`, before `return`, compute and pass the five fields:

```python
    valuation = {}
    if size and not suppressed:
        final_distribution, categoria_distribution, final_stats, categoria_stats, guia1 = _valuation(assignment, scores)
        valuation = dict(
            final_distribution=final_distribution,
            categoria_distribution=categoria_distribution,
            final_stats=final_stats,
            categoria_stats=categoria_stats,
            guia1=guia1,
        )
```

and add `**valuation` to the `Results(...)` call.

- [ ] **Step 4: Run to verify pass, then commit**

Run: `pytest apps/nom035 -v`
Expected: PASS.

```bash
git add apps/nom035
git commit -m "feat(nom035): NDR distribution, score statistics and Guía I outcomes"
```

---

### Task 10: Results data — participation by área

**Files:**
- Modify: `apps/nom035/results.py`
- Test: `apps/nom035/tests/test_results.py`

**Interfaces:**
- Produces: `ParticipationRow(area_id: int | None, label: str, registered: int | None, responded: int, participation: int | None, counts: tuple[tuple[str, int], ...], suppressed: bool)` with property `slices`; `Results.participation: tuple[ParticipationRow, ...]`.

- [ ] **Step 1: Write the failing tests** — append (reuses the `people` fixture from Task 8):

```python
def test_participation_rows(people, make_user_with_profile):
    # One more Ventas member who never answered.
    make_user_with_profile(email="quiet@x.mx", company=people["company"], area=people["ventas"])
    results = results_for(people["assignment"], ResultsQuery(), suppress_small_groups=False)
    rows = {r.label: r for r in results.participation}
    assert [r.label for r in results.participation] == ["Operaciones", "Ventas"]
    assert (rows["Ventas"].registered, rows["Ventas"].responded, rows["Ventas"].participation) == (3, 2, 67)
    assert rows["Operaciones"].registered == 6


def test_participation_area_rows_follow_the_small_group_rule(people):
    locked = results_for(people["assignment"], ResultsQuery(), suppress_small_groups=True)
    rows = {r.label: r for r in locked.participation}
    assert rows["Ventas"].suppressed      # 2 respondents
    assert rows["Operaciones"].suppressed  # complement of 2 within 8
    assert rows["Ventas"].counts == ()


def test_participation_sin_area_row_for_orphaned_respondents(people):
    make_score(people["assignment"], None)  # deleted account
    results = results_for(people["assignment"], ResultsQuery(), suppress_small_groups=False)
    last = results.participation[-1]
    assert (last.label, last.registered, last.responded, last.participation) == ("Sin área", None, 1, None)


def test_participation_respects_filters(people):
    query = ResultsQuery(sex="female", sex_slug="femenino")
    results = results_for(people["assignment"], query, suppress_small_groups=False)
    rows = {r.label: r for r in results.participation}
    assert (rows["Operaciones"].registered, rows["Operaciones"].responded) == (3, 3)


def test_foreign_area_buckets_as_sin_area(people, make_company, make_area, make_user_with_profile):
    other = make_company(name="Otra")
    stray = make_user_with_profile(email="stray@x.mx", company=people["company"],
                                   area=make_area(other, name="Ajena"))
    make_score(people["assignment"], stray)
    results = results_for(people["assignment"], ResultsQuery(), suppress_small_groups=False)
    assert "Ajena" not in [r.label for r in results.participation]
    assert results.participation[-1].label == "Sin área"
```

Change the Task 9 query-budget test to `django_assert_max_num_queries(5)` (count, scores, group rows, áreas, registered).

- [ ] **Step 2: Run to verify failure**

Run: `pytest apps/nom035/tests/test_results.py -v`
Expected: FAIL — `results.participation` is empty.

- [ ] **Step 3: Implement** — add to `results.py`:

```python
from apps.accounts.models import CompanyArea

NO_AREA = "Sin área"


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
        return tuple(Slice(level, c.NDR_LABELS[level], count, f"ndr-{level}") for level, count in self.counts)


def _area_of(profile, company):
    """The respondent's área, but only if it belongs to `company` (else "Sin área")."""
    area = profile.area if profile is not None else None
    if area is not None and area.company_id != company.pk:
        return None
    return area


def _participation(assignment, query, scores, today, *, group_suppressed, suppress):
    company = assignment.company
    registered = dict(
        narrow(UserProfile.objects.filter(company=company, is_activated=True), query, today, prefix="")
        .values("area_id")
        .annotate(n=Count("pk"))
        .values_list("area_id", "n")
    )
    by_area = defaultdict(list)
    for score in scores:
        area = _area_of(_profile(score), company)
        by_area[area.pk if area else None].append(score.final_ndr)

    size = len(scores)

    def row(area_id, label, registered_count):
        ndrs = by_area.get(area_id, [])
        visible = bool(ndrs) and not group_suppressed and shows(len(ndrs), size, suppress=suppress)
        return ParticipationRow(
            area_id=area_id,
            label=label,
            registered=registered_count,
            responded=len(ndrs),
            participation=round(len(ndrs) * 100 / registered_count) if registered_count else None,
            counts=tuple((lvl, Counter(ndrs)[lvl]) for lvl in c.NDR_ORDER) if visible else (),
            suppressed=bool(ndrs) and not visible,
        )

    areas = CompanyArea.objects.filter(company=company).order_by("name")
    if query.area_ids:
        areas = areas.filter(pk__in=query.area_ids)
    rows = [
        row(area.pk, area.name, registered.get(area.pk, 0))
        for area in areas
        if area.is_active or registered.get(area.pk) or by_area.get(area.pk)
    ]
    if by_area.get(None):
        rows.append(row(None, NO_AREA, None))
    return tuple(rows)
```

In `results_for`, add:

```python
        participation=_participation(
            assignment, query, scores, today,
            group_suppressed=suppressed, suppress=suppress_small_groups,
        ),
```

`assignment.company` is preloaded by `assignment_options` (Task 7); tests that build assignments directly pay one extra query, which the `max_num_queries(5)` budget does not cover — in `test_group_rows_query_count_does_not_grow` fetch the assignment with `SurveyAssignment.objects.select_related("company").get(pk=scored_large.pk)` before the `with` block.

- [ ] **Step 4: Run to verify pass, then commit**

Run: `pytest apps/nom035 -v`
Expected: PASS.

```bash
git add apps/nom035
git commit -m "feat(nom035): participation by área with per-row suppression"
```

---

### Task 11: Results page — views, routes, templates

**Files:**
- Modify: `apps/core/views.py` (`_company_for`, `_results_context`, `CompanyResultsView`, `CompanyResultsFragmentView`)
- Modify: `apps/core/urls.py`
- Create: `templates/core/company_results.html`
- Create: `templates/core/results/_body.html`, `_group_line.html`, `_suppressed.html`, `_ndr_legend.html`, `_participation.html`, `_sex_profile.html`, `_age_profile.html`, `_final_distribution.html`, `_final_stats.html`, `_stats_row.html`, `_guia1.html`, `_categoria_distribution.html`, `_categoria_stats.html`
- Test: `apps/core/tests/test_results_views.py`

**Interfaces:**
- Consumes: Tasks 4, 6, 7–10.
- Produces: URL names `core:company_results`, `core:company_results_fragment`, `core:company_results_for`, `core:company_results_fragment_for`; context keys `company`, `is_admin_view`, `options`, `selected`, `areas`, `locations`, `age_bands`, `query`, `results`, `pills`, `participation_rows` (list of `{"row", "filter_url"}`), `page_url`, `fragment_url`, `active_filter_count`, `ndr_levels`, `container_width`.

- [ ] **Step 1: Write the failing tests** (`apps/core/tests/test_results_views.py`)

```python
import pytest
from django.db import connection
from django.test.utils import CaptureQueriesContext
from django.urls import reverse

from apps.accounts.roles import ROLES
from apps.nom035 import constants as c
from apps.nom035.models import SubmissionScore
from apps.responses.models import SurveySubmission
from apps.surveys.models import Survey, SurveyAssignment

pytestmark = pytest.mark.django_db

MESSAGE = "Grupo demasiado pequeño para mostrar resultados sin identificar a las personas (mínimo 5)"


@pytest.fixture
def setup(company, make_user_with_profile, make_area, bootstrap_groups):
    survey = Survey.objects.create(key="nom035", title="NOM-035", status=Survey.Status.PUBLISHED)
    assignment = SurveyAssignment.objects.create(
        company=company, survey=survey, variant="large", status=SurveyAssignment.Status.ACTIVE
    )
    area = make_area(company, name="Operaciones")
    exec_user = make_user_with_profile(email="exec@x.mx", company=company)
    exec_user.groups.add(bootstrap_groups[ROLES[1].name])
    admin = make_user_with_profile(email="admin@x.mx", company=company)
    admin.groups.add(bootstrap_groups[ROLES[0].name])
    employee = make_user_with_profile(email="emp@x.mx", company=company)
    employee.groups.add(bootstrap_groups[ROLES[3].name])
    return {"company": company, "assignment": assignment, "area": area,
            "exec": exec_user, "admin": admin, "employee": employee}


def add_respondents(setup, make_user_with_profile, count, *, area=None, prefix="r"):
    for i in range(count):
        user = make_user_with_profile(
            email=f"{prefix}{i}@x.mx", company=setup["company"], area=area
        )
        sub = SurveySubmission.objects.create(
            assignment=setup["assignment"], user=user, status=SurveySubmission.Status.IN_PROGRESS
        )
        SubmissionScore.objects.create(submission=sub, final_score=60, final_ndr=c.NDR_BAJO)


def test_employee_gets_403(client, setup):
    client.force_login(setup["employee"])
    assert client.get(reverse("core:company_results")).status_code == 403


def test_executive_sees_own_company_results(client, setup, make_user_with_profile):
    add_respondents(setup, make_user_with_profile, 6)
    client.force_login(setup["exec"])
    resp = client.get(reverse("core:company_results"))
    assert resp.status_code == 200
    body = resp.content.decode()
    assert "Participación por área" in body
    assert "Calificación final" in body
    assert 'id="results-body"' in body


def test_executive_cannot_use_admin_route(client, setup):
    client.force_login(setup["exec"])
    url = reverse("core:company_results_for", args=[setup["company"].reference_code])
    assert client.get(url).status_code == 403


def test_small_filtered_group_locked_for_executive_not_admin(client, setup, make_user_with_profile):
    add_respondents(setup, make_user_with_profile, 3, area=setup["area"], prefix="ops")
    add_respondents(setup, make_user_with_profile, 10, prefix="rest")
    params = {"area": setup["area"].pk}

    client.force_login(setup["exec"])
    locked = client.get(reverse("core:company_results_fragment"), params).content.decode()
    assert MESSAGE in locked
    assert "Distribución por categoría" not in locked

    client.force_login(setup["admin"])
    url = reverse("core:company_results_fragment_for", args=[setup["company"].reference_code])
    free = client.get(url, params).content.decode()
    assert MESSAGE not in free
    assert "Distribución por categoría" in free


def test_fragment_is_a_fragment(client, setup, make_user_with_profile):
    add_respondents(setup, make_user_with_profile, 5)
    client.force_login(setup["exec"])
    body = client.get(reverse("core:company_results_fragment")).content.decode()
    assert "<html" not in body
    assert "Toda la empresa" in body


def test_invalid_parameters_are_ignored(client, setup, make_user_with_profile):
    add_respondents(setup, make_user_with_profile, 5)
    client.force_login(setup["exec"])
    resp = client.get(reverse("core:company_results"),
                      {"encuesta": "999", "edad": "nope", "area": "abc", "sexo": "x"})
    assert resp.status_code == 200
    assert resp.context["query"].is_filtered is False


def test_no_nom035_assignment(client, company, make_user_with_profile, bootstrap_groups):
    user = make_user_with_profile(email="solo@x.mx", company=company)
    user.groups.add(bootstrap_groups[ROLES[1].name])
    client.force_login(user)
    body = client.get(reverse("core:company_results")).content.decode()
    assert "Esta empresa aún no tiene encuestas NOM-035 asignadas." in body
    assert 'id="results-filters"' not in body


def test_query_count_is_independent_of_respondents(client, setup, make_user_with_profile):
    client.force_login(setup["admin"])
    url = reverse("core:company_results_fragment_for", args=[setup["company"].reference_code])
    add_respondents(setup, make_user_with_profile, 3, prefix="a")
    client.get(url)  # warm session/permission caches
    with CaptureQueriesContext(connection) as small:
        client.get(url)
    add_respondents(setup, make_user_with_profile, 12, prefix="b")
    with CaptureQueriesContext(connection) as large:
        client.get(url)
    assert len(large.captured_queries) == len(small.captured_queries)
```

- [ ] **Step 2: Run to verify failure**

Run: `pytest apps/core/tests/test_results_views.py -v`
Expected: FAIL — `NoReverseMatch: 'company_results'`.

- [ ] **Step 3: Views and routes**

`apps/core/urls.py` — add after the dashboard routes:

```python
    path("tablero-empresa/resultados/", views.CompanyResultsView.as_view(), name="company_results"),
    path("tablero-empresa/resultados/fragmento/", views.CompanyResultsFragmentView.as_view(), name="company_results_fragment"),
    path("empresas/<str:reference_code>/resultados/", views.CompanyResultsView.as_view(), name="company_results_for"),
    path("empresas/<str:reference_code>/resultados/fragmento/", views.CompanyResultsFragmentView.as_view(), name="company_results_fragment_for"),
```

`apps/core/views.py`:

```python
from dataclasses import replace

from django.urls import reverse

from apps.accounts.demographics import AGE_BANDS
from apps.accounts.models import CompanyArea, CompanyLocation
from apps.core.query_params import SEX_SLUGS_TO_LABELS
from apps.core.results_query import filter_pills, parse_results_query, results_url
from apps.nom035 import constants as nom035_constants
from apps.nom035.results import assignment_options, results_for, select_assignment


def _company_for(request, reference_code):
    """The company a results view shows, or None when the viewer has none yet."""
    if reference_code is not None:
        if not request.user.has_perm("accounts.can_manage_surveys"):
            raise PermissionDenied
        return get_object_or_404(Company, reference_code=reference_code)
    profile = getattr(request.user, "profile", None)
    return profile.company if profile is not None and profile.company_id else None


def _results_context(request, company, reference_code) -> dict:
    if reference_code is None:
        page_url = reverse("core:company_results")
        fragment_url = reverse("core:company_results_fragment")
    else:
        page_url = reverse("core:company_results_for", args=[reference_code])
        fragment_url = reverse("core:company_results_fragment_for", args=[reference_code])

    options = assignment_options(company)
    areas = list(CompanyArea.objects.filter(company=company).order_by("name"))
    locations = list(CompanyLocation.objects.filter(company=company).order_by("name"))
    query = parse_results_query(
        request.GET,
        assignment_ids={o.assignment.pk for o in options},
        area_ids={a.pk for a in areas},
        location_ids={loc.pk for loc in locations},
    )
    selected = select_assignment(options, query.assignment_id)
    results = None
    if selected is not None:
        query = replace(query, assignment_id=selected.assignment.pk)
        results = results_for(
            selected.assignment,
            query,
            suppress_small_groups=not request.user.has_perm("accounts.can_view_small_groups"),
        )
    participation_rows = [
        {
            "row": row,
            "filter_url": (
                results_url(page_url, query, add=("area", str(row.area_id)))
                if row.area_id is not None and row.area_id not in query.area_ids
                else None
            ),
        }
        for row in (results.participation if results else ())
    ]
    return {
        "company": company,
        "is_admin_view": reference_code is not None,
        "options": options,
        "selected": selected,
        "areas": areas,
        "locations": locations,
        "age_bands": AGE_BANDS,
        "sex_choices": list(SEX_SLUGS_TO_LABELS.items()),
        "query": query,
        "results": results,
        "pills": filter_pills(
            query, page_url,
            area_names={a.pk: a.name for a in areas},
            location_names={loc.pk: loc.name for loc in locations},
        ),
        "participation_rows": participation_rows,
        "active_filter_count": len(query.params()) - (1 if query.assignment_id is not None else 0),
        "ndr_levels": [(level, nom035_constants.NDR_LABELS[level]) for level in nom035_constants.NDR_ORDER],
        "page_url": page_url,
        "fragment_url": fragment_url,
        "container_width": "max-w-6xl",
    }


class CompanyResultsView(LoginRequiredMixin, View):
    """The NOM-035 results page: one assignment, one filter bar, SVG charts."""

    template_name = "core/company_results.html"

    def get(self, request, reference_code=None):
        if not request.user.has_perm("accounts.can_view_insights"):
            raise PermissionDenied
        company = _company_for(request, reference_code)
        if company is None:
            return redirect("accounts:setup_profile")
        return render(request, self.template_name, _results_context(request, company, reference_code))


class CompanyResultsFragmentView(CompanyResultsView):
    """The results body alone, swapped into the page by results_dashboard.ts."""

    template_name = "core/results/_body.html"
```

- [ ] **Step 4: Templates**

`templates/core/company_results.html`:

```django
{% extends "base_app.html" %}
{% load static %}

{% block title %}Resultados | {{ company.name }} | SOFIA-S{% endblock %}

{% block header_nav %}
  <span class="text-gray-300 select-none">|</span>
  <a href="{% if is_admin_view %}{% url 'core:company_dashboard_for' company.reference_code %}{% else %}{% url 'core:company_dashboard' %}{% endif %}"
     class="text-sm text-gray-400 hover:text-gray-600 transition-colors">&larr; Regresa al tablero</a>
{% endblock %}

{% block content %}
  <div class="mb-5">
    <h1 class="text-2xl font-bold text-gray-900">Resultados NOM-035</h1>
    <p class="mt-1 text-sm text-gray-500">{{ company.name }}</p>
  </div>

  {% if not options %}
    <div class="rounded-2xl border border-dashed border-gray-300 bg-white px-8 py-12 text-center">
      <p class="text-sm text-gray-500">Esta empresa aún no tiene encuestas NOM-035 asignadas.</p>
    </div>
  {% else %}
    <form method="get" action="{{ page_url }}" id="results-filters" data-fragment-url="{{ fragment_url }}"
          class="rounded-2xl border border-gray-200 bg-white p-3 shadow-sm">
      <div class="flex flex-col gap-3 md:flex-row md:items-start">
        <label class="min-w-0 flex-1">
          <span class="sr-only">Encuesta</span>
          <select name="encuesta" class="w-full rounded-xl border border-gray-300 bg-white px-3 py-2 text-sm text-gray-900">
            {% for option in options %}
              <option value="{{ option.assignment.pk }}"{% if option.assignment.pk == selected.assignment.pk %} selected{% endif %}>{{ option.label }}</option>
            {% endfor %}
          </select>
        </label>
        <details class="group min-w-0 md:w-auto">
          <summary class="flex cursor-pointer list-none items-center justify-center gap-2 rounded-xl border border-gray-300 px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50">
            Filtros (<span data-filter-count>{{ active_filter_count }}</span>)
          </summary>
          <div class="mt-3 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
            <fieldset class="m-0 min-w-0 border-0 p-0">
              <legend class="mb-2 p-0 text-xs font-semibold uppercase tracking-wide text-gray-500">Sexo</legend>
              <label class="flex items-center gap-2 py-1 text-sm"><input type="radio" name="sexo" value=""{% if not query.sex_slug %} checked{% endif %}> Todos</label>
              {% for slug, label in sex_choices %}
                <label class="flex items-center gap-2 py-1 text-sm"><input type="radio" name="sexo" value="{{ slug }}"{% if query.sex_slug == slug %} checked{% endif %}> {{ label }}</label>
              {% endfor %}
            </fieldset>
            <fieldset class="m-0 min-w-0 border-0 p-0">
              <legend class="mb-2 p-0 text-xs font-semibold uppercase tracking-wide text-gray-500">Edad</legend>
              {% for band in age_bands %}
                <label class="flex items-center gap-2 py-1 text-sm"><input type="checkbox" name="edad" value="{{ band.slug }}"{% if band.slug in query.age_slugs %} checked{% endif %}> {{ band.label }}</label>
              {% endfor %}
            </fieldset>
            <fieldset class="m-0 min-w-0 border-0 p-0">
              <legend class="mb-2 p-0 text-xs font-semibold uppercase tracking-wide text-gray-500">Área</legend>
              {% for area in areas %}
                <label class="flex items-center gap-2 py-1 text-sm"><input type="checkbox" name="area" value="{{ area.pk }}"{% if area.pk in query.area_ids %} checked{% endif %}> {{ area.name }}</label>
              {% endfor %}
            </fieldset>
            {% if locations %}
              <fieldset class="m-0 min-w-0 border-0 p-0">
                <legend class="mb-2 p-0 text-xs font-semibold uppercase tracking-wide text-gray-500">Localidad</legend>
                {% for location in locations %}
                  <label class="flex items-center gap-2 py-1 text-sm"><input type="checkbox" name="localidad" value="{{ location.pk }}"{% if location.pk in query.location_ids %} checked{% endif %}> {{ location.name }}</label>
                {% endfor %}
              </fieldset>
            {% endif %}
          </div>
          <div class="mt-3 flex justify-end">
            <button type="submit" class="w-full rounded-xl bg-indigo-600 px-4 py-2 text-sm font-semibold text-white hover:bg-indigo-700 sm:w-auto">Aplicar</button>
          </div>
        </details>
      </div>
    </form>

    <div id="results-body" class="mt-6" aria-live="polite">
      {% include "core/results/_body.html" %}
    </div>
    <div id="chart-tooltip" role="tooltip" hidden
         class="pointer-events-none fixed z-50 max-w-xs rounded-lg bg-gray-900 px-3 py-2 text-xs text-white shadow-lg"></div>
    <script src="{% static 'js/results_dashboard.js' %}"></script>
  {% endif %}
{% endblock %}
```

`templates/core/results/_body.html`:

```django
{% if results %}
  {% include "core/results/_group_line.html" %}
  {% if results.empty %}
    <div class="mt-6 rounded-2xl border border-dashed border-gray-300 bg-white px-6 py-10 text-center">
      <p class="text-sm text-gray-500">Ningún cuestionario coincide con los filtros.</p>
    </div>
  {% else %}
    <h2 class="mt-8 text-xs font-semibold uppercase tracking-wide text-gray-500">Empresa</h2>
    {% include "core/results/_participation.html" %}
    <div class="mt-4 grid gap-4 lg:grid-cols-2">
      {% include "core/results/_sex_profile.html" %}
      {% include "core/results/_age_profile.html" %}
    </div>
    {% if results.suppressed %}
      <div class="mt-4 rounded-2xl border border-gray-200 bg-white px-6 py-8 text-center">
        {% include "core/results/_suppressed.html" %}
      </div>
    {% else %}
      {% include "core/results/_final_distribution.html" %}
      {% include "core/results/_final_stats.html" %}
      {% include "core/results/_guia1.html" %}
      <h2 class="mt-10 text-xs font-semibold uppercase tracking-wide text-gray-500">Por categoría</h2>
      {% include "core/results/_categoria_distribution.html" %}
      {% include "core/results/_categoria_stats.html" %}
    {% endif %}
  {% endif %}
{% endif %}
```

`_suppressed.html`:

```django
<p class="text-sm text-gray-500">Grupo demasiado pequeño para mostrar resultados sin identificar a las personas (mínimo 5)</p>
```

`_group_line.html`:

```django
<div class="flex flex-wrap items-center gap-2">
  {% for pill in pills %}
    <a href="{{ pill.remove_url }}" data-results-link
       class="inline-flex items-center gap-1 rounded-full bg-indigo-50 px-3 py-1 text-xs font-medium text-indigo-700 ring-1 ring-inset ring-indigo-600/20 hover:bg-indigo-100">
      {{ pill.label }} <span aria-hidden="true">&times;</span><span class="sr-only">Quitar filtro</span>
    </a>
  {% endfor %}
</div>
<p class="mt-2 text-sm text-gray-600">
  {% for pill in pills %}{{ pill.label }}{% if not forloop.last %} · {% endif %}{% empty %}Toda la empresa{% endfor %}
  — <span class="font-semibold text-gray-900">{{ results.size }}</span> cuestionario{{ results.size|pluralize }}
</p>
```

`_ndr_legend.html`:

```django
{% load valuation_extras %}
<ul class="mt-3 flex flex-wrap gap-x-4 gap-y-1 text-xs text-gray-600">
  {% for level, label in ndr_levels %}
    <li class="flex items-center gap-1.5"><span class="size-2.5 shrink-0 rounded-sm {{ level|ndr_bar }}" aria-hidden="true"></span>{{ label }}</li>
  {% endfor %}
</ul>
```

`_participation.html`:

```django
{% load charts %}
<section class="mt-3 rounded-2xl border border-gray-200 bg-white p-5 shadow-sm">
  <h3 class="text-base font-semibold text-gray-900">Participación por área</h3>
  <div class="mt-4 hidden gap-4 border-b border-gray-100 pb-2 text-xs font-medium uppercase tracking-wide text-gray-400 md:grid md:grid-cols-[minmax(0,1.2fr)_5.5rem_6.5rem_6.5rem_minmax(0,2fr)]">
    <span>Área</span><span class="text-right">Registrados</span><span class="text-right">Respondieron</span><span class="text-right">Participación</span><span>Distribución (final)</span>
  </div>
  <ul class="divide-y divide-gray-100">
    {% for item in participation_rows %}{% with row=item.row %}
      <li class="grid grid-cols-3 gap-x-4 gap-y-2 py-3 md:grid-cols-[minmax(0,1.2fr)_5.5rem_6.5rem_6.5rem_minmax(0,2fr)] md:items-center">
        <div class="col-span-3 min-w-0 md:col-span-1">
          {% if item.filter_url %}
            <a href="{{ item.filter_url }}" data-results-link class="font-medium text-indigo-700 hover:underline">{{ row.label }}</a>
          {% else %}
            <span class="font-medium text-gray-900">{{ row.label }}</span>
          {% endif %}
        </div>
        <div class="text-sm text-gray-900 md:text-right"><span class="block text-xs text-gray-400 md:hidden">Registrados</span>{{ row.registered|default_if_none:"—" }}</div>
        <div class="text-sm text-gray-900 md:text-right"><span class="block text-xs text-gray-400 md:hidden">Respondieron</span>{{ row.responded }}</div>
        <div class="text-sm text-gray-900 md:text-right"><span class="block text-xs text-gray-400 md:hidden">Participación</span>{% if row.participation is not None %}{{ row.participation }} %{% else %}—{% endif %}</div>
        <div class="col-span-3 min-w-0 md:col-span-1">
          {% if row.suppressed %}
            {% include "core/results/_suppressed.html" %}
          {% elif row.counts %}
            {% stacked_bar row.slices %}
          {% else %}
            <span class="text-xs text-gray-400">—</span>
          {% endif %}
        </div>
      </li>
    {% endwith %}{% empty %}
      <li class="py-3 text-sm text-gray-500">Esta empresa no tiene áreas registradas.</li>
    {% endfor %}
  </ul>
  {% include "core/results/_ndr_legend.html" %}
</section>
```

`_sex_profile.html`:

```django
{% load charts %}
<section class="rounded-2xl border border-gray-200 bg-white p-5 shadow-sm">
  <h3 class="text-base font-semibold text-gray-900">Perfil de quienes respondieron — sexo</h3>
  {% if query.sex_slug %}<p class="mt-1 text-xs text-gray-400">Sin filtro de sexo</p>{% endif %}
  <div class="mt-4">{% stacked_bar results.sex unit="persona" legend=True %}</div>
</section>
```

`_age_profile.html`:

```django
{% load charts %}
<section class="rounded-2xl border border-gray-200 bg-white p-5 shadow-sm">
  <h3 class="text-base font-semibold text-gray-900">Perfil de quienes respondieron — edad</h3>
  {% if query.age_slugs %}<p class="mt-1 text-xs text-gray-400">Sin filtro de edad</p>{% endif %}
  <div class="mt-2">{% column_chart results.age unit="persona" %}</div>
</section>
```

`_final_distribution.html`:

```django
{% load charts %}
<section class="mt-4 rounded-2xl border border-gray-200 bg-white p-5 shadow-sm">
  <h3 class="text-base font-semibold text-gray-900">Calificación final — distribución</h3>
  {% with row=results.final_distribution %}
    <div class="mt-4 grid items-center gap-2 md:grid-cols-[12rem_minmax(0,1fr)_4rem]">
      <span class="text-sm font-medium text-gray-900">{{ row.label }}</span>
      {% stacked_bar row.slices %}
      <span class="text-xs text-gray-500 md:text-right">n = {{ row.n }}</span>
    </div>
  {% endwith %}
  {% include "core/results/_ndr_legend.html" %}
</section>
```

`_stats_row.html` (expects `row`):

```django
{% load charts %}
<div class="grid gap-3 md:grid-cols-[minmax(0,14rem)_minmax(0,16rem)_minmax(0,1fr)] md:items-center">
  <span class="text-sm font-medium text-gray-900">{{ row.label }}</span>
  <dl class="grid grid-cols-5 gap-2 text-center text-xs">
    <div><dt class="text-gray-400">n</dt><dd class="font-semibold text-gray-900">{{ row.n }}</dd></div>
    <div><dt class="text-gray-400">Prom.</dt><dd class="font-semibold text-gray-900">{{ row.mean|default_if_none:"—" }}</dd></div>
    <div><dt class="text-gray-400">Mediana</dt><dd class="font-semibold text-gray-900">{{ row.median|default_if_none:"—" }}</dd></div>
    <div><dt class="text-gray-400">Mín</dt><dd class="font-semibold text-gray-900">{{ row.minimum|default_if_none:"—" }}</dd></div>
    <div><dt class="text-gray-400">Máx</dt><dd class="font-semibold text-gray-900">{{ row.maximum|default_if_none:"—" }}</dd></div>
  </dl>
  <div class="min-w-0">{% if row.n %}{% range_strip row.strip_bands row.scale_max row.strip_points %}{% endif %}</div>
</div>
```

`_final_stats.html`:

```django
<section class="mt-4 rounded-2xl border border-gray-200 bg-white p-5 shadow-sm">
  <h3 class="text-base font-semibold text-gray-900">Calificación final — estadística</h3>
  <div class="mt-4">{% include "core/results/_stats_row.html" with row=results.final_stats %}</div>
  {% include "core/results/_ndr_legend.html" %}
</section>
```

`_guia1.html`:

```django
{% load charts %}
<section class="mt-4 rounded-2xl border border-gray-200 bg-white p-5 shadow-sm">
  <h3 class="text-base font-semibold text-gray-900">Guía I — acontecimientos traumáticos severos</h3>
  <p class="mt-3 text-3xl font-bold text-gray-900">{{ results.guia1.positive }}</p>
  <p class="text-sm text-gray-600">colaborador{{ results.guia1.positive|pluralize:"es" }} requiere{{ results.guia1.positive|pluralize:"n" }} valoración clínica</p>
  <div class="mt-4">{% stacked_bar results.guia1.slices legend=True %}</div>
</section>
```

`_categoria_distribution.html`:

```django
{% load charts %}
<section class="mt-3 rounded-2xl border border-gray-200 bg-white p-5 shadow-sm">
  <h3 class="text-base font-semibold text-gray-900">Distribución por categoría</h3>
  <div class="mt-4 space-y-2">
    {% for row in results.categoria_distribution %}
      <details class="group">
        <summary class="grid cursor-pointer list-none items-center gap-2 rounded-lg py-1 md:grid-cols-[14rem_minmax(0,1fr)_4rem]">
          <span class="flex items-center gap-1.5 text-sm font-medium text-gray-900">
            <svg class="size-4 shrink-0 text-gray-400 transition-transform group-open:rotate-90" viewBox="0 0 20 20" fill="currentColor" aria-hidden="true"><path fill-rule="evenodd" d="M7.21 14.77a.75.75 0 0 1 .02-1.06L11.168 10 7.23 6.29a.75.75 0 1 1 1.04-1.08l4.5 4.25a.75.75 0 0 1 0 1.08l-4.5 4.25a.75.75 0 0 1-1.06-.02Z" clip-rule="evenodd"/></svg>
            {{ row.label }}
          </span>
          {% stacked_bar row.slices %}
          <span class="text-xs text-gray-500 md:text-right">n = {{ row.n }}</span>
        </summary>
        <div class="mt-2 space-y-2 border-l border-gray-100 pl-4 md:ml-6">
          {% for child in row.children %}
            <div class="grid items-center gap-2 md:grid-cols-[13rem_minmax(0,1fr)_4rem]">
              <span class="text-xs text-gray-700">{{ child.label }}</span>
              {% stacked_bar child.slices %}
              <span class="text-xs text-gray-500 md:text-right">n = {{ child.n }}</span>
            </div>
          {% endfor %}
        </div>
      </details>
    {% endfor %}
  </div>
  {% include "core/results/_ndr_legend.html" %}
</section>
```

`_categoria_stats.html`:

```django
<section class="mt-4 rounded-2xl border border-gray-200 bg-white p-5 shadow-sm">
  <h3 class="text-base font-semibold text-gray-900">Estadística por categoría</h3>
  <div class="mt-4 space-y-4">
    {% for row in results.categoria_stats %}
      <details class="group">
        <summary class="cursor-pointer list-none">{% include "core/results/_stats_row.html" with row=row %}</summary>
        <div class="mt-3 space-y-3 border-l border-gray-100 pl-4 md:ml-6">
          {% for child in row.children %}{% include "core/results/_stats_row.html" with row=child %}{% endfor %}
        </div>
      </details>
    {% endfor %}
  </div>
  {% include "core/results/_ndr_legend.html" %}
</section>
```

- [ ] **Step 5: Run to verify pass**

Run: `pytest apps/core -v`
Expected: PASS, including `test_responsive.py` (no fixed width above 328px was introduced) and `test_localization.py`.

- [ ] **Step 6: Build CSS and commit**

Run: `npm run build:css`

```bash
git add apps/core templates static/css/output.css
git commit -m "feat(core): NOM-035 results page with global filters"
```

---

### Task 12: In-place filtering and tooltips (`results_dashboard.ts`)

**Files:**
- Create: `static/ts/results_dashboard.ts`
- Create (generated): `static/js/results_dashboard.js`

**Interfaces:**
- Consumes: `#results-filters[data-fragment-url]`, `#results-body`, `[data-filter-count]`, `a[data-results-link]`, `[data-tooltip]`, `#chart-tooltip` (Task 11).

- [ ] **Step 1: Write `static/ts/results_dashboard.ts`**

```ts
/**
 * results_dashboard.ts
 *
 * The NOM-035 results page (templates/core/company_results.html).
 *
 * Swaps #results-body with the fragment URL when the survey changes or the
 * filter form is applied, keeps the address bar in step, and shows a tooltip
 * for chart marks on hover, focus and tap. Without this script the form is a
 * plain GET form and the page reloads; nothing here holds state the server
 * does not also render.
 */

const FILTER_KEYS = ["sexo", "edad", "area", "localidad"];

/** The form's non-empty values, in document order. */
function queryFromForm(form: HTMLFormElement): URLSearchParams {
  const params = new URLSearchParams();
  new FormData(form).forEach((value, key) => {
    if (typeof value === "string" && value !== "") params.append(key, value);
  });
  return params;
}

function activeFilterCount(params: URLSearchParams): number {
  return FILTER_KEYS.reduce((n, key) => n + params.getAll(key).length, 0);
}

/** Check exactly the controls `params` names; the "Todos" radio when no sexo. */
function applyParamsToForm(form: HTMLFormElement, params: URLSearchParams): void {
  for (const element of Array.from(form.elements)) {
    if (element instanceof HTMLInputElement && (element.type === "checkbox" || element.type === "radio")) {
      const chosen = params.getAll(element.name);
      element.checked =
        element.type === "radio" && element.value === "" ? chosen.length === 0 : chosen.includes(element.value);
    } else if (element instanceof HTMLSelectElement) {
      const value = params.get(element.name);
      if (value !== null) element.value = value;
    }
  }
}

function withQuery(base: string, params: URLSearchParams): string {
  const qs = params.toString();
  return qs ? `${base}?${qs}` : base;
}

/** Above the mark when it fits, below otherwise; never past the viewport edges. */
function tooltipPosition(
  mark: DOMRect,
  tip: { width: number; height: number },
  viewportWidth: number,
): { left: number; top: number } {
  const left = Math.min(Math.max(8, mark.left + mark.width / 2 - tip.width / 2), viewportWidth - tip.width - 8);
  const above = mark.top - tip.height - 8;
  return { left, top: above < 8 ? mark.bottom + 8 : above };
}

function initTooltip(): void {
  const tip = document.getElementById("chart-tooltip");
  if (!tip) return;
  const tooltip: HTMLElement = tip;

  function markOf(target: EventTarget | null): Element | null {
    return target instanceof Element ? target.closest("[data-tooltip]") : null;
  }
  function show(mark: Element): void {
    tooltip.textContent = mark.getAttribute("data-tooltip");
    tooltip.hidden = false;
    const pos = tooltipPosition(mark.getBoundingClientRect(), tooltip.getBoundingClientRect(), window.innerWidth);
    tooltip.style.left = `${pos.left}px`;
    tooltip.style.top = `${pos.top}px`;
  }
  function hide(): void {
    tooltip.hidden = true;
  }

  document.addEventListener("pointerover", (event) => {
    const mark = markOf(event.target);
    if (mark) show(mark);
  });
  document.addEventListener("pointerout", (event) => {
    if (markOf(event.target)) hide();
  });
  document.addEventListener("focusin", (event) => {
    const mark = markOf(event.target);
    if (mark) show(mark);
    else hide();
  });
  document.addEventListener("click", (event) => {
    const mark = markOf(event.target);
    if (mark) show(mark);
    else hide();
  });
  window.addEventListener("scroll", hide, { passive: true });
}

function initFilters(): void {
  const formElement = document.getElementById("results-filters");
  const bodyElement = document.getElementById("results-body");
  if (!(formElement instanceof HTMLFormElement) || !bodyElement) return;
  const form: HTMLFormElement = formElement;
  const body: HTMLElement = bodyElement;
  const fragmentUrl = form.dataset.fragmentUrl ?? "";
  const pageUrl = new URL(form.action).pathname;
  let inflight: AbortController | null = null;

  async function update(): Promise<void> {
    const params = queryFromForm(form);
    inflight?.abort();
    const controller = new AbortController();
    inflight = controller;
    body.setAttribute("aria-busy", "true");
    try {
      const response = await fetch(withQuery(fragmentUrl, params), { signal: controller.signal });
      if (!response.ok) {
        window.location.assign(withQuery(pageUrl, params));
        return;
      }
      body.innerHTML = await response.text();
      history.replaceState(null, "", withQuery(pageUrl, params));
      const count = form.querySelector("[data-filter-count]");
      if (count) count.textContent = String(activeFilterCount(params));
      const panel = form.querySelector("details");
      if (panel) panel.open = false;
    } catch (error) {
      if (!(error instanceof DOMException && error.name === "AbortError")) {
        window.location.assign(withQuery(pageUrl, params));
      }
    } finally {
      if (inflight === controller) {
        body.removeAttribute("aria-busy");
        inflight = null;
      }
    }
  }

  form.addEventListener("submit", (event) => {
    event.preventDefault();
    void update();
  });
  form.querySelector("select[name=encuesta]")?.addEventListener("change", () => void update());
  body.addEventListener("click", (event) => {
    const link = event.target instanceof Element ? event.target.closest("a[data-results-link]") : null;
    if (!(link instanceof HTMLAnchorElement)) return;
    event.preventDefault();
    applyParamsToForm(form, new URL(link.href).searchParams);
    void update();
  });
}

initFilters();
initTooltip();
```

- [ ] **Step 2: Build and verify**

Run: `npm run build:js && npm run build:css`
Expected: `static/js/results_dashboard.js` exists; `tsc` reports no errors.

Run: `pytest`
Expected: PASS.

- [ ] **Step 3: Commit**

```bash
git add static/ts/results_dashboard.ts static/js/results_dashboard.js static/css/output.css
git commit -m "feat(core): swap results in place and show chart tooltips"
```

---

### Task 13: Dashboard link card; retire `company_valuation`

**Files:**
- Modify: `apps/core/views.py` (`CompanyDashboardView`)
- Modify: `templates/core/company_dashboard.html` (the `can_view_insights` section)
- Modify: `apps/nom035/aggregates.py` (delete `company_valuation`, `_area_breakdown`, `_most_severe_present`, `_area_of` if unused)
- Modify: `apps/nom035/_nom035_scoring.py` only if `action_text`/`_ACTION_TEXT` become unused — check with grep; if nothing reads them, leave the data in place (it is transcribed reference data) and delete nothing there.
- Rewrite: `apps/core/tests/test_company_valuation_panel.py`
- Modify: `apps/nom035/tests/test_aggregates.py` (drop `company_valuation` tests; keep `employee_valuation` tests)

**Interfaces:**
- Produces: dashboard context key `latest_scored_count: int | None` (None when the company has no NOM-035 assignment) and `results_url: str`.

- [ ] **Step 1: Rewrite the dashboard tests** (`test_company_valuation_panel.py`)

```python
import pytest
from django.urls import reverse

from apps.nom035 import constants as c
from apps.nom035.models import SubmissionScore
from apps.responses.models import SurveySubmission
from apps.surveys.models import Survey, SurveyAssignment

pytestmark = pytest.mark.django_db


def test_dashboard_links_to_results(client, bootstrap_groups, make_user_with_profile, make_company):
    company = make_company()
    admin = make_user_with_profile(email="a@x.mx", company=company)
    admin.groups.add(bootstrap_groups["Admins"])
    survey = Survey.objects.create(key="nom035", title="NOM-035", status=Survey.Status.PUBLISHED)
    assignment = SurveyAssignment.objects.create(
        company=company, survey=survey, variant="large", status=SurveyAssignment.Status.ACTIVE
    )
    sub = SurveySubmission.objects.create(assignment=assignment, status=SurveySubmission.Status.IN_PROGRESS)
    SubmissionScore.objects.create(submission=sub, final_score=160, final_ndr=c.NDR_MUY_ALTO)

    client.force_login(admin)
    resp = client.get(reverse("core:company_dashboard_for", args=[company.reference_code]))
    body = resp.content.decode()
    assert "Valoración de resultados" in body
    assert reverse("core:company_results_for", args=[company.reference_code]) in body
    assert "Por área" not in body
    assert "company_valuation" not in resp.context


def test_dashboard_hides_results_card_without_permission(client, bootstrap_groups, make_user_with_profile, make_company):
    from apps.accounts.roles import ROLES

    company = make_company()
    user = make_user_with_profile(email="s@x.mx", company=company)
    user.groups.add(bootstrap_groups[ROLES[2].name])  # Ejecutivo secundario
    client.force_login(user)
    body = client.get(reverse("core:company_dashboard")).content.decode()
    assert "Ver resultados" not in body
```

Delete the `company_valuation` tests from `apps/nom035/tests/test_aggregates.py` (`test_company_valuation_counts`, `test_company_valuation_area_breakdown`, and every other test calling `company_valuation`, plus the now-unused `scored` fixture and `_make_score` helper if nothing else uses them) and its import.

- [ ] **Step 2: Run to verify failure**

Run: `pytest apps/core/tests/test_company_valuation_panel.py -v`
Expected: FAIL — results URL not in the dashboard.

- [ ] **Step 3: Implement**

In `CompanyDashboardView.get`, replace the `company_valuation` block with:

```python
        latest_scored_count = None
        if request.user.has_perm("accounts.can_view_insights"):
            from apps.nom035.results import assignment_options, select_assignment

            latest = select_assignment(assignment_options(company), None)
            latest_scored_count = latest.scored_count if latest is not None else None
```

and in the context replace `"company_valuation": company_valuation,` with:

```python
                "latest_scored_count": latest_scored_count,
                "results_url": (
                    reverse("core:company_results_for", args=[reference_code])
                    if reference_code is not None
                    else reverse("core:company_results")
                ),
```

Replace the whole `{# Valoración de resultados … #}` section of `company_dashboard.html` with:

```django
  {# Valoración de resultados — only for users with can_view_insights #}
  {% if perms.accounts.can_view_insights %}
    <section class="mt-8">
      <h2 class="text-base font-semibold text-gray-900 mb-4">Valoración de resultados</h2>
      <a href="{{ results_url }}"
         class="group flex flex-col gap-3 rounded-2xl border-2 border-indigo-100 bg-white px-6 py-5 shadow-sm transition-all hover:border-indigo-300 hover:shadow-md sm:flex-row sm:items-center sm:justify-between">
        <div>
          {% if latest_scored_count is None %}
            <p class="text-sm text-gray-500">Esta empresa aún no tiene encuestas NOM-035 asignadas.</p>
          {% else %}
            <p class="text-xs font-medium uppercase tracking-wide text-gray-400">Cuestionarios valorados</p>
            <p class="mt-1 text-3xl font-bold text-gray-900">{{ latest_scored_count }}</p>
          {% endif %}
        </div>
        <span class="text-sm font-semibold text-indigo-600 group-hover:text-indigo-700">Ver resultados &rarr;</span>
      </a>
    </section>
  {% endif %}
```

Remove `{% load valuation_extras %}` from the dashboard template if nothing else in it uses those filters. Delete `company_valuation`, `_area_breakdown`, `_most_severe_present` from `aggregates.py`; keep `_area_of` only if `employee_valuation` uses it (it does not — delete it too, its guard now lives in `results._area_of`). Grep `apps/` and `templates/` for `company_valuation`, `_area_breakdown`, `action_text` and fix every remaining reference.

- [ ] **Step 4: Run to verify pass**

Run: `pytest`
Expected: PASS.

- [ ] **Step 5: Build CSS and commit**

Run: `npm run build:css`

```bash
git add apps templates static/css/output.css
git commit -m "feat(core): link the dashboard to the results page; retire company_valuation"
```

---

### Task 14: Documentation (ships in this PR)

**Files:**
- Modify: `docs/platform/nom-035-results-dashboard.md`
- Modify: `docs/platform/nom-035-analytics.md`
- Modify: `docs/platform/nom-035-valoracion-supuestos.md`
- Modify: `docs/platform/database.md`, `docs/platform/overview.md`
- Modify: `apps/nom035/CLAUDE.md`, `apps/core/CLAUDE.md`, root `.claude/CLAUDE.md` (only where it describes dashboards/valuation panels)

Every file is written in present tense describing the shipped behavior, with no migration commentary ("replaces", "formerly", "no longer", before/after). ADRs are not edited.

- [ ] **Step 1: `nom-035-results-dashboard.md`** — set `Status` to `Current — implemented in apps/nom035/results.py and apps/core; the page is /tablero-empresa/resultados/.` Reconcile every file path, name and behavior with what was built (grep each identifier the doc names). Keep "Open questions" pointing at the supuestos doc.

- [ ] **Step 2: `nom-035-analytics.md` — trim to the scoring engine.**
  - *What this does*: the engine only — answers → scores → NDR, plus the Guía I flags; presentation is one sentence linking to `nom-035-results-dashboard.md` (company level) and naming the employee-detail card.
  - *Guía I*: describe both stored flags, `guia1_event` (Sección I "Sí") and `guia1_positive`, and that positive implies event.
  - *Area grouping*: delete the section — área grouping is now described in the results doc; keep only what `employee_valuation` needs, if anything.
  - *Reads and aggregation*: `employee_valuation` only; company-level reads are `apps/nom035/results.py`, linked.
  - *Presentation*: the employee card only, plus the NDR color centralization (`valuation_extras.py`, now including `ndr_fill`).
  - *Where the code lives*: add `results.py`; `aggregates.py` described as `employee_valuation`.
  - *Schema*: add `guia1_event`.
  - *Key decisions*: remove the per-área action-text decision, the most-severe open question and the per-company `CompanyArea` decision (the latter now belongs to the results doc's ADR-0004 link); keep engine decisions.
  - *Scope boundaries*: the engine and the employee card; company-level presentation is out of scope here and in scope for the results doc.

- [ ] **Step 3: `nom-035-valoracion-supuestos.md`** (Spanish, stakeholder-facing — match its existing voice and 🟡 markers). Add or rewrite sections:
  - **Grupos pequeños** — a Ejecutivo principal ve los resultados de un grupo filtrado solo si reúne al menos 5 cuestionarios; Administración puede verlos sin límite; la vista completa de la encuesta siempre se muestra. Confirmar el umbral y la excepción.
  - **Complementos y límite conocido** — también se oculta un grupo que deja fuera de 1 a 4 personas; restar dos vistas filtradas distintas sigue siendo posible y se documenta como límite conocido.
  - **Quiénes se cuentan** — las gráficas de sexo y edad y la tabla por área cuentan a quienes respondieron la encuesta seleccionada; los datos faltantes (y cuentas eliminadas) se agrupan como "Sin dato" / "Sin área"; la edad se calcula a la fecha de consulta.
  - **Guía I: tres resultados** — sin acontecimiento / acontecimiento sin requerir valoración / requiere valoración clínica; por qué se guarda el acontecimiento.
  - **§3 rewritten** — la plataforma no muestra un nivel de riesgo ni texto de acción por área o por empresa; se muestran distribuciones y estadísticas (promedio, mediana, rango). Pregunta abierta para la experta: cómo obtener la calificación general de la empresa y del área.

- [ ] **Step 4: Remaining docs** — `database.md`: `SubmissionScore.guia1_event`; the `can_view_small_groups` permission wherever permissions are listed. `overview.md:100`: replace the `company_valuation` reference with `apps/nom035/results.py`. `apps/nom035/CLAUDE.md`: `results.py` bullet, `aggregates.py` reduced to `employee_valuation`, `guia1_event` in the Guía I bullet. `apps/core/CLAUDE.md`: the results views and routes, `results_query.py`, `query_params.py`, `charts.py`, the `charts` tag library and the "run `npm run build:js` when touching `results_dashboard.ts`" note, the fragment view's query-count test. Root `CLAUDE.md`: mention the results page in the survey-data-flow line only if it names the dashboards panels. `docs/platform/overview.md` and `apps/accounts/CLAUDE.md`: `demographics.py` and the new permission.

- [ ] **Step 5: Verify and commit**

Run: `grep -rn "company_valuation\|_area_breakdown\|Por área" docs/platform apps templates .claude/CLAUDE.md` — Expected: no hits outside `docs/adr/` and migrations.
Run: `pytest && ruff check . && ruff format --check .`
Expected: PASS.

```bash
git add docs apps .claude/CLAUDE.md
git commit -m "docs: document the NOM-035 results dashboard; trim the analytics doc to the engine"
```

---

## Human verification (hand to the reviewer with the PR)

Run `python manage.py runserver`, log in as an Ejecutivo principal and as an Administrador, and on `/tablero-empresa/resultados/` (or `/empresas/<code>/resultados/`):

1. Change the survey selector — the body updates without a page reload; the address bar gains `?encuesta=…`.
2. Open *Filtros*, pick Femenino + an age band + an área, press *Aplicar* — the body updates, the disclosure closes, the count reads the number of values, pills appear.
3. Click a pill's × and an área name in the participation table — each updates in place.
4. Reload the page — the same filters and results render. Back button leaves the page (filters use `replaceState`).
5. Hover and tab onto bar segments, columns and strip points — a tooltip appears next to the mark and never leaves the viewport; tap on a phone shows it, tapping elsewhere hides it.
6. Expand a categoría in both the distribution and the statistics sections — dominio rows appear.
7. As Ejecutivo, filter to an área with fewer than 5 respondents — the message replaces the results; the sex and age charts still show. As Administrador, the same filter shows everything.
8. At 360px wide: no horizontal scroll; participation rows stack as cards; statistics strips sit below their numbers; overlapping strip labels alternate above and below.
9. Disable JavaScript — *Aplicar* reloads the page with the filters applied.
