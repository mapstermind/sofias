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
- `CompanyEmployeeListView` / `EmployeeDetailView` — per-employee survey progress; full answer breakdown gated behind `can_view_submissions`. Each answer row is a dict (`question`, `answer`, `score`) — read it the way templates do, never by attribute, in a filter or tag. On a NOM-035 assignment a frequency row's `score` is `apps.nom035.scoring.answer_score` and the module carries `scored=True`, so `_frequency_answer.html` orders its squircle strip from lowest to highest risk and the module header reads "Menor → mayor riesgo"; any other instrument's frequency rows keep the options' own order. The roster accepts six optional GET parameters — `q` (search), `sexo`, `rol`, `area`, `localidad` and `orden` — of which `rol`, `area` and `localidad` may be **repeated**, OR-ing their values within the dimension while the dimensions AND with each other. They are parsed and applied by `roster.py`: `parse_roster_query()` validates them against the company being viewed (an absent, empty, unrecognized or foreign-company value is ignored, never an error), `narrow_profiles()` applies the search, the filters and the name/activation ordering, and `sort_members()` does the progress ordering and pins the viewer's own card to the top. Spanish slugs in, English values out — `rol` maps through `apps/accounts/roles.py`, `sexo` through `SEX_SLUGS` (defined in `query_params.py`, re-exported by `roster.py`).
  - `parse_roster_query` reads its GET parameters through `apps/core/query_params.py`, shared with the results page's `ResultsQuery`: `values(params, key)` reads every value for a key from either a `QueryDict` (the view) or a plain dict (unit tests), since only the former has `getlist`. `valid_pks()` then keeps the values that name an entry the company owns, **dropping a bad one on its own** rather than discarding its neighbours, and deduplicating: `?area=3&area=nonsense&area=999` yields `(3,)`. `sexo` is scalar and takes the **first recognized** value via `first_sex()` — `QueryDict.get()` returns the last, which would let a bad value shadow a good one before it. Role order is the declared order in `roles.py`, not URL order.
  - `narrow_profiles()` applies the role filter with `user__groups__name__in=...` followed by **`.distinct()`**: `__in` across the groups M2M returns one row per matching group, so without it a colaborador holding two of the selected roles is listed twice. Do not drop it when editing that branch.
  - The page carries TypeScript — `static/ts/roster_filters.ts`, which only opens and closes the filter `<dialog>`, allows a chosen `sexo` radio to be un-chosen, and restores the pills on dismiss. No filter state lives in it. **Run `npm run build:js` and commit `static/js/roster_filters.js` when touching it**; nothing in the Python suite covers it.
- `EmployeeSurveyListView` — an employee's assigned surveys.
- `CompanyResultsView` / `CompanyResultsFragmentView` — the NOM-035 results page (`core:company_results`, `/tablero-empresa/resultados/`; `core:company_results_for`, `/empresas/<reference_code>/resultados/`) and its body alone at `…/fragmento/` (`core:company_results_fragment`, `core:company_results_fragment_for`). Both require `can_view_insights`; the fragment view is the page view with `template_name = "core/results/_body.html"`, and both build their context in `_results_context`. GET parameters (`encuesta`, `sexo`, repeatable `edad`/`area`/`localidad`) are parsed by `results_query.py` (`parse_results_query` → `ResultsQuery`; `results_url` and `filter_pills` build the page's links) with the same ignore-bad-values rule as the roster; the data comes from `apps/nom035/results.py`, which applies the small-group rule unless the viewer holds `can_view_small_groups`. `tests/test_results_views.py` pins the fragment view's query count: it must not grow with the number of respondents. See `docs/platform/nom-035-results-dashboard.md`.
  - The page carries TypeScript — `static/ts/results_dashboard.ts` swaps `#results-body` with the fragment, keeps the address bar in step with `history.replaceState`, and writes the new group line into the `#results-status` live region. **Run `npm run build:js` and commit `static/js/results_dashboard.js` when touching it**; nothing in the Python suite covers it.

`CompanyDashboardView`'s "Valoración de resultados" card (gated on
`can_view_insights`) shows `latest_scored_count` — the scored count of the
assignment the results page opens on, from `select_assignment(assignment_options(company), None)`
— and links to the results page.

