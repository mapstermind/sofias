# Survey Model Redesign — Design

**Date:** 2026-06-20
**Status:** Approved (pending spec review)
**Affects:** `apps/surveys`, `apps/responses`, `apps/core` (workflows, commands, views, templates), `conftest.py`, docs

## 1. Problem & motivation

The current survey authoring model is built around a reusable library plus
copy-on-stamp versioning:

```
QuestionTemplate / ChoiceTemplate  (library)
SurveyTemplate ──< SurveyVersion ──< Section ──< Question ──< Choice
QuestionTemplate.stamp_into(version)  (copies library → version)
SurveyAssignment → SurveyVersion → Company
```

This machinery exists to support **self-service survey authoring**: a reusable
question library, copy-on-stamp so edits never mutate live surveys, and numbered
immutable versions. That is not how SOFIA-S is actually used.

Confirmed during brainstorming:

- **Operators seed fixed instruments.** Pinit defines surveys (NOM-035 today, an
  unrelated second survey later) once, via seed/admin. Client admins never author
  questions. Surveys are fixed instruments tied to scoring logic.
- Surveys are **rarely created and rarely modified** after creation.
- When an instrument *does* change materially → **create a new survey; old data
  stays frozen** against the old survey. No numbered-version chain is needed.

So the library + version + stamping layer pays continuous complexity rent for a
use case that does not exist. This redesign removes it.

## 2. The modular instrument (NOM-035)

Source: `docs/internal/roadmap_context/Guias de Referencia.pdf`. NOM-035 is
delivered as three reference guides, which map directly onto the "modules":

| Module | Guide | Items | Applies to | Type | Scored into NDR? |
|---|---|---|---|---|---|
| 1 | Guía I — Acontecimientos traumáticos severos | ~17 | **everyone** | boolean (Sí/No) | No — produces a "requiere valoración clínica" flag via its own rules |
| 2 | Guía II — Factores de riesgo psicosocial | 46 | centers **15–50** workers | likert (Siempre…Nunca) | Yes |
| 3 | Guía III — … y entorno organizacional | 72 | centers **>50** workers | likert | Yes |

Key facts the model must respect:

- **Module 1 (Guía I) is identical for everyone** — same items, same referral
  logic — regardless of size. (This is the "shared module 1, identical incl.
  scoring" established in brainstorming.)
- A respondent receives **Guía I + (Guía II *or* Guía III)** as one seamless
  experience; the variant is chosen by company headcount.
- **Conditional/branching logic is intrinsic** to the instruments:
  - Guía I: *if all Section I answers are "No" → skip the rest* (no clinical
    valuation).
  - Guía II & III: *"¿Debo brindar servicio a clientes?" Sí/No* gates a block;
    *"¿Soy jefe de otros trabajadores?" Sí/No* gates the final supervision block.
- **Scoring is data, not code** (roadmap Initiative 1): inverted items, the
  dimensión→dominio→categoría grouping, and threshold tables are configuration
  for a future valuation engine — **out of scope here**. The survey model owes
  that engine only a **stable per-item `code`**.

## 3. Chosen approach

**Approach A — single survey, modules with applicability** (selected over
"three stitched surveys" and "two duplicated full surveys"). One `Survey` owns
ordered `Module`s; each module is tagged with who it applies to; modules own
`Question`s directly. Each item — and later its scoring — is defined exactly once.
The assignment freezes the resolved variant per company.

### 3.1 Data model (`apps/surveys/models.py`)

```
Survey ──< Module ──< Question ──< Choice
SurveyAssignment → Survey   (+ frozen variant)
```

**`Survey`** — the instrument.
- `key` — stable slug, unique (e.g. `nom035`).
- `title`, `description`, `status` (draft/published/archived).
- `headcount_threshold` — int, default `50`. `headcount > threshold → large`.
- `created_at`, `updated_at`.

**`Module`** — ordered group of questions within a survey.
- `survey` (FK), `title`, `description`, `order`.
- `applies_to` — `all` / `small` / `large` (TextChoices).
- `visible_when` — JSON rule, nullable (see §3.3).

**`Question`** — owned by a module.
- `module` (FK), `code` (stable; unique per survey, e.g. `g3-29`).
- `question_type` (existing enum: text, integer, decimal, date, single_choice,
  multiple_choice, boolean, rating, likert).
- `text`, `order`, `config` (JSON: min/max/labels/placeholder/etc.).
- `visible_when` — JSON rule, nullable.
- **Removed:** `version`, `section`, `source` FKs.

**`Choice`** — owned by question.
- `question` (FK), `label`, `value`, `order`.
- **Removed:** `source` FK.

**`SurveyAssignment`** — links a survey to a company.
- `company` (FK), `survey` (FK — was `version`).
- `variant` — `small` / `large`, frozen at creation (§3.2).
- `status` (active/closed), `due_date`, `created_at`.

**Deleted entirely:** `QuestionTemplate`, `ChoiceTemplate`, `SurveyTemplate`,
`SurveyVersion`, `Section`, `stamp_into()`, the reusable library, numbered
versions, copy-on-stamp provenance.

### 3.2 Variant resolution & freezing

On `SurveyAssignment` creation, the default variant is computed from the
company's headcount vs `survey.headcount_threshold` (`> threshold → large`, else
`small`), pre-filled, and **operator-overridable**. The chosen value is stored on
the assignment, so it stays fixed even if headcount later changes.

