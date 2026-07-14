# NOM-035 Analytics (Valuation Engine + Insights)

## Status

Shipped (MVP). Implemented in `apps/nom035`; results render in the `core`
dashboards.

## What this does

SOFIA-S turns raw NOM-035 survey answers into a **valuation**: each scored answer
becomes a number, those numbers roll up into a **Nivel de Riesgo (NDR)** per
Dominio, Categoría and a final overall score, and the results surface as
**text-only risk indicators** inside the _Insights_ panels of the company
dashboard and employee-detail pages, under the heading **"Valoración de
resultados"**.

The feature has two halves:

1. **The valuation engine** (`apps/nom035`) — computes and stores per-submission
   scores and NDR from `responses.Answer` rows, plus a separate Guía I
   (traumatic-events) clinical-referral flag.
2. **The presentation** — the "Valoración de resultados" panels, readable only by
   roles holding `can_view_insights`. Employees never see their own results.

NDR levels follow the official NOM-035 tables, which define thresholds only at the
**dominio, categoría and final** levels. Dimensión organizes items within the
taxonomy but is **not** assigned an NDR — the standard publishes no per-dimensión
threshold table.

All scoring reference data (inverted items, taxonomy, threshold tables) and the
Guía I referral rule are transcribed from the single source of truth,
[`docs/internal/roadmap_context/Guias de Referencia.md`](../internal/roadmap_context/Guias%20de%20Referencia.md)
(Guía II and Guía III). Stakeholder-facing tracking of the scoring assumptions
lives in Spanish at
[`docs/platform/nom-035-valoracion-supuestos.md`](./nom-035-valoracion-supuestos.md).

## How it works

### The app

`apps/nom035` is a dedicated, **NOM-035-specific** app (`AppConfig` with
`name="apps.nom035"`, `label="nom035"`, registered in `INSTALLED_APPS`). It was
created by repurposing the previously-empty `analytics` stub. A future second
instrument would get its own app rather than being generalized into this one (see
[ADR-0003](../adr/adr-0003-per-instrument-survey-processing-apps.md)).

### Scoring configuration (data as Python)

Because the engine is NOM-035-specific, its configuration lives as data in
`apps/nom035/_nom035_scoring.py` (mirroring the `apps/core/.../_nom035_data.py`
seed pattern), keyed by the stable `surveys.Question.code` (`g1-1…g1-15`,
`g2-1…g2-46`, `g3-1…g3-72`):

- **Taxonomy** — per-variant `dominio → item-numbers` maps (`_LARGE_DOMINIO_ITEMS`
  for Guía III, `_SMALL_DOMINIO_ITEMS` for Guía II) plus a shared
  `dominio → categoría` map, compiled into `{item code → (categoría, dominio)}`.
  Guía II has no "Entorno organizacional" categoría.
- **`INVERTED_ITEMS`** — the set of Likert item codes scored in reverse because they
  are positively worded.
- **Threshold tables** — per-variant band tables mapping a summed score to an NDR
  level (`{Nulo, Bajo, Medio, Alto, Muy alto}`) at the **final, categoría, and
  dominio** levels.
- **Action text** — the canonical "Necesidad de acción según NOM-035" string for
  each NDR level.
- **Guía I section codes** — the trigger question and the three section groupings
  the clinical-referral rule counts over.

Accessor functions (`taxonomy_for_variant`, `is_inverted`, `thresholds_for`,
`action_text`, `group_label`) expose this data to the engine. Shared string
constants (NDR levels, categoría/dominio group levels) live in
`apps/nom035/constants.py`. There are **no scoring-config database tables and no
config UI** — changing the configuration means editing these files and re-running
`recompute_nom035_scores`.

### Answer → score mapping

`surveys` stores Likert answers as integers **1–5** (`1 = Siempre … 5 = Nunca`) and
booleans as `true`/`false`. `likert_item_score` maps each scored Likert answer to
the NOM-035 0–4 scale:

- **Normal item:** `score = value − 1` (Siempre → 0 … Nunca → 4).
- **Inverted item:** `score = 5 − value` (Siempre → 4 … Nunca → 0).

