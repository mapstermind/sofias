# NOM-035 Analytics Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the NOM-035 valuation engine (answers → score → Nivel de Riesgo) in a dedicated `apps/nom035` app and surface text-only results in the existing _Insights_ panels.

**Architecture:** A NOM-035-specific Django app holds scoring config as Python constants keyed by `surveys.Question.code`, a pure scoring service computes per-submission scores, a `post_save` signal materializes `SubmissionScore`/`GroupScore` rows on completion, and `apps/core` views read on-demand company/employee aggregates into the two dashboard panels. See `docs/platform/nom-035-analytics.md` and `docs/adr/adr-0003-per-instrument-survey-processing-apps.md`.

**Tech Stack:** Python 3.13, Django 6.0, PostgreSQL 17 (psycopg 3), pytest + pytest-django, ruff.

## Global Constraints

- **User-facing copy and URLs are in Spanish; code, comments, and identifiers are in English.**
- Python 3.13 / Django 6.0 only; no new third-party dependencies.
- Tests: `pytest` (settings `config.settings`, `addopts = --reuse-db -x`). Run a single test with `pytest path::test -v`.
- Lint/format must stay clean: `ruff format .` then `ruff check .` before every commit.
- Results are gated on the existing `accounts.can_view_insights` permission; the codename does **not** change. Tests that exercise permission-gated views use the `bootstrap_groups` fixture from the root `conftest.py`.
- `apps/surveys` and `apps/responses` own no scoring; the only integration key is `surveys.Question.code` (`g1-1…g1-15`, `g2-1…g2-46`, `g3-1…g3-72`).
- Likert answers are stored as ints 1–5 (1=Siempre … 5=Nunca); booleans as `true`/`false`.
- Every git commit message ends with the trailer:
  `Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>`
- Work on a feature branch, not `main`.

---

## 1. Rename and register the app

### Task 1: Rename `apps/analytics` → `apps/nom035` and register it

> ⚠️ **Risk (low, cross-file):** touches `INSTALLED_APPS`, two CLAUDE.md files, and removes an empty stub. No data migration — the stub was never registered and has no real migrations.

**Files:**
- Rename: `apps/analytics/` → `apps/nom035/` (use `git mv` to preserve history)
- Modify: `apps/nom035/apps.py`
- Modify: `config/settings.py:46-49` (`INSTALLED_APPS`)
- Replace: `apps/nom035/models.py`, `apps/nom035/views.py`, `apps/nom035/admin.py` (empty the stub bodies)
- Replace: `apps/analytics/CLAUDE.md` → `apps/nom035/CLAUDE.md`
- Modify: `.claude/CLAUDE.md` (architecture list + INSTALLED_APPS note), `apps/reports/CLAUDE.md` (analytics reference)
- Create: `apps/nom035/tests/__init__.py`, `apps/nom035/tests/test_app.py`

**Interfaces:**
- Produces: a registered, importable Django app `apps.nom035` (label `nom035`).

- [x] **Step 1: Write the failing test**

```python
# apps/nom035/tests/test_app.py
from django.apps import apps


def test_nom035_app_is_registered():
    assert apps.is_installed("apps.nom035")
    config = apps.get_app_config("nom035")
    assert config.name == "apps.nom035"
```

- [x] **Step 2: Run test to verify it fails**

Run: `pytest apps/nom035/tests/test_app.py -v`
Expected: FAIL — `LookupError: No installed app with label 'nom035'` (app not yet registered).

- [x] **Step 3: Rename the directory and update the app config**

```bash
git mv apps/analytics apps/nom035   # moves CLAUDE.md, apps.py, models.py, etc. with history
```

```python
# apps/nom035/apps.py
from django.apps import AppConfig


class Nom035Config(AppConfig):
    name = "apps.nom035"
    label = "nom035"
    default_auto_field = "django.db.models.BigAutoField"
```

- [x] **Step 4: Register the app and empty the stub bodies**

```python
# config/settings.py  (INSTALLED_APPS)
    "apps.accounts",
    "apps.core",
    "apps.surveys",
    "apps.responses",
    "apps.nom035",
```

```python
# apps/nom035/models.py
from django.db import models  # noqa: F401  (models added in Task 3)
```

```python
# apps/nom035/views.py
# Views live in apps/core; nom035 exposes no routes of its own.
```

```python
# apps/nom035/admin.py
# Result models are registered in Task 3.
```

- [x] **Step 5: Run test to verify it passes**

Run: `pytest apps/nom035/tests/test_app.py -v`
Expected: PASS.

- [x] **Step 6: Update the doc references**

Replace `apps/nom035/CLAUDE.md` with a short description of the valuation engine (engine + materialized scores + signal + command, NOM-035-specific). In `.claude/CLAUDE.md` change the `analytics/` architecture line and the "Registered apps" note to reference `apps.nom035`; in `apps/reports/CLAUDE.md` update the `analytics` mention to `nom035`.

- [x] **Step 7: Commit**

```bash
ruff format . && ruff check .
git add -A
git commit -m "chore: rename analytics stub to nom035 app and register it

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

## 2. Scoring primitives and constants

### Task 2: Pure scoring primitives + shared constants

> No external data needed — fully deterministic, the foundation other tasks import.

**Files:**
- Create: `apps/nom035/constants.py`
- Create: `apps/nom035/scoring.py`
- Create: `apps/nom035/tests/test_scoring_primitives.py`

**Interfaces:**
- Produces:
  - `constants.NDR_NULO/NDR_BAJO/NDR_MEDIO/NDR_ALTO/NDR_MUY_ALTO` (`str`), `NDR_ORDER: list[str]`, `NDR_LABELS: dict[str, str]`
  - `constants.SEV_NONE/SEV_LOW/SEV_MED/SEV_HIGH` (`str`)
  - `constants.LEVEL_CATEGORIA/LEVEL_DOMINIO/LEVEL_DIMENSION` (`str`)
  - `scoring.likert_item_score(value: int, *, inverted: bool) -> int`
  - `scoring.classify(bands: list[tuple[float, str]], score: int) -> str` — `bands` ascending by upper bound; returns the level of the first band whose `score < upper`. Last band uses `float("inf")`.
  - `scoring.guia1_severity(event: bool, followup_count: int) -> str`

- [x] **Step 1: Write the failing test**

```python
# apps/nom035/tests/test_scoring_primitives.py
from apps.nom035 import constants as c
from apps.nom035.scoring import classify, guia1_severity, likert_item_score


def test_normal_item_maps_1_to_5_onto_0_to_4():
    assert likert_item_score(1, inverted=False) == 0  # Siempre
    assert likert_item_score(5, inverted=False) == 4  # Nunca


def test_inverted_item_reverses_the_scale():
    assert likert_item_score(1, inverted=True) == 4  # Siempre
    assert likert_item_score(5, inverted=True) == 0  # Nunca


