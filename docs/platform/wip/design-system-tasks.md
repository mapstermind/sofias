# Design system — Phase 2b: navigation, dialogs, empty states, error pages

## What changes

**What.** The design system gains four patterns, and every existing template adopts them:

- **Navigation:** one header row holding a section switcher on a phone and inline tabs from `lg`, plus a user menu.
- **Dialogs:** the native `<dialog>`, styled by a `.dialog` class and driven by `dialog.ts`.
- **Empty states:** one empty-state partial.
- **Error pages:** branded 404, 403 and 500 pages.

**Why.**

- **Navigation.** There is no navigation today. Each page puts one desktop-only "← Regresa a…"
  link in the header. An executive gets from Resultados to Reportes by going back through the
  dashboard. On a phone there is no link at all, and the avatar's hover-to-log-out does nothing.
- **Dialogs.** Five of the six dialogs are hand-made `div` overlays: no dialog role, no Esc, no
  focus trap, and the page behind stays tabbable. Three of them sit on the survey.
- **Empty states.** There are 11 of them, written five ways.
- **Error pages.** No error templates exist, so production shows Django's bare English pages.

The inventory found no `<table>` outside the report, and no list that paginates. The grid rows
already stack on a phone, so tables need no component. Pagination of the roster is a behaviour
change, with queries, URLs and filters, and belongs to its own feature.

**Live doc sections this makes wrong:**

- In `docs/platform/design-system.md`:
  - *Out of scope → Navigation, tables, the dialog, empty and error pages, pagination*: everything
    but pagination moves into Scope.
  - *Scope → Components*: gains the four patterns.
  - *Phone shape*, *Key decisions* and *Enforcement*: gain their entries.
