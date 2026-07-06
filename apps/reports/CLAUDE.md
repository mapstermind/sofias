# reports

**Placeholder / not yet implemented.** Intended home for dashboard and report generation (exports, rendered reports) built on top of `apps/nom035`.

## Current state

- `models.py` and `views.py` are empty stubs (`# Create your models here.`).
- `AppConfig.name = "reports"` (bare name, **not** `apps.reports`) and the app is **not** in `INSTALLED_APPS` — it is not loaded by Django yet.
- No migrations, URLs, or tests.

## If you build this out

- Register it: add `"apps.reports"` to `INSTALLED_APPS` and set `AppConfig.name = "apps.reports"` with an explicit `label` (match the pattern in `apps/core/apps.py`).
- The dashboard *views* that exist today live in `apps/core` (`CompanyDashboardView`, etc.); decide whether report generation here complements or absorbs them.