`CompanyDashboardView` computes `can_take_surveys` — the permission **plus**
membership in the company being viewed — and the "Mi respuesta" card is gated on
it. Do not gate that card on `perms.accounts.can_take_assigned_surveys`: a
superuser passes every `perms.*` check in a template whatever their group, which
would show an admin a link `apps.surveys.views._respondent_company` refuses.

**Convention:** each view that accepts an optional `reference_code` shows the caller's own company when it's absent, or an arbitrary company (admin-only, `can_manage_surveys`) when present. The list/detail views are heavily optimized to avoid N+1 — prefetch/annotate maps are built up front; preserve that pattern when editing.

## Page chrome: back-to-top button

`templates/base_app.html` renders `templates/_back_to_top.html` inside
`{% block back_to_top %}` on every signed-in page: a "Volver arriba" button whose
ring shows scroll progress. It sits in the side gutter beside the
`container_width` column when there is room and in the bottom-right corner
otherwise, appears after one viewport of scroll, lifts above the footer, and is
hidden in print. A page opts out by overriding the block with nothing — the
survey form does, because its phone bar owns that corner. Behaviour is
`static/ts/back_to_top.ts` (**run `npm run build:js` and commit
`static/js/back_to_top.js` when touching it**); `tests/test_back_to_top.py` pins
the server-rendered half. Clicking it focuses `<main id="main" tabindex="-1">`,
so keep those attributes.

## Brand and palette (`brand.py`, `context_processors.py`, `templatetags/brand.py`)

`context_processors.brand` puts four values in every request-rendered template:
`brand` (`settings.BRAND`: `name`, `short_name`, `meaning`, `logo`), `palette`
(the active palette slug), `palettes` (`settings.BRAND_PALETTES`, slug and
Spanish label) and `show_palette_switch`. `brand.active_palette(request)` reads
the `paleta` cookie and falls back to `BRAND_PALETTE_DEFAULT` for a missing or
unknown value, so `base.html` can print it straight into `data-palette`; it also
accepts `None`, for templates rendered without a request (the report PDF).
`show_palette_switch` is lazy — `brand.can_switch_palette` runs a group query,
and only `base.html` asks — and is true for the Admins group and superusers, or
for everyone under `DEBUG`.

`templates/_palette_switch.html` is the switch: a fixed pill, bottom-left,
posting to `PaletteSwitchView` (`core:palette_switch`, `/paleta/`), which sets
the cookie for a known slug and redirects to `next` when it is a same-host URL,
or to `/` otherwise. `base.html` renders it in `{% block palette_switch %}`; the
survey form overrides that block with nothing, because its phone bar spans the
bottom edge. The switch exists while the client chooses a palette.

