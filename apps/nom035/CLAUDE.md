# nom035

The **NOM-035 valuation engine**: turns submitted survey answers into scores and a
Nivel de Riesgo (NDR), and surfaces them in the `core` dashboards as color-coded
NDR badges over a categoría→dominio→dimensión hierarchy. This app
is **NOM-035-specific by design** — a future instrument gets its own app, not a
generalization of this one (see `docs/adr/adr-0003-per-instrument-survey-processing-apps.md`).

## What lives here

- `constants.py` — shared string constants: NDR levels (`nulo`…`muy_alto`) and
  group levels (categoría/dominio/dimensión — dimensión is score-only, no NDR).
- `_nom035_scoring.py` — the scoring **configuration as data**, keyed by
  `surveys.Question.code`: the Categoría→Dominio→Dimensión taxonomy, the inverted-item
  set, the NDR threshold tables, and the "Necesidad de acción" text. All transcribed
  from `docs/internal/roadmap_context/Guias de Referencia.md` (the single source of
  truth). No config DB tables; change the config by editing here and re-running the
  recompute command.
- `scoring.py` — pure functions: `likert_item_score`, `classify`, `guia1_positive`,
  and `score_submission(submission) -> ScoreResult`.
- `services.py` — `materialize(submission)`: upserts the result rows in a transaction.
- `models.py` — `SubmissionScore` (one per submission) and `GroupScore` (per
  categoría/dominio/dimensión breakdown — dimensión is score-only, no NDR).
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
- Guía I (`g1-*`) is **not** scored into the NDR — it yields a separate **binary**
  `guia1_positive` flag from the official section-based clinical-referral rule
  (event + any Sí in Section II, or ≥3 in Section III, or ≥2 in Section IV).
- Scoring data is transcribed from the source of truth (`Guias de Referencia.md`);
  the remaining open assumption (partial/skipped conditional blocks) is tracked in
  `docs/platform/nom-035-valoracion-supuestos.md` (Spanish, for the domain expert).
- Full design: `docs/platform/nom-035-analytics.md`.
