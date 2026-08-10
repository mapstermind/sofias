# reports

**Placeholder / not yet implemented.** Intended home for dashboard and report generation (exports, rendered reports) built on top of `apps/nom035`.

## Current state

- `models.py` and `views.py` are empty stubs (`# Create your models here.`).
- `AppConfig.name = "reports"` (bare name, **not** `apps.reports`) and the app is **not** in `INSTALLED_APPS` — it is not loaded by Django yet.
- No migrations, URLs, or tests.

## If you build this out

- Register it: add `"apps.reports"` to `INSTALLED_APPS` and set `AppConfig.name = "apps.reports"` with an explicit `label` (match the pattern in `apps/core/apps.py`).
- Give the `AppConfig` a Spanish `verbose_name` — it becomes the app's heading in the admin index, alongside *Cuentas*, *Encuestas*, *Respuestas* and *NOM-035*.
- Give every model a Spanish `Meta.verbose_name`/`verbose_name_plural` and every field an explicit lowercase Spanish `verbose_name`. Registering the app puts it inside the set `project_app_labels()` derives, so `test_every_project_app_is_covered_by_the_label_guard` starts checking it and `rename_permissions_to_spanish` starts translating its permission names — both automatically, and the label guard will fail until the metadata is there. See `docs/platform/localization.md`.
- The dashboard *views* that exist today live in `apps/core` (`CompanyDashboardView`, etc.); decide whether report generation here complements or absorbs them.