def test_classify_returns_band_level():
    bands = [(50, c.NDR_NULO), (75, c.NDR_BAJO), (float("inf"), c.NDR_ALTO)]
    assert classify(bands, 49) == c.NDR_NULO
    assert classify(bands, 50) == c.NDR_BAJO
    assert classify(bands, 200) == c.NDR_ALTO


def test_guia1_severity_bands():
    assert guia1_severity(False, 9) == c.SEV_NONE   # no event → no flag
    assert guia1_severity(True, 1) == c.SEV_LOW
    assert guia1_severity(True, 3) == c.SEV_MED
    assert guia1_severity(True, 6) == c.SEV_HIGH
```

- [x] **Step 2: Run test to verify it fails**

Run: `pytest apps/nom035/tests/test_scoring_primitives.py -v`
Expected: FAIL — `ModuleNotFoundError: apps.nom035.constants`.

- [x] **Step 3: Write minimal implementation**

```python
# apps/nom035/constants.py
NDR_NULO = "nulo"
NDR_BAJO = "bajo"
NDR_MEDIO = "medio"
NDR_ALTO = "alto"
NDR_MUY_ALTO = "muy_alto"
NDR_ORDER = [NDR_NULO, NDR_BAJO, NDR_MEDIO, NDR_ALTO, NDR_MUY_ALTO]
NDR_LABELS = {
    NDR_NULO: "Nulo",
    NDR_BAJO: "Bajo",
    NDR_MEDIO: "Medio",
    NDR_ALTO: "Alto",
    NDR_MUY_ALTO: "Muy alto",
}

SEV_NONE = "none"
SEV_LOW = "low"
SEV_MED = "med"
SEV_HIGH = "high"

LEVEL_CATEGORIA = "categoria"
LEVEL_DOMINIO = "dominio"
LEVEL_DIMENSION = "dimension"
```

```python
# apps/nom035/scoring.py
from apps.nom035 import constants as c


def likert_item_score(value: int, *, inverted: bool) -> int:
    """Map a stored Likert answer (1=Siempre … 5=Nunca) to the NOM-035 0–4 scale."""
    return (5 - value) if inverted else (value - 1)


def classify(bands: list[tuple[float, str]], score: int) -> str:
    """Return the NDR level for `score`. `bands` is ascending by upper bound."""
    for upper, level in bands:
        if score < upper:
            return level
    return bands[-1][1]


# MVP assumption (see docs/platform/nom-035-valoracion-supuestos.md §2.5):
# event with 1–2 follow-ups = low, 3–5 = med, 6+ = high.
def guia1_severity(event: bool, followup_count: int) -> str:
    if not event:
        return c.SEV_NONE
    if followup_count >= 6:
        return c.SEV_HIGH
    if followup_count >= 3:
        return c.SEV_MED
    return c.SEV_LOW
```

- [x] **Step 4: Run test to verify it passes**

Run: `pytest apps/nom035/tests/test_scoring_primitives.py -v`
Expected: PASS.

- [x] **Step 5: Commit**

```bash
ruff format . && ruff check .
git add apps/nom035/constants.py apps/nom035/scoring.py apps/nom035/tests/test_scoring_primitives.py
git commit -m "feat: add nom035 scoring primitives and constants

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

## 3. Result models

### Task 3: `SubmissionScore` and `GroupScore` models + migration

**Files:**
- Modify: `apps/nom035/models.py`
- Modify: `apps/nom035/admin.py`
- Create: `apps/nom035/migrations/0001_initial.py` (via `makemigrations`)
- Create: `apps/nom035/tests/test_models.py`

**Interfaces:**
- Consumes: `constants` (Task 2).
- Produces:
  - `models.SubmissionScore(submission: OneToOne[responses.SurveySubmission], final_score: int, final_ndr: str, guia1_event: bool, guia1_followup_count: int, guia1_severity: str, computed_at: datetime)`
  - `models.GroupScore(submission_score: FK[SubmissionScore, related_name="groups"], level: str, key: str, score: int, ndr: str)` with `unique_together = (submission_score, level, key)`
  - `models.NDR`, `models.Severity`, `models.GroupLevel` (`TextChoices`)

- [x] **Step 1: Write the failing test**

```python
# apps/nom035/tests/test_models.py
import pytest

from apps.nom035 import constants as c
from apps.nom035.models import GroupScore, SubmissionScore
from apps.responses.models import SurveySubmission

pytestmark = pytest.mark.django_db


def _submission(active_assignment):
    return SurveySubmission.objects.create(
        assignment=active_assignment, status=SurveySubmission.Status.COMPLETED
    )


def test_submission_score_is_one_per_submission(active_assignment):
    sub = _submission(active_assignment)
    SubmissionScore.objects.create(
        submission=sub,
        final_score=120,
        final_ndr=c.NDR_ALTO,
        guia1_event=True,
        guia1_followup_count=4,
        guia1_severity=c.SEV_MED,
    )
    with pytest.raises(Exception):
        SubmissionScore.objects.create(submission=sub, final_score=1, final_ndr=c.NDR_NULO)


def test_group_score_unique_per_level_and_key(active_assignment):
    sub = _submission(active_assignment)
    score = SubmissionScore.objects.create(
        submission=sub, final_score=10, final_ndr=c.NDR_NULO
    )
    GroupScore.objects.create(
        submission_score=score, level=c.LEVEL_CATEGORIA, key="ambiente", score=5, ndr=c.NDR_NULO
    )
    with pytest.raises(Exception):
        GroupScore.objects.create(
            submission_score=score, level=c.LEVEL_CATEGORIA, key="ambiente", score=9, ndr=c.NDR_BAJO
        )
```

- [x] **Step 2: Run test to verify it fails**

Run: `pytest apps/nom035/tests/test_models.py -v`
Expected: FAIL — `ImportError: cannot import name 'SubmissionScore'`.

- [x] **Step 3: Write the models**

