# core

Three distinct responsibilities live here:
1. **Web home & dashboards** — the authenticated landing pages, company dashboards, and employee/answer views (`views.py`, `urls.py`). URL prefix: `/` (mounted at root; `app_name = "core"`).
2. **NOM-035 seed** — the declarative seed command for the canonical survey instrument (`management/commands/seed_nom035_survey.py`, data in `_nom035_data.py`). Operates on `apps/surveys` models.
3. **Spanish permission names** — `permissions.py` holds `rename_permissions_to_spanish`, a `post_migrate` receiver connected in `CoreConfig.ready()`. It derives each name from the model's rendered `verbose_name` (not `verbose_name_raw`, which returns the untranslated msgid) and rewrites `auth_permission.name` for the apps `project_app_labels()` derives from `INSTALLED_APPS`, so the Groups picker reads Spanish; Django builds the built-in names from an untranslated `"Can %s %s"` template, and `create_permissions` never renames a row once created. Display-only — codenames are untouched, so `bootstrap_groups` and every `has_perm` check are unaffected. It lives here because it spans every project app rather than belonging to any one. Declaring the names on each model is the alternative and is rejected in `docs/platform/localization.md`.

`core` has **no models of its own** (`models.py` is empty). It composes data from `accounts`, `surveys`, and `responses`.

> The interactive authoring CLI (`workflows/` + `create_*`/`manage_*`/`seed_*template*` commands) was removed in ADR-0002. See `docs/archive/internal/interactive-workflows.md` for the retired guide.

## Web views (`views.py`)

All are `LoginRequiredMixin` class-based views that authorize via the custom permissions defined on `accounts.Role`:

- `HomeView` (`core:home`, also `LOGIN_REDIRECT_URL`) — routes by group/permission: Admins → company list; `can_view_dashboard` → dashboard; `can_take_assigned_surveys` → survey list.
- `CompanyListView` — admin overview of all companies with annotated counts.
- `CompanyDashboardView` — per-company stats; serves both the user's own company (`/tablero-empresa/`) and an admin viewing any company (`/empresas/<reference_code>/`). Computes a statistical "representative minimum" sample size (`_representative_minimum`).
- `CompanyEmployeeListView` / `EmployeeDetailView` — per-employee survey progress; full answer breakdown gated behind `can_view_submissions`.
- `EmployeeSurveyListView` — an employee's assigned surveys.

`CompanyDashboardView` computes `can_take_surveys` — the permission **plus**
membership in the company being viewed — and the "Mi respuesta" card is gated on
it. Do not gate that card on `perms.accounts.can_take_assigned_surveys`: a
superuser passes every `perms.*` check in a template whatever their group, which
would show an admin a link `apps.surveys.views._respondent_company` refuses.

**Convention:** each view that accepts an optional `reference_code` shows the caller's own company when it's absent, or an arbitrary company (admin-only, `can_manage_surveys`) when present. The list/detail views are heavily optimized to avoid N+1 — prefetch/annotate maps are built up front; preserve that pattern when editing.

## Template filters (`templatetags/valuation_extras.py`)

`ndr_badge`, `ndr_bar` and `ndr_scale` — the single source of truth for
NDR→Tailwind-color mapping (Nulo/Bajo/Medio/Alto/Muy alto), used by the
"Valoración de resultados" panels (`employee_detail.html`,
`company_dashboard.html`). Add new NDR-derived colors here, not as literals in a
template. `ndr_scale` returns the five levels in order, filled up to the reached
one; render it through `templates/core/_ndr_scale.html`.

## Management commands (`management/commands/`)

```bash
python manage.py seed_nom035_survey   # seed (idempotent) the NOM-035 survey
```

`seed_nom035_survey` builds the canonical NOM-035 instrument (`Survey → Module → Question → Choice`) from the declarative data in `_nom035_data.py`: Guía I (`all`), Guía II (`small`), Guía III (`large`), with stable `code`s and `visible_when` gates. It upserts by `key="nom035"` and replaces modules on re-run. This is the only survey-building command; there is no interactive authoring CLI.

## Gotchas

- Authorization is permission-based, not group-name-based (except the `Admins` group, checked by name in a few places). Run `bootstrap_groups` (in `apps/accounts`) before these views behave correctly.
- Per-employee progress goes through `_progress_entry`, which delegates to `apps.surveys.visibility.progress_for_modules` so `answered`/`total` count only the questions a respondent's gate answers leave visible — that is what makes a completed survey read 100%. `_variant_question_count` is still used, but only as the *nominal* total, to derive the `not_applicable` figure the UI shows. Never compute progress from `_variant_question_count` alone.
- The employee list needs answer **values** (not just counts) to evaluate gates: one `values_list` sweep over `Answer` plus one module prefetch per assignment, both reused across every member. Preserve that pattern — a per-member query here is an N+1 in a page that renders the whole company.
- `tests/` covers views and the seed (`test_views.py`, `test_seed_nom035.py`).
- User-facing strings/URLs are Spanish.
