# NOM-035 Analytics (Valuation Engine + Insights)

## Status

Accepted — design complete, MVP.

## What this does

SOFIA-S turns raw NOM-035 survey answers into a **valuation**: each scored answer
becomes a number, those numbers roll up into a **Nivel de Riesgo (NDR)** per
Dominio, Categoría and a final overall score, and the results surface as
**text-only risk indicators** inside the existing _Insights_ panels.

> **NDR levels follow the official NOM-035 tables, which define thresholds only at
> the dominio, categoría and final levels.** Dimensión is used to *organize* items
> within the taxonomy but is **not** assigned an NDR (the standard publishes no
> per-dimensión threshold table). See the supuestos doc for the validation note.

The work has two halves:

1. **The valuation engine** (`apps/nom035`) — computes and stores per-submission
   scores and NDR from `responses.Answer` rows, plus a separate Guía I
   (traumatic-events) referral flag.
2. **The presentation** — replaces the placeholder _Insights_ sections in the
   company dashboard and employee-detail pages with text indicators (heading:
   **"Valoración de resultados"**), readable only by roles holding
   `can_view_insights`.

Charts, the downloadable/PDF report, an employee self-view, and any
operator-facing scoring-config UI are **out of scope** (see
[Scope boundaries](#scope-boundaries)).

> The scoring reference data (inverted items, taxonomy, threshold tables) and the
> Guía I referral rule are transcribed from the single source of truth,
> `docs/internal/roadmap_context/Guias de Referencia.md`. Remaining open points for
> the domain expert (chiefly how to treat skipped conditional blocks) are tracked in
> Spanish at
> [`docs/platform/nom-035-valoracion-supuestos.md`](./nom-035-valoracion-supuestos.md)
> and kept in sync as the feature evolves.

## How it works

### The app

The previously-empty `apps/analytics` stub is **renamed to `apps/nom035`** and
registered: `apps.nom035.apps.AppConfig` uses `name = "apps.nom035"` with an
explicit short `label = "nom035"`, and `"apps.nom035"` is added to
`INSTALLED_APPS`. The app is NOM-035-specific by design; a future second instrument
would get its own app rather than being generalized into this one.

### Scoring configuration (data as Python constants)

Because the engine is NOM-035-specific, its configuration lives as constants in
`apps/nom035/_nom035_scoring.py` (mirroring the existing
`apps/core/management/commands/_nom035_data.py` pattern), all keyed by the stable
`surveys.Question.code` (`g1-1…g1-15`, `g2-1…g2-46`, `g3-1…g3-72`):

- **`INVERTED_ITEMS`** — the set of Likert item codes that are scored in reverse
  because they are positively worded.
- **`TAXONOMY`** — `item code → (Categoría, Dominio)`, defined separately for the
  Guía II (small) and Guía III (large) variants. (The taxonomy source is organized
  by dimensión for traceability, but dimensión is not scored — see the note above.)
- **`THRESHOLDS`** — band tables mapping a summed score to an NDR level
  (`{Nulo, Bajo, Medio, Alto, Muy alto}`) at the **final, categoría, and dominio**
  levels. Guía II and Guía III have distinct tables.
- **`ACTION_TEXT`** — the canonical "Necesidad de acción según NOM-035" string for
  each NDR level.

There are **no scoring-config database tables and no admin UI**. Changing the
configuration means editing these constants and re-running the recompute command.

### Answer → score mapping

`surveys` stores Likert answers as integers **1–5** (`1 = Siempre … 5 = Nunca`) and
booleans as `true`/`false`. The engine maps each scored Likert answer to the
NOM-035 0–4 scale:

- **Normal item:** `score = value − 1` (Siempre → 0 … Nunca → 4).
- **Inverted item:** `score = 5 − value` (Siempre → 4 … Nunca → 0).

Only **answered, visible** questions are scored; unanswered or
`visible_when`-hidden items contribute nothing. Question types other than `likert`
(scored into NDR) and `boolean` (Guía I) are ignored — NOM-035 has no others.

### Aggregation into NDR

For a completed submission the engine:

1. Scores each Likert item to 0–4.
2. Sums items into their **Dominios**, dominios into **Categorías**, and everything
   into the **final** score (`Cfinal`).
3. Classifies each dominio, categoría and final sum against the matching threshold
   table to assign an NDR level.

### Guía I — traumatic-events referral flag

Guía I is **not** scored into the NDR. Its 15 boolean items produce a single
**binary** flag, `guia1_positive`, following the official NOM-035 clinical-referral
rule (Guías de Referencia, "Interpretación … Guía de Referencia I"):

- The trigger question (`g1-1`, Sección I) must be answered "Sí" — a severe traumatic
  event occurred; otherwise the flag is `False`.
- Given the event, the worker is **positive** when any section threshold is met: any
  "Sí" in Section II (`g1-2…g1-3`), **or** ≥3 "Sí" in Section III (`g1-4…g1-10`),
  **or** ≥2 "Sí" in Section IV (`g1-11…g1-15`).

A positive result surfaces as the text **"Usuario positivo a un acontecimiento
traumático severo."** and indicates the worker requires clinical valuation. There is
**no severity gradient** — the standard defines a binary referral outcome.

### When scoring runs (materialized)

Scores are **materialized**, not recomputed on every page load:

- A `post_save` signal receiver in `apps/nom035` listens on
  `responses.SurveySubmission`. When a submission's `status` is `completed`, the
  receiver calls `materialize(submission)`, which upserts the result rows inside a
  transaction (idempotent — safe to re-run). `apps/surveys` and `apps/responses`
  stay ignorant of scoring; the dependency points one way, from `nom035` to them.
- `python manage.py recompute_nom035_scores [--company <reference_code>]` backfills
  existing submissions and refreshes all scores after a configuration change.

Company-level figures are **not** materialized — they are computed on demand from
the stored per-submission rows (cheap and always consistent).

## Affected files, modules, and routes

### New / renamed — `apps/nom035/`

| Path | Role |
|---|---|
| `apps/nom035/apps.py` | `AppConfig` (`name="apps.nom035"`, `label="nom035"`); connects the scoring signal in `ready()` |
| `apps/nom035/models.py` | `SubmissionScore`, `GroupScore` |
| `apps/nom035/_nom035_scoring.py` | Scoring config constants (inverted items, taxonomy, thresholds, action text, group labels) |
| `apps/nom035/scoring.py` | `score_submission()` (pure) + the `ScoreResult`/`GroupResult` dataclasses |
| `apps/nom035/services.py` | `materialize()` (transactional upsert of the result rows) |
| `apps/nom035/signals.py` | `post_save` receiver on `responses.SurveySubmission` |
| `apps/nom035/aggregates.py` | On-demand company/employee aggregation helpers |
| `apps/nom035/management/commands/recompute_nom035_scores.py` | Backfill / refresh command |
| `apps/nom035/migrations/` | Result-model schema (`0001_initial`, `0002_*`) |
| `apps/nom035/tests/` | Engine unit tests + known-case validation |
| `apps/nom035/CLAUDE.md` | Replaces `apps/analytics/CLAUDE.md` |

### Modified — existing apps

| Path | Change |
|---|---|
| `config/settings.py` | Add `"apps.nom035"` to `INSTALLED_APPS` (remove the never-registered analytics reference if present) |
| `apps/core/views.py` | `EmployeeDetailView` and `CompanyDashboardView` call `apps/nom035` helpers and add results to context (preserving the existing N+1-avoidance pattern) |
| `templates/core/employee_detail.html` | Replace the _Insights_ placeholder with the "Valoración de resultados" panel |
| `templates/core/company_dashboard.html` | Replace the _Insights_ placeholder with the "Valoración de resultados" panel |
| `.claude/CLAUDE.md`, `apps/reports/CLAUDE.md` | Update references from `analytics` to `nom035` |

### Routes

**No new routes.** Results render inside the existing `core` pages:
`CompanyDashboardView` (`/tablero-empresa/`, `/empresas/<reference_code>/`) and
`EmployeeDetailView`. Both panels remain gated on the existing
`accounts.can_view_insights` permission, so employees never see scored results.

## Schema changes

Two new tables in `apps/nom035` (migration `0001_initial`):

**`SubmissionScore`** — one row per scored submission.

| Field | Type | Notes |
|---|---|---|
| `submission` | `OneToOneField(responses.SurveySubmission, on_delete=CASCADE)` | The scored submission (incl. anonymous, `user=None`) |
| `final_score` | `IntegerField` | `Cfinal` |
| `final_ndr` | `CharField(choices=NDR)` | Nulo / Bajo / Medio / Alto / Muy alto |
| `guia1_positive` | `BooleanField` | Official Guía I clinical-referral outcome (binary) |
| `computed_at` | `DateTimeField(auto_now=True)` | Last materialization |

**`GroupScore`** — per-grouping breakdown for a submission.

| Field | Type | Notes |
|---|---|---|
| `submission_score` | `ForeignKey(SubmissionScore, on_delete=CASCADE, related_name="groups")` | |
| `level` | `CharField(choices)` | `categoria` / `dominio` (dimensión is not scored) |
| `key` | `CharField` | Stable group identifier from the taxonomy |
| `score` | `IntegerField` | Summed score for the group |
| `ndr` | `CharField(choices=NDR)` | Group NDR |

`unique_together = (submission_score, level, key)`; index on
`(submission_score, level)` for the per-employee panel and on `(level, ndr)` for
company aggregation.

No changes to `apps/surveys` or `apps/responses` schemas — `Question.code` remains
the integration key, exactly as documented in `docs/platform/survey-model.md`.

## Key decisions

- **Decision:** Build a NOM-035-specific engine in its own app (`apps/nom035`,
  renamed from the `analytics` stub), not a generic configurable engine.
  **Reason:** A generic engine + config tables/UI is unneeded scope today; a future
  instrument can get its own app without entangling this one.
- **Decision:** Hold scoring configuration as Python constants, not database
  tables. **Reason:** With a single fixed instrument, constants are the simplest
  source of truth and need no migration/seed to evolve.
- **Decision:** Materialize per-submission scores via a `post_save` signal on
  `SurveySubmission`, with a recompute command for backfill/refresh.
  **Reason:** Keeps dashboards cheap, gives stored results to aggregate over, and
  keeps `surveys`/`responses` unaware of scoring (one-way dependency).
- **Decision:** Compute company aggregates on demand from stored rows rather than
  materializing them. **Reason:** They change as each employee completes; deriving
  them keeps results consistent with no extra invalidation logic.
- **Decision:** Guía I yields a single **binary** referral flag from the official
  section-based clinical rule, separate from the NDR. **Reason:** Matches the
  standard (Guía I is a clinical-referral screen with a defined binary outcome, not
  a psychosocial score); the norm publishes no severity gradient.
- **Decision:** Results are visible only to `can_view_insights` roles; employees do
  not see their own results. **Reason:** NOM-035 confidentiality norms and the
  existing permission gating.
- **Decision:** Rename the UI heading to "Valoración de resultados" but keep the
  `can_view_insights` permission codename. **Reason:** Avoids a permissions
  migration and `bootstrap_groups` churn for a cosmetic change.

## Validation requirements and remaining assumptions

The scoring reference data is transcribed from the single source of truth,
`docs/internal/roadmap_context/Guias de Referencia.md`. The stakeholder-facing
tracking of assumptions (Spanish, free of implementation detail) lives in
[`docs/platform/nom-035-valoracion-supuestos.md`](./nom-035-valoracion-supuestos.md).
In summary:

1. **Guía II and Guía III** taxonomy, inverted items, and the
   **categoría/dominio/final** threshold tables are transcribed authoritatively from
   the source-of-truth document (Guía III also reconciles against `Ejemplo Reporte
   Resultados.pdf`).
2. **Dimensión is not assigned an NDR** — the official tables define thresholds only
   at dominio/categoría/final. Flagged for the expert in case per-dimensión scoring
   is later desired.
3. **Skipped conditional blocks** (a respondent who is not a jefe / does not attend
   clientes) leave their items absent. The MVP sums only present items but compares
   against the full fixed thresholds — a known bias, still open for the expert.
4. **Guía I** uses the official section-based binary referral rule from the source
   document; there is no invented severity gradient.
5. **At least one fully-worked example** (from `Ejemplo Reporte Resultados.pdf`) is
   still useful so an automated test can assert `Cfinal` and NDR against a known case.

## Scope boundaries

**In scope:** the `apps/nom035` valuation engine; materialized `SubmissionScore` /
`GroupScore`; the scoring signal and `recompute_nom035_scores` command; on-demand
company aggregation; the NOM-035 scoring config constants; and the **text-only**
"Valoración de resultados" panels in the company-dashboard and employee-detail
pages.

**Out of scope:** interactive charts/graphs; the downloadable/static PDF report
(Iniciativa 2); an employee-facing self-view of results; any operator UI for
authoring scoring configuration; a second survey instrument; and automatic
generation of the Plan Bianual de Prevención.

## Linked ADRs

- [`docs/adr/adr-0003-per-instrument-survey-processing-apps.md`](../adr/adr-0003-per-instrument-survey-processing-apps.md)
  — the decision to build a NOM-035-specific engine in its own app rather than a
  generic configurable engine.
- [`docs/adr/adr-0002-flatten-survey-authoring-model.md`](../adr/adr-0002-flatten-survey-authoring-model.md)
  — establishes `Question.code` as the stable integration key this engine consumes.