```python
# apps/nom035/models.py
from django.db import models

from apps.nom035 import constants as c


class NDR(models.TextChoices):
    NULO = c.NDR_NULO, "Nulo"
    BAJO = c.NDR_BAJO, "Bajo"
    MEDIO = c.NDR_MEDIO, "Medio"
    ALTO = c.NDR_ALTO, "Alto"
    MUY_ALTO = c.NDR_MUY_ALTO, "Muy alto"


class Severity(models.TextChoices):
    NONE = c.SEV_NONE, "Ninguna"
    LOW = c.SEV_LOW, "Baja"
    MED = c.SEV_MED, "Media"
    HIGH = c.SEV_HIGH, "Alta"


class GroupLevel(models.TextChoices):
    CATEGORIA = c.LEVEL_CATEGORIA, "Categoría"
    DOMINIO = c.LEVEL_DOMINIO, "Dominio"
    DIMENSION = c.LEVEL_DIMENSION, "Dimensión"


class SubmissionScore(models.Model):
    submission = models.OneToOneField(
        "responses.SurveySubmission",
        on_delete=models.CASCADE,
        related_name="nom035_score",
    )
    final_score = models.IntegerField(default=0)
    final_ndr = models.CharField(max_length=10, choices=NDR.choices, default=NDR.NULO)
    guia1_event = models.BooleanField(default=False)
    guia1_followup_count = models.IntegerField(default=0)
    guia1_severity = models.CharField(
        max_length=10, choices=Severity.choices, default=Severity.NONE
    )
    computed_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Score({self.submission_id}={self.final_ndr})"


class GroupScore(models.Model):
    submission_score = models.ForeignKey(
        SubmissionScore, on_delete=models.CASCADE, related_name="groups"
    )
    level = models.CharField(max_length=12, choices=GroupLevel.choices)
    key = models.CharField(max_length=64)
    score = models.IntegerField(default=0)
    ndr = models.CharField(max_length=10, choices=NDR.choices, default=NDR.NULO)

    class Meta:
        unique_together = ("submission_score", "level", "key")
        indexes = [
            models.Index(fields=["submission_score", "level"]),
            models.Index(fields=["level", "ndr"]),
        ]
```

```python
# apps/nom035/admin.py
from django.contrib import admin

from apps.nom035.models import GroupScore, SubmissionScore


class GroupScoreInline(admin.TabularInline):
    model = GroupScore
    extra = 0


@admin.register(SubmissionScore)
class SubmissionScoreAdmin(admin.ModelAdmin):
    list_display = ("submission", "final_ndr", "final_score", "guia1_severity", "computed_at")
    inlines = [GroupScoreInline]
```

- [x] **Step 4: Make and run the migration**

Run: `python manage.py makemigrations nom035`
Then: `pytest apps/nom035/tests/test_models.py -v`
Expected: migration `0001_initial.py` created; tests PASS.

- [x] **Step 5: Commit**

```bash
ruff format . && ruff check .
git add apps/nom035/models.py apps/nom035/admin.py apps/nom035/migrations/ apps/nom035/tests/test_models.py
git commit -m "feat: add nom035 SubmissionScore and GroupScore models

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

## 4. NOM-035 scoring configuration data

### Task 4: Transcribe the NOM-035 scoring config

> ⚠️ **HIGH RISK / DECISION-BEARING.** This is the transcription of the Guías de Referencia: the Categoría→Dominio→Dimensión taxonomy (all 46 Guía II + 72 Guía III item codes), the inverted-item set, and the threshold tables. The official numbers require domain-expert validation; gaps are filled with documented MVP assumptions tracked in `docs/platform/nom-035-valoracion-supuestos.md`. The tests below assert **structural completeness and monotonicity**, NOT clinical correctness — that is validated later against a worked example (see §0 note in the spec). Do not invent silently: every assumption added here gets a line in the supuestos doc's bitácora.

**Files:**
- Create: `apps/nom035/_nom035_scoring.py`
- Create: `apps/nom035/tests/test_config.py`
- Modify: `docs/platform/nom-035-valoracion-supuestos.md` (log any assumption made while transcribing)

**Interfaces:**
- Consumes: `surveys.Question.code` values, `constants` (Task 2).
- Produces:
  - `GUIA1_TRIGGER_CODE: str` (`"g1-1"`), `GUIA1_FOLLOWUP_CODES: list[str]` (`g1-2…g1-15`)
  - `taxonomy_for_variant(variant: str) -> dict[str, tuple[str, str, str]]` — likert code → `(categoria_key, dominio_key, dimension_key)`. `variant` is `"small"` (Guía II) or `"large"` (Guía III).
  - `is_inverted(code: str) -> bool`
  - `thresholds_for(level: str, key: str, variant: str) -> list[tuple[float, str]]` — ascending bands ending in `float("inf")`
  - `action_text(ndr: str) -> str`

- [x] **Step 1: Write the failing test**

```python
# apps/nom035/tests/test_config.py
from apps.nom035 import _nom035_scoring as cfg
from apps.nom035 import constants as c


def _required_codes(prefix, count):
    return {f"{prefix}-{i}" for i in range(1, count + 1)}


def test_guia1_codes():
    assert cfg.GUIA1_TRIGGER_CODE == "g1-1"
    assert set(cfg.GUIA1_FOLLOWUP_CODES) == _required_codes("g1", 15) - {"g1-1"}


def test_taxonomy_covers_every_likert_item():
    small = cfg.taxonomy_for_variant("small")
    large = cfg.taxonomy_for_variant("large")
    # Conditional blocks (clientes/jefe) may be absent for a given respondent but
    # MUST exist in the taxonomy so they can be scored when answered.
    assert _required_codes("g2", 46) <= set(small)
    assert _required_codes("g3", 72) <= set(large)
    for mapping in (small, large):
        for cat, dom, dim in mapping.values():
            assert cat and dom and dim


def test_thresholds_are_monotonic_and_end_in_infinity():
    bands = cfg.thresholds_for(c.LEVEL_DIMENSION, next(iter(cfg.taxonomy_for_variant("large").values()))[2], "large")
    uppers = [u for u, _ in bands]
    assert uppers == sorted(uppers)
    assert bands[-1][0] == float("inf")
    assert {lvl for _, lvl in bands} <= set(c.NDR_ORDER)


def test_action_text_exists_for_every_level():
    for level in c.NDR_ORDER:
        assert cfg.action_text(level)


def test_known_final_band_large():
    # From the documented Guía III final table.
    assert cfg.thresholds_for("final", "final", "large") == [
        (50, c.NDR_NULO),
        (75, c.NDR_BAJO),
        (99, c.NDR_MEDIO),
        (140, c.NDR_ALTO),
        (float("inf"), c.NDR_MUY_ALTO),
    ]
```

- [x] **Step 2: Run test to verify it fails**

Run: `pytest apps/nom035/tests/test_config.py -v`
Expected: FAIL — `ModuleNotFoundError: apps.nom035._nom035_scoring`.

- [x] **Step 3: Build the config module**

Transcribe from `docs/internal/roadmap_context/Guias de Referencia.pdf` and `Ejemplo Reporte Resultados.pdf`. Structure (fill **every** required code; example rows shown):

```python
# apps/nom035/_nom035_scoring.py
from apps.nom035 import constants as c

GUIA1_TRIGGER_CODE = "g1-1"
GUIA1_FOLLOWUP_CODES = [f"g1-{i}" for i in range(2, 16)]

# code -> (categoria_key, dominio_key, dimension_key). Transcribe ALL items.
# Example rows (replace with the full official mapping):
_TAXONOMY_SMALL = {
    "g2-1": ("ambiente_de_trabajo", "condiciones_ambiente", "condiciones_peligrosas"),
    # … g2-2 … g2-46 …
}
_TAXONOMY_LARGE = {
    "g3-1": ("ambiente_de_trabajo", "condiciones_ambiente", "condiciones_peligrosas"),
    # … g3-2 … g3-72 …
}

