# core

Two distinct responsibilities live here:
1. **Web home & dashboards** — the authenticated landing pages, company dashboards, and employee/answer views (`views.py`, `urls.py`). URL prefix: `/` (mounted at root; `app_name = "core"`).
2. **NOM-035 seed** — the declarative seed command for the canonical survey instrument (`management/commands/seed_nom035_survey.py`, data in `_nom035_data.py`). Operates on `apps/surveys` models.

`core` has **no models of its own** (`models.py` is empty). It composes data from `accounts`, `surveys`, and `responses`.

> The interactive authoring CLI (`workflows/` + `create_*`/`manage_*`/`seed_*template*` commands) was removed in ADR-0002. See `docs/archive/internal/interactive-workflows.md` for the retired guide.

## Web views (`views.py`)

All are `LoginRequiredMixin` class-based views that authorize via the custom permissions defined on `accounts.Role`:

- `HomeView` (`core:home`, also `LOGIN_REDIRECT_URL`) — routes by group/permission: Admins → company list; `can_view_dashboard` → dashboard; `can_take_assigned_surveys` → survey list.
- `CompanyListView` — admin overview of all companies with annotated counts.
- `CompanyDashboardView` — per-company stats; serves both the user's own company (`/tablero-empresa/`) and an admin viewing any company (`/empresas/<reference_code>/`). Computes a statistical "representative minimum" sample size (`_representative_minimum`).
- `CompanyEmployeeListView` / `EmployeeDetailView` — per-employee survey progress; full answer breakdown gated behind `can_view_submissions`.
- `EmployeeSurveyListView` — an employee's assigned surveys.

**Convention:** each view that accepts an optional `reference_code` shows the caller's own company when it's absent, or an arbitrary company (admin-only, `can_manage_surveys`) when present. The list/detail views are heavily optimized to avoid N+1 — prefetch/annotate maps are built up front; preserve that pattern when editing.

## Management commands (`management/commands/`)

```bash
python manage.py seed_nom035_survey   # seed (idempotent) the NOM-035 survey
```

`seed_nom035_survey` builds the canonical NOM-035 instrument (`Survey → Module → Question → Choice`) from the declarative data in `_nom035_data.py`: Guía I (`all`), Guía II (`small`), Guía III (`large`), with stable `code`s and `visible_when` gates. It upserts by `key="nom035"` and replaces modules on re-run. This is the only survey-building command; there is no interactive authoring CLI.

## Gotchas

- Authorization is permission-based, not group-name-based (except the `Admins` group, checked by name in a few places). Run `bootstrap_groups` (in `apps/accounts`) before these views behave correctly.
- Per-assignment question totals in dashboards use `_variant_question_count` (counts the variant's modules); preserve the prefetch/annotate N+1-avoidance pattern when editing list/detail views.
- `tests/` covers views and the seed (`test_views.py`, `test_seed_nom035.py`).
- User-facing strings/URLs are Spanish.
