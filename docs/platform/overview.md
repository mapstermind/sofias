# System Overview

SOFIA-S is a Django web application for administering fixed survey instruments,
collecting responses, and turning them into per-company valuations and dashboards.
It is built around the Mexican **NOM-035** psychosocial-risk questionnaire, but the
survey-authoring layer is deliberately instrument-agnostic. User-facing copy and
URLs are Spanish; code and identifiers are English.

This document is the map of how the pieces fit. For the schema see
[`database.md`](./database.md); for a specific feature see its own doc in this
folder; for the reasoning behind a structural choice see the ADRs in `docs/adr/`.

## The apps

| App | Role | Registered |
|---|---|---|
| `accounts` | Custom user (email + OTP login), companies, roles/permissions, CSV import | ✅ |
| `surveys` | The **instrument authoring/structure base**: `Survey → Module → Question → Choice`, assignments, and survey-taking | ✅ |
| `responses` | Response storage: `SurveySubmission` + `Answer` | ✅ |
| `nom035` | The **NOM-035 valuation engine**: answers → scores → Nivel de Riesgo (NDR) + Guía I referral flag | ✅ |
| `core` | Home routing, company/employee dashboards, and the NOM-035 instrument seed | ✅ |
| `reports` | Placeholder for future exports/rendered reports built on `apps/nom035` | ❌ (stub) |

## Architectural shape: a shared base with per-instrument engines

The system is designed so that survey *structure* is generic and reusable, while
each instrument's *scoring and processing* is self-contained:

- **`apps/surveys` is the shared authoring base for every instrument.** It models
  `Survey → Module → Question` keyed by a stable `key` (per survey) and `code` (per
  question), with headcount-driven variants and data-driven `visible_when`
  branching. It stores **no scoring** — no inverted-item flags, no
  dimensión/dominio/categoría grouping, no thresholds. Nothing in `surveys` is
  NOM-035-specific.
- **Each instrument's scoring/processing lives in its own engine app.** For NOM-035
  that is `apps/nom035`. An engine depends on `surveys`/`responses` **one-way**,
  through the stable `Question.code` — the dependency never points back. The engine
  holds its configuration (taxonomy, inverted items, thresholds, referral rules) as
  instrument-specific data, not a generic config schema.
- **A future, unrelated second instrument gets its own engine app**
  (`apps/<instrument>`) rather than a generalization of `nom035`. If real
  duplication emerges across two engines, extracting a shared library is a later
  decision — not a framework built in advance. See
  [ADR-0003](../adr/adr-0003-per-instrument-survey-processing-apps.md).

This mirrors the fixed-instrument premise of
[ADR-0002](../adr/adr-0002-flatten-survey-authoring-model.md): a small number of
fixed instruments, seeded once and rarely changed, so generic authoring/scoring
frameworks are unwarranted standing complexity.

### Where the wrinkles are (current state)

Only **one** instrument (NOM-035) exists today, so the base+engine split is a
designed-for pattern validated once, not yet exercised across multiple instruments.
Two things do not live where the clean pattern would eventually put them:

- **The NOM-035 instrument definition/seed** lives in `apps/core`
  (`seed_nom035_survey`, data in `_nom035_data.py`), not in `surveys` or `nom035`.
- **Results presentation** (the text-only "Valoración de resultados" panels)
  currently renders in `apps/core` views and templates, calling `nom035`'s
  aggregate helpers. `apps/reports` is reserved as a future, dedicated reporting
  home but is an empty, unregistered stub today.

## End-to-end data flow

```
seed (apps/core)          →  Survey → Module → Question → Choice        (apps/surveys)
assign to a Company       →  SurveyAssignment (frozen variant by headcount)
employee takes the survey →  SurveySubmission + Answer (JSON, typed)     (apps/responses)
submission completed      →  post_save signal materializes scores        (apps/nom035)
                             SubmissionScore + GroupScore (per dominio/categoría)
view results              →  dashboards + valuation panels               (apps/core)
                             gated on can_view_insights
```

Company-level figures are aggregated on demand from the stored per-submission
scores; per-submission scores are materialized once on completion and re-buildable
with `python manage.py recompute_nom035_scores`.

## Cross-cutting concerns

- **Identity & auth** — custom `accounts.User`, email + passwordless OTP (password
  and setup-access-code fallbacks). See [`auth-and-onboarding.md`](./auth-and-onboarding.md).
- **Authorization** — custom permissions on the unmanaged `accounts.Role`, bundled
  into four groups by `python manage.py bootstrap_groups`. Views authorize on
  permission codenames (e.g. `can_view_dashboard`, `can_view_insights`).
- **Company isolation** — all response and valuation data traces back to a
  `SurveyAssignment` belonging to exactly one `Company`.

## Where to read next

- [`survey-model.md`](./survey-model.md) — the authoring base in detail.
- [`database.md`](./database.md) — full schema, including the `nom035` result tables.
- [`nom-035-analytics.md`](./nom-035-analytics.md) — the valuation engine and Insights panels.
- [`adr/adr-0002-…`](../adr/adr-0002-flatten-survey-authoring-model.md),
  [`adr/adr-0003-…`](../adr/adr-0003-per-instrument-survey-processing-apps.md) — the
  decisions behind the shape above.