# Positively-worded items scored in reverse. Transcribe from the Guías.
INVERTED_ITEMS: set[str] = {
    # "g2-...", "g3-...",
}

# bands: ascending (upper_exclusive, level), last is float("inf").
_FINAL_LARGE = [
    (50, c.NDR_NULO),
    (75, c.NDR_BAJO),
    (99, c.NDR_MEDIO),
    (140, c.NDR_ALTO),
    (float("inf"), c.NDR_MUY_ALTO),
]
# Per-categoria / per-dominio / per-dimension band tables, per variant.
# Transcribe from the example report; where the source is silent, derive a
# documented assumption and log it in the supuestos doc.
_THRESHOLDS = {
    ("final", "final", "large"): _FINAL_LARGE,
    # ("final", "final", "small"): [...],
    # ("categoria", "ambiente_de_trabajo", "large"): [...],
    # ("dominio", "condiciones_ambiente", "large"): [...],
    # ("dimension", "condiciones_peligrosas", "large"): [...],
}

_ACTION_TEXT = {
    c.NDR_NULO: "El riesgo resulta despreciable, por lo que no se requiere acción adicional.",
    c.NDR_BAJO: "Es necesario observar y revisar periódicamente las condiciones evaluadas.",
    c.NDR_MEDIO: "Se requiere revisar la política de prevención de riesgos psicosociales y reforzar su aplicación.",
    c.NDR_ALTO: "Se requiere realizar un análisis de cada categoría y dominio para establecer acciones de intervención.",
    c.NDR_MUY_ALTO: "Se requiere intervención inmediata y la atención clínica de los colaboradores que lo requieran.",
}


def taxonomy_for_variant(variant: str) -> dict[str, tuple[str, str, str]]:
    return _TAXONOMY_LARGE if variant == "large" else _TAXONOMY_SMALL


def is_inverted(code: str) -> bool:
    return code in INVERTED_ITEMS


def thresholds_for(level: str, key: str, variant: str) -> list[tuple[float, str]]:
    return _THRESHOLDS[(level, key, variant)]


def action_text(ndr: str) -> str:
    return _ACTION_TEXT[ndr]
```

> If `thresholds_for` would otherwise raise `KeyError` for a real group during Task 5, that is the signal a band table is missing — add it here and log the assumption, don't swallow the error.

- [x] **Step 4: Run test to verify it passes**

Run: `pytest apps/nom035/tests/test_config.py -v`
Expected: PASS once every required code is mapped and band tables are present and monotonic.

- [x] **Step 5: Update the supuestos doc and commit**

Add a bitácora row for each assumption made (inverted items chosen, threshold gaps filled, taxonomy ambiguities resolved).

```bash
ruff format . && ruff check .
git add apps/nom035/_nom035_scoring.py apps/nom035/tests/test_config.py docs/platform/nom-035-valoracion-supuestos.md
git commit -m "feat: add NOM-035 scoring configuration (MVP, assumptions logged)

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

## 5. The scoring service

### Task 5: `score_submission` — answers + config → result

> ⚠️ **Decision (documented):** items in conditional blocks a respondent did not see (non-jefe / non-clientes) are simply absent from the sum; thresholds are the full fixed tables. This is the known skipped-blocks bias logged in the supuestos doc §2.4.

**Files:**
- Modify: `apps/nom035/scoring.py`
- Create: `apps/nom035/tests/test_score_submission.py`

**Interfaces:**
- Consumes: `likert_item_score`, `classify`, `guia1_severity` (Task 2); `_nom035_scoring` accessors (Task 4); `responses.SurveySubmission`/`Answer`, `surveys` seed.
- Produces:
  - `scoring.GroupResult(level: str, key: str, score: int, ndr: str)` (frozen dataclass)
  - `scoring.ScoreResult(final_score: int, final_ndr: str, groups: list[GroupResult], guia1_event: bool, guia1_followup_count: int, guia1_severity: str)` (frozen dataclass)
  - `scoring.score_submission(submission) -> ScoreResult`

- [x] **Step 1: Write the failing test**

```python
# apps/nom035/tests/test_score_submission.py
import pytest
from django.core.management import call_command

from apps.nom035 import _nom035_scoring as cfg
from apps.nom035 import constants as c
from apps.nom035.scoring import score_submission
from apps.responses.models import Answer, SurveySubmission
from apps.surveys.models import Question, Survey, SurveyAssignment

pytestmark = pytest.mark.django_db


@pytest.fixture
def nom035_assignment(make_company):
    call_command("seed_nom035_survey")
    survey = Survey.objects.get(key="nom035")
    return SurveyAssignment.objects.create(
        company=make_company(),
        survey=survey,
        variant=SurveyAssignment.Variant.LARGE,
        status=SurveyAssignment.Status.ACTIVE,
    )


def test_all_nunca_yields_max_normal_item_scores(nom035_assignment):
    sub = SurveySubmission.objects.create(
        assignment=nom035_assignment, status=SurveySubmission.Status.COMPLETED
    )
    taxonomy = cfg.taxonomy_for_variant("large")
    codes = {q.code: q for q in Question.objects.filter(survey=nom035_assignment.survey)}
    for code in taxonomy:
        Answer.objects.create(submission=sub, question=codes[code], value=5)  # Nunca

    result = score_submission(sub)

    expected_final = sum(
        (0 if cfg.is_inverted(code) else 4) for code in taxonomy
    )
    assert result.final_score == expected_final
    assert {g.level for g in result.groups} == {
        c.LEVEL_CATEGORIA, c.LEVEL_DOMINIO, c.LEVEL_DIMENSION
    }


def test_guia1_flag_and_severity(nom035_assignment):
    sub = SurveySubmission.objects.create(
        assignment=nom035_assignment, status=SurveySubmission.Status.COMPLETED
    )
    codes = {q.code: q for q in Question.objects.filter(survey=nom035_assignment.survey)}
    Answer.objects.create(submission=sub, question=codes["g1-1"], value=True)
    for code in cfg.GUIA1_FOLLOWUP_CODES[:3]:
        Answer.objects.create(submission=sub, question=codes[code], value=True)

    result = score_submission(sub)
    assert result.guia1_event is True
    assert result.guia1_followup_count == 3
    assert result.guia1_severity == c.SEV_MED
```

- [x] **Step 2: Run test to verify it fails**

Run: `pytest apps/nom035/tests/test_score_submission.py -v`
Expected: FAIL — `ImportError: cannot import name 'score_submission'`.

- [x] **Step 3: Implement `score_submission`**

