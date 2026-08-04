# ADR-0002: Flatten the survey authoring model (drop the library + versioning + stamping layer)

Date: 2026-06-20
Status: Accepted

## Context

The survey authoring model was built around a reusable question library plus
copy-on-stamp versioning: `QuestionTemplate`/`ChoiceTemplate` (library) →
`SurveyTemplate` → `SurveyVersion` → `Section` → `Question` → `Choice`, with
`QuestionTemplate.stamp_into(version)` copying library items into immutable
numbered versions, and `SurveyAssignment` pointing at a version. This machinery
exists to support self-service authoring (reusable library, edits that never
mutate live surveys, version history). That is not how SOFIA-S is used: operators
seed a small number of **fixed instruments** (NOM-035 today, an unrelated second
survey later), surveys are rarely created and rarely modified, and a material
change is best handled by creating a new survey rather than versioning an existing
one. The layer therefore pays continuous complexity rent — across models, the
interactive authoring CLI in `apps/core/workflows/`, admin actions, templates, and
tests — for a use case that does not exist. We also need to model NOM-035's
modular structure (Guía I for everyone, plus Guía II *or* III by company
headcount) and its intrinsic conditional/branching logic, which the version model
does not address.

## Decision

Replace the library/version/stamping layer with a direct ownership tree
`Survey → Module → Question → Choice`. Modules carry an `applies_to`
(`all`/`small`/`large`) tag; the company's headcount selects a variant that is
**frozen on `SurveyAssignment`** (operator-overridable); conditional logic is a
generic data-driven `visible_when` rule on modules and questions; and each
question carries a stable `code` so the future valuation engine and reports can
reference items without the survey model owning any scoring. Material instrument
changes create a new `Survey`; there is no version chain. The interactive
authoring CLI is removed in favor of a single declarative `seed_nom035_survey`.
Full design: `docs/platform/survey-model.md`.

## Consequences

**Positive:**

- Each item (and later its scoring) is defined exactly once; the modular NOM-035
  instrument is expressed directly via `applies_to` rather than duplicated or
  stitched.
- Large net reduction in surface area: five model concepts collapse to four, and
  the entire `apps/core/workflows/` authoring CLI plus its `create_*`/`manage_*`/
  `seed_*template*` commands are deleted.
- Conditional branching becomes a first-class, survey-agnostic mechanism reusable
  by the future second survey.
- A stable `Question.code` gives the future valuation engine a clean integration
  point while keeping scoring out of `apps/surveys`.
- A frozen per-company `variant` keeps historical assignments stable even if
  headcount later changes.

**Negative:**

- Loss of built-in version history and copy-on-stamp isolation; correcting a
  published instrument means editing in place or seeding a new survey, with no
  automatic snapshot of the prior wording.
- No reusable question library; shared items across *different* surveys would be
  duplicated (acceptable — the two planned surveys are unrelated).
- Breaking schema change: `apps/surveys` and `apps/responses` migrations are
  reset and existing survey/response rows are dropped (pre-production; data is
  re-seeded). `Answer`'s FK target (`surveys.Question`) is preserved.
- `visible_when` introduces a small rule-evaluation engine that must stay
  consistent between server-side completeness checks and client-side show/hide.

## Alternatives considered

- **Keep the template/version/stamping model.** Already built and supports
  authoring/history. Rejected: it solves a self-service authoring problem SOFIA-S
  does not have, and pays that cost on every downstream feature.
- **Three separate surveys (module 1/2/3) stitched at presentation.** Models the
  modules as independent surveys concatenated in the UI. Rejected: a submission
  and a report would span multiple survey objects, pushing stitching complexity
  into every downstream read (progress, scoring, reports) forever.
- **Two full duplicated surveys (small / large).** Simpler to render. Rejected:
  the shared module is identical including scoring, so this duplicates content and
  valuation config and forces permanent two-way sync.
- **Keep numbered versions but drop only the library/stamping.** Retains history.
  Rejected: still carries version-chain machinery for instruments that change
  rarely and are better re-seeded as new surveys.

## Links

- Spec: `docs/platform/survey-model.md`
- Context: `docs/internal/Guias de Referencia.md`
- App docs: `apps/surveys/CLAUDE.md`, `apps/core/CLAUDE.md`,
  `apps/responses/CLAUDE.md`
