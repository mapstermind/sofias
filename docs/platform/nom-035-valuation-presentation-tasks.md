# NOM-035 Valuation Presentation Shift — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Move NOM-035 "necesidad de acción" language off individual employees and onto areas/company, enrich the employee breakdown to Categoría→Dominio→Dimensión with scores, and give both valuation panels a clearer visual design.

**Architecture:** Add a free-text `department` to `UserProfile` (CSV + admin populated). Extend the `apps/nom035` scoring config with a dimensión→items taxonomy so dimensión scores materialize as `GroupScore` rows (score only, no NDR). Reword the action text to be organization-framed and surface it only in the aggregate reads; drop it from the per-employee read. `company_valuation` gains a per-area breakdown keyed to the most-severe NDR present; `employee_valuation` returns a nested cat→dom→dim tree with scores. Templates get a centralized NDR color helper, a nested employee hierarchy, and per-area distribution bars. The scoring math is untouched.

**Tech Stack:** Django 6.0, PostgreSQL 17, pytest + pytest-django, TailwindCSS (compiled to `static/css/output.css`).

## Global Constraints

- **Source of truth:** all NOM-035 scoring data (taxonomy, thresholds, action text) is transcribed from `docs/internal/roadmap_context/Guias de Referencia.md`. Do not invent values; if another doc conflicts, that file wins.
- **Language:** user-facing copy and URLs in Spanish; code, comments, identifiers in English.
- **Scoring math is frozen:** no changes to thresholds, inverted-item sets, or the final/categoría/dominio classification. Dimensión is **score-only** (no NDR — the standard publishes no dimensión threshold table).
- **Tailwind:** a template class not already present in some template compiles to nothing. After any task that edits `templates/` or `static/`, run `npm run build:css` and commit the regenerated `static/css/output.css`.
- **Insights gating:** both valuation panels stay gated on `accounts.can_view_insights`; employees never see scored results.
- **Tests:** `pytest` uses `config.settings` with `--reuse-db -x`. Run from the repo root with the venv active (`source .venv/bin/activate`).
- **Commits:** end every commit message body with `Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>`.

---

### Task 1: Add `UserProfile.department` field

**Files:**
- Modify: `apps/accounts/models.py:45-58` (`UserProfile`)
- Modify: `apps/accounts/admin.py` (expose `department` in the profile admin)
- Create: `apps/accounts/migrations/00XX_userprofile_department.py` (generated)
- Test: `apps/accounts/tests/test_models.py` (add a test; create the file/section if the assertion location differs)

**Interfaces:**
- Produces: `UserProfile.department` — `CharField(max_length=255, blank=True, default="")`.

- [ ] **Step 1: Write the failing test**

Add to `apps/accounts/tests/test_models.py`:

```python
import pytest

from apps.accounts.models import UserProfile


@pytest.mark.django_db
def test_userprofile_department_defaults_blank_and_stores(make_user):
    user = make_user(email="dept@x.mx")
    profile = UserProfile.objects.create(user=user)
    assert profile.department == ""
    profile.department = "Sistemas"
    profile.save()
    profile.refresh_from_db()
    assert profile.department == "Sistemas"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest apps/accounts/tests/test_models.py::test_userprofile_department_defaults_blank_and_stores -v`
Expected: FAIL — `AttributeError`/`TypeError` (no `department` field).

- [ ] **Step 3: Add the field**

In `apps/accounts/models.py`, inside `UserProfile` (after `position`):

```python
    position = models.CharField(max_length=255, blank=True)
    department = models.CharField(max_length=255, blank=True, default="")
```

- [ ] **Step 4: Generate the migration**

Run: `python manage.py makemigrations accounts`
Expected: a new migration adding `department` to `userprofile`.

- [ ] **Step 5: Expose it in admin**

In `apps/accounts/admin.py`, add `department` alongside `position` wherever the `UserProfile` fields are listed (`list_display`, `fields`, or the inline — match the existing structure). If `UserProfile` is edited as an inline on the `User` admin, add `"department"` to that inline's `fields`/`fieldsets`.

- [ ] **Step 6: Run tests**

Run: `pytest apps/accounts/tests/test_models.py -v`
Expected: PASS.

- [ ] **Step 7: Commit**

```bash
git add apps/accounts/models.py apps/accounts/admin.py apps/accounts/migrations/ apps/accounts/tests/test_models.py
git commit -m "Add free-text department field to UserProfile"
```

---

### Task 2: Accept optional `department` column in the CSV importer

**Files:**
- Modify: `apps/accounts/importers.py:15` (`OPTIONAL_HEADERS`), `:140-145` (profile creation)
- Test: `apps/accounts/tests/test_importers.py`

**Interfaces:**
- Consumes: `UserProfile.department` (Task 1).
- Produces: importer writes `row["department"]` (or `""`) to the created profile; `department` is **not** added to `REQUIRED_HEADERS`, so CSVs without the column still import.

- [ ] **Step 1: Write the failing tests**