```python
# apps/nom035/scoring.py  (append)
from dataclasses import dataclass

from apps.nom035 import _nom035_scoring as cfg


@dataclass(frozen=True)
class GroupResult:
    level: str
    key: str
    score: int
    ndr: str


@dataclass(frozen=True)
class ScoreResult:
    final_score: int
    final_ndr: str
    groups: list[GroupResult]
    guia1_event: bool
    guia1_followup_count: int
    guia1_severity: str


def score_submission(submission) -> ScoreResult:
    variant = submission.assignment.variant
    answers = {
        a.question.code: a.value
        for a in submission.answers.select_related("question")
    }

    taxonomy = cfg.taxonomy_for_variant(variant)
    dim, dom, cat = {}, {}, {}
    final = 0
    for code, (cat_key, dom_key, dim_key) in taxonomy.items():
        value = answers.get(code)
        if value is None:
            continue  # unanswered or hidden block — excluded (see supuestos §2.4)
        s = likert_item_score(int(value), inverted=cfg.is_inverted(code))
        final += s
        dim[dim_key] = dim.get(dim_key, 0) + s
        dom[dom_key] = dom.get(dom_key, 0) + s
        cat[cat_key] = cat.get(cat_key, 0) + s

    groups = []
    for level, sums in (
        (c.LEVEL_DIMENSION, dim),
        (c.LEVEL_DOMINIO, dom),
        (c.LEVEL_CATEGORIA, cat),
    ):
        for key, score in sums.items():
            ndr = classify(cfg.thresholds_for(level, key, variant), score)
            groups.append(GroupResult(level=level, key=key, score=score, ndr=ndr))

    final_ndr = classify(cfg.thresholds_for("final", "final", variant), final)

    event = answers.get(cfg.GUIA1_TRIGGER_CODE) is True
    followups = sum(1 for code in cfg.GUIA1_FOLLOWUP_CODES if answers.get(code) is True)

    return ScoreResult(
        final_score=final,
        final_ndr=final_ndr,
        groups=groups,
        guia1_event=event,
        guia1_followup_count=followups,
        guia1_severity=guia1_severity(event, followups),
    )
```

- [x] **Step 4: Run test to verify it passes**

Run: `pytest apps/nom035/tests/test_score_submission.py -v`
Expected: PASS.

- [x] **Step 5: Commit**

```bash
ruff format . && ruff check .
git add apps/nom035/scoring.py apps/nom035/tests/test_score_submission.py
git commit -m "feat: compute NOM-035 score from a submission

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

## 6. Materialization

### Task 6: `materialize` — write/refresh result rows

**Files:**
- Create: `apps/nom035/services.py`
- Create: `apps/nom035/tests/test_materialize.py`

**Interfaces:**
- Consumes: `score_submission` (Task 5), `SubmissionScore`/`GroupScore` (Task 3).
- Produces: `services.materialize(submission) -> SubmissionScore` (idempotent upsert in a transaction).

- [x] **Step 1: Write the failing test**

```python
# apps/nom035/tests/test_materialize.py
import pytest
from django.core.management import call_command

from apps.nom035.models import GroupScore, SubmissionScore
from apps.nom035.services import materialize
from apps.responses.models import Answer, SurveySubmission
from apps.surveys.models import Question, Survey, SurveyAssignment

pytestmark = pytest.mark.django_db


@pytest.fixture
def completed_submission(make_company):
    call_command("seed_nom035_survey")
    survey = Survey.objects.get(key="nom035")
    assignment = SurveyAssignment.objects.create(
        company=make_company(), survey=survey,
        variant=SurveyAssignment.Variant.LARGE,
        status=SurveyAssignment.Status.ACTIVE,
    )
    sub = SurveySubmission.objects.create(
        assignment=assignment, status=SurveySubmission.Status.COMPLETED
    )
    codes = {q.code: q for q in Question.objects.filter(survey=survey)}
    for code in [f"g3-{i}" for i in range(1, 10)]:
        Answer.objects.create(submission=sub, question=codes[code], value=5)
    return sub


def test_materialize_creates_rows(completed_submission):
    score = materialize(completed_submission)
    assert SubmissionScore.objects.count() == 1
    assert score.groups.count() > 0


def test_materialize_is_idempotent(completed_submission):
    first = materialize(completed_submission)
    before = first.groups.count()
    second = materialize(completed_submission)
    assert SubmissionScore.objects.count() == 1
    assert second.groups.count() == before
```

- [x] **Step 2: Run test to verify it fails**

Run: `pytest apps/nom035/tests/test_materialize.py -v`
Expected: FAIL — `ModuleNotFoundError: apps.nom035.services`.

- [x] **Step 3: Implement `materialize`**

```python
# apps/nom035/services.py
from django.db import transaction

from apps.nom035.models import GroupScore, SubmissionScore
from apps.nom035.scoring import score_submission


@transaction.atomic
def materialize(submission) -> SubmissionScore:
    result = score_submission(submission)
    score, _ = SubmissionScore.objects.update_or_create(
        submission=submission,
        defaults={
            "final_score": result.final_score,
            "final_ndr": result.final_ndr,
            "guia1_event": result.guia1_event,
            "guia1_followup_count": result.guia1_followup_count,
            "guia1_severity": result.guia1_severity,
        },
    )
    score.groups.all().delete()
    GroupScore.objects.bulk_create(
        [
            GroupScore(
                submission_score=score, level=g.level, key=g.key, score=g.score, ndr=g.ndr
            )
            for g in result.groups
        ]
    )
    return score
```

- [x] **Step 4: Run test to verify it passes**

Run: `pytest apps/nom035/tests/test_materialize.py -v`
Expected: PASS.

- [x] **Step 5: Commit**

```bash
ruff format . && ruff check .
git add apps/nom035/services.py apps/nom035/tests/test_materialize.py
git commit -m "feat: materialize NOM-035 scores into result rows

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

## 7. Automatic scoring on completion

### Task 7: `post_save` signal on `SurveySubmission`

> ⚠️ **Risk (wiring):** the receiver must be connected in `AppConfig.ready()`, and must do nothing for non-completed submissions to avoid scoring drafts. It must not re-save the submission (no recursion).

**Files:**
- Create: `apps/nom035/signals.py`
- Modify: `apps/nom035/apps.py` (`ready()`)
- Create: `apps/nom035/tests/test_signal.py`

**Interfaces:**
- Consumes: `materialize` (Task 6).
- Produces: a connected `post_save` receiver that materializes a score when `submission.status == "completed"`.

- [x] **Step 1: Write the failing test**

```python
# apps/nom035/tests/test_signal.py
import pytest
from django.core.management import call_command

from apps.nom035.models import SubmissionScore
from apps.responses.models import Answer, SurveySubmission
from apps.surveys.models import Question, Survey, SurveyAssignment

pytestmark = pytest.mark.django_db


@pytest.fixture
def assignment(make_company):
    call_command("seed_nom035_survey")
    return SurveyAssignment.objects.create(
        company=make_company(), survey=Survey.objects.get(key="nom035"),
        variant=SurveyAssignment.Variant.LARGE,
        status=SurveyAssignment.Status.ACTIVE,
    )


def test_completed_submission_is_scored_automatically(assignment):
    sub = SurveySubmission.objects.create(
        assignment=assignment, status=SurveySubmission.Status.IN_PROGRESS
    )
    q = Question.objects.filter(survey=assignment.survey, code="g3-1").first()
    Answer.objects.create(submission=sub, question=q, value=5)
    assert not SubmissionScore.objects.filter(submission=sub).exists()

    sub.status = SurveySubmission.Status.COMPLETED
    sub.save()

    assert SubmissionScore.objects.filter(submission=sub).exists()
```