- In `docs/platform/responsive-layout.md`: the header's phone shape.
- `apps/core/CLAUDE.md` (the back-to-top notes mention `base_app.html`'s header) and
  `apps/surveys/CLAUDE.md` (its modals) describe markup that changes.

**ADRs.** None touched.

## Design

### Navigation

**Header.** `base_app.html` draws one white row with a `neutral-200` bottom border.

- **On a phone** it is 56px tall: the logo (a link home), the section switcher, the user menu.
- **From `lg`** it is the logo with the brand name, then the inline tabs, then the user menu.
- **The `header_nav` block** and every header-level "Regresa a…" link go away.

**The sections.** `{% company_nav %}` is an inclusion tag in `apps/core/templatetags/navigation.py`,
rendering `templates/_company_nav.html`. It builds the list from the request's user and the page's
context (`company`, `is_admin_view`). It renders nothing when fewer than two sections are open to
the viewer.

| Section | Admin URL (`is_admin_view`) | Own-company URL | Shown when the viewer has |
|---|---|---|---|
| Tablero | `core:company_dashboard_for` | `core:company_dashboard` | `can_view_dashboard` (admin: `can_manage_surveys`) |
| Colaboradores | `core:company_employee_list_for` | `core:company_employee_list` | `can_manage_employees` (admin: `can_manage_surveys`) |
| Resultados | `core:company_results_for` | `core:company_results` | `can_view_insights` |
| Reportes | `reports:admin_list` | `reports:exec_list` | `can_view_insights` (admin: `can_manage_surveys` too) |

The checks mirror each view's own. The tests compare them against the views by requesting each
link as each role.

**Active section.** The active section comes from `request.resolver_match.url_name`. A child page
lights its parent:

- `company_employee_detail*` lights Colaboradores.
- `reports:admin_detail`, `admin_edit` and `exec_detail` light Reportes.
- `company_results_fragment*` lights Resultados.

The active section carries `aria-current="page"`.

**How the sections render.**

- **Phone switcher.** A `<details>` whose `<summary>` is a 44px button: the current section name
  at 15px weight 600, then a chevron. It opens a panel (white, 12px radius, `shadow-lg`) of 48px
  links at 16px. The current link is tinted `primary-50` in `primary-700` with a squircle marker.
  It is a disclosure of links, not an ARIA menu. Hidden from `lg`.
- **Desktop tabs.** A `<nav aria-label="Secciones de la empresa">` of 60px-tall links at 14px
  weight 500 in `neutral-600`. The active tab is `neutral-900` with a 2px `primary-600` bottom
  border. Shown from `lg`.

**User menu.** The avatar is the `<summary>` of a second `<details>`. Its panel holds:

- the full name, the role label (`apps/accounts/roles.py`) and the email
- a *Cerrar sesión* `btn-text`, which posts to logout

Without JS both panels open and close on their own. `static/ts/disclosure.ts` closes an open panel
on Esc or a click outside, returns focus to its summary, and keeps only one panel open at a time.

**Page context.** A `{% block page_context %}` sits in `base_app.html`, above the content. It holds
a line, a back link, or nothing:

- **Admin on a company page:** *Empresas / {company}* (`_page_context.html`).
- **Executive:** nothing.
- **Child pages:**
  - employee detail: *← Colaboradores* (keeps the roster query string)
  - a report: *← Reportes*
  - the report form: *← Reporte*

  Each is a `btn-text btn-sm`, visible at every width.

**Respondents** (`can_take_assigned_surveys` without `can_view_dashboard`):

- The header holds the logo, a *Mis encuestas* link (hidden on that page) and the user menu.
- The survey's "← Inicio" goes away; *Mis encuestas* replaces it.

### Dialogs

**The `.dialog` class.** A component class for a native `<dialog>`, opened with `showModal()`:

- 12px radius, white, `shadow-xl`, 24px padding.
- `w-[calc(100%-2rem)] max-w-md`, `max-h-[85vh] overflow-y-auto`, centered.
- `::backdrop` is `neutral-900` at 40%.
- **Motion:** opening fades and scales from 96% over 150ms; under `prefers-reduced-motion` it
  appears at once.

**Convention, written in each template:**

- Optional icon tile: a 48px tinted circle.
- A `text-lg` title that the dialog names with `aria-labelledby`.
- The body.
- An actions row, `flex flex-col-reverse gap-3 sm:flex-row sm:justify-end`.
- A close button, where there is one: `btn-text` with `aria-label="Cerrar"`.

**`static/ts/dialog.ts`:**

| Hook | Behaviour |
|---|---|
| `[data-dialog-open="<id>"]` | opens that dialog |
| `[data-dialog-close]` | closes its dialog |
| `<dialog data-open-on-load>` | opens on `DOMContentLoaded` |
| a click on the backdrop | closes the dialog |
| `data-dialog-static` | Esc and backdrop clicks do nothing, through `cancel` → `preventDefault` |

Focus restore and the trap are the browser's.

**Adopted by:**

- **The survey's four modals.**
  - *Instrucciones*: opened by its button; open on load on the first visit, as now.
  - *Progreso guardado*: `data-open-on-load` when `show_saved`.
  - *¿Enviar tus respuestas?*: `data-open-on-load` when `show_confirm`. Its `confirm=1` submit is
    unchanged.
  - *Sesión expirada*: `data-dialog-static`. `survey_progress.ts` calls `showModal()` on it.

  The inline `style.display` scripts go away.
- **The dashboard's Cochran formula.** Its inline `onclick` handlers go away.
- **The roster filter dialog.** Already native, it takes `.dialog`. `roster_filters.ts` keeps its
  logic.

### Empty states

**The partial.** `templates/components/_empty.html` takes:

- `body`, required
- `title`, `icon`, `action_url` and `action_label`, optional
- `compact`, which uses less padding inside a grid

**Look.** A `card shadow-none border-dashed border-neutral-300` box, centered:

- **icon:** 20px `neutral-500`, on a 40px `neutral-100` tile with a 8px radius
- **title:** 16px, weight 600, `neutral-900`
- **body:** 14px `neutral-600`
- **action:** `btn-secondary`

**Adoption.** All 11 empty states use it, with their current copy. The roster's *Limpiar filtros*
becomes the partial's action. Copy changes belong to the Phase 4 copy review.

### Error pages

**Templates.** `templates/404.html`, `403.html` and `500.html` extend `templates/base_error.html`,
the centered layout of the login screens. Each holds:

- the logo
- a `text-xl` title and one sentence
- a `btn-primary` *Ir al inicio*
- a `text-sm neutral-500` line, "Error 404"


| Page | Title | Sentence |
|---|---|---|
| 404 | No encontramos esta página | La dirección puede estar mal escrita, o la página ya no existe. |
| 403 | No tienes acceso a esta página | Tu cuenta no tiene permiso para verla. Si la necesitas, pide acceso a tu administrador. |
| 500 | No pudimos cargar esta página | Ocurrió un error en el servidor. Intenta de nuevo en unos minutos. |

**Rendering.**

- **404 and 403** use Django's default handlers, which render with the request context.
- **500** sets `handler500 = "apps.core.views.server_error"` in `config/urls.py`. It renders
  `500.html` with `brand` (`settings.BRAND`) and the default palette, and makes no database query.

### Decisions

- **One header row everywhere, with a switcher on a phone and tabs on desktop.** Stacked tabs take
  a fifth of a phone screen. A hamburger hides where you are. The switcher names the current
  section and reaches any other in two taps.
- **The sections come from one tag that mirrors the views' permission checks.** A section a viewer
  cannot open is never offered.
- **Company context and back links live in the page body.** The header holds only navigation.
- **Every dialog is a native `<dialog>`.** The browser supplies the focus trap, Esc, the inert
  background and focus restore, which the hand-made overlays lacked.
- **Disclosures are `<details>`.** They open and close without JS. JS adds only Esc, outside
  clicks and one-at-a-time.
- **The 500 page has its own view.** Django renders it without the request context, and the
  database may be what failed.
- **No table component and no pagination.** Nothing in the app needs either yet.

### Tests

- **Navigation:**
  - Each role sees exactly its sections, and every offered link answers 200 for that role.
  - The active section carries `aria-current="page"` on each section page and child page.
  - A respondent sees *Mis encuestas* and no sections.
  - The switcher and the tabs render the same links.
  - The user menu shows the role label and posts to logout.
  - No template defines `header_nav`.
- **Dialogs:**
  - No `fixed inset-0` overlay is left in `templates/`.
  - Every `<dialog>` names an `aria-labelledby` target that exists.
  - The survey renders `data-open-on-load` on the confirm dialog only with `show_confirm`, and
    the expired-session dialog carries `data-dialog-static`.
- **Empty states:**
  - The partial renders its icon tile, title, body and action.
  - No hand-made dashed card is left.
- **Error pages:**
  - With `DEBUG` off, an unknown URL renders the Spanish 404 with the brand.
  - A view raising `PermissionDenied` renders the 403.
  - `server_error` renders with zero queries.
- **Checked by hand:**
  - the switcher, the user menu and every dialog, by keyboard and touch
  - every changed page at 360px and on desktop, in both palettes

### Out of scope

- Pagination of the roster: a feature of its own.
- A table component.
- A loading skeleton: the one async swap already sets `aria-busy`.
- Copy changes beyond the error pages, which are new.
- The survey's phone bar.
- The Django admin.

---

# Phase 2b Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Navigation, dialogs, empty states and error pages as components, adopted everywhere.

**Architecture:** A `company_nav` inclusion tag builds the permitted sections once. `base_app.html` renders them two ways (`<details>` switcher below `lg`, tabs from `lg`). Native `<dialog>`s are driven by one `dialog.ts`. `<details>` panels are polished by one `disclosure.ts`. Partials handle empty states, and Django's error templates plus a `handler500` view handle errors.

**Tech Stack:** Django 6 templates and tags, Tailwind v4, TypeScript via `tsc`, pytest-django.

**Spec:** the brief above.

## Global Constraints

- Every user-facing string is Spanish; classes come from the tokens and components only.
- Unprefixed classes describe the phone; the header is one row at every width.
- No new dependency. Never commit without asking.
- `npm run build:css` after templates/static; `npm run build:js` after `static/ts/`.

## Review Focus

- An admin viewing a company whose page context has no `company` (the company list, the styleguide) must render no sections and no context line, not crash.
- The Ejecutivo secundario has two sections: the switcher still renders (two is enough) and never offers Resultados or Reportes.
- A `<details>` panel open when the page is restored from the back/forward cache must not cover the page: `disclosure.ts` closes panels on `pageshow`.
- The survey's confirm dialog submits its form with `confirm=1` from inside a `<dialog>`; the button must keep its `form=` / `name` / `value`.
- `server_error` must render when the database is down: no context processor that queries, no `request.user` access.

---

### Task 1: The sections tag

**Files:** Create `apps/core/templatetags/navigation.py`, `templates/_company_nav.html`; Test `apps/core/tests/test_navigation.py`.

**Interfaces:** Produces `{% load navigation %}{% company_nav %}`, which takes context and reads `request`, `company`, `is_admin_view`. It renders the switcher and the tabs, or nothing. Python `sections(request, company, is_admin_view) -> list[dict(label, url, active)]`.

- [x] **Step 1: Write the failing tests:**

  ```python
  @pytest.mark.parametrize("role, expected", [
      ("Admins", ["Tablero", "Colaboradores", "Resultados", "Reportes"]),
      ("Principal Exec", ["Tablero", "Colaboradores", "Resultados", "Reportes"]),
      ("Secondary Exec", ["Tablero", "Colaboradores"]),
  ])
  def test_each_role_sees_its_sections(...)
  ```

  Each test builds the user with that group and a profile in `company`. It calls `sections()` with a `RequestFactory` request whose `resolver_match` is the dashboard's, and `is_admin_view` true for Admins only.

  Also:
  - `test_every_offered_section_opens_for_that_role`: GET each URL with that role's client and expect 200.
  - `test_an_employee_gets_no_sections`.
  - `test_a_child_page_lights_its_parent`, parametrized over `company_employee_detail` → Colaboradores, `reports:exec_detail` → Reportes, `company_results_fragment` → Resultados.
  - `test_fewer_than_two_sections_render_nothing`.
- [x] **Step 2: Run** `pytest apps/core/tests/test_navigation.py`. It should FAIL.
- [x] **Step 3: Implement.** `sections()` holds a tuple of `(label, admin_url_name, own_url_name, admin_perms, own_perms, url_names_lit)`, per the brief's table. It keeps the rows whose perms the user has. It reverses with `company.reference_code` when `is_admin_view`, and marks one active when the `resolver_match` view name is in `url_names_lit`. The tag returns `[]` without a `company`.

  `_company_nav.html` renders:
  - **Below `lg`:** `<details class="lg:hidden relative" data-disclosure>`, whose summary is a `btn btn-secondary` showing the active label and a `chevron-down` icon. The panel holds 48px links, with the active one carrying `aria-current="page"`.
  - **From `lg`:** a `<nav class="hidden lg:flex …" aria-label="Secciones de la empresa">` of tab links.

  Add the `chevron-down` icon from heroicons@2.2.0.
- [x] **Step 4: Run** `pytest -q`. It should PASS.

### Task 2: Header, user menu, page context

**Files:**
- Modify `templates/base_app.html`.
- Create `templates/_user_menu.html`, `templates/_page_context.html`, `static/ts/disclosure.ts`.
- Modify every template with `{% block header_nav %}`.
- Test `apps/core/tests/test_navigation.py`.

**Interfaces:**
- Consumes `{% company_nav %}`.
- Produces `{% block page_context %}` in `base_app.html`. Its default includes `_page_context.html`, which shows *Empresas / {company}* when `is_admin_view` and `company`.

- [x] **Step 1: Write the failing tests:**
  - No template contains `block header_nav`.
  - An admin on `/empresas/<code>/resultados/` sees `aria-current="page"` on Resultados and *Empresas* linked.
  - An executive sees no *Empresas*.
  - Employee detail renders *← Colaboradores* with the roster query string.
  - A respondent on `/` (survey list) does not see *Mis encuestas*, but does on the survey form.
  - The user menu shows the role label (`label_for_name`) and a logout form.
- [x] **Step 2: Run** them. They should FAIL.
- [x] **Step 3: Implement.**
  - **Header:** one row of the logo, then `{% company_nav %}`, then the *Mis encuestas* link (respondents only, when `request.resolver_match.url_name != "employee_survey_list"`), then `_user_menu.html`.
  - **User menu:** a `<details data-disclosure>` whose summary is the avatar. The panel holds the name, role label, email and the logout `<form>` with a `btn-text` button.
  - **`base_app.html`:** add `{% block page_context %}{% include "_page_context.html" %}{% endblock %}` at the top of `<main>`.
  - **Child pages:** override `page_context` with the back link (`btn btn-text btn-sm -ml-3`).
  - **Remove:** every `header_nav` block, and the survey's "← Inicio".
  - **The role label:** expose it to the template through a context processor value or a filter. Use a `role_label` filter in `navigation.py` that calls `labels_for_names(user.groups names)` and joins them.
  - **`disclosure.ts`:**
    - on Esc, close the open `details[data-disclosure][open]` and focus its summary
    - on a click outside, close it
    - on `toggle` to open, close the others
    - on `pageshow`, close all

    Load it in `base.html` with `defer`.
- [x] **Step 4:** Run `npm run build:css && npm run build:js && pytest -q`. It should PASS.

### Task 3: Dialogs

**Files:**
- Modify `static/css/main.css` (`.dialog`).
- Create `static/ts/dialog.ts`.
- Modify the four survey modals, `survey_detail.html`, `static/ts/survey_progress.ts`, `company_dashboard.html` and `employee_list.html`.
- Test `apps/core/tests/test_dialogs.py`.

- [x] **Step 1: Write the failing tests:**
  - No template contains `fixed inset-0`.
  - Every `<dialog` in `templates/` has `aria-labelledby="X"`, and `id="X"` exists in the same file.
  - The survey page with `?confirm=1` after answering everything (reuse the surveys test helpers) renders `id="submit-confirm-modal"` with `data-open-on-load`, and without it does not.
  - `session-expired-modal` carries `data-dialog-static`.
  - `.dialog` is compiled into `output.css`.
- [x] **Step 2: Run** them. They should FAIL.
- [x] **Step 3: Implement.**
  - **`.dialog` in the components layer:**
    ```css
    .dialog {
      @apply m-auto w-[calc(100%-2rem)] max-w-md max-h-[85vh] overflow-y-auto rounded-xl border-0 bg-white p-6 text-neutral-900 shadow-xl;
    }
    .dialog::backdrop {
      background: color-mix(in srgb, var(--color-neutral-900) 40%, transparent);
    }
    .dialog[open] {
      animation: dialog-in 150ms ease-out;
    }
    ```
    Define `@keyframes dialog-in`, from `opacity: 0; scale: .96`. Under `prefers-reduced-motion` set `animation: none`.
  - **`dialog.ts`:**
    - delegated clicks for `[data-dialog-open]` and `[data-dialog-close]`
    - a click whose target is the dialog element itself (the backdrop) closes it, unless static
    - `cancel` → `preventDefault` on `[data-dialog-static]`
    - on `DOMContentLoaded`, `showModal()` each `dialog[data-open-on-load]`
  - **Each modal** becomes `<dialog id=… class="dialog" aria-labelledby=…>`, keeping its content.
    - Buttons that hid it get `data-dialog-close`.
    - Openers get `data-dialog-open`.
    - The `{% if show_* %}<script>` blocks become `data-open-on-load` on the dialog.
  - **`survey_progress.ts`:** `(modal as HTMLDialogElement).showModal()`.
  - **Roster:** add `class="dialog"`, drop the duplicated utility classes, and keep `roster_filters.ts` working.
- [x] **Step 4:** Run `npm run build:css && npm run build:js && pytest -q`. It should PASS.

### Task 4: Empty states

**Files:** Create `templates/components/_empty.html`; modify the 11 templates with dashed cards and the styleguide; Test `apps/core/tests/test_empty_states.py`.

- [x] **Step 1: Write the failing tests:**
  - **The partial:** it renders the icon tile when given `icon`, the title, the body, and the action link with `btn-secondary`; `compact` uses the smaller padding.
  - **Guard:** no template outside `components/_empty.html` and the styleguide contains `border-dashed`.
  - **Roster:** the narrowed-empty roster renders *Limpiar filtros* through the partial.
- [x] **Step 2: Run** them. They should FAIL.
- [x] **Step 3: Implement** the partial per the brief, then replace each dashed card with an include carrying its current copy as `body`. Use icons where they fit: `users` for the roster, `document-text` for reports, `clipboard-document-list` for surveys, `chart-bar` for results. Download each from heroicons@2.2.0, and keep the icon-name test green.
- [x] **Step 4:** Run `npm run build:css && pytest -q`. It should PASS.

### Task 5: Error pages

**Files:**
- Create `templates/base_error.html`, `templates/404.html`, `templates/403.html`, `templates/500.html`.
- Modify `apps/core/views.py` (`server_error`) and `config/urls.py` (`handler500`).
- Test `apps/core/tests/test_error_pages.py`.

- [x] **Step 1: Write the failing tests.** All of them run with `DEBUG=False`.
  - `client.get("/no-existe/")` returns 404, containing "No encontramos esta página" and `brand.name`.
  - The styleguide as an employee returns 404 too.
  - A view raising `PermissionDenied`, for example `core:company_list` as an executive (it raises `PermissionDenied`; check it), returns 403 with "No tienes acceso a esta página".
  - `server_error(RequestFactory().get("/"))` returns 500 with "No pudimos cargar esta página", under `django_assert_num_queries(0)`.
  - None of the three templates contains "SOFIA".
- [x] **Step 2: Run** them. They should FAIL.
- [x] **Step 3: Implement.**
  - `base_error.html` mirrors `base_centered.html`'s card layout without `_messages.html`, and sets `data-palette` from `palette|default:"petrol"`.
  - `server_error` renders `500.html` with `{"brand": settings.BRAND, "palette": settings.BRAND_PALETTE_DEFAULT}` through `render_to_string` with no request, status 500.
  - `config/urls.py` sets `handler500 = "apps.core.views.server_error"`.
- [x] **Step 4:** Run `npm run build:css && pytest -q`. It should PASS.

### Task 6: Documentation

- [x] **Step 1:** In `docs/platform/design-system.md`, Scope → Components gains navigation, the dialog, empty states and error pages, per the brief, in present tense. Out of scope keeps pagination and the table component. Phone shape, Key decisions and Enforcement gain their entries.
- [x] **Step 2:** `docs/platform/responsive-layout.md` gets the header's phone shape. `apps/core/CLAUDE.md` gets the nav tag, page context, dialog and disclosure scripts, and error pages. `apps/surveys/CLAUDE.md` says the survey's dialogs are native `<dialog>`s. The `.claude/CLAUDE.md` Design-system bullet gets one sentence on `company_nav`, `.dialog`, `_empty.html` and the error pages.
- [x] **Step 3:** Run `pytest -q && ruff check . && ruff format --check .`. It should PASS.
