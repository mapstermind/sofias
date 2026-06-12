# surveys

Survey authoring data model and the employee survey-taking experience. URL prefix: `/encuestas/` (`app_name = "surveys"`). Submitted answers live in `apps/responses`; the authoring CLI/admin tooling lives in `apps/core`.

## The template → version → stamped-instance model

This is the central concept. Understand it before changing `models.py`.

**Library (reusable, company-agnostic):**
- `QuestionTemplate` + `ChoiceTemplate` — a reusable question/choice library.

**Concrete survey (owned by a version):**
- `SurveyTemplate` — a survey (title, `status`: draft/published/archived).
- `SurveyVersion` — a numbered, immutable-ish snapshot of a survey (`unique(template, version_number)`). Questions belong to a version, never directly to the template.
- `Section` — optional grouping of questions within a version (ordered).
- `Question` + `Choice` — the actual questions answered by respondents, **owned by a `SurveyVersion`**.

`QuestionTemplate.stamp_into(version, section, order)` **copies** a library template into a version as an independent `Question` (and copies its `ChoiceTemplate`s into `Choice`s). The copy keeps a nullable `source` FK back to the template for provenance, but is otherwise fully independent — editing the library never mutates already-stamped questions. This is the mechanism behind the admin "Stamp into survey version" action (`admin.py`) and the core authoring workflows.

**Assignment:**
- `SurveyAssignment` — links a `SurveyVersion` to a `Company` (status active/closed, optional `due_date`). This is what makes a survey available to a company's employees.

`config` (JSONField on both `QuestionTemplate` and `Question`) holds flexible per-type settings: `min`, `max`, `placeholder`, `labels` (likert), `validation_rules`, etc.

### Question types (`QuestionTemplate.QuestionType`)
`text, integer, decimal, date, single_choice, multiple_choice, boolean, rating, likert`. `Question.QuestionType` is an alias of the same enum. Answer parsing per type is handled in `views.py` (and mirrored in `apps/core` answer-rendering) — keep these in sync when adding a type.

## Views (`views.py`) — taking a survey

- `survey_detail(assignment_id)` — renders the form and handles POST. Reuses an in-progress `SurveySubmission` per (user, assignment); marks `COMPLETED` only when **all** questions are answered, else `IN_PROGRESS`. Closed/completed assignments redirect to `core:home`. Anonymous submissions are allowed (`user=None`).
- `autosave_survey(assignment_id)` — POST-only AJAX endpoint; persists single changed fields without changing submission status. Returns JSON.
- `survey_submitted(assignment_id)` — confirmation page.

Per-type form parsing (`question_<id>` keys) is duplicated between `survey_detail` and `autosave_survey` — change both together.

## Other files

- `templatetags/survey_extras.py` — `dict_get` and `likert_pairs` (maps likert config `labels` → value/label pairs; values always 1–5, default 5-point Spanish scale).
- `admin.py` — manages both the library and concrete surveys; notable "Stamp into version" bulk action.
- `tests/` — split into `test_models.py`, `test_views.py`.

## Gotchas

- Answers are **not** stored here — see `apps/responses.Answer` (FK to `surveys.Question`, value is JSON whose shape depends on `question_type`).
- `SurveyAssignment.company` FKs `accounts.Company`.
- User-facing strings/URLs are Spanish; some validation error strings in `views.py` are still English.