- [x] **Step 2: Run test to verify it fails**

Run: `pytest apps/nom035/tests/test_signal.py -v`
Expected: FAIL — `SubmissionScore` not created (no signal connected).

- [x] **Step 3: Implement the signal and connect it**

```python
# apps/nom035/signals.py
from django.db.models.signals import post_save
from django.dispatch import receiver

from apps.nom035.services import materialize
from apps.responses.models import SurveySubmission


@receiver(post_save, sender=SurveySubmission)
def score_on_completion(sender, instance, **kwargs):
    if instance.status == SurveySubmission.Status.COMPLETED:
        materialize(instance)
```

```python
# apps/nom035/apps.py  (add ready)
from django.apps import AppConfig


class Nom035Config(AppConfig):
    name = "apps.nom035"
    label = "nom035"
    default_auto_field = "django.db.models.BigAutoField"

    def ready(self):
        from apps.nom035 import signals  # noqa: F401
```

- [x] **Step 4: Run test to verify it passes**

Run: `pytest apps/nom035/tests/test_signal.py -v`
Expected: PASS.

- [x] **Step 5: Run the surveys view tests to confirm no regression**

Run: `pytest apps/surveys/tests/ -v`
Expected: PASS (submission completion in the survey flow now also scores, without errors).

- [x] **Step 6: Commit**

```bash
ruff format . && ruff check .
git add apps/nom035/signals.py apps/nom035/apps.py apps/nom035/tests/test_signal.py
git commit -m "feat: score NOM-035 submissions on completion via signal

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

## 8. Backfill / refresh command

### Task 8: `recompute_nom035_scores` management command

**Files:**
- Create: `apps/nom035/management/__init__.py`, `apps/nom035/management/commands/__init__.py`
- Create: `apps/nom035/management/commands/recompute_nom035_scores.py`
- Create: `apps/nom035/tests/test_recompute_command.py`

**Interfaces:**
- Consumes: `materialize` (Task 6).
- Produces: `python manage.py recompute_nom035_scores [--company <reference_code>]` — materializes every completed submission (optionally filtered by company).

- [x] **Step 1: Write the failing test**

```python
# apps/nom035/tests/test_recompute_command.py
import pytest
from django.core.management import call_command

from apps.nom035.models import SubmissionScore
from apps.responses.models import Answer, SurveySubmission
from apps.surveys.models import Question, Survey, SurveyAssignment

pytestmark = pytest.mark.django_db


def test_recompute_scores_all_completed(make_company):
    call_command("seed_nom035_survey")
    survey = Survey.objects.get(key="nom035")
    assignment = SurveyAssignment.objects.create(
        company=make_company(), survey=survey,
        variant=SurveyAssignment.Variant.LARGE,
        status=SurveyAssignment.Status.ACTIVE,
    )
    sub = SurveySubmission.objects.create(
        assignment=assignment, status=SurveySubmission.Status.COMPLETED
    )
    q = Question.objects.get(survey=survey, code="g3-1")
    Answer.objects.create(submission=sub, question=q, value=5)
    SubmissionScore.objects.all().delete()  # simulate stale/missing scores

    call_command("recompute_nom035_scores")

    assert SubmissionScore.objects.filter(submission=sub).exists()
```

- [x] **Step 2: Run test to verify it fails**

Run: `pytest apps/nom035/tests/test_recompute_command.py -v`
Expected: FAIL — `CommandError: Unknown command 'recompute_nom035_scores'`.

- [x] **Step 3: Implement the command**

```python
# apps/nom035/management/commands/recompute_nom035_scores.py
from django.core.management.base import BaseCommand

from apps.nom035.services import materialize
from apps.responses.models import SurveySubmission


class Command(BaseCommand):
    help = "Recompute NOM-035 scores for completed submissions."

    def add_arguments(self, parser):
        parser.add_argument("--company", default=None, help="Company reference_code")

    def handle(self, *args, **options):
        qs = SurveySubmission.objects.filter(status=SurveySubmission.Status.COMPLETED)
        if options["company"]:
            qs = qs.filter(assignment__company__reference_code=options["company"])
        count = 0
        for submission in qs.iterator():
            materialize(submission)
            count += 1
        self.stdout.write(self.style.SUCCESS(f"Recomputed {count} submission scores."))
```

- [x] **Step 4: Run test to verify it passes**

Run: `pytest apps/nom035/tests/test_recompute_command.py -v`
Expected: PASS.

- [x] **Step 5: Commit**

```bash
ruff format . && ruff check .
git add apps/nom035/management/ apps/nom035/tests/test_recompute_command.py
git commit -m "feat: add recompute_nom035_scores command

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

## 9. Aggregation helpers

### Task 9: `employee_valuation` and `company_valuation`

**Files:**
- Create: `apps/nom035/aggregates.py`
- Create: `apps/nom035/tests/test_aggregates.py`

**Interfaces:**
- Consumes: `SubmissionScore`/`GroupScore` (Task 3), `_nom035_scoring.action_text` (Task 4), `constants`.
- Produces:
  - `aggregates.employee_valuation(user, company) -> dict | None` — `None` if the user has no scored submission in the company. Dict keys: `final_ndr`, `final_ndr_label`, `final_score`, `final_action`, `categories` (list of `{key, ndr, ndr_label, action}`), `guia1_event`, `guia1_severity`.
  - `aggregates.company_valuation(company) -> dict` — keys: `scored_count`, `distribution` (`dict[str, int]` over `NDR_ORDER`), `needing_action` (alto+muy_alto count), `guia1_flags` (count of `guia1_event`).

- [x] **Step 1: Write the failing test**

```python
# apps/nom035/tests/test_aggregates.py
import pytest

from apps.nom035 import constants as c
from apps.nom035.aggregates import company_valuation, employee_valuation
from apps.nom035.models import SubmissionScore
from apps.responses.models import SurveySubmission
from apps.surveys.models import SurveyAssignment

pytestmark = pytest.mark.django_db


@pytest.fixture
def scored(make_company, make_user, survey):
    company = make_company()
    user = make_user(email="e@x.mx")
    assignment = SurveyAssignment.objects.create(
        company=company, survey=survey,
        variant=SurveyAssignment.Variant.LARGE,
        status=SurveyAssignment.Status.ACTIVE,
    )
    sub = SurveySubmission.objects.create(
        assignment=assignment, user=user, status=SurveySubmission.Status.COMPLETED
    )
    SubmissionScore.objects.create(
        submission=sub, final_score=160, final_ndr=c.NDR_MUY_ALTO,
        guia1_event=True, guia1_followup_count=6, guia1_severity=c.SEV_HIGH,
    )
    return {"company": company, "user": user}


def test_company_valuation_counts(scored):
    data = company_valuation(scored["company"])
    assert data["scored_count"] == 1
    assert data["needing_action"] == 1
    assert data["guia1_flags"] == 1
    assert data["distribution"][c.NDR_MUY_ALTO] == 1


def test_employee_valuation_returns_text(scored):
    data = employee_valuation(scored["user"], scored["company"])
    assert data["final_ndr"] == c.NDR_MUY_ALTO
    assert data["final_action"]


def test_employee_valuation_none_when_unscored(make_company, make_user):
    assert employee_valuation(make_user(email="n@x.mx"), make_company()) is None
```

