# nom035

The **NOM-035 valuation engine**: turns submitted survey answers into scores and a
Nivel de Riesgo (NDR), and surfaces them as text in the `core` dashboards. This app
is **NOM-035-specific by design** — a future instrument gets its own app, not a
generalization of this one (see `docs/adr/adr-0003-per-instrument-survey-processing-apps.md`).

## What lives here

- `constants.py` — shared string constants: NDR levels (`nulo`…`muy_alto`), Guía I
  severities, and group levels (categoría/dominio/dimensión).
- `_nom035_scoring.py` — the scoring **configuration as data**, keyed by
  `surveys.Question.code`: the Categoría→Dominio→Dimensión taxonomy, the inverted-item
  set, the NDR threshold tables, and the "Necesidad de acción" text. No config DB
  tables; change the config by editing here and re-running the recompute command.
- `scoring.py` — pure functions: `likert_item_score`, `classify`, `guia1_severity`,
  and `score_submission(submission) -> ScoreResult`.
- `services.py` — `materialize(submission)`: upserts the result rows in a transaction.
- `models.py` — `SubmissionScore` (one per submission) and `GroupScore` (per
  categoría/dominio/dimensión breakdown).
- `signals.py` — a `post_save` receiver on `responses.SurveySubmission` that
  materializes a score when a submission becomes `completed` (connected in
  `apps.py:ready()`).
- `aggregates.py` — on-demand `employee_valuation` and `company_valuation` read by
  `apps/core` views.
- `management/commands/recompute_nom035_scores.py` — backfill/refresh.

## Conventions & gotchas

- Likert answers are stored as ints 1–5 (1=Siempre … 5=Nunca); the engine maps them
  to the NOM-035 0–4 scale (normal item = `value-1`, inverted = `5-value`).
- Only **completed** submissions are scored; only **answered, visible** items count.
- Guía I (`g1-*`) is **not** scored into the NDR — it yields a separate referral flag.
- The MVP scoring data carries documented assumptions tracked in
  `docs/platform/nom-035-valoracion-supuestos.md` (Spanish, for the domain expert).
- Full design: `docs/platform/nom-035-analytics.md`.