`{% brand_logo css_class %}` (`{% load brand %}`) inlines the SVG that
`BRAND["logo"]` names — a bare `<svg>` whose shapes use `fill="currentColor"` —
adding `class`, `role="img"` and an `aria-label`. `brand.palette_hex(slug)`
returns one palette's `--brand-*` values parsed from `main.css`, for renderers
that cannot resolve a CSS variable (the chart tags' hex `fill`). `templates/_logo.html` is the
only caller; pass a size and a `text-*` color. See
`docs/platform/design-system.md`; `tests/test_brand.py` and
`tests/test_design_tokens.py` cover this.

## Template filters (`templatetags/valuation_extras.py`)

`ndr_badge`, `ndr_bar`, `ndr_fill` and `ndr_scale` — the single source of truth
for NDR→Tailwind-color mapping (Nulo/Bajo/Medio/Alto/Muy alto), used by the
employee card (`employee_detail.html`) and the results page's charts and legends.
`ndr_fill` is the SVG `fill-*` class for chart marks. `ndr_badge`, `ndr_bar` and
`ndr_fill` take an optional tier: `{{ level|ndr_badge:"dominio" }}` selects the
deeper dominio palette (solid badges), which every dominio-level mark uses;
the default is the categoría/final tier. In the charts the tier rides on the
color key — `ndr-<level>` or `dom-<level>`, chosen by `apps/nom035/results.py`
— and both sets live in `_COLORS` and `_HEX`. In a template, an unset variable
passed as a filter argument raises, so default it first (see
`results/_ndr_legend.html`). Add new NDR-derived colors here, not as literals
in a template. `ndr_scale` returns the five levels in
order, filled up to the reached one; render it through
`templates/core/_ndr_scale.html`.

## Charts (`charts.py`, `templatetags/charts.py`)

Instrument-agnostic, server-rendered SVG components. `charts.py` holds the pure
geometry — `stacked_segments`, `columns`, `level_columns`, `range_strip`,
`largest_remainder` —
from items carrying a `color` *key*, and knows nothing of NOM-035 or Tailwind.
The `charts` tag library (`{% load charts %}`) provides the inclusion tags
`stacked_bar`, `column_chart`, `level_columns` (a distribution over fixed levels: one slot per level
on a 0–100 % scale, each value printed beneath) and `range_strip`, rendering
`templates/components/charts/*.html`, and is the chart palette: it maps each
color key to spelled-out `fill-*`/`bg-*` classes (NDR keys through
`valuation_extras`). Every mark also carries its color as a hex `fill`
presentation attribute, and the chart `<text>` elements carry
`fill`, `font-size` and `font-family` attributes: WeasyPrint (the report PDF,
`apps/reports/pdf.py`) ignores the Tailwind `fill-*` classes, while on screen the
class wins over the attribute. A fixed color (a risk level, Guía I) takes its hex
from `_HEX`; a series that follows the palette (sex, age, the empty baseline) is
listed in `_PALETTE_TOKENS` with its token, and its hex is that token's value in
the active palette — `brand.palette_hex`, which reads `static/css/main.css`. The
chart tags therefore take the template context (`takes_context=True`) and read
`palette` from it, falling back to the default palette. A new color key goes in
`_COLORS` and in exactly one of `_HEX` or `_PALETTE_TOKENS`
(`test_every_color_key_has_a_hex_in_every_palette` checks it);
Tailwind scans `apps/**/templatetags/*.py`, but run `npm run build:css` after
adding one.
Each SVG is one `role="img"` with an `aria-label`; its marks are never
focusable and carry no tooltip or SVG `<title>` — every value is printed as text
instead, so nothing interactive ends up inside a `<summary>`. SVG coordinates
render inside `{% localize off %}`.

## Management commands (`management/commands/`)

```bash
python manage.py seed_nom035_survey   # seed (idempotent) the NOM-035 survey
```

`seed_nom035_survey` builds the canonical NOM-035 instrument (`Survey → Module → Question → Choice`) from the declarative data in `_nom035_data.py`: Guía I (`all`), Guía II (`small`), Guía III (`large`), with stable `code`s and `visible_when` gates. It upserts by `key="nom035"` and replaces modules on re-run. This is the only survey-building command; there is no interactive authoring CLI.

## Gotchas

- Authorization is permission-based, not group-name-based (except the `Admins` group, checked by name in a few places). Run `bootstrap_groups` (in `apps/accounts`) before these views behave correctly.
- Per-employee progress goes through `_progress_entry`, which delegates to `apps.surveys.visibility.progress_for_modules` so `answered`/`total` count only the questions a respondent's gate answers leave visible — that is what makes a completed survey read 100%. `_variant_question_count` is still used, but only as the *nominal* total, to derive the `not_applicable` figure the UI shows. Never compute progress from `_variant_question_count` alone.
- The employee list needs answer **values** (not just counts) to evaluate gates: one `values_list` sweep over `Answer` plus one module prefetch per assignment, both reused across every member. Preserve that pattern — a per-member query here is an N+1 in a page that renders the whole company. Search and filtering narrow the profile queryset **before** the per-member loop, so the loop only walks what will be rendered, and `user__groups` is prefetched on it because every card's metadata line prints the Rol. The whole arrangement is pinned by an invariance test in `tests/test_views.py`: a roster of 3 colaboradores and one of 30 must cost the same number of queries, so a dropped prefetch fails the suite rather than the page.
- `tests/` covers views and the seed (`test_views.py`, `test_seed_nom035.py`), the results page (`test_results_views.py`, `test_results_query.py`, `test_dashboard_results_card.py`), the chart geometry and components (`test_charts.py`, `test_chart_components.py`), phone-width layout (`test_responsive.py`), the back-to-top button (`test_back_to_top.py`), and the brand, palette switch and design tokens (`test_brand.py`, `test_design_tokens.py`).
- User-facing strings/URLs are Spanish.
