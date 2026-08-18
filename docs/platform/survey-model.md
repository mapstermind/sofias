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

### Finding what is left to answer

A respondent who skips a question and comes back to a 72-item form should not have
to hunt for it. `static/ts/survey_progress.ts` recomputes, on load and on every
`change`/`input`, the set of question cards that are **visible and unanswered** —
mirroring `visibility.py`, so a card gated out by `visible_when` is never counted
nor listed. That single set drives both the progress bar and the **Pendientes**
panel.

The panel is the last card in the sticky sidebar, below **Guardar progreso**. It
renders only while at least one visible question is unanswered and removes itself
once the count reaches zero. It lists the **first six** pending questions in
document order, each a button showing the question text clamped to two lines and
read straight out of that card's own `<label>` — the text is never duplicated into
a data attribute or a second context variable. When more than six remain, a
`y N más` line sits below the list and outside its scroll container, so the
remaining count is legible without scrolling. The list carries its own
viewport-relative height cap, which is what absorbs pressure on the sidebar's
vertical budget: the instructions card keeps its own cap, and the panel yields
rather than pushing the save button off-screen.

Clicking an entry scrolls its card to the centre of the viewport, flashes a ring
for 1.5 s, and moves keyboard focus to the card's first control. Focus moves
because scrolling alone leaves the tab order untouched — a keyboard or
screen-reader user would end up looking at the question without being in it. The
panel carries no `aria-live`: it rebuilds on every keystroke, and announcing each
rebuild would make it chatter continuously.

**Ir a la siguiente ↓** walks the pending set: it jumps to the first pending
question that *follows the last one jumped to* in document order, wrapping to the
top when there is none. The cursor is a document position and never a viewport
position — once the page is scrolled to its limit `scrollIntoView` cannot move it
further, so the final few cards hold a fixed screen position and any
"below the fold" test picks the same one forever while stranding its neighbours.
Comparing against the previous element rather than its index also survives the
respondent answering the question they jumped to: it leaves the pending set, and
the walk still resumes from where it left off.

Between the two controls nothing is unreachable: the six listed entries are the
*earliest* pending questions, which is exactly where a skipped one lands, and the
button covers the tail below the reader. A one-line hint under the heading says
the entries are selectable, since a hover state alone does not advertise it.

The panel is desktop-shaped. `survey_detail.html` lays the sidebar out as a fixed
`w-96` flex column with no breakpoint, so on a narrow viewport it overflows
horizontally along with the rest of that sidebar. The panel's own markup avoids
fixed pixel widths and uses viewport-relative caps, so a responsive pass can
re-place it without rewriting it.

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

`?saved=1` opens `_progress_saved_modal.html`, which names how many questions
are still unanswered — `survey_detail` passes `pending_count` alongside the
progress figures, and the modal states it in full (`Te falta 1 pregunta` /
`Te faltan 3 preguntas`, since the Spanish verb inflects with the noun). Saving is
the moment a respondent believes they are finished, so it is where the count has
to appear; the sentence is suppressed at `pending_count == 0`, which a stale
`?saved=1` in the URL can still produce.

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

The company dashboard's "Mi respuesta" card is gated on the viewer holding the
permission **and** having a profile in the company on screen, rather than on the
permission alone. A superuser satisfies every `perms.*` check a template makes
regardless of group, so the permission by itself would offer an admin a card
leading to a page the view turns them away from.

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