Only **answered, visible** questions are scored; unanswered or
`visible_when`-hidden items contribute nothing. Question types other than `likert`
(scored into NDR) and `boolean` (Guía I) are ignored — NOM-035 has no others.

### Aggregation into NDR

`score_submission(submission)` (pure) returns a `ScoreResult` of
`GroupResult`s. For a completed submission it:

1. Scores each Likert item to 0–4.
2. Adds each item's score to its **Dominio**, its **Categoría**, and the **final**
   total (`Cfinal`) — categoría and final sums are accumulated directly from items,
   not re-summed from dominios.
3. Classifies each dominio, categoría and the final sum against the matching
   threshold band table (`classify`) to assign an NDR level.

### Guía I — traumatic-events referral flag

Guía I is **not** scored into the NDR. Its 15 boolean items produce a single
**binary** flag, `guia1_positive`, following the official NOM-035 clinical-referral
rule (Guías de Referencia, "Interpretación … Guía de Referencia I"):

- The trigger question (`g1-1`, Sección I) must be answered "Sí" — a severe
  traumatic event occurred; otherwise the flag is `False`.
- Given the event, the worker is **positive** when any section threshold is met: any
  "Sí" in Section II (`g1-2…g1-3`), **or** ≥3 "Sí" in Section III (`g1-4…g1-10`),
  **or** ≥2 "Sí" in Section IV (`g1-11…g1-15`).

A positive result surfaces on the employee-detail panel as **"Usuario positivo a un
acontecimiento traumático severo."** and indicates the worker requires clinical
valuation. There is **no severity gradient** — the standard defines a binary
referral outcome.

### When scoring runs (materialized)

Scores are **materialized**, not recomputed on every page load:

- A `post_save` receiver in `apps/nom035/signals.py` listens on
  `responses.SurveySubmission`. When a submission's `status` is `completed` **and**
  its survey is the NOM-035 instrument (`survey.key == "nom035"`), it calls
  `materialize(submission)`, which upserts the result rows inside a transaction
  (idempotent — safe to re-run). `apps/surveys` and `apps/responses` stay ignorant
  of scoring; the dependency points one way, from `nom035` to them.
- `python manage.py recompute_nom035_scores [--company <reference_code>]` backfills
  existing submissions and refreshes all scores after a configuration change.

### Reads and aggregation

`apps/nom035/aggregates.py` exposes two on-demand read helpers consumed by
`apps/core` views:

- **`employee_valuation(user, company)`** — the latest scored submission for the
  user, as display text: final NDR + score + action, per-categoría NDRs with action
  text, and the `guia1_positive` flag.
- **`company_valuation(company)`** — the company roll-up: count of scored
  submissions, the NDR distribution, a "needing action" count (submissions whose
  final NDR is Alto or Muy alto), and the count of Guía I-positive workers.

Company-level figures are **not** materialized — they are computed on demand from
the stored per-submission rows (cheap and always consistent as employees complete).

### Known limitation — skipped conditional blocks

A respondent who skips a conditional block (e.g. not a jefe, or does not attend
clientes) leaves those items absent. The MVP sums only the present items but still
compares against the full fixed threshold tables — a known scoring bias, flagged for
the domain expert in
[`nom-035-valoracion-supuestos.md`](./nom-035-valoracion-supuestos.md).

## Where the code lives

### `apps/nom035/`

| Path | Role |
|---|---|
| `apps.py` | `AppConfig` (`name="apps.nom035"`, `label="nom035"`); connects the scoring signal in `ready()` |
| `constants.py` | Shared string constants: NDR levels and categoría/dominio group levels |
| `_nom035_scoring.py` | Scoring config as data (taxonomy, inverted items, thresholds, action text, Guía I sections) + accessor functions |
| `scoring.py` | Pure functions (`likert_item_score`, `classify`, `guia1_positive`, `score_submission`) + the `ScoreResult`/`GroupResult` dataclasses |
| `services.py` | `materialize()` — transactional upsert of the result rows |
| `signals.py` | `post_save` receiver on `responses.SurveySubmission` |
| `aggregates.py` | On-demand `employee_valuation` / `company_valuation` helpers |
| `models.py` | `SubmissionScore`, `GroupScore` |
| `admin.py` | Read-only `SubmissionScore` admin with an inline `GroupScore` |
| `management/commands/recompute_nom035_scores.py` | Backfill / refresh command |
| `migrations/` | Result-model schema |
| `tests/` | Engine unit tests + known-case validation |

