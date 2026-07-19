# NOM-035 Valuation — Presentation Shift (Area-framed action, richer employee breakdown, visual pass)

## Status

Design (approved for planning). Date: 2026-07-18. Extends the shipped
[NOM-035 Analytics](./nom-035-analytics.md) feature; this is a **presentation and
aggregation** change, not a new instrument or a change to the scoring math. No ADR.

## Motivation

The platform admin (our SME) is **not entitled to act on individual employees** —
the questionnaire compiles data to analyze **areas/departments of the company**, not
to declare that a named person "requires analysis." Today the "necesidad de acción"
text renders on the **individual employee card**, which reads as a per-person verdict
("this person needs attention"). The official NOM-035 *Criterios para la toma de
acciones* are in fact **organizational** (they prescribe a *Programa de intervención*,
*política de prevención*, at the *centro de trabajo* level) — so this guidance was
always meant for the aggregate, not the individual.

At the same time, the employee-level breakdown is thin: it shows **categoría only**,
as a bare NDR label ("Muy Alto") with **no score**. The SME wants the individual view
to show results by **categoría, dominio and dimensión, with the numeric score**, and
the whole "Valoración de resultados" surface to be **visually clearer**.

## Goals

1. **Move the prescriptive action language off the individual and onto the aggregate**
   (per-area and company), phrased about the área/organización.
2. **Enrich the employee breakdown**: Categoría → Dominio → Dimensión, each with its
   numeric score; NDR (risk level) shown for categoría/dominio, score-only for
   dimensión.
3. **Introduce an area/department dimension** so risk can be aggregated and framed per
   area.
4. **A visual pass** on both "Valoración de resultados" surfaces so the data reads
   clearly (risk-colored badges, a nested hierarchy, per-area distribution bars).

Non-goals: changing the scoring formulas/thresholds; charts beyond simple
distribution bars; a downloadable PDF report; an employee-facing self-view; a second
instrument.

## Design

### 1. Area/department field (`apps/accounts`)

- Add `UserProfile.department` — free-text `CharField(max_length=255, blank=True)`,
  mirroring the existing free-text `position` (cargo). **No fixed enum and no
  per-company Department model**: area names vary between companies, the admin uploads
  already-cleaned data, and a managed list would add an unneeded management surface.
- `importers.py` (`import_users_from_csv`): accept an **optional** `department` CSV
  column. The column is **not** added to the required-headers set — CSVs without it
  keep importing (all-blank department). When present, its value is written to the
  profile.
- Expose `department` in the `UserProfile` admin for one-off edits.
- **Grouping normalization:** aggregation groups employees by
  `department.strip()` case-folded, displaying the first-seen original casing. A blank
  department falls into a **"Sin área"** bucket so no scored employee is dropped.
- Requires a **schema migration** (one new nullable/blank text column).

### 2. Dimensión scoring (`apps/nom035`)

The engine currently maps `{item code → (categoría, dominio)}` and materializes
categoría/dominio/final. To show dimensión scores:

- Extend the taxonomy to `{item code → (categoría, dominio, dimensión)}`, transcribing
  the **dimensión → items** grouping from the single source of truth
  (`Guias de Referencia.md`: Guía II lines ~183–204, Guía III lines ~454+). Item
  membership is unchanged — dimensión is a finer partition of the same items already
  assigned to each dominio.
- Add `LEVEL_DIMENSION = "dimension"` (`constants.py`) and
  `GroupLevel.DIMENSION` (`models.py`). Add dimensión display labels to the
  group-label map.
- `score_submission` also accumulates a per-dimensión sum and emits
  `GroupResult(level="dimension", key=<dim>, score=<sum>, ndr="")`. **Dimensión carries
  a score but no NDR** — the standard publishes no per-dimensión threshold table (empty
  string signals "no risk level").
- `services.materialize` stores the dimensión rows alongside categoría/dominio (same
  `GroupScore` table; `unique_together=(submission_score, level, key)` already
  accommodates the new level). The `GroupScore` table shape is unchanged — dimensión
  rows are just more rows — though adding a value to `GroupLevel.choices` makes Django
  emit a **state-only (no-op) migration** for the `level` field. A **data backfill** is
  required to populate dimensión rows on existing submissions:
  `recompute_nom035_scores` re-materializes them.
- `GroupScore.ndr` keeps its `choices`; dimensión rows store `ndr=""`. Confirm the
  field/tests tolerate the empty value (it is not one of the NDR choices, but blank is
  allowed for a `CharField`).

### 3. Reframing the action text (`apps/nom035`)

- **Reword `_ACTION_TEXT`** to área/organización-framed language, dropping the
  individual-sounding clause in the *Muy alto* entry ("…así como la atención clínica de
  los colaboradores que lo requieran"). The five levels stay keyed by NDR; the wording
  speaks about the área/centro de trabajo, e.g. *Muy alto* → "El área presenta
  colaboradores en nivel de riesgo muy alto; se requiere el análisis de cada categoría
  y dominio para establecer acciones de intervención a nivel del área o centro de
  trabajo." (Final wording drafted during implementation, staying faithful to the
  official *Criterios para la toma de acciones*.)
- **Remove the action text from the individual employee card entirely** (decision A):
  `employee_valuation` no longer returns `final_action` or per-categoría `action`, and
  the employee template drops the "necesidad de acción" sentence. The individual view
  keeps the final NDR + score as **data**, never a verdict.
- The reworded action text is surfaced **only at the aggregate level** (per-area and
  company), via §4.

### 4. Aggregation (`apps/nom035/aggregates.py`)