Add to `apps/accounts/tests/test_importers.py` (match the file's existing imports/fixtures; it already exercises `import_users_from_csv` with a company + group present):

```python
def test_import_sets_department_when_column_present(bootstrap_groups, make_company):
    from apps.accounts.importers import import_users_from_csv
    from apps.accounts.models import UserProfile

    company = make_company()
    csv_text = (
        "email,company_reference_code,group,auth_method,department\n"
        f"dep1@x.mx,{company.reference_code},Employees,otp,Sistemas\n"
    )
    result = import_users_from_csv(csv_text)
    assert result.created_count == 1
    profile = UserProfile.objects.get(user__email="dep1@x.mx")
    assert profile.department == "Sistemas"


def test_import_leaves_department_blank_when_column_absent(bootstrap_groups, make_company):
    from apps.accounts.importers import import_users_from_csv
    from apps.accounts.models import UserProfile

    company = make_company()
    csv_text = (
        "email,company_reference_code,group,auth_method\n"
        f"dep2@x.mx,{company.reference_code},Employees,otp\n"
    )
    result = import_users_from_csv(csv_text)
    assert result.created_count == 1
    assert UserProfile.objects.get(user__email="dep2@x.mx").department == ""
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest apps/accounts/tests/test_importers.py -k department -v`
Expected: FAIL — the first test finds `department == ""` (not written).

- [ ] **Step 3: Register the optional header**

In `apps/accounts/importers.py`:

```python
OPTIONAL_HEADERS = {"first_name", "last_name", "position", "department"}
```

- [ ] **Step 4: Write department onto the profile**

In `_import_row`, update the `UserProfile.objects.create(...)` call:

```python
        UserProfile.objects.create(
            user=user,
            position=row.get("position", ""),
            department=row.get("department", ""),
            company=company,
            is_activated=False,
        )
```

(`_normalize_row` already strips every column, so no extra normalization is needed.)

- [ ] **Step 5: Run tests**

Run: `pytest apps/accounts/tests/test_importers.py -v`
Expected: PASS (both new tests and all existing importer tests).

- [ ] **Step 6: Commit**

```bash
git add apps/accounts/importers.py apps/accounts/tests/test_importers.py
git commit -m "Accept optional department column in user CSV import"
```

---

### Task 3: Dimensión taxonomy, constants, labels, and model level (config only)

**Files:**
- Modify: `apps/nom035/constants.py` (add `LEVEL_DIMENSION`)
- Modify: `apps/nom035/models.py:14-18` (`GroupLevel.DIMENSION`)
- Modify: `apps/nom035/_nom035_scoring.py` (dimensión maps, extend `_build_taxonomy`, labels, accessors)
- Create: `apps/nom035/migrations/00XX_groupscore_level_dimension.py` (generated, state-only)
- Modify: `apps/nom035/tests/test_config.py:129-133` (fix 2-tuple unpack), add reconciliation test

**Interfaces:**
- Produces:
  - `constants.LEVEL_DIMENSION = "dimension"`.
  - `GroupLevel.DIMENSION`.
  - `taxonomy_for_variant(variant) -> dict[str, tuple[str, str, str]]` — now `{code: (categoria, dominio, dimension)}` (3-tuple).
  - `group_label(key)` — now also resolves dimensión keys.
  - `categoria_of(dominio) -> str`, `dominios_for_categoria(categoria) -> list[str]`, `dimensions_for_dominio(dominio, variant) -> list[str]`, `CATEGORIA_ORDER: list[str]`.

- [ ] **Step 1: Add the dimensión constant and model level**

In `apps/nom035/constants.py` (after `LEVEL_DOMINIO`):

```python
LEVEL_CATEGORIA = "categoria"
LEVEL_DOMINIO = "dominio"
LEVEL_DIMENSION = "dimension"
```

In `apps/nom035/models.py`, inside `GroupLevel`:

```python
class GroupLevel(models.TextChoices):
    # NOM-035 defines NDR thresholds only at dominio/categoría/final. Dimensión is
    # stored score-only (no NDR) so the per-employee panel can show it.
    CATEGORIA = c.LEVEL_CATEGORIA, "Categoría"
    DOMINIO = c.LEVEL_DOMINIO, "Dominio"
    DIMENSION = c.LEVEL_DIMENSION, "Dimensión"
```

- [ ] **Step 2: Write the failing config tests**

In `apps/nom035/tests/test_config.py`, first **fix** the existing 2-tuple unpack so the suite still imports:

```python
def test_group_label_covers_every_categoria_and_dominio():
    for variant in ("small", "large"):
        for categoria, dominio, dimension in cfg.taxonomy_for_variant(variant).values():
            assert cfg.group_label(categoria)
            assert cfg.group_label(dominio)
            assert cfg.group_label(dimension)
    # Labels are the official accented Spanish names, not slug prettifications.
```

Then add:

```python
from apps.nom035._nom035_scoring import (
    _LARGE_DIMENSION_ITEMS,
    _LARGE_DOMINIO_ITEMS,
    _SMALL_DIMENSION_ITEMS,
    _SMALL_DOMINIO_ITEMS,
)


def _dimension_numbers(dim_map):
    """{dominio: set(all item numbers across its dimensiones)}."""
    return {
        dominio: {n for _key, _label, nums in dims for n in nums}
        for dominio, dims in dim_map.items()
    }


@pytest.mark.parametrize(
    "dominio_map, dimension_map",
    [(_LARGE_DOMINIO_ITEMS, _LARGE_DIMENSION_ITEMS),
     (_SMALL_DOMINIO_ITEMS, _SMALL_DIMENSION_ITEMS)],
)
def test_dimension_items_reconcile_with_dominio_items(dominio_map, dimension_map):
    dim_numbers = _dimension_numbers(dimension_map)
    assert set(dim_numbers) == set(dominio_map)
    for dominio, numbers in dominio_map.items():
        assert dim_numbers[dominio] == set(numbers), dominio


def test_taxonomy_values_are_three_tuples():
    for variant in ("small", "large"):
        for value in cfg.taxonomy_for_variant(variant).values():
            assert len(value) == 3
```

(`pytest` is already imported at the top of `test_config.py`.)

- [ ] **Step 3: Run tests to verify they fail**

Run: `pytest apps/nom035/tests/test_config.py -v`
Expected: FAIL — `_LARGE_DIMENSION_ITEMS` does not exist / taxonomy values are 2-tuples.

- [ ] **Step 4: Add the dimensión data maps**

In `apps/nom035/_nom035_scoring.py`, after `_SMALL_DOMINIO_ITEMS` (line ~108), add. Values are `(dim_key, label, [item numbers])`, transcribed from `Guias de Referencia.md` (Guía III lines ~454–480; Guía II lines ~183–204). Dim keys are shared across variants where the concept matches:

```python
# ── Dimensión → items (finer partition of each dominio; score-only, no NDR) ──
# (dim_key, official label, item numbers). Transcribed from Guias de Referencia.md
# "Grupos de ítems por dimensión, dominio y categoría".
_LARGE_DIMENSION_ITEMS = {
    DOM_CONDICIONES: [
        ("cond_peligrosas_inseguras", "Condiciones peligrosas e inseguras", [1, 3]),
        ("cond_deficientes_insalubres", "Condiciones deficientes e insalubres", [2, 4]),
        ("trabajos_peligrosos", "Trabajos peligrosos", [5]),
    ],
    DOM_CARGA: [
        ("cargas_cuantitativas", "Cargas cuantitativas", [6, 12]),
        ("ritmos_acelerados", "Ritmos de trabajo acelerado", [7, 8]),
        ("carga_mental", "Carga mental", [9, 10, 11]),
        ("cargas_psicologicas_emocionales", "Cargas psicológicas emocionales", [65, 66, 67, 68]),
        ("cargas_alta_responsabilidad", "Cargas de alta responsabilidad", [13, 14]),
        ("cargas_contradictorias", "Cargas contradictorias o inconsistentes", [15, 16]),
    ],
    DOM_CONTROL: [
        ("falta_control_autonomia", "Falta de control y autonomía sobre el trabajo", [25, 26, 27, 28]),
        ("limitada_posibilidad_desarrollo", "Limitada o nula posibilidad de desarrollo", [23, 24]),
        ("insuficiente_participacion_cambio", "Insuficiente participación y manejo del cambio", [29, 30]),
        ("limitada_capacitacion", "Limitada o inexistente capacitación", [35, 36]),
    ],
    DOM_JORNADA: [
        ("jornadas_extensas", "Jornadas de trabajo extensas", [17, 18]),
    ],
    DOM_INTERFERENCIA: [
        ("influencia_trabajo_fuera", "Influencia del trabajo fuera del centro laboral", [19, 20]),
        ("influencia_responsabilidades_familiares", "Influencia de las responsabilidades familiares", [21, 22]),
    ],
    DOM_LIDERAZGO: [
        ("escasa_claridad_funciones", "Escasa claridad de funciones", [31, 32, 33, 34]),
        ("caracteristicas_liderazgo", "Características del liderazgo", [37, 38, 39, 40, 41]),
    ],
    DOM_RELACIONES: [
        ("relaciones_sociales", "Relaciones sociales en el trabajo", [42, 43, 44, 45, 46]),
        ("deficiente_relacion_supervisados", "Deficiente relación con los colaboradores que supervisa", [69, 70, 71, 72]),
    ],
    DOM_VIOLENCIA: [
        ("violencia_laboral", "Violencia laboral", [57, 58, 59, 60, 61, 62, 63, 64]),
    ],
    DOM_RECONOCIMIENTO: [
        ("escasa_retroalimentacion", "Escasa o nula retroalimentación del desempeño", [47, 48]),
        ("escaso_reconocimiento_compensacion", "Escaso o nulo reconocimiento y compensación", [49, 50, 51, 52]),
    ],
    DOM_PERTENENCIA: [
        ("limitado_sentido_pertenencia", "Limitado sentido de pertenencia", [55, 56]),
        ("inestabilidad_laboral", "Inestabilidad laboral", [53, 54]),
    ],
}

_SMALL_DIMENSION_ITEMS = {
    DOM_CONDICIONES: [
        ("cond_peligrosas_inseguras", "Condiciones peligrosas e inseguras", [2]),
        ("cond_deficientes_insalubres", "Condiciones deficientes e insalubres", [1]),
        ("trabajos_peligrosos", "Trabajos peligrosos", [3]),
    ],
    DOM_CARGA: [
        ("cargas_cuantitativas", "Cargas cuantitativas", [4, 9]),
        ("ritmos_acelerados", "Ritmos de trabajo acelerado", [5, 6]),
        ("carga_mental", "Carga mental", [7, 8]),
        ("cargas_psicologicas_emocionales", "Cargas psicológicas emocionales", [41, 42, 43]),
        ("cargas_alta_responsabilidad", "Cargas de alta responsabilidad", [10, 11]),
        ("cargas_contradictorias", "Cargas contradictorias o inconsistentes", [12, 13]),
    ],
    DOM_CONTROL: [
        ("falta_control_autonomia", "Falta de control y autonomía sobre el trabajo", [20, 21, 22]),
        ("limitada_posibilidad_desarrollo", "Limitada o nula posibilidad de desarrollo", [18, 19]),
        ("limitada_capacitacion", "Limitada o inexistente capacitación", [26, 27]),
    ],
    DOM_JORNADA: [
        ("jornadas_extensas", "Jornadas de trabajo extensas", [14, 15]),
    ],
    DOM_INTERFERENCIA: [
        ("influencia_trabajo_fuera", "Influencia del trabajo fuera del centro laboral", [16]),
        ("influencia_responsabilidades_familiares", "Influencia de las responsabilidades familiares", [17]),
    ],
    DOM_LIDERAZGO: [
        ("escasa_claridad_funciones", "Escasa claridad de funciones", [23, 24, 25]),
        ("caracteristicas_liderazgo", "Características del liderazgo", [28, 29]),
    ],
    DOM_RELACIONES: [
        ("relaciones_sociales", "Relaciones sociales en el trabajo", [30, 31, 32]),
        ("deficiente_relacion_supervisados", "Deficiente relación con los colaboradores que supervisa", [44, 45, 46]),
    ],
    DOM_VIOLENCIA: [
        ("violencia_laboral", "Violencia laboral", [33, 34, 35, 36, 37, 38, 39, 40]),
    ],
}
```

- [ ] **Step 5: Extend `_build_taxonomy` to emit 3-tuples and build dimensión lookups**

Replace `_build_taxonomy` and the taxonomy build lines (~111–122) with:

```python
def _build_taxonomy(prefix, dominio_items, dimension_items):
    """{code: (categoria, dominio, dimension)} from a dominio → item-numbers map
    and a dominio → [(dim_key, label, item numbers)] map."""
    dim_of_number = {}
    for dims in dimension_items.values():
        for dim_key, _label, numbers in dims:
            for n in numbers:
                dim_of_number[n] = dim_key
    taxonomy = {}
    for dominio, numbers in dominio_items.items():
        categoria = _DOMINIO_CATEGORIA[dominio]
        for n in numbers:
            taxonomy[f"{prefix}-{n}"] = (categoria, dominio, dim_of_number[n])
    return taxonomy


_TAXONOMY_LARGE = _build_taxonomy("g3", _LARGE_DOMINIO_ITEMS, _LARGE_DIMENSION_ITEMS)
_TAXONOMY_SMALL = _build_taxonomy("g2", _SMALL_DOMINIO_ITEMS, _SMALL_DIMENSION_ITEMS)

# Dimensión display labels + dimensión → dominio parent (variant-independent: a
# dimensión concept belongs to exactly one dominio).
_DIMENSION_LABELS = {}
_DIMENSION_DOMINIO = {}
for _dim_map in (_LARGE_DIMENSION_ITEMS, _SMALL_DIMENSION_ITEMS):
    for _dominio, _dims in _dim_map.items():
        for _dim_key, _label, _numbers in _dims:
            _DIMENSION_LABELS[_dim_key] = _label
            _DIMENSION_DOMINIO[_dim_key] = _dominio

CATEGORIA_ORDER = [CAT_AMBIENTE, CAT_FACTORES, CAT_TIEMPO, CAT_LIDERAZGO, CAT_ENTORNO]
```

- [ ] **Step 6: Update `group_label` and add ordering accessors**

Replace `group_label` (bottom of file) and add accessors:

```python
def group_label(key: str) -> str:
    """Human-readable Spanish name for a categoría, dominio, or dimensión key."""
    return (
        _GROUP_LABELS.get(key)
        or _DIMENSION_LABELS.get(key)
        or key.replace("_", " ").capitalize()
    )


def categoria_of(dominio: str) -> str:
    return _DOMINIO_CATEGORIA[dominio]


def dominios_for_categoria(categoria: str) -> list[str]:
    return [d for d, cat in _DOMINIO_CATEGORIA.items() if cat == categoria]


def dimensions_for_dominio(dominio: str, variant: str) -> list[str]:
    dim_map = _LARGE_DIMENSION_ITEMS if variant == "large" else _SMALL_DIMENSION_ITEMS
    return [dim_key for dim_key, _label, _numbers in dim_map.get(dominio, [])]
```

- [ ] **Step 7: Generate the state-only migration**

Run: `python manage.py makemigrations nom035`
Expected: an `AlterField` migration on `groupscore.level` (choices change; no DB column change).

- [ ] **Step 8: Run tests**

Run: `pytest apps/nom035/tests/test_config.py -v`
Expected: PASS (reconciliation, 3-tuple, label coverage).

- [ ] **Step 9: Commit**

```bash
git add apps/nom035/constants.py apps/nom035/models.py apps/nom035/_nom035_scoring.py apps/nom035/migrations/ apps/nom035/tests/test_config.py
git commit -m "Add NOM-035 dimensión taxonomy, labels, and GroupScore dimension level"
```

---

### Task 4: Materialize dimensión scores in `score_submission`

**Files:**
- Modify: `apps/nom035/scoring.py:48-95` (`score_submission`)
- Test: `apps/nom035/tests/test_scoring.py` (add cases; if the file name differs, use the existing scoring-unit test module)

**Interfaces:**
- Consumes: `taxonomy_for_variant` 3-tuples, `constants.LEVEL_DIMENSION` (Task 3).
- Produces: `score_submission` emits `GroupResult(level="dimension", key=<dim_key>, score=<sum>, ndr="")` per dimensión that had ≥1 answered item, alongside the existing categoría/dominio/final results. `services.materialize` stores them unchanged (it already iterates `result.groups` generically).

- [ ] **Step 1: Write the failing test**

Add to the nom035 scoring-unit test module (the one that builds a submission with answers and calls `score_submission`; follow its existing fixture/helper for creating answered items). If no such helper exists, add this self-contained test to `apps/nom035/tests/test_scoring.py`:

```python
import pytest

from apps.nom035 import constants as c
from apps.nom035.scoring import score_submission
from apps.responses.models import Answer, SurveySubmission
from apps.surveys.models import Module, Question, Survey, SurveyAssignment


@pytest.mark.django_db
def test_score_submission_emits_dimension_groups(make_company, make_user):
    survey = Survey.objects.create(key="nom035", title="NOM-035",
                                   status=Survey.Status.PUBLISHED)
    module = Module.objects.create(survey=survey, key="g3", title="G3",
                                   applies_to=Module.AppliesTo.ALL, order=0)
    # Two items of the "Trabajos peligrosos" dimensión is a single item (g3-5);
    # answer g3-5 = 5 (Nunca) → inverted? g3-5 is inverted → score 5-5 = 0.
    # Use g3-1 (not inverted) and g3-3 (inverted) = dimensión cond_peligrosas.
    for code in ("g3-1", "g3-3"):
        Question.objects.create(module=module, code=code, question_type="likert",
                                text=code, order=int(code.split("-")[1]))
    company = make_company()
    user = make_user(email="dim@x.mx")
    assignment = SurveyAssignment.objects.create(
        company=company, survey=survey, variant=SurveyAssignment.Variant.LARGE,
        status=SurveyAssignment.Status.ACTIVE)
    sub = SurveySubmission.objects.create(
        assignment=assignment, user=user, status=SurveySubmission.Status.IN_PROGRESS)
    # g3-1 normal: value 3 → score 2 ; g3-3 inverted: value 3 → score 2
    Answer.objects.create(submission=sub, question=Question.objects.get(code="g3-1"), value=3)
    Answer.objects.create(submission=sub, question=Question.objects.get(code="g3-3"), value=3)

    result = score_submission(sub)
    dims = {g.key: g for g in result.groups if g.level == c.LEVEL_DIMENSION}
    assert "cond_peligrosas_inseguras" in dims
    assert dims["cond_peligrosas_inseguras"].score == 4  # 2 + 2
    assert dims["cond_peligrosas_inseguras"].ndr == ""   # no NDR at dimensión level
```

> If the repo already has a submission-with-answers helper/fixture, prefer it and keep only the last three assertions. Verify `Answer`'s field names (`submission`, `question`, `value`) against `apps/responses/models.py` before running.

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest apps/nom035/tests/test_scoring.py::test_score_submission_emits_dimension_groups -v`
Expected: FAIL — no dimensión groups in `result.groups`.

- [ ] **Step 3: Accumulate and emit dimensión sums**

In `apps/nom035/scoring.py`, edit `score_submission`. Update the unpack and add a `dim_scores` accumulator:

```python
    taxonomy = cfg.taxonomy_for_variant(variant)
    cat_scores: dict[str, int] = {}
    dom_scores: dict[str, int] = {}
    dim_scores: dict[str, int] = {}
    final = 0
    for code, (cat_key, dom_key, dim_key) in taxonomy.items():
        value = answers.get(code)
        if value is None:
            continue  # unanswered or hidden block — excluded (see supuestos §2.4)
        item = likert_item_score(int(value), inverted=cfg.is_inverted(code))
        final += item
        cat_scores[cat_key] = cat_scores.get(cat_key, 0) + item
        dom_scores[dom_key] = dom_scores.get(dom_key, 0) + item
        dim_scores[dim_key] = dim_scores.get(dim_key, 0) + item

    groups = []
    for level, sums in (
        (c.LEVEL_DOMINIO, dom_scores),
        (c.LEVEL_CATEGORIA, cat_scores),
    ):
        for key, score in sums.items():
            ndr = classify(cfg.thresholds_for(level, key, variant), score)
            groups.append(GroupResult(level=level, key=key, score=score, ndr=ndr))
    # Dimensión: score-only, no NDR (the standard defines no dimensión threshold).
    for key, score in dim_scores.items():
        groups.append(GroupResult(level=c.LEVEL_DIMENSION, key=key, score=score, ndr=""))
```

- [ ] **Step 4: Run tests**

Run: `pytest apps/nom035/tests/test_scoring.py -v && pytest apps/nom035/tests/ -v`
Expected: PASS — new test passes; existing scoring/materialize/aggregate tests still green (materialize stores the extra rows unchanged).

- [ ] **Step 5: Commit**

```bash
git add apps/nom035/scoring.py apps/nom035/tests/test_scoring.py
git commit -m "Materialize per-dimensión scores (score-only, no NDR)"
```

---

### Task 5: Reword action text to organization/area framing

**Files:**
- Modify: `apps/nom035/_nom035_scoring.py:225-248` (`_ACTION_TEXT`)
- Test: `apps/nom035/tests/test_config.py`

**Interfaces:**
- Produces: `action_text(ndr)` returns área/organización-framed strings for every NDR level; no individual/clinical phrasing.

- [ ] **Step 1: Write the failing test**

In `apps/nom035/tests/test_config.py`, replace `test_action_text_exists_for_every_level` with:

```python
def test_action_text_is_org_framed_for_every_level():
    for level in c.NDR_ORDER:
        text = cfg.action_text(level)
        assert text
    # The Muy alto guidance must not carry individual-clinical phrasing.
    assert "clínica" not in cfg.action_text(c.NDR_MUY_ALTO).lower()
    assert "colaboradores que" not in cfg.action_text(c.NDR_MUY_ALTO).lower()
    # It speaks about the área / centro de trabajo.
    assert "área" in cfg.action_text(c.NDR_MUY_ALTO).lower()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest apps/nom035/tests/test_config.py::test_action_text_is_org_framed_for_every_level -v`
Expected: FAIL — current Muy alto text contains "atención clínica de los colaboradores".

- [ ] **Step 3: Reword `_ACTION_TEXT`**

Replace `_ACTION_TEXT` in `apps/nom035/_nom035_scoring.py`. Faithful to the official *Criterios para la toma de acciones* (Guías de Referencia), generalized to the área/centro de trabajo and stripped of individual-clinical wording:

```python
# ── "Necesidad de acción" per NDR level, framed for the ÁREA / organización ──
# The NOM-035 action criteria are organizational (Programa de intervención, política
# de prevención, centro de trabajo); they are surfaced only in aggregate reads, never
# as a per-person verdict. See docs/platform/nom-035-valuation-presentation.md.
_ACTION_TEXT = {
    c.NDR_NULO: (
        "El nivel de riesgo del área resulta despreciable, por lo que no se "
        "requieren medidas adicionales."
    ),
    c.NDR_BAJO: (
        "Es necesaria una mayor difusión, en el área, de la política de prevención "
        "de riesgos psicosociales y de los programas para la prevención de los "
        "factores de riesgo psicosocial."
    ),
    c.NDR_MEDIO: (
        "Se requiere revisar la política de prevención de riesgos psicosociales y "
        "reforzar su aplicación y difusión en el área, mediante un Programa de "
        "intervención."
    ),
    c.NDR_ALTO: (
        "El área requiere un análisis de cada categoría y dominio para determinar "
        "las acciones de intervención apropiadas, a través de un Programa de "
        "intervención."
    ),
    c.NDR_MUY_ALTO: (
        "El área presenta un nivel de riesgo muy alto: se requiere el análisis de "
        "cada categoría y dominio para establecer acciones de intervención a nivel "
        "del área o centro de trabajo, mediante un Programa de intervención."
    ),
}
```

- [ ] **Step 4: Run tests**

Run: `pytest apps/nom035/tests/test_config.py -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add apps/nom035/_nom035_scoring.py apps/nom035/tests/test_config.py
git commit -m "Reword NOM-035 action text to area/organization framing"
```

---

### Task 6: `employee_valuation` returns nested cat→dom→dim with scores, no action

**Files:**
- Modify: `apps/nom035/aggregates.py:35-64` (`employee_valuation`)
- Test: `apps/nom035/tests/test_aggregates.py:44-47` (rewrite `test_employee_valuation_returns_text`)

**Interfaces:**
- Consumes: `cfg.CATEGORIA_ORDER`, `cfg.dominios_for_categoria`, `cfg.dimensions_for_dominio`, `cfg.group_label`, `constants.LEVEL_DIMENSION`.
- Produces: `employee_valuation(user, company)` returns
  `{final_ndr, final_ndr_label, final_score, categories, guia1_positive}` where each
  category is `{key, label, score, ndr, ndr_label, domains:[{key,label,score,ndr,ndr_label,dimensions:[{key,label,score}]}]}`.
  **No** `final_action` / per-category `action`.

- [ ] **Step 1: Write the failing test**

Rewrite `test_employee_valuation_returns_text` in `apps/nom035/tests/test_aggregates.py`. The existing `scored` fixture creates a `SubmissionScore` with no `GroupScore` rows; extend the test to add category/domain/dimension rows:

```python
def test_employee_valuation_returns_nested_scores(scored):
    from apps.nom035 import constants as c
    from apps.nom035.models import GroupScore, SubmissionScore

    score = SubmissionScore.objects.get(submission__user=scored["user"])
    GroupScore.objects.create(submission_score=score, level=c.LEVEL_CATEGORIA,
                              key="ambiente_de_trabajo", score=13, ndr=c.NDR_ALTO)
    GroupScore.objects.create(submission_score=score, level=c.LEVEL_DOMINIO,
                              key="condiciones_en_el_ambiente_de_trabajo", score=13, ndr=c.NDR_ALTO)
    GroupScore.objects.create(submission_score=score, level=c.LEVEL_DIMENSION,
                              key="trabajos_peligrosos", score=4, ndr="")

    data = employee_valuation(scored["user"], scored["company"])
    assert data["final_ndr"] == c.NDR_MUY_ALTO
    assert "final_action" not in data
    cat = data["categories"][0]
    assert cat["key"] == "ambiente_de_trabajo"
    assert cat["score"] == 13
    assert cat["ndr_label"] == "Alto"
    dom = cat["domains"][0]
    assert dom["score"] == 13
    dim = dom["dimensions"][0]
    assert dim["key"] == "trabajos_peligrosos"
    assert dim["score"] == 4
    assert "ndr" not in dim  # dimensión is score-only
```

> The `scored` fixture uses `variant=LARGE`; `trabajos_peligrosos` is a dimensión of `condiciones_en_el_ambiente_de_trabajo` in the large variant, so `dimensions_for_dominio` will include it.

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest apps/nom035/tests/test_aggregates.py::test_employee_valuation_returns_nested_scores -v`
Expected: FAIL — current `employee_valuation` returns flat `categories` with `action`, no `domains`.

- [ ] **Step 3: Rewrite `employee_valuation`**

Replace `employee_valuation` in `apps/nom035/aggregates.py`:

```python
def employee_valuation(user, company) -> dict | None:
    """The latest scored submission for a user, as a nested categoría→dominio→
    dimensión tree with scores. Dimensión is score-only (no NDR)."""
    score = (
        _scores_for_company(company)
        .filter(submission__user=user)
        .select_related("submission__assignment")
        .prefetch_related("groups")
        .order_by("-submission__completed_at", "-computed_at")
        .first()
    )
    if score is None:
        return None
    variant = score.submission.assignment.variant
    rows = {(g.level, g.key): g for g in score.groups.all()}

    categories = []
    for cat_key in cfg.CATEGORIA_ORDER:
        cat_row = rows.get((c.LEVEL_CATEGORIA, cat_key))
        if cat_row is None:
            continue
        domains = []
        for dom_key in cfg.dominios_for_categoria(cat_key):
            dom_row = rows.get((c.LEVEL_DOMINIO, dom_key))
            if dom_row is None:
                continue
            dimensions = [
                {
                    "key": dim_key,
                    "label": cfg.group_label(dim_key),
                    "score": rows[(c.LEVEL_DIMENSION, dim_key)].score,
                }
                for dim_key in cfg.dimensions_for_dominio(dom_key, variant)
                if (c.LEVEL_DIMENSION, dim_key) in rows
            ]
            domains.append({
                "key": dom_key,
                "label": cfg.group_label(dom_key),
                "score": dom_row.score,
                "ndr": dom_row.ndr,
                "ndr_label": NDR(dom_row.ndr).label,
                "dimensions": dimensions,
            })
        categories.append({
            "key": cat_key,
            "label": cfg.group_label(cat_key),
            "score": cat_row.score,
            "ndr": cat_row.ndr,
            "ndr_label": NDR(cat_row.ndr).label,
            "domains": domains,
        })

    return {
        "final_ndr": score.final_ndr,
        "final_ndr_label": NDR(score.final_ndr).label,
        "final_score": score.final_score,
        "categories": categories,
        "guia1_positive": score.guia1_positive,
    }
```

- [ ] **Step 4: Run tests**

Run: `pytest apps/nom035/tests/test_aggregates.py -v`
Expected: PASS (the other aggregate tests use `final_score`/`final_ndr`, still present).

- [ ] **Step 5: Commit**

```bash
git add apps/nom035/aggregates.py apps/nom035/tests/test_aggregates.py
git commit -m "Return nested categoría/dominio/dimensión scores from employee_valuation"
```

---

### Task 7: `company_valuation` per-area breakdown with most-severe action line

**Files:**
- Modify: `apps/nom035/aggregates.py:6-32` (`_scores_for_company`, `company_valuation`) + new helpers
- Test: `apps/nom035/tests/test_aggregates.py`

**Interfaces:**
- Consumes: `UserProfile.department` (Task 1), `cfg.action_text` (Task 5), `constants.NDR_ORDER/NDR_ALTO/NDR_MUY_ALTO/NDR_LABELS`.
- Produces: `company_valuation(company)` keeps its existing keys and adds `areas: list[dict]`, each
  `{label, scored_count, distribution, distribution_rows, needing_action, guia1_positive_count, action, action_ndr, action_ndr_label}`. Grouping is by `department.strip().casefold()`; blank → display `"Sin área"`. `action_ndr` = most-severe NDR present in the area.

- [ ] **Step 1: Write the failing test**

Add to `apps/nom035/tests/test_aggregates.py`:

```python
def test_company_valuation_area_breakdown(make_company, make_user_with_profile, survey):
    from apps.nom035 import constants as c
    from apps.nom035.models import SubmissionScore

    company = make_company()

    def _score(email, dept, ndr):
        user = make_user_with_profile(email=email, company=company)
        user.profile.department = dept
        user.profile.save()
        assignment = SurveyAssignment.objects.create(
            company=company, survey=survey, variant=SurveyAssignment.Variant.LARGE,
            status=SurveyAssignment.Status.ACTIVE)
        sub = SurveySubmission.objects.create(
            assignment=assignment, user=user, status=SurveySubmission.Status.IN_PROGRESS)
        SubmissionScore.objects.create(submission=sub, final_score=1, final_ndr=ndr)

    _score("a@x.mx", "Sistemas", c.NDR_MUY_ALTO)
    _score("b@x.mx", "sistemas ", c.NDR_BAJO)   # same area, different casing/space
    _score("c@x.mx", "", c.NDR_MEDIO)           # → "Sin área"

    data = company_valuation(company)
    areas = {a["label"]: a for a in data["areas"]}
    assert set(areas) == {"Sistemas", "Sin área"}
    sistemas = areas["Sistemas"]
    assert sistemas["scored_count"] == 2
    assert sistemas["needing_action"] == 1
    assert sistemas["action_ndr"] == c.NDR_MUY_ALTO      # most-severe present
    assert sistemas["action"] == cfg.action_text(c.NDR_MUY_ALTO)
    assert areas["Sin área"]["action_ndr"] == c.NDR_MEDIO
```

(Add `from apps.nom035 import _nom035_scoring as cfg` to the test module imports if not already present — the module imports `constants as c` only.)

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest apps/nom035/tests/test_aggregates.py::test_company_valuation_area_breakdown -v`
Expected: FAIL — `company_valuation` has no `areas` key.

- [ ] **Step 3: Add the import and helpers**

At the top of `apps/nom035/aggregates.py` it already imports `cfg` and `c`. Add these helpers above `company_valuation`:

```python
def _department_of(score) -> str:
    user = score.submission.user
    profile = getattr(user, "profile", None) if user else None
    return (getattr(profile, "department", "") or "").strip()


def _most_severe_present(distribution: dict[str, int]) -> str | None:
    present = [level for level in c.NDR_ORDER if distribution[level] > 0]
    return present[-1] if present else None


def _area_breakdown(scores) -> list[dict]:
    groups: dict[str, dict] = {}
    for s in scores:
        raw = _department_of(s)
        gkey = raw.casefold()
        area = groups.get(gkey)
        if area is None:
            area = groups[gkey] = {
                "label": raw or "Sin área",
                "distribution": {level: 0 for level in c.NDR_ORDER},
                "scored_count": 0,
                "needing_action": 0,
                "guia1_positive_count": 0,
            }
        area["scored_count"] += 1
        area["distribution"][s.final_ndr] += 1
        if s.final_ndr in (c.NDR_ALTO, c.NDR_MUY_ALTO):
            area["needing_action"] += 1
        if s.guia1_positive:
            area["guia1_positive_count"] += 1

    areas = []
    for area in groups.values():
        most_severe = _most_severe_present(area["distribution"])
        area["distribution_rows"] = [
            {"ndr": level, "label": c.NDR_LABELS[level], "count": area["distribution"][level]}
            for level in c.NDR_ORDER
        ]
        area["action_ndr"] = most_severe or ""
        area["action_ndr_label"] = c.NDR_LABELS[most_severe] if most_severe else ""
        area["action"] = cfg.action_text(most_severe) if most_severe else ""
        areas.append(area)

    # Most-severe areas first, then most people needing action, then name.
    areas.sort(key=lambda a: (
        -(c.NDR_ORDER.index(a["action_ndr"]) if a["action_ndr"] else -1),
        -a["needing_action"],
        a["label"],
    ))
    return areas
```

- [ ] **Step 4: Wire the breakdown into `company_valuation`**

Update `_scores_for_company` and `company_valuation` to fetch the profile and attach `areas`:

```python
def _scores_for_company(company):
    return SubmissionScore.objects.filter(
        submission__assignment__company=company
    ).select_related("submission__user__profile")
```

At the end of `company_valuation`'s return dict, add `"areas"`:

```python
    return {
        "scored_count": len(scores),
        "distribution": distribution,
        "distribution_rows": distribution_rows,
        "needing_action": needing_action,
        "guia1_positive_count": guia1_positive_count,
        "areas": _area_breakdown(scores),
    }
```

- [ ] **Step 5: Run tests**

Run: `pytest apps/nom035/tests/test_aggregates.py -v`
Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add apps/nom035/aggregates.py apps/nom035/tests/test_aggregates.py
git commit -m "Add per-area breakdown with most-severe action line to company_valuation"
```

---

### Task 8: Centralized NDR color template filters

**Files:**
- Create: `apps/core/templatetags/__init__.py` (empty, if the dir doesn't exist)
- Create: `apps/core/templatetags/valuation_extras.py`
- Test: `apps/core/tests/test_valuation_extras.py`

**Interfaces:**
- Produces: template filters `ndr_badge(ndr)` → Tailwind badge classes (bg/text/ring) and `ndr_bar(ndr)` → a solid bar background class, for every NDR value; unknown/empty → a neutral gray.

- [ ] **Step 1: Write the failing test**

Create `apps/core/tests/test_valuation_extras.py`:

```python
from apps.core.templatetags.valuation_extras import ndr_bar, ndr_badge
from apps.nom035 import constants as c


def test_ndr_badge_covers_every_level():
    for level in c.NDR_ORDER:
        assert ndr_badge(level)


def test_ndr_badge_muy_alto_is_red():
    assert "red" in ndr_badge(c.NDR_MUY_ALTO)


def test_ndr_bar_unknown_is_neutral():
    assert "gray" in ndr_bar("")
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest apps/core/tests/test_valuation_extras.py -v`
Expected: FAIL — module does not exist.

- [ ] **Step 3: Create the templatetag library**

Create `apps/core/templatetags/__init__.py` (empty) if missing, then `apps/core/templatetags/valuation_extras.py`:

```python
from django import template

from apps.nom035 import constants as c

register = template.Library()

_BADGE = {
    c.NDR_NULO: "bg-gray-100 text-gray-600 ring-gray-500/20",
    c.NDR_BAJO: "bg-green-50 text-green-700 ring-green-600/20",
    c.NDR_MEDIO: "bg-amber-50 text-amber-700 ring-amber-600/20",
    c.NDR_ALTO: "bg-orange-50 text-orange-700 ring-orange-600/20",
    c.NDR_MUY_ALTO: "bg-red-50 text-red-700 ring-red-600/20",
}
_NEUTRAL_BADGE = "bg-gray-100 text-gray-500 ring-gray-500/20"

_BAR = {
    c.NDR_NULO: "bg-gray-300",
    c.NDR_BAJO: "bg-green-500",
    c.NDR_MEDIO: "bg-amber-500",
    c.NDR_ALTO: "bg-orange-500",
    c.NDR_MUY_ALTO: "bg-red-500",
}
_NEUTRAL_BAR = "bg-gray-200"


@register.filter
def ndr_badge(ndr):
    """Tailwind classes for a colored NDR badge (pill)."""
    return _BADGE.get(ndr, _NEUTRAL_BADGE)


@register.filter
def ndr_bar(ndr):
    """Tailwind background class for an NDR distribution-bar segment."""
    return _BAR.get(ndr, _NEUTRAL_BAR)
```

- [ ] **Step 4: Run tests**

Run: `pytest apps/core/tests/test_valuation_extras.py -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add apps/core/templatetags/ apps/core/tests/test_valuation_extras.py
git commit -m "Add centralized NDR color template filters"
```

---

### Task 9: Redesign the employee valuation panel (nested hierarchy + scores)

**Files:**
- Modify: `templates/core/employee_detail.html:55-86` (the "Valoración de resultados" section)
- Modify: `static/css/output.css` (regenerated by build)
- Test: `apps/core/tests/test_employee_valuation_panel.py`

**Interfaces:**
- Consumes: `employee_valuation` nested shape (Task 6), `ndr_badge` filter (Task 8).

- [ ] **Step 1: Write the failing test**

Extend `apps/core/tests/test_employee_valuation_panel.py`. Add GroupScore rows to the existing test and assert the new structure renders (score + a dimensión label), and that no action sentence appears:

```python
def test_panel_shows_scores_and_hierarchy(
    client, bootstrap_groups, make_user_with_profile, make_company, survey
):
    from apps.nom035.models import GroupScore

    company = make_company()
    admin = make_user_with_profile(email="admin2@x.mx", company=company)
    admin.groups.add(bootstrap_groups["Admins"])
    employee = make_user_with_profile(email="emp2@x.mx", company=company)
    assignment = SurveyAssignment.objects.create(
        company=company, survey=survey, variant=SurveyAssignment.Variant.LARGE,
        status=SurveyAssignment.Status.ACTIVE)
    sub = SurveySubmission.objects.create(
        assignment=assignment, user=employee, status=SurveySubmission.Status.IN_PROGRESS)
    score = SubmissionScore.objects.create(
        submission=sub, final_score=160, final_ndr=c.NDR_MUY_ALTO)
    GroupScore.objects.create(submission_score=score, level=c.LEVEL_CATEGORIA,
                              key="ambiente_de_trabajo", score=13, ndr=c.NDR_ALTO)
    GroupScore.objects.create(submission_score=score, level=c.LEVEL_DOMINIO,
                              key="condiciones_en_el_ambiente_de_trabajo", score=13, ndr=c.NDR_ALTO)
    GroupScore.objects.create(submission_score=score, level=c.LEVEL_DIMENSION,
                              key="trabajos_peligrosos", score=4, ndr="")

    client.force_login(admin)
    resp = client.get(reverse("core:company_employee_detail", args=[employee.id]))
    body = resp.content.decode()
    assert "Ambiente de trabajo" in body
    assert "Trabajos peligrosos" in body       # dimensión label rendered
    assert "Se requiere" not in body            # no action sentence on the card
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest apps/core/tests/test_employee_valuation_panel.py -v`
Expected: FAIL — dimensión label not rendered (old template shows category-only, no domains/dimensions), and the old `final_action` may still render "Se requiere…".

- [ ] **Step 3: Rewrite the panel**

In `templates/core/employee_detail.html`, ensure the top loads the filters: change line 2 to `{% load survey_extras valuation_extras %}`. Replace the section body (lines ~59–85, the `<div class="rounded-2xl …">…</div>` inside the `{% if perms.accounts.can_view_insights %}` section) with:

```html
  <div class="rounded-2xl border border-gray-200 bg-white px-6 py-5">
    {% if valuation %}
      <div class="flex items-center justify-between gap-4 pb-4 mb-4 border-b border-gray-100">
        <div>
          <p class="text-xs font-medium text-gray-400 uppercase tracking-wide">Nivel de riesgo final</p>
          <p class="mt-1 text-lg font-bold text-gray-900">
            {{ valuation.final_ndr_label }}
            <span class="ml-1 text-sm font-normal text-gray-400">({{ valuation.final_score }})</span>
          </p>
        </div>
        <span class="inline-flex items-center rounded-full px-3 py-1 text-xs font-semibold ring-1 ring-inset {{ valuation.final_ndr|ndr_badge }}">
          {{ valuation.final_ndr_label }}
        </span>
      </div>

      <div class="space-y-4">
        {% for cat in valuation.categories %}
          <div>
            <div class="flex items-center justify-between gap-3">
              <span class="text-sm font-semibold text-gray-900">{{ cat.label }}</span>
              <span class="shrink-0 flex items-center gap-2">
                <span class="text-sm tabular-nums text-gray-500">{{ cat.score }}</span>
                <span class="inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium ring-1 ring-inset {{ cat.ndr|ndr_badge }}">{{ cat.ndr_label }}</span>
              </span>
            </div>
            <div class="mt-2 ml-3 pl-3 border-l border-gray-100 space-y-2">
              {% for dom in cat.domains %}
                <div>
                  <div class="flex items-center justify-between gap-3">
                    <span class="text-sm text-gray-700">{{ dom.label }}</span>
                    <span class="shrink-0 flex items-center gap-2">
                      <span class="text-sm tabular-nums text-gray-500">{{ dom.score }}</span>
                      <span class="inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium ring-1 ring-inset {{ dom.ndr|ndr_badge }}">{{ dom.ndr_label }}</span>
                    </span>
                  </div>
                  {% if dom.dimensions %}
                    <ul class="mt-1 ml-3 pl-3 border-l border-gray-100 space-y-1">
                      {% for dim in dom.dimensions %}
                        <li class="flex items-center justify-between gap-3 text-xs text-gray-500">
                          <span>{{ dim.label }}</span>
                          <span class="tabular-nums">{{ dim.score }}</span>
                        </li>
                      {% endfor %}
                    </ul>
                  {% endif %}
                </div>
              {% endfor %}
            </div>
          </div>
        {% endfor %}
      </div>

      {% if valuation.guia1_positive %}
        <p class="mt-4 pt-4 border-t border-gray-100 text-sm font-medium text-amber-700">
          Usuario positivo a un acontecimiento traumático severo.
        </p>
      {% endif %}
    {% else %}
      <p class="text-sm text-gray-500">Sin resultados: la encuesta no ha sido completada.</p>
    {% endif %}
  </div>
```

- [ ] **Step 4: Rebuild CSS**

Run: `npm run build:css`
Expected: `static/css/output.css` regenerated (now includes `bg-orange-*`, `bg-red-*`, `tabular-nums`, etc.).

- [ ] **Step 5: Run tests**

Run: `pytest apps/core/tests/test_employee_valuation_panel.py -v`
Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add templates/core/employee_detail.html static/css/output.css apps/core/tests/test_employee_valuation_panel.py
git commit -m "Redesign employee valuation panel: nested cat/dom/dim with scores, no action text"
```

---

### Task 10: Redesign the company valuation panel (per-area distribution + action)

**Files:**
- Modify: `templates/core/company_dashboard.html:190-218` (the "Valoración de resultados" section)
- Modify: `static/css/output.css` (regenerated by build)
- Test: `apps/core/tests/test_company_valuation_panel.py`

**Interfaces:**
- Consumes: `company_valuation` `areas` shape (Task 7), `ndr_badge` + `ndr_bar` filters (Task 8).

- [ ] **Step 1: Write the failing test**

Extend `apps/core/tests/test_company_valuation_panel.py`. Give the scored submission a user with a department and assert the area label + action appear:

```python
def test_dashboard_shows_area_breakdown(
    client, bootstrap_groups, make_user_with_profile, make_company, survey
):
    company = make_company()
    admin = make_user_with_profile(email="a2@x.mx", company=company)
    admin.groups.add(bootstrap_groups["Admins"])
    employee = make_user_with_profile(email="e2@x.mx", company=company)
    employee.profile.department = "Sistemas"
    employee.profile.save()
    assignment = SurveyAssignment.objects.create(
        company=company, survey=survey, variant=SurveyAssignment.Variant.LARGE,
        status=SurveyAssignment.Status.ACTIVE)
    sub = SurveySubmission.objects.create(
        assignment=assignment, user=employee, status=SurveySubmission.Status.IN_PROGRESS)
    SubmissionScore.objects.create(submission=sub, final_score=160, final_ndr=c.NDR_MUY_ALTO)

    client.force_login(admin)
    resp = client.get(reverse("core:company_dashboard_for", args=[company.reference_code]))
    body = resp.content.decode()
    assert "Sistemas" in body
    assert "El área presenta un nivel de riesgo muy alto" in body
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest apps/core/tests/test_company_valuation_panel.py -v`
Expected: FAIL — area label/action not rendered.

- [ ] **Step 3: Add the per-area section**

In `templates/core/company_dashboard.html`, add `{% load valuation_extras %}` near the top with the other `{% load %}` tags. Inside the `{% if perms.accounts.can_view_insights %}` section, **after** the existing company-wide summary `<div>` (keep it) and still inside `<section>`, insert the per-area block:

```html
      {% if company_valuation.areas %}
        <div class="mt-6 space-y-3">
          <h3 class="text-xs font-semibold text-gray-500 uppercase tracking-wide">Por área / departamento</h3>
          {% for area in company_valuation.areas %}
            <div class="rounded-xl border border-gray-200 bg-white px-5 py-4">
              <div class="flex items-center justify-between gap-3">
                <span class="text-sm font-semibold text-gray-900">{{ area.label }}</span>
                <span class="inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium ring-1 ring-inset {{ area.action_ndr|ndr_badge }}">
                  {{ area.action_ndr_label }}
                </span>
              </div>

              <div class="mt-3 flex h-2 w-full overflow-hidden rounded-full bg-gray-100">
                {% for row in area.distribution_rows %}
                  {% if row.count %}
                    <div class="{{ row.ndr|ndr_bar }}" style="width: {% widthratio row.count area.scored_count 100 %}%" title="{{ row.label }}: {{ row.count }}"></div>
                  {% endif %}
                {% endfor %}
              </div>

              <div class="mt-2 flex flex-wrap items-center gap-x-4 gap-y-1 text-xs text-gray-500">
                <span>{{ area.scored_count }} valorado{{ area.scored_count|pluralize:"s" }}</span>
                <span>{{ area.needing_action }} en Alto/Muy alto</span>
                {% if area.guia1_positive_count %}<span>{{ area.guia1_positive_count }} Guía I</span>{% endif %}
              </div>

              <p class="mt-2 text-sm text-gray-600">{{ area.action }}</p>
            </div>
          {% endfor %}
        </div>
      {% endif %}
```

- [ ] **Step 4: Rebuild CSS**

Run: `npm run build:css`
Expected: `static/css/output.css` regenerated.

- [ ] **Step 5: Run tests**

Run: `pytest apps/core/tests/test_company_valuation_panel.py -v`
Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add templates/core/company_dashboard.html static/css/output.css apps/core/tests/test_company_valuation_panel.py
git commit -m "Add per-area distribution and org-framed action to company valuation panel"
```

---

### Task 11: Backfill, docs, and full-suite verification

**Files:**
- Modify: `docs/platform/nom-035-analytics.md` (reflect dimensión materialization, per-area aggregation, presentation change)

**Interfaces:**
- Consumes: everything above.

- [ ] **Step 1: Update the analytics doc**

In `docs/platform/nom-035-analytics.md`, make these edits (keep them tight):
- In **"Aggregation into NDR"** / schema notes, state that `GroupScore` now also stores **dimensión** rows (`level="dimension"`, score-only, `ndr=""`), and update the `GroupScore.level` row of the Schema table from `categoria / dominio (dimensión is not scored)` to `categoria / dominio / dimension (dimensión is score-only, no NDR)`.
- In **"Reads and aggregation"**, update `employee_valuation` to "returns the nested categoría→dominio→dimensión tree with scores (no action text)" and `company_valuation` to "…plus a per-area breakdown (grouped by `UserProfile.department`, normalized) with an organization-framed action line keyed to the most-severe NDR present."
- In **"Key decisions"**, note the presentation shift: action text is organization/area-framed and shown only in aggregate reads; add a pointer to `docs/platform/nom-035-valuation-presentation.md`.
- Add one line pointing to the open SME question in `nom-035-valoracion-supuestos.md` §3 (area action rule).

- [ ] **Step 2: Backfill existing scores (operational)**

Run: `python manage.py recompute_nom035_scores`
Expected: `Recomputed N submission scores.` — this re-materializes existing completed submissions so their dimensión `GroupScore` rows exist. (In a fresh dev DB with no completed submissions, N may be 0; that's fine.)

- [ ] **Step 3: Apply migrations**

Run: `python manage.py migrate`
Expected: the `accounts` department migration and the `nom035` state-only migration apply cleanly.

- [ ] **Step 4: Run the full test suite**

Run: `pytest`
Expected: PASS (all apps). Investigate and fix any failure before proceeding — in particular re-grep for any remaining 2-tuple taxonomy unpack:

Run: `grep -rn "taxonomy_for_variant" apps/ | grep -v "def taxonomy_for_variant"`
Confirm every consumer unpacks 3 values (or indexes safely). Fix any stragglers, re-run `pytest`.

- [ ] **Step 5: Lint & format**

Run: `ruff format . && ruff check .`
Expected: no errors (fix any).

- [ ] **Step 6: Commit**

```bash
git add docs/platform/nom-035-analytics.md
git commit -m "Docs: dimensión materialization + per-area aggregation in NOM-035 analytics"
```

---

## Self-Review Notes (coverage map)

- Spec §1 (department field) → Tasks 1–2. §2 (dimensión scoring) → Tasks 3–4 + backfill (Task 11). §3 (action reframing) → Task 5 (reword) + Task 6 (drop from employee card) + Task 7 (surface at aggregate). §4 (aggregation) → Tasks 6–7. §5 (visual design) → Tasks 8–10. Testing section → per-task tests + Task 11 full run. Decisions A/B/C → Task 6 (no action, keep guía1 flag) / Task 7 (most-severe-present) / supuestos §3 already written.
- **Cross-task type consistency:** taxonomy is a 3-tuple everywhere (Tasks 3, 4, and the fixed test in Task 3); `employee_valuation` category dict shape (`domains`/`dimensions`) matches Task 9 template; `company_valuation` `areas` dict shape matches Task 10 template; filter names `ndr_badge`/`ndr_bar` consistent across Tasks 8–10.
- **Known verification points for the implementer:** confirm `responses.Answer` field names before running the Task 4 test; confirm the `UserProfile` admin structure (inline vs standalone) in Task 1; confirm `company_dashboard.html` `{% load %}` line placement in Task 10.
