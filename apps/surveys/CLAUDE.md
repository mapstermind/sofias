# surveys

Survey instrument data model and the employee survey-taking experience. URL prefix: `/encuestas/` (`app_name = "surveys"`). Submitted answers live in `apps/responses`; the NOM-035 seed lives in `apps/core`.

## The Survey → Module → Question model

This is the central concept. Understand it before changing `models.py`. There is **no reusable question library, no numbered versions, and no copy-on-stamp** — surveys are fixed instruments, seeded once. Rationale: `docs/adr/adr-0002-flatten-survey-authoring-model.md`.

- `Survey` — the instrument. `key` (stable unique slug, e.g. `nom035`), `title`, `description`, `status` (draft/published/archived), `headcount_threshold` (default 50). A material change = a **new** `Survey`, not a version.
- `Module` — an ordered group of questions within a survey (replaces the old `Section`). `applies_to` ∈ `all`/`small`/`large`; `key` (unique per survey); optional `visible_when`.
- `Question` — owned by a `Module`. `code` (stable, **unique per survey** — the integration key the valuation engine consumes), `question_type`, `text`, `config` (JSON), optional `visible_when`. Carries a denormalized `survey` FK (set in `save()` from `module.survey`) to back the `unique(survey, code)` constraint.
- `Choice` — selectable option for `single_choice`/`multiple_choice`. (Boolean Sí/No renders from hardcoded radios, not `Choice` rows.)
- `SurveyAssignment` — links a `Survey` to a `Company` with a frozen `variant` (`small`/`large`). `resolve_default_variant(company, survey)` computes the default from `company.members.count()` vs `survey.headcount_threshold` (operator-overridable); `modules_for_variant()` returns the modules to present (`all` plus the variant's).

`apps/surveys` stores **no scoring** (no inverted flags, dimensión/dominio/categoría, or thresholds) — that lives in the instrument's engine app, keyed by `Question.code`. For NOM-035 that is `apps/nom035` (see its CLAUDE.md).

### Question types (`Question.QuestionType`)
`text, integer, decimal, date, single_choice, multiple_choice, boolean, rating, likert`. Answer parsing per type is in `views.py._parse_value` (and answer-rendering in `apps/core`) — keep these in sync when adding a type.

## Conditional visibility (`visibility.py`)

`visible_when` (on `Module` and `Question`) is a small JSON rule, evaluated by `is_visible()` / `visible_questions()` — the **single source of truth** for both server-side completeness and the client mirror in `static/ts/survey_progress.ts`. Forms:
- `{"question": "<code>", "equals": <value>}` — single-answer gate.
- `{"any_in_module": "<module key>", "equals": <value>}` — module aggregate.

Null/empty = always visible. A submission is `COMPLETED` only when all **visible** questions are answered; hidden questions never block completion. `_normalize` loosely coerces `"si"/"sí"/"true"` etc. to booleans so rules match boolean answers.

## Views (`views.py`) — taking a survey

- `survey_detail(assignment_id)` — renders modules for the assignment's variant and handles POST. Reuses an in-progress `SurveySubmission` per (user, assignment); marks `COMPLETED` only when all visible questions are answered. Closed/completed assignments redirect to `core:home`. Anonymous submissions allowed (`user=None`).
- `autosave_survey(assignment_id)` — POST-only AJAX; persists single changed fields without changing status.
- `survey_submitted(assignment_id)` — confirmation page.

`_parse_value(question, post)` is the shared per-type parser used by both `survey_detail` and `autosave_survey` — change it once.

## Other files

- `templatetags/survey_extras.py` — `dict_get`, `as_json` (compact JSON for `data-visible-when` attributes), `likert_pairs` (config `labels` → value/label pairs; values 1–5).
- `admin.py` — registers the flat models (`Survey`, `Module`, `Question`, `Choice`, `SurveyAssignment`) for inspection. No authoring actions.
- `tests/` — `test_models.py`, `test_views.py`, `test_visibility.py`.

## Gotchas

- Answers are **not** stored here — see `apps/responses.Answer` (FK to `surveys.Question`).
- The NOM-035 instrument is built by `python manage.py seed_nom035_survey` (data in `apps/core/management/commands/_nom035_data.py`). There is no interactive authoring CLI.
- Migrations were reset for this model (ADR-0002); `apps/surveys` and `apps/responses` start at a fresh `0001`.
- User-facing strings/URLs are Spanish; some validation error strings in `views.py` are still English.