At take-time the modules presented are those where
`applies_to == "all"` **OR** `applies_to == assignment.variant`. Guía I (`all`)
always shows; Guía II or III shows per variant.

Helper: `SurveyAssignment.resolve_default_variant(company, survey)` (pure,
testable) computes the suggested variant; the assignment creation path calls it.

### 3.3 Conditional visibility (`visible_when`)

A small, generic JSON rule on `Module` and `Question`, evaluated **server-side**
(completeness/scoring) and **client-side** (live show/hide). Supported forms:

- Single-answer gate:
  `{"question": "g3-clientes", "equals": "si"}`
  → covers "atiendo clientes" and "soy jefe".
- Module aggregate:
  `{"any_in_module": "g1-trauma", "equals": "si"}`
  → covers Guía I "if any Section I = Sí continue, else skip the rest".

Rules:
- Null / empty `visible_when` ⇒ always visible.
- A question hidden by its own rule, or inside a hidden module, is **excluded**
  from the "all required answered → COMPLETED" check, and its stored answer (if
  any) is ignored.
- Evaluation lives in one place: `apps/surveys/visibility.py` —
  `is_visible(rule, answers_by_code) -> bool` and a
  `visible_questions(assignment, answers) -> list[Question]` helper used by both
  views and (later) scoring. Stays survey-agnostic so the second survey reuses it.

### 3.4 Scoring boundary

`apps/surveys` stores **no scoring**: no inverted flag, no
dimensión/dominio/categoría, no thresholds. `Question.code` is the durable key the
future valuation engine (Initiative 1, separate app/config) references. This keeps
the survey model focused and lets scoring evolve independently.

### 3.5 Taking & submission flow

Shape is preserved; only the resolution source changes.

- `survey_detail` / `autosave_survey` / `survey_submitted` resolve questions via
  `assignment.survey` + `variant` + `visible_when`, instead of `version` +
  `section`.
- Completeness = all **visible**, required questions answered.
- `responses.SurveySubmission` (one per user+assignment) and `responses.Answer`
  (FK `surveys.Question`) are **unchanged** — the FK target still exists.
- Per-type parse logic stays duplicated across `survey_detail` and
  `autosave_survey` (kept in sync); not refactored in this change.

## 4. Migration strategy

This is pre-production seed data, so we **reset migrations** rather than write
data-preserving migrations.

