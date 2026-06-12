# analytics

**Placeholder / not yet implemented.** Intended home for data processing and aggregation over survey responses.

## Current state

- `models.py` and `views.py` are empty stubs (`# Create your models here.`).
- `AppConfig.name = "analytics"` (bare name, **not** `apps.analytics`) and the app is **not** in `INSTALLED_APPS` — it is not loaded by Django yet.
- No migrations, URLs, or tests.

## If you build this out

- Register it: add `"apps.analytics"` to `INSTALLED_APPS` and set `AppConfig.name = "apps.analytics"` with an explicit `label` (match the pattern in `apps/core/apps.py`).
- Read source data from `apps/responses` (`SurveySubmission`, `Answer`) and `apps/surveys` (`Question`, `SurveyVersion`). Remember `Answer.value` is JSON typed by `question.question_type`.
- Note `apps/core/views.py` already computes some inline aggregates (completion rates, representative-sample minimums); consider consolidating that logic here.