### Integration points in `core`

`CompanyDashboardView` and `EmployeeDetailView` (`apps/core/views.py`) call the
`apps/nom035` aggregate helpers **only when the caller has `can_view_insights`**,
and pass the result to context. The "Valoración de resultados" panels live in
`templates/core/company_dashboard.html` and `templates/core/employee_detail.html`.

### Routes

**No new routes.** Results render inside the existing `core` pages:
`CompanyDashboardView` (`/tablero-empresa/`, `/empresas/<reference_code>/`) and
`EmployeeDetailView`. Both panels are gated on `accounts.can_view_insights`, so
employees never see scored results. `Question.code` remains the integration key
between the instrument and the engine — no changes to `apps/surveys` or
`apps/responses`.

## Schema

Two tables in `apps/nom035`:

**`SubmissionScore`** — one row per scored submission.

| Field | Type | Notes |
|---|---|---|
| `submission` | `OneToOneField(responses.SurveySubmission, on_delete=CASCADE, related_name="nom035_score")` | The scored submission (incl. one whose `user` went null because the employee was deleted) |
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

`unique_together = (submission_score, level, key)`; indexes on
`(submission_score, level)` for the per-employee panel and `(level, ndr)` for
company aggregation.

## Key decisions

- **NOM-035-specific engine in its own app**, not a generic configurable engine. A
  generic engine + config tables/UI is unneeded scope today; a future instrument can
  get its own app without entangling this one. (See ADR-0003.)
- **Scoring configuration as Python data**, not database tables. With a single fixed
  instrument, in-code data is the simplest source of truth and needs no
  migration/seed to evolve.
- **Materialize per-submission scores via a `post_save` signal** on `SurveySubmission`
  (scoped to the NOM-035 survey), with a recompute command for backfill/refresh.
  Keeps dashboards cheap, gives stored results to aggregate over, and keeps
  `surveys`/`responses` unaware of scoring (one-way dependency).
- **Compute company aggregates on demand** from stored rows rather than materializing
  them. They change as each employee completes, so deriving them keeps results
  consistent with no invalidation logic.
- **Guía I yields a single binary referral flag** from the official section-based
  clinical rule, separate from the NDR. Guía I is a clinical-referral screen with a
  defined binary outcome, not a psychosocial score; the norm publishes no severity
  gradient.
- **No per-dimensión NDR.** The official tables define thresholds only at
  dominio/categoría/final.
- **Results visible only to `can_view_insights` roles**; employees do not see their
  own results (NOM-035 confidentiality and existing permission gating).
- **UI heading is "Valoración de resultados" but the permission codename stays
  `can_view_insights`** — avoids a permissions migration and `bootstrap_groups` churn
  for a cosmetic change.

## Scope boundaries

**In scope:** the `apps/nom035` valuation engine; materialized `SubmissionScore` /
`GroupScore`; the scoring signal and `recompute_nom035_scores` command; on-demand
company aggregation; the NOM-035 scoring config; and the **text-only** "Valoración
de resultados" panels in the company-dashboard and employee-detail pages.

**Out of scope:** interactive charts/graphs; the downloadable/static PDF report
(Iniciativa 2); an employee-facing self-view of results; any operator UI for
authoring scoring configuration; a second survey instrument; and automatic
generation of the Plan Bianual de Prevención.

## Linked ADRs

- [ADR-0003 — per-instrument survey-processing apps](../adr/adr-0003-per-instrument-survey-processing-apps.md)
  — the decision to build a NOM-035-specific engine in its own app rather than a
  generic configurable engine.
- [ADR-0002 — flatten survey authoring model](../adr/adr-0002-flatten-survey-authoring-model.md)
  — establishes `Question.code` as the stable integration key this engine consumes.