- Delete and regenerate `apps/surveys/migrations` and
  `apps/responses/migrations` to a fresh `0001_initial` against the new schema.
- Existing survey/response rows are dropped (approved). Re-seed via
  `seed_nom035_survey`.
- `accounts` migrations are untouched except where they referenced surveys
  (they do not).

## 5. Dead-code removal & simplification

Driven by "operators seed fixed instruments" — the interactive authoring CLI is
obsolete.

**Delete:**
- `apps/core/workflows/` — `survey.py`, `question.py`, `question_template.py`,
  `choices.py`, `sections.py`, `version_helpers.py`, `introspect.py` (and
  `prompts.py` if nothing else uses it — verify; it's terminal-only authoring I/O).
- Commands: `create_survey`, `create_question`, `manage_sections`,
  `manage_question_templates`, `manage_choices`, `seed_likert_templates`,
  `seed_demographic_templates`.
- `templates/admin/surveys/stamp_into_version.html`.
- The "stamp into version" admin action and library admin in
  `apps/surveys/admin.py`.

**Rewrite:**
- `seed_nom035_survey` — build `Survey → Module → Question → Choice` directly from
  a declarative data source (a Python/JSON data module holding Guía I/II/III items
  with stable `code`s). Single source of truth for the instrument.
- `apps/surveys/admin.py` — register the flat models (`Survey`, `Module`,
  `Question`, `Choice`, `SurveyAssignment`) for inspection; no authoring actions.
- `apps/core/views.py` + `templates/core/employee_list.html`,
  `employee_detail.html`, `company_dashboard.html` — replace `version`/`section`
  references with `survey`/`module`; preserve the existing N+1-avoidance
  prefetch/annotate pattern.
- `conftest.py` — rebuild the survey-chain fixtures for the new tree
  (survey + modules + questions + assignment with variant).

**General:** remove any now-unreferenced imports/helpers surfaced after the above;
prefer deleting over leaving dead branches.

## 6. Documentation

- **Update (active):**
  - `apps/surveys/CLAUDE.md` — replace the template→version→stamp section with the
    Survey→Module→Question model, `applies_to`, `variant`, `visible_when`, `code`.
  - `apps/core/CLAUDE.md` — remove the authoring-workflows/commands section; keep
    web views; document the single `seed_nom035_survey` command.
  - `apps/responses/CLAUDE.md` — adjust references (FK target unchanged; remove
    version mentions).
  - `.claude/CLAUDE.md` — update the "Survey data flow" cross-cutting bullet
    (drop stamping/versioning; describe modules + variant).
- **Archive (outdated):** move superseded design/explainer docs to `docs/archive/`
  (preserving relative path under it). Candidates: any platform/internal doc that
  describes the template/version/stamping model or the interactive authoring CLI.
  Audit `docs/` during implementation; move rather than delete so history of
  intent is kept. The NOM-035 roadmap (`hoja-de-ruta-nom035.md`) stays active.

## 7. Testing

- **Model:** variant resolution (`resolve_default_variant` across the threshold);
  `visible_when` evaluation — single-answer gate and `any_in_module` aggregate;
  completeness ignoring hidden questions.
- **Views:** take / autosave / submit for a `small` assignment and a `large`
  assignment (correct module set shown); Guía I skip path (all "No" ⇒ rest hidden
  ⇒ submission can complete); gated blocks (`clientes`, `jefe`).
- **Seed smoke test:** `seed_nom035_survey` produces one `nom035` survey with
  Module 1 (`all`) + Module 2 (`small`) + Module 3 (`large`), expected question
  counts, and unique `code`s per survey.

## 8. Out of scope (named, not built)

Scoring / NDR engine, dimensión/dominio/categoría config, threshold tables, the
representative-sample math (`_representative_minimum` already lives in
`apps/core`), the PDF report, and the second survey itself. The model is built to
not block any of these — chiefly via stable `Question.code` and the
survey-agnostic `visible_when`.
