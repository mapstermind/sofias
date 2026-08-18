# Survey model

How SOFIA-S represents survey instruments and presents them to respondents.
Surveys are **fixed instruments** (NOM-035 today, an unrelated second survey
later): operators seed them once and rarely change them. The decision to drop the
former library/version/stamping authoring model in favor of this one is recorded
in [`docs/adr/adr-0002-flatten-survey-authoring-model.md`](../adr/adr-0002-flatten-survey-authoring-model.md).

## The instrument: Survey → Module → Question → Choice

A survey is a direct ownership tree. There is no reusable question library, no
numbered versions, and no copy-on-stamp; a material change to a published
instrument is made by creating a **new** `Survey`.

- **`Survey`** — the instrument. `key` (stable unique slug, e.g. `nom035`),
  `title`, `description`, `status` (draft/published/archived), and
  `headcount_threshold` (default 50).
- **`Module`** — an ordered group of questions.
  `applies_to` is `all`, `small`, or `large`; `key` is unique per survey;
  `visible_when` is an optional branching rule.
- **`Question`** — owned by a `Module`. Carries a stable `code` (unique per
  survey), `question_type`, `text`, `config`, and an optional `visible_when`. A
  denormalized `survey` FK (kept in sync in `save()`) backs the per-survey `code`
  uniqueness constraint.
- **`Choice`** — selectable option for `single_choice`/`multiple_choice`
  questions. (Boolean Sí/No renders from fixed radios, not `Choice` rows.)
- **`SurveyAssignment`** — links a `Survey` to a `Company` with a frozen
  `variant`. The company-level campaign through which all submissions flow.

## NOM-035 is modular

NOM-035 ships as three reference guides, which map onto module applicability
(see `docs/internal/Guias de Referencia.md`):

| Guide | Items | `applies_to` | Type | Scored into NDR? |
|---|---|---|---|---|
| Guía I — Acontecimientos traumáticos severos | 15 | `all` | boolean (Sí/No) | No — produces a clinical-referral flag via its own rules |
| Guía II — Factores de riesgo psicosocial | 46 | `small` | likert (Siempre…Nunca) | Yes |
| Guía III — … y entorno organizacional | 72 | `large` | likert | Yes |

Guía I is identical for everyone; a respondent receives Guía I plus **either**
Guía II **or** Guía III, selected by company size. The instrument is seeded
declaratively by `python manage.py seed_nom035_survey` (data in
`apps/core/management/commands/_nom035_data.py`).

## Variant selection

When a `SurveyAssignment` is created, the default variant is computed from the
company's headcount (`company.members.count()`) versus `survey.headcount_threshold`
— greater than the threshold → `large`, otherwise `small`
(`SurveyAssignment.resolve_default_variant`). The operator may override it, and
the chosen value is **frozen on the assignment**, so a later headcount change does
not alter an in-flight or historical assignment.

At take-time the respondent sees `assignment.modules_for_variant()` — modules
tagged `all` plus those matching the assignment's variant.

## Conditional visibility

NOM-035 has intrinsic branching: Guía I skips its follow-up questions when the
trigger is answered "No"; Guía II/III gate the "atiendo clientes" and "soy jefe"
blocks. This is expressed by a generic JSON `visible_when` rule on `Module` and
`Question`, evaluated by `apps/surveys/visibility.py` — the single source of truth
used by both server-side completeness logic and the client mirror in
`static/ts/survey_progress.ts`. Forms:

- `{"question": "<code>", "equals": <value>}` — single-answer gate.
- `{"any_in_module": "<module key>", "equals": <value>}` — module aggregate.

A null/empty rule means always visible. Completion requires every **visible**
question to be answered; hidden questions never block it, and `_normalize`
loosely coerces `"si"/"true"` etc. to booleans so rules match boolean answers.

## Taking a survey and storing answers

`apps/surveys/views.py` renders the variant's modules and handles submission:
`survey_detail` (form + POST), `autosave_survey` (AJAX field saves), and
`survey_submitted` (the acknowledgement page). `_parse_value` is the shared
per-type parser used by both POST paths. Answers persist in `apps/responses`
(`SurveySubmission` one-per-(user, assignment); `Answer` FK to `surveys.Question`,
JSON value typed by `question_type`). `apps/core` reads these for dashboards and
per-employee progress.

### Confirming a submission

A `COMPLETED` submission is final — `survey_detail` redirects a respondent who
already has one to `core:home`, so there is no way back into the form. Locking it
therefore takes **two independent keys**: the server finding every visible
question answered, *and* an explicit `confirm` in the POST. Answering the last
question does not lock anything by itself, and a `confirm` posted against a
half-filled form only saves progress.

Every POST saves the answers first, then routes on those two keys:

| Every visible question answered | `confirm` posted | Result |
| --- | --- | --- |
| no | either | `IN_PROGRESS` → redirect `?saved=1` |
| yes | no | `IN_PROGRESS` → redirect `?confirm=1` |
| yes | yes | `COMPLETED` → redirect to `survey_submitted` |

`?confirm=1` re-renders the form with the confirmation modal
(`_submit_confirm_modal.html`) open, warning that submitting is irreversible. Its
"Enviar respuestas" button is a `form="survey-form"` submit carrying
`name="confirm"`, so accepting reposts the whole form; "Seguir editando" just
closes the modal, since the answers are already saved. Abandoning the page at
this point leaves the submission `IN_PROGRESS` with everything stored, and the
next save offers the same confirmation.

Both query parameters are *intents*, not state: the URL outlives the POST that
set it, via the back button, a reload, or hand-editing. `survey_detail` therefore
re-checks each against the stored answers before opening a modal — `show_confirm`
requires the progress count to actually be complete, and `show_saved` requires a
submission to exist. Neither parameter can change data; the POST body is the only
thing that completes a submission.

### Who may answer an assignment

A respondent must hold `can_take_assigned_surveys` and have an **activated**
profile linked to a company, and the assignment must belong to **that** company.
All three views resolve the caller's company first and filter the assignment
lookup by it, so an assignment id belonging to another client is
indistinguishable from one that does not exist — the id space cannot be walked to
reach another company's survey.

`RequireProfileActivationMiddleware` already turns unactivated users away before
they reach these views; the activation condition is repeated here so the survey
path stays correct on its own rather than depending on middleware ordering.

This is a tenancy guarantee rather than a convenience. `SurveySubmission` rows
feed `apps/nom035`, which rolls them up per company: a submission written against
the wrong assignment would silently contaminate another client's NOM-035 results,
and nothing downstream could tell it apart from a legitimate one. `apps/nom035`
independently refuses to label a score with an área from a different company, but
that guard only cleans up a display symptom — the boundary is enforced here.

Admins hold no `can_take_assigned_surveys` and have no profile, so they cannot
open a survey at all; there is no operator preview path today.

## The scoring boundary

`apps/surveys` stores **no scoring** — no inverted flags, no
dimensión/dominio/categoría grouping, no threshold tables. `Question.code` is the
stable integration key consumed by the valuation engine, which holds that
configuration as data, keyed by `code`. For NOM-035 that engine lives in
`apps/nom035` (see `docs/platform/nom-035-analytics.md`); a future instrument would
get its own engine app rather than adding scoring here.

## Out of scope

The static PDF report and the second survey instrument remain unbuilt; the
representative-sample math already lives in `apps/core`. The NOM-035 scoring / NDR
engine (dimensión/dominio/categoría config and thresholds) is implemented in
`apps/nom035`, deliberately outside `apps/surveys`. The survey model is built not to
block any of these — chiefly via the stable `Question.code` and the survey-agnostic
`visible_when`.