- **`employee_valuation(user, company)`** returns the full hierarchy instead of
  categoría-only:
  - `final_ndr` + `final_ndr_label` + `final_score` (kept; **no** `final_action`).
  - `categories`: each with `key`, `label`, `score`, `ndr`, `ndr_label`, and a nested
    `domains` list; each dominio with `key`, `label`, `score`, `ndr`, `ndr_label`, and
    a nested `dimensions` list; each dimensión with `key`, `label`, `score` (no NDR).
    Built from the stored `GroupScore` rows plus the taxonomy's dominio↔categoría and
    dimensión↔dominio parent relationships.
  - `guia1_positive` (kept — decision B).
- **`company_valuation(company)`** keeps its existing top-level roll-up and **adds a
  per-area breakdown**. For each area (grouped/normalized per §1):
  - `label` (display name, or "Sin área"), `scored_count`, NDR `distribution` +
    `distribution_rows`, `needing_action` (Alto/Muy alto), `guia1_positive_count`, and
    **one org-framed `action` line**.
  - **Area action rule (interim):** key the area's single action line to the
    **most-severe NDR present** among that area's scored employees, with the full
    distribution shown alongside for transparency. This is a product judgment (an area
    is a mix of levels); it is **flagged for the SME** in
    [`nom-035-valoracion-supuestos.md`](./nom-035-valoracion-supuestos.md) for later
    confirmation (proportion threshold vs. most-severe-present).
  - The existing company-wide figures remain; the company may also show an org-framed
    action line by the same most-severe-present rule.

### 5. Visual design (`apps/core` templates + Tailwind)

Applies to the two "Valoración de resultados" surfaces; keeps them inside the existing
pages (no new routes), gated on `can_view_insights` as today.

- **NDR color ramp**, centralized in **one place** (a template filter, e.g.
  `ndr_classes`, so no color literals are scattered across templates): Nulo → gris,
  Bajo → verde, Medio → ámbar, Alto → naranja, Muy alto → rojo. A small **legend**
  accompanies each surface.
- **Employee card** (`employee_detail.html`): an **indented hierarchy** —
  Categoría (bold, score + colored NDR badge) → Dominio (score + NDR badge) →
  Dimensión (score only, muted). Final NDR + score summarized at the top. The Guía I
  message shows **only when positive** (unchanged behavior). No action sentence.
- **Company dashboard** (`company_dashboard.html`): a **per-area** section — one
  row/card per area with a **stacked NDR distribution bar** (the five colors),
  headcount scored, needing-action count, Guía I count, and the org-framed action line.
  The existing company-wide summary stays.
- **Build step (mandatory):** new Tailwind classes render only after
  `npm run build:css`; commit the regenerated `static/css/output.css`. (Per project
  CLAUDE.md — a template class not already present compiles to nothing otherwise.)

## Data flow (unchanged spine, extended ends)

`responses.Answer` → `score_submission` (now also sums dimensión) →
`materialize` stores `SubmissionScore` + `GroupScore` (categoría/dominio/**dimensión**)
→ `aggregates.employee_valuation` (full hierarchy, no action) and
`aggregates.company_valuation` (top-level + **per-area** with org-framed action) →
`core` views (gated on `can_view_insights`) → the two redesigned templates.

The `post_save` materialization signal is unchanged; **existing scored submissions need
`recompute_nom035_scores`** once to gain dimensión rows.

## Testing

- **accounts:** importer accepts/ignores the optional `department` column; profile
  stores it; blank when absent.
- **nom035 scoring:** dimensión taxonomy covers exactly the items of its parent
  dominio (per variant); `score_submission` emits dimensión `GroupResult`s with the
  correct summed score and `ndr=""`; item→dimensión reconciles against the source
  tables. Existing categoría/dominio/final tests stay green.
- **nom035 aggregates:** `employee_valuation` returns the nested
  categoría→dominio→dimensión structure with scores and no action keys;
  `company_valuation` returns a per-area breakdown with correct grouping
  (normalization, "Sin área" bucket) and the most-severe-present action line.
- **core views/templates:** the panels render for `can_view_insights` and are absent
  otherwise; the individual card shows no action sentence.
- Update the existing `test_action_text_exists_for_every_level` and
  `test_employee_valuation_returns_text` to the new shape.

## Decisions

- **A — No action sentence on the individual card.** The individual view is data
  (scores + NDR), never a per-person prescription.
- **B — Keep the Guía I flag on the individual card**, shown only when positive; it is
  factual, boolean, standard-defined data (no message when negative).
- **C — Area action line keyed to the most-severe NDR present** for now; the
  correct rule (proportion vs. most-severe) is an open question **flagged for the SME**
  in `nom-035-valoracion-supuestos.md`.
- **Free-text department, not a model/enum** — area names vary by company and data is
  admin-cleaned; a managed list is unneeded scope.
- **Dimensión is score-only** — no NDR, matching the standard's tables.
- **Reframing reuses the NDR→text mapping** (reworded, org-framed) rather than
  inventing new scoring; the scoring math is untouched.

## Scope boundaries

**In scope:** `UserProfile.department` + CSV/admin population; dimensión taxonomy +
materialized dimensión `GroupScore` rows + backfill; org-framed reworded action text at
the aggregate level; per-area company aggregation; the nested employee breakdown with
scores; the visual pass (badges, hierarchy, distribution bars, legend) on the two
existing panels; the CSS rebuild.

**Out of scope:** changes to scoring thresholds/formulas; a Department model/management
UI; charts beyond distribution bars; PDF report; employee self-view; a second
instrument; any change to `apps/surveys`/`apps/responses`.
