# NOM-035 Analytics (Valuation Engine)

## Status

Current — implemented in `apps/nom035`.

## What this does

SOFIA-S turns raw NOM-035 survey answers into a **valuation**: each scored answer
becomes a number, those numbers roll up into a **Nivel de Riesgo (NDR)** per
Dominio, Categoría and a final overall score, and the Guía I answers yield two
stored flags — whether a severe traumatic event occurred, and whether the worker
requires clinical valuation. This document covers that engine (`apps/nom035`):
how answers become stored scores, and the one per-employee read built on them.

Results are presented in two places, both readable only by roles holding
`can_view_insights`: the company-level **Resultados** page, described in
[`nom-035-results-dashboard.md`](./nom-035-results-dashboard.md), and the
**"Valoración de resultados"** card on the employee-detail page, described under
[Presentation](#presentation). Employees never see their own results. The
platform surfaces no prescriptive "necesidad de acción" verdict anywhere.

NDR levels follow the official NOM-035 tables, which define thresholds only at the
**dominio, categoría and final** levels. Dimensión organizes items within the
taxonomy but is **not** assigned an NDR — the standard publishes no per-dimensión
threshold table.

All scoring reference data (inverted items, taxonomy, threshold tables) and the
Guía I referral rule are transcribed from the single source of truth,
[`docs/internal/Guias de Referencia.md`](../internal/Guias%20de%20Referencia.md)
(Guía II and Guía III). Stakeholder-facing tracking of the scoring assumptions
lives in Spanish at
[`docs/platform/nom-035-valoracion-supuestos.md`](./nom-035-valoracion-supuestos.md).

## How it works

### The app

`apps/nom035` is a dedicated, **NOM-035-specific** app (`AppConfig` with
`name="apps.nom035"`, `label="nom035"`, registered in `INSTALLED_APPS`). A future
second instrument would get its own app rather than being generalized into this
one (see
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
  each NDR level, transcribed with the tables; no page displays it.
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

### Guía I — traumatic event and referral flags

Guía I is **not** scored into the NDR. Its 15 boolean items produce two stored
flags, following the official NOM-035 clinical-referral rule (Guías de
Referencia, "Interpretación … Guía de Referencia I"):

- **`guia1_event`** — the trigger question (`g1-1`, Sección I) was answered "Sí":
  a severe traumatic event occurred.
- **`guia1_positive`** — given the event, the worker is **positive** when any
  section threshold is met: any "Sí" in Section II (`g1-2…g1-3`), **or** ≥3 "Sí"
  in Section III (`g1-4…g1-10`), **or** ≥2 "Sí" in Section IV (`g1-11…g1-15`).
  Without the event it is `False`, so `guia1_positive` implies `guia1_event`.

The two flags give three outcomes — no event, an event not requiring valuation,
and a positive referral — which the results page counts. A positive result
surfaces on the employee-detail card as **"Usuario positivo a un acontecimiento
traumático severo."** and indicates the worker requires clinical valuation. There
is **no severity gradient** — the standard defines a binary referral outcome.

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

### Reads

`apps/nom035/aggregates.py` holds one on-demand read:

- **`employee_valuation(user, company)`** — the user's latest scored submission
  in that company as a nested categoría→dominio→dimensión tree with scores (no
  action text), plus the final NDR + score and the `guia1_positive` flag.

Company-level reads — distributions, statistics, participation and Guía I
outcomes for one assignment and one filtered group — live in
`apps/nom035/results.py` and are described in
[`nom-035-results-dashboard.md`](./nom-035-results-dashboard.md). Neither kind of
read is materialized: both are computed on demand from the stored per-submission
rows (cheap and always consistent as employees complete).

### Presentation

The **employee card** is the "Valoración de resultados" section of
`templates/core/employee_detail.html`: the final NDR + score as a colored badge,
then an indented hierarchy — Categoría (bold, score + colored NDR badge) →
Dominio (score + NDR badge) → Dimensión (score only, muted — no NDR, per the
scoring rule above). The Guía I message shows only when `guia1_positive` is true.
There is no action-sentence verdict on the card (see Key decisions).

NDR colors are centralized in one place —
`apps/core/templatetags/valuation_extras.py` (`ndr_badge` for pill badges,
`ndr_bar` for bar segments and legend swatches, `ndr_fill` for SVG chart marks,
`ndr_scale` for the ordinal five-step scale) — so no color literals are scattered
across templates: Nulo → gris, Bajo → verde, Medio → ámbar, Alto → naranja,
Muy alto → rojo.

Progress/assignment rows elsewhere in `core` display the assignment's variant as
**"Guía II"** or **"Guía III"** (`SurveyAssignment.Variant`'s labels), so admins
can see at a glance which guía a company's employees were assigned.

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
| `constants.py` | Shared constants: NDR levels and labels, categoría/dominio/dimensión group levels, `MIN_GROUP_SIZE` |
| `_nom035_scoring.py` | Scoring config as data (taxonomy, inverted items, thresholds, action text, Guía I sections) + accessor functions |
| `scoring.py` | Pure functions (`likert_item_score`, `classify`, `guia1_positive`, `score_submission`) + the `ScoreResult`/`GroupResult` dataclasses (`ScoreResult` carries `guia1_positive` and `guia1_event`) |
| `services.py` | `materialize()` — transactional upsert of the result rows |
| `signals.py` | `post_save` receiver on `responses.SurveySubmission` |
| `aggregates.py` | On-demand `employee_valuation` (the employee card) |
| `results.py` | Company-level results for one assignment — see [`nom-035-results-dashboard.md`](./nom-035-results-dashboard.md) |
| `models.py` | `SubmissionScore`, `GroupScore` |
| `admin.py` | Read-only `SubmissionScore` admin with an inline `GroupScore` |
| `management/commands/recompute_nom035_scores.py` | Backfill / refresh command |
| `migrations/` | Result-model schema |
| `tests/` | Engine unit tests + known-case validation |

### Integration points in `core`

`EmployeeDetailView` (`apps/core/views.py`) calls `employee_valuation` **only
when the caller has `can_view_insights`** and passes the result to
`templates/core/employee_detail.html`. The company-level results page and its
routes are described in
[`nom-035-results-dashboard.md`](./nom-035-results-dashboard.md).
`Question.code` remains the integration key between the instrument and the
engine — `apps/surveys` and `apps/responses` know nothing of scoring.

## Schema

Two tables in `apps/nom035`:

**`SubmissionScore`** — one row per scored submission.

| Field | Type | Notes |
|---|---|---|
| `submission` | `OneToOneField(responses.SurveySubmission, on_delete=CASCADE, related_name="nom035_score")` | The scored submission (incl. one whose `user` went null because the employee was deleted) |
| `final_score` | `IntegerField` | `Cfinal` |
| `final_ndr` | `CharField(choices=NDR)` | Nulo / Bajo / Medio / Alto / Muy alto |
| `guia1_positive` | `BooleanField` | Official Guía I clinical-referral outcome (binary) |
| `guia1_event` | `BooleanField` | Guía I Sección I (`g1-1`) answered "Sí" — a severe traumatic event occurred; true whenever `guia1_positive` is |
| `computed_at` | `DateTimeField(auto_now=True)` | Last materialization |

**`GroupScore`** — per-grouping breakdown for a submission. Alongside categoría and
dominio rows, it also stores a **dimensión** row per dimensión (`level="dimension"`,
score-only — `ndr` is left blank since the standard defines no per-dimensión
threshold table).

| Field | Type | Notes |
|---|---|---|
| `submission_score` | `ForeignKey(SubmissionScore, on_delete=CASCADE, related_name="groups")` | |
| `level` | `CharField(choices)` | `categoria` / `dominio` / `dimension` (dimensión is score-only, no NDR) |
| `key` | `CharField` | Stable group identifier from the taxonomy |
| `score` | `IntegerField` | Summed score for the group |
| `ndr` | `CharField(choices=NDR)` | Group NDR |

`unique_together = (submission_score, level, key)`; indexes on
`(submission_score, level)` for the per-employee card and `(level, ndr)` for
company-level reads.

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
- **Compute company-level reads on demand** from stored rows rather than materializing
  them. They change as each employee completes, so deriving them keeps results
  consistent with no invalidation logic.
- **Guía I yields a binary referral flag plus a stored event flag**, separate from
  the NDR. Guía I is a clinical-referral screen with a defined binary outcome, not
  a psychosocial score; the norm publishes no severity gradient. The event flag is
  stored like the referral flag so company-level reads count outcomes without
  touching the `Answer` table.
- **No per-dimensión NDR.** The official tables define thresholds only at
  dominio/categoría/final; dimensión is materialized score-only to support the
  per-employee panel.
- **No action text on the employee card.** The per-employee tree
  (`employee_valuation`) carries scores only. The official NOM-035 criteria
  (*Programa de intervención*, *política de prevención*) are defined at the
  área/centro-de-trabajo level, not the individual, so a per-person "necesidad de
  acción" verdict would misrepresent what the platform (and the SME operating it)
  is entitled to conclude about a named employee.
- **NDR colors centralized in one template-filter module**
  (`apps/core/templatetags/valuation_extras.py`), not literal Tailwind classes
  scattered per template, so the Nulo/Bajo/Medio/Alto/Muy alto ramp stays a
  single source of truth for the employee card and the results page's charts.
- **Results visible only to `can_view_insights` roles**; employees do not see their
  own results (NOM-035 confidentiality and existing permission gating).
- **UI heading is "Valoración de resultados" but the permission codename stays
  `can_view_insights`** — avoids a permissions migration and `bootstrap_groups` churn
  for a cosmetic change.

## Scope boundaries

**In scope:** the `apps/nom035` valuation engine (categoría/dominio/dimensión,
including dimensión score-only materialization, the Guía I event and referral
flags, and the `recompute_nom035_scores` backfill/refresh command); the NOM-035
scoring config; `employee_valuation`; and the employee-detail "Valoración de
resultados" card — the nested categoría→dominio→dimensión breakdown with NDR
badges — gated on `can_view_insights`.

**Out of scope:** company-level presentation — the results page, its filters,
charts and small-group rule, in scope for
[`nom-035-results-dashboard.md`](./nom-035-results-dashboard.md); the
downloadable/static PDF report (Iniciativa 2); an employee-facing self-view of
results; any operator UI for authoring scoring configuration; a second survey
instrument; and automatic generation of the Plan Bianual de Prevención.

## Linked ADRs

- [ADR-0003 — per-instrument survey-processing apps](../adr/adr-0003-per-instrument-survey-processing-apps.md)
  — the decision to build a NOM-035-specific engine in its own app rather than a
  generic configurable engine.
- [ADR-0002 — flatten survey authoring model](../adr/adr-0002-flatten-survey-authoring-model.md)
  — establishes `Question.code` as the stable integration key this engine consumes.
