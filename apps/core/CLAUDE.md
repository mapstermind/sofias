# core

Two distinct responsibilities live here:
1. **Web home & dashboards** — the authenticated landing pages, company dashboards, and employee/answer views (`views.py`, `urls.py`). URL prefix: `/` (mounted at root; `app_name = "core"`).
2. **Survey-authoring tooling** — interactive terminal workflows and management commands for building surveys/templates (`workflows/`, `management/commands/`). These operate on `apps/surveys` models.

`core` has **no models of its own** (`models.py` is empty). It composes data from `accounts`, `surveys`, and `responses`.

## Web views (`views.py`)

All are `LoginRequiredMixin` class-based views that authorize via the custom permissions defined on `accounts.Role`:

- `HomeView` (`core:home`, also `LOGIN_REDIRECT_URL`) — routes by group/permission: Admins → company list; `can_view_dashboard` → dashboard; `can_take_assigned_surveys` → survey list.
- `CompanyListView` — admin overview of all companies with annotated counts.
- `CompanyDashboardView` — per-company stats; serves both the user's own company (`/tablero-empresa/`) and an admin viewing any company (`/empresas/<reference_code>/`). Computes a statistical "representative minimum" sample size (`_representative_minimum`).
- `CompanyEmployeeListView` / `EmployeeDetailView` — per-employee survey progress; full answer breakdown gated behind `can_view_submissions`.
- `EmployeeSurveyListView` — an employee's assigned surveys.

**Convention:** each view that accepts an optional `reference_code` shows the caller's own company when it's absent, or an arbitrary company (admin-only, `can_manage_surveys`) when present. The list/detail views are heavily optimized to avoid N+1 — prefetch/annotate maps are built up front; preserve that pattern when editing.

## Authoring workflows (`workflows/`)

Reusable interactive (stdin/stdout) building blocks, invoked by the management commands. Pure terminal tooling — **not** used by the web app.

- `prompts.py` — all terminal I/O primitives (`ask`, `ask_int`, `choose`, `confirm`, …). All user input funnels through here.
- `introspect.py` — derives prompt specs from Django model fields (`prompt_for_model`).
- `version_helpers.py` — `get_or_create_latest_version`.
- `survey.py`, `question.py`, `sections.py`, `question_template.py`, `choices.py` — orchestrate creating/editing the corresponding `surveys` models, including stamping library templates into versions.

## Management commands (`management/commands/`)

```bash
python manage.py create_survey              # interactive survey + first version
python manage.py create_question            # interactive question within a version
python manage.py manage_sections            # interactive section management
python manage.py manage_question_templates  # interactive library management
python manage.py manage_choices             # interactive choice management
python manage.py seed_likert_templates      # seed 72 Likert statements into the library
python manage.py seed_demographic_templates # seed demographic question templates
python manage.py seed_nom035_survey         # seed the full NOM-035 survey
```

The `seed_*` commands build the project's canonical survey content (Mexican NOM-035 psychosocial-risk questionnaire). The `create_*`/`manage_*` commands wrap `workflows/`.

## Gotchas

- Authorization is permission-based, not group-name-based (except the `Admins` group, checked by name in a few places). Run `bootstrap_groups` (in `apps/accounts`) before these views behave correctly.
- `tests/` covers both views and workflows (`test_views.py`, `test_workflows.py`).
- User-facing strings/URLs are Spanish.