- [x] **Step 2: Run test to verify it fails**

Run: `pytest apps/nom035/tests/test_aggregates.py -v`
Expected: FAIL — `ModuleNotFoundError: apps.nom035.aggregates`.

- [x] **Step 3: Implement the aggregates**

```python
# apps/nom035/aggregates.py
from apps.nom035 import _nom035_scoring as cfg
from apps.nom035 import constants as c
from apps.nom035.models import NDR, GroupLevel, SubmissionScore


def _scores_for_company(company):
    return SubmissionScore.objects.filter(submission__assignment__company=company)


def company_valuation(company) -> dict:
    scores = list(_scores_for_company(company))
    distribution = {level: 0 for level in c.NDR_ORDER}
    needing_action = 0
    guia1_flags = 0
    for s in scores:
        distribution[s.final_ndr] += 1
        if s.final_ndr in (c.NDR_ALTO, c.NDR_MUY_ALTO):
            needing_action += 1
        if s.guia1_event:
            guia1_flags += 1
    return {
        "scored_count": len(scores),
        "distribution": distribution,
        "needing_action": needing_action,
        "guia1_flags": guia1_flags,
    }


def employee_valuation(user, company) -> dict | None:
    score = (
        _scores_for_company(company)
        .filter(submission__user=user)
        .prefetch_related("groups")
        .order_by("-computed_at")
        .first()
    )
    if score is None:
        return None
    categories = [
        {
            "key": g.key,
            "ndr": g.ndr,
            "ndr_label": NDR(g.ndr).label,
            "action": cfg.action_text(g.ndr),
        }
        for g in score.groups.all()
        if g.level == GroupLevel.CATEGORIA
    ]
    return {
        "final_ndr": score.final_ndr,
        "final_ndr_label": NDR(score.final_ndr).label,
        "final_score": score.final_score,
        "final_action": cfg.action_text(score.final_ndr),
        "categories": categories,
        "guia1_event": score.guia1_event,
        "guia1_severity": score.guia1_severity,
    }
```

- [x] **Step 4: Run test to verify it passes**

Run: `pytest apps/nom035/tests/test_aggregates.py -v`
Expected: PASS.

- [x] **Step 5: Commit**

```bash
ruff format . && ruff check .
git add apps/nom035/aggregates.py apps/nom035/tests/test_aggregates.py
git commit -m "feat: add NOM-035 company and employee aggregation helpers

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

## 10. Employee-detail panel

### Task 10: Render "Valoración de resultados" on the employee page

**Files:**
- Modify: `apps/core/views.py` (`EmployeeDetailView.get`, context dict ~line 285-294)
- Modify: `templates/core/employee_detail.html:55-64`
- Create: `apps/core/tests/test_employee_valuation_panel.py`

**Interfaces:**
- Consumes: `aggregates.employee_valuation` (Task 9).
- Produces: context key `valuation` on the employee-detail page (only when `can_view_insights`).

- [x] **Step 1: Write the failing test**

```python
# apps/core/tests/test_employee_valuation_panel.py
import pytest
from django.urls import reverse

from apps.nom035 import constants as c
from apps.nom035.models import SubmissionScore
from apps.responses.models import SurveySubmission
from apps.surveys.models import SurveyAssignment

pytestmark = pytest.mark.django_db


def test_panel_shows_ndr_for_insights_user(
    client, bootstrap_groups, make_user_with_profile, make_company, survey
):
    company = make_company()
    admin = make_user_with_profile(email="admin@x.mx", company=company)
    admin.groups.add(bootstrap_groups["Admins"])
    employee = make_user_with_profile(email="emp@x.mx", company=company)
    assignment = SurveyAssignment.objects.create(
        company=company, survey=survey,
        variant=SurveyAssignment.Variant.LARGE,
        status=SurveyAssignment.Status.ACTIVE,
    )
    sub = SurveySubmission.objects.create(
        assignment=assignment, user=employee, status=SurveySubmission.Status.COMPLETED
    )
    SubmissionScore.objects.create(submission=sub, final_score=160, final_ndr=c.NDR_MUY_ALTO)

    client.force_login(admin)
    resp = client.get(reverse("core:employee_detail", args=[employee.id]))
    assert resp.status_code == 200
    assert b"Valoraci\xc3\xb3n de resultados" in resp.content
    assert b"Muy alto" in resp.content
```

> Confirm the exact reverse name/args for `employee_detail` in `apps/core/urls.py` before running; adjust the `reverse(...)` call if the URL takes `employee_id` under a different kwarg.

- [x] **Step 2: Run test to verify it fails**

Run: `pytest apps/core/tests/test_employee_valuation_panel.py -v`
Expected: FAIL — content still shows the "Próximamente" placeholder.

- [x] **Step 3: Add the context in the view**

In `EmployeeDetailView.get`, before building the response context, compute:

```python
        from apps.nom035.aggregates import employee_valuation

        valuation = None
        if request.user.has_perm("accounts.can_view_insights"):
            valuation = employee_valuation(employee_user, company)
