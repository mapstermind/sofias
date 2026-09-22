# nom035

The **NOM-035 valuation engine**: turns submitted survey answers into scores and a
Nivel de Riesgo (NDR), and provides the reads `apps/core` presents — the company
results page and the employee valuation card. This app
is **NOM-035-specific by design** — a future instrument gets its own app, not a
generalization of this one (see `docs/adr/adr-0003-per-instrument-survey-processing-apps.md`).

## What lives here

- `constants.py` — shared constants: NDR levels (`nulo`…`muy_alto`) and their
  labels, group levels (categoría/dominio/dimensión — dimensión is score-only, no
  NDR), and `MIN_GROUP_SIZE` (5) for the results page's small-group rule.
- `_nom035_scoring.py` — the scoring **configuration as data**, keyed by
  `surveys.Question.code`: the Categoría→Dominio→Dimensión taxonomy, the inverted-item
  set, the NDR threshold tables, and the "Necesidad de acción" text. All transcribed
  from `docs/internal/Guias de Referencia.md` (the single source of
  truth). No config DB tables; change the config by editing here and re-running the
  recompute command.
- `scoring.py` — pure functions: `likert_item_score`, `classify`, `guia1_positive`,
  and `score_submission(submission) -> ScoreResult`.
- `services.py` — `materialize(submission)`: upserts the result rows in a transaction.
- `models.py` — `SubmissionScore` (one per submission, with `guia1_positive` and
  `guia1_event`) and `GroupScore` (per
  categoría/dominio/dimensión breakdown — dimensión is score-only, no NDR).
- `signals.py` — a `post_save` receiver on `responses.SurveySubmission` that
  materializes a score when a submission becomes `completed` (connected in
  `apps.py:ready()`).
- `aggregates.py` — `employee_valuation`, the on-demand read behind the
  employee-detail card.
- `results.py` — everything the company results page shows for one assignment:
  `assignment_options`/`select_assignment` (the survey selector, also used for
  the dashboard card's count), `results_for(assignment, query, *,
  suppress_small_groups)` returning frozen `Results` dataclasses, `narrow` (the
  query's respondent filters in the database), `shows` (the small-group and
  complement rule), `_hide_until_safe` (the participation table's secondary
  rule: when the hidden área rows hold 1–4 respondents, the smallest visible
  rows are hidden too until they hold at least 5) and `_area_of` (an área
  counts only when it belongs to the company; otherwise "Sin área"). Área grouping is by `CompanyArea` **pk**, so
  identically named áreas in different companies never merge. A suppressed result
  carries no numbers — keep the rule here, never in a template. Its query count
  is fixed regardless of respondents (`tests/test_results.py` caps it). See
  `docs/platform/nom-035-results-dashboard.md`.
- `management/commands/recompute_nom035_scores.py` — backfill/refresh.

## Conventions & gotchas

- Likert answers are stored as ints 1–5 (1=Siempre … 5=Nunca); the engine maps them
  to the NOM-035 0–4 scale (normal item = `value-1`, inverted = `5-value`).
- Only **completed** submissions are scored; only **answered, visible** items count.
- Guía I (`g1-*`) is **not** scored into the NDR — it yields two stored flags:
  `guia1_event` (Sección I `g1-1` answered Sí) and the **binary** `guia1_positive`
  from the official section-based clinical-referral rule (event + any Sí in
  Section II, or ≥3 in Section III, or ≥2 in Section IV). `guia1_positive` implies
  `guia1_event`. After a scoring change, `recompute_nom035_scores` refreshes both.
- Scoring data is transcribed from the source of truth (`Guias de Referencia.md`);
  the remaining open assumption (partial/skipped conditional blocks) is tracked in
  `docs/platform/nom-035-valoracion-supuestos.md` (Spanish, for the domain expert).
- Full design: `docs/platform/nom-035-analytics.md` (engine and employee card) and
  `docs/platform/nom-035-results-dashboard.md` (company results page).