```

Add `"valuation": valuation,` to the context dict passed to `render(...)`.

- [x] **Step 4: Replace the template placeholder**

```django
{# templates/core/employee_detail.html — replace lines 55-64 #}
{% if perms.accounts.can_view_insights %}
<section class="mb-8">
  <h2 class="text-base font-semibold text-gray-900 mb-4">Valoración de resultados</h2>
  <div class="rounded-2xl border border-gray-200 bg-white px-6 py-5">
    {% if valuation %}
      <p class="text-sm text-gray-900">
        Nivel de riesgo final:
        <span class="font-semibold">{{ valuation.final_ndr_label }}</span>
        ({{ valuation.final_score }})
      </p>
      <p class="mt-1 text-sm text-gray-600">{{ valuation.final_action }}</p>
      {% if valuation.categories %}
        <ul class="mt-4 space-y-1">
          {% for cat in valuation.categories %}
            <li class="text-sm text-gray-700">{{ cat.key }}: <span class="font-medium">{{ cat.ndr_label }}</span></li>
          {% endfor %}
        </ul>
      {% endif %}
      {% if valuation.guia1_event %}
        <p class="mt-4 text-sm font-medium text-amber-700">
          Guía I: posible necesidad de canalización (severidad {{ valuation.guia1_severity }}).
        </p>
      {% endif %}
    {% else %}
      <p class="text-sm text-gray-500">Sin resultados: la encuesta no ha sido completada.</p>
    {% endif %}
  </div>
</section>
{% endif %}
```

- [x] **Step 5: Run test to verify it passes**

Run: `pytest apps/core/tests/test_employee_valuation_panel.py -v`
Expected: PASS.

- [x] **Step 6: Commit**

```bash
ruff format . && ruff check .
git add apps/core/views.py templates/core/employee_detail.html apps/core/tests/test_employee_valuation_panel.py
git commit -m "feat: show NOM-035 valuation on the employee detail page

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

## 11. Company-dashboard panel

### Task 11: Render "Valoración de resultados" on the company dashboard

**Files:**
- Modify: `apps/core/views.py` (`CompanyDashboardView.get`, context dict ~line 187-198)
- Modify: `templates/core/company_dashboard.html:190-198`
- Create: `apps/core/tests/test_company_valuation_panel.py`

**Interfaces:**
- Consumes: `aggregates.company_valuation` (Task 9).
- Produces: context key `company_valuation` on the company dashboard (only when `can_view_insights`).

- [x] **Step 1: Write the failing test**

```python
# apps/core/tests/test_company_valuation_panel.py
import pytest
from django.urls import reverse

from apps.nom035 import constants as c
from apps.nom035.models import SubmissionScore
from apps.responses.models import SurveySubmission
from apps.surveys.models import SurveyAssignment

pytestmark = pytest.mark.django_db


def test_dashboard_shows_distribution(
    client, bootstrap_groups, make_user_with_profile, make_company, survey
):
    company = make_company()
    admin = make_user_with_profile(email="a@x.mx", company=company)
    admin.groups.add(bootstrap_groups["Admins"])
    assignment = SurveyAssignment.objects.create(
        company=company, survey=survey,
        variant=SurveyAssignment.Variant.LARGE,
        status=SurveyAssignment.Status.ACTIVE,
    )
    sub = SurveySubmission.objects.create(
        assignment=assignment, status=SurveySubmission.Status.COMPLETED
    )
    SubmissionScore.objects.create(submission=sub, final_score=160, final_ndr=c.NDR_MUY_ALTO)

    client.force_login(admin)
    resp = client.get(reverse("core:company_dashboard_detail", args=[company.reference_code]))
    assert resp.status_code == 200
    assert b"Valoraci\xc3\xb3n de resultados" in resp.content
```

> Confirm the dashboard URL name in `apps/core/urls.py` (the admin-view-by-`reference_code` route) and adjust `reverse(...)` accordingly.

- [x] **Step 2: Run test to verify it fails**

Run: `pytest apps/core/tests/test_company_valuation_panel.py -v`
Expected: FAIL — content still shows "Insights coming soon."

- [x] **Step 3: Add the context in the view**

In `CompanyDashboardView.get`, before `render(...)`:

```python
        from apps.nom035.aggregates import company_valuation as company_valuation_data

        valuation = None
        if request.user.has_perm("accounts.can_view_insights"):
            valuation = company_valuation_data(company)
```

Add `"company_valuation": valuation,` to the context dict.

- [x] **Step 4: Replace the template placeholder**

```django
{# templates/core/company_dashboard.html — replace the Insights panel, lines 190-198 #}
{% if perms.accounts.can_view_insights %}
  <section class="mt-8">
    <h2 class="text-base font-semibold text-gray-900 mb-4">Valoración de resultados</h2>
    <div class="rounded-2xl border border-gray-200 bg-white px-6 py-5">
      {% if company_valuation and company_valuation.scored_count %}
        <p class="text-sm text-gray-700">
          Cuestionarios valorados: <span class="font-semibold">{{ company_valuation.scored_count }}</span>
        </p>
        <p class="mt-1 text-sm text-gray-700">
          Colaboradores que requieren acción (Alto/Muy alto):
          <span class="font-semibold">{{ company_valuation.needing_action }}</span>
        </p>
        <p class="mt-1 text-sm text-gray-700">
          Señales de canalización (Guía I):
          <span class="font-semibold">{{ company_valuation.guia1_flags }}</span>
        </p>
        <ul class="mt-4 space-y-1">
          {% for level, count in company_valuation.distribution.items %}
            <li class="text-sm text-gray-600">{{ level }}: {{ count }}</li>
          {% endfor %}
        </ul>
      {% else %}
        <p class="text-sm text-gray-500">Aún no hay cuestionarios completados para valorar.</p>
      {% endif %}
    </div>
  </section>
{% endif %}
```

- [x] **Step 5: Run test to verify it passes**

Run: `pytest apps/core/tests/test_company_valuation_panel.py -v`
Expected: PASS.

- [x] **Step 6: Run the full suite**

Run: `pytest`
Expected: PASS across all apps.

- [x] **Step 7: Commit**

```bash
ruff format . && ruff check .
git add apps/core/views.py templates/core/company_dashboard.html apps/core/tests/test_company_valuation_panel.py
git commit -m "feat: show NOM-035 valuation on the company dashboard

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

## Task dependency summary

- **Task 1** (app) → prerequisite for all.
- **Task 2** (primitives) → used by 3, 5.
- **Task 3** (models) → used by 6, 9.
- **Task 4** (config) → used by 5, 9. **Highest risk; blocks meaningful 5/9 output.**
- **Task 5** (score_submission) → needs 2 + 4; used by 6.
- **Task 6** (materialize) → needs 3 + 5; used by 7, 8.
- **Task 7** (signal) → needs 6.
- **Task 8** (command) → needs 6.
- **Task 9** (aggregates) → needs 3 + 4; used by 10, 11.
- **Task 10** (employee panel) → needs 9.
- **Task 11** (company panel) → needs 9.

Linear order 1→11 satisfies every dependency. Tasks 7 and 8 are independent of each other; 10 and 11 are independent of each other.

## Risk / decision register

- **Task 4 — reference data (HIGH):** taxonomy, inverted items, and thresholds are transcribed from the Guías de Referencia with MVP assumptions; structural tests guard completeness, not official correctness. Validate against a worked example from `Ejemplo Reporte Resultados.pdf` and the domain expert; track every assumption in `docs/platform/nom-035-valoracion-supuestos.md`.
- **Task 5 — skipped-blocks bias (MEDIUM, decided):** absent conditional-block items lower the sum against fixed thresholds. Accepted for the MVP; flagged for expert review.
- **Task 1 — rename fallout (LOW):** ensure no lingering `analytics` import/reference remains (`grep -rn "analytics" apps config .claude`).
- **Task 7 — signal wiring (LOW):** receiver connected only in `ready()`; guarded on `status == completed`; never re-saves the submission.
