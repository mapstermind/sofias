# Design system — Phase 3: page pass

## What changes

**What.** Every page is brought onto the components and type roles of Phases 2a and 2b. The pass
adds five small pieces the pages share:

- a page-header partial
- `card-link`, a card that is a link
- `link`, an inline link in a sentence
- `chip`, a checkbox or radio worn as a pill
- `answer`, the survey's answer row

It also restructures two places that the header's navigation and the report's layout made
redundant: the dashboard's *Valoración de resultados* section, and the report's repeated chart
labels.

**Why.** The page audit found these problems:

- **All-caps labels.** There are 23 `uppercase tracking-wide` labels. The results page's two
  section "headings" are 14px gray labels.
- **Inconsistent headings.** Section `h2`s are `text-base` where the type roles say `text-lg`.
  Spacing under the page title is either `mb-5` or `mb-8`. The page title with its company
  subtitle is hand-written on seven pages. The login page has two `h1`s, and a survey module puts
  an `h3` before its `h2`.
- **Clickable cards in four styles.** Some have `border-2`, some have none, some add a hover
  shadow, and most end in "Ver … →".
- **Hover-only tooltips.** The explanation for a closed survey is a `bg-black` hover tooltip that a
  phone cannot reach, on a card at `opacity-60` whose text fails AA.
- **A broken phone layout.** On the dashboard, *Mi respuesta* sits beside the survey's progress
  card at every width (`style="flex: 3"` / `flex: 1`), so it is about 80px wide at 360px.
- **Hand-rolled leftovers:**
  - the survey's error banner, question card and instructions panel
  - the Guía I alert on employee detail
  - the results *Filtros* summary
  - `focus:ring` on the survey radios
  - hand-drawn focus outlines on two disclosure toggles
- **Tap targets under 44px:** the roster sort buttons, the results filter rows, and the dominio
  rows on employee detail.
- **Other one-offs:**
  - *Despublicar* uses `confirm()` from an inline `onsubmit`.
  - *Acerca de* uses an inline `onclick`.
  - The login page types the brand's meaning instead of reading `{{ brand.meaning }}`.
  - The footer's three columns wrap to several lines at 360px.
- **The report repeats itself.** A heading names a categoría, and the two charts under it each
  name it again: the distribution's label and the stats block's label. *Por dominio* and
  *Calificación final* do the same.
- **A selected survey answer is hard to see.** Respondents may struggle with devices, and the
  only sign of their choice is a 16px radio dot.

Copy rewrites (*¡Gracias!*, button wording) remain Phase 4's copy pass.

**Live doc sections this makes wrong:**

- In `docs/platform/design-system.md`:
  - *Scope → Components* gains the five pieces.
  - *Scope → Usage rules* gains the heading ladder and sentence-case labels.
  - *Out of scope → Page-by-page layout and copy changes* narrows to copy.
  - *Phone shape*, *Key decisions* and *Enforcement* gain their entries.
- `docs/platform/nom-035-results-dashboard.md`: the entry point is the dashboard's *Valoración de
  resultados* card (Scope list, and the section near line 439).
- `docs/platform/nom-035-report.md`: the report is reached "next to *Valoración de resultados*"
  (line 131), and the result sections' chart labels change.
- `docs/platform/survey-model.md`: the dashboard's *Mi respuesta* card (line 215).
- `apps/core/CLAUDE.md`: the *Valoración de resultados* and *Mi respuesta* cards (lines 27–33).
  `apps/surveys/CLAUDE.md` and `apps/reports/CLAUDE.md` describe markup that changes, and
  `.claude/CLAUDE.md`'s design-system paragraph lists the components.

**ADRs.** None touched. No ADR records the dashboard's sections or the report's chart labels.

## Design

### Shared pieces

**Page header.** `templates/components/_page_header.html` takes `title` and an optional
`subtitle`.

- The title is the page's one `h1`, at `text-xl font-bold text-neutral-900`.
- The subtitle is a `mt-1 text-sm text-neutral-600` paragraph.
- The wrapper carries `mb-6`.
- Pages whose title is drawn inside a card keep their own `h1`: employee detail (inside the
  identity card), the confirmation page and the centered sign-in screens.
- It is used by the dashboard, roster, results, report list, report detail, report form, company
  list, *Mis encuestas* and the survey.

**Heading ladder.**

| Element | Classes |
|---|---|
| Page title, `h1` | `text-xl font-bold text-neutral-900` |
| Page section, `h2` | `mt-10 mb-4 text-lg font-semibold text-neutral-900` (the first section after the page header drops `mt-10`) |
| Card title, `h3` | `text-base font-semibold text-neutral-900` |

**Sentence-case labels.** Every `uppercase tracking-wide` label becomes sentence case:

- A label for a value (a `dt`, a stat caption, a fieldset legend) is
  `text-sm font-medium text-neutral-600`.
- Column headers over a chart on the results page keep `text-xs`, since they label a graphic.
- `_avatar.html`'s initials keep `uppercase`.

**`card-link`.** A component class in `main.css` for a card that is wholly a link or a button:
`card` plus `flex items-center gap-4 transition-colors hover:border-primary-300`.

- The call site places a trailing `{% icon "chevron-right" "size-5 shrink-0 text-neutral-400 group-hover:text-primary-600" %}`
  and the `group` class.
- There is no hover shadow, no `border-2` and no "Ver … →" text.
- Focus comes from the base rule.

**`link`.** A component class for a link inside a sentence:
`font-medium text-primary-700 underline-offset-2 hover:underline`. It replaces the
`text-primary-600 hover:text-primary-500` links on the sign-in pages, the results area links and
*Acerca de*.

**`chip`.** A component class for the label of a visually hidden checkbox or radio (`peer sr-only`
input before it).

- It is `inline-flex min-h-11 items-center rounded-full border border-neutral-300 bg-white px-4 text-sm text-neutral-700 hover:bg-neutral-50`.
- From `sm` it is `min-h-9`.
- Checked state, applied by `peer-checked:` utilities that the class bundles: `primary-600`
  border and fill with white text.
- Keyboard focus is drawn by a `peer-focus-visible` outline that matches the base rule.
- It is used by the roster's filter dialog and the results filters.
- The removable filter chips above the results are links. They take
  `chip bg-primary-50 border-primary-200 text-primary-700` with an `x-mark` icon.

**Unavailable cards.** A closed or finished survey on *Mis encuestas* or the dashboard is a plain
`card`, not a link. It has no `opacity-60` and no hover tooltip. It shows its state pill and one
visible `text-sm text-neutral-600` line: *La encuesta cerró; ya no puedes ver tus respuestas.*
for a closed survey, and *Ya enviaste tus respuestas.* for a completed one.

**No inline layout styles.** `style="flex: …"` becomes grid classes that stack on a phone. Inline
`style` stays only for computed widths and offsets (bars, the threshold tick, the progress ring).

### Company pages

**Dashboard.**

- **Header:** the page header, with the company name as the title and *Código de referencia
  `ABC123`* as the subtitle (the code in `font-mono`).
- **Stats:** a `<dl>` grid, `grid-cols-2 lg:grid-cols-4`, of cards each holding a `dt` label and
  a `text-2xl` `dd`.
  1. *Colaboradores registrados*: `42 / 50`, the `primary-600` meter, and *84 %* as `text-sm`.
     It is a `card-link` to the roster when the viewer holds `can_manage_employees`, and a plain
     card otherwise.
  2. *Encuestas asignadas*.
  3. *Mínimo representativo*: a `card-link` `<button>` with `data-dialog-open="cochran-modal"`,
     carrying a `calculator` icon in place of the chevron. *Sin datos* when there is none.
  4. *Cuestionarios valorados*: shown only with `can_view_insights`, as a `card-link` to
     `results_url`. When the company has no NOM-035 assignment it reads *Sin encuestas NOM-035*.
- **Estado de encuestas:** an `h2` section with one card per assignment.
  - **Top:** the title and variant, then *Activa* or *Cerrada* and the due date, then the
    completion percentage at `text-2xl` with `completed / members` under it.
  - **The bar:** `primary-600` on `neutral-100`, with the threshold tick. Under the bar, when
    there is a threshold, a `text-xs` caption reads *Mínimo representativo: N respuestas*, next to
    a small tick swatch.
  - **The strip:** when `can_take_surveys`, a `border-t` strip at the bottom of the same card. It
    is labelled *Tu respuesta*, then holds either a `btn btn-primary btn-sm` *Responder* (the
    survey is active and the viewer hasn't completed it) or the *Completada* / *Cerrada* pill with
    its one-line reason. It stacks on a phone.
  - **Empty:** the existing empty state.
- **The *Valoración de resultados* section is removed.** Results are reached from stat 4 and the
  header; reports from the header. A viewer with `can_view_insights` always holds two sections, so
  the switcher shows.

**Roster.**

- **Sort control:** each option is `min-h-11 sm:min-h-9 px-3 text-sm`.
- **Filter dialog:** its pills become `chip`.
- **Headings:** the page header replaces the hand-written one.

**Employee detail.**

- **Layout:** the identity and progress cards sit in `grid gap-4 lg:grid-cols-2`.
- **Labels:** the `dl` labels are sentence case.
- **Guía I warning:** `_alert` with `tone="danger"`.
- **Dominio rows:** the summaries and plain rows are `min-h-11 lg:min-h-0 lg:py-0.5`, with the
  hand-drawn focus outline classes removed.
- **Answer modules:** their `h3` is `text-base font-semibold text-neutral-900`.
- **Section headings:** the `h2`s follow the ladder.

**Results.**

- ***Filtros*:** the summary becomes `btn btn-secondary`, with the `funnel` icon and the same
  count badge as the roster, hiding the browser's marker. The options become chips, grouped under
  sentence-case legends.
- **Headings:** the body's two headings become `h2` *Empresa* and *Por categoría*.
- **Card titles:** *Distribución de la calificación final*, *Estadística de la calificación final*
  and *Guía I: acontecimientos traumáticos severos* replace the em-dash titles.
- **Links:** the area links take `link`.

**Reports.**

- **List:** each row is an `<a>` with the label, the count line, the state pill and a trailing
  chevron, inside the one `card` with dividers. *Abrir →* goes.
- **Detail:** *Despublicar* opens a `<dialog id="unpublish-dialog">` holding the existing
  sentence and two actions: *Cancelar* (`btn-secondary`, `data-dialog-close`) and *Despublicar*
  (`btn-danger`, the form's submit). The inline `onsubmit` goes.
- **Form:** its `h2`s follow the ladder.
- **Result sections (screen and PDF):** say the subject once.
  - `_stats.html` takes its label from an optional `label` argument, defaulting to `row.label`.
  - *Por categoría*: the `h4` names the categoría. The distribution chart is captioned
    *Distribución por nivel*, and the stats block is captioned *Calificación*.
  - *Por dominio*: the `h4` names the categoría and each dominio's name appears once. Its two
    charts take the same captions.
  - *Calificación final*: the stats block is captioned *Calificación*.
  - Captions use a new `.report-caption` (the `report-small` size, `neutral-600`).

**Company list.** Each company is a `card-link`. Its three counts are a left-aligned `dl` with
sentence-case labels.

### Survey and sign-in pages

**`answer`.** A component class for a survey option's `<label>`:
`flex min-h-11 cursor-pointer items-center gap-3 rounded-lg border border-neutral-200 bg-white px-3 py-2.5 transition-colors hover:bg-neutral-50 has-[:checked]:border-primary-600 has-[:checked]:bg-primary-50`.

- Its input is `size-5 shrink-0 accent-primary-600`, with no `focus:ring`.
- Single choice, multiple choice and *Sí/No* are rows. *Sí/No* sits in
  `grid gap-2 lg:grid-cols-2`.
- Likert and rating are rows on a phone. From `lg` they are a `grid-cols-5` grid of tiles: the
  label `lg:flex-col lg:justify-center lg:text-center`, the radio above its text, and the text at
  `text-sm` in `neutral-700`.
- The highlight is a selection, not a status. It is `primary` whatever the answer.

**The rest of the survey page.**

- **Question card:** `card p-5 mb-6`, with `border-danger-300` when it holds an error.
- **Error banner:** `_alert` with `tone="danger"`.
- **Instructions panel (desktop):** `card p-4`.
- **Module intro:** a `text-base font-semibold text-neutral-900` paragraph.
- **Module title:** an `h2` at `text-lg font-semibold text-neutral-900`.
- **Progress bar:** `primary-600`.
- **Page header:** the survey title uses it.

**Confirmation page.** The icon sits in a 48px `success-100` circle, the same as the dialog's
icon circle, and the card's padding is `p-8 sm:p-10`.

***Mis encuestas*.** An open survey is a `card-link` holding the title, the *Activa* pill and the
due date. A closed or finished one is the unavailable card above.

**Sign-in.**

- **Login:** one `h1`, *Inicio de sesión por correo*. `{{ brand.meaning }}` is shown once, under
  the logo, as a `text-sm text-neutral-600` line from `base_centered.html`'s header block on the
  login page only.
- ***Otras formas de ingresar*:** two `card-link`s stacked under the card, in its column. The
  `sm:w-[42rem] -translate-x-1/2` workaround goes.
- **Footer links:** on the four sign-in screens they take `link`.

***Acerca de*.** It extends `base_centered.html` with `container_width` `max-w-xl`. Its prose is
`text-base`. *← Regresar* and its `onclick` become a `link` to *Ir al inicio*.

**Footer.** `flex flex-col items-center gap-1` on a phone, and the three-column grid from `sm`.

### Decisions

- **Labels are sentence case.** An all-caps tracked label is a template's default, not a choice,
  and it is slower to read.
- **The selected answer's highlight is a selection, not a status.** One `primary` treatment for
  every answer keeps the rule that an answer is never right or wrong.
- **The dashboard does not repeat the header's navigation.** The sections are one tap away from
  every page. A dashboard entry earns its place with a number, as *Cuestionarios valorados* does.
- **A report names a subject once and captions each chart by what it shows.** The results page
  lists stats rows together, so there each row keeps its name. The report sets each chart under
  its own heading.
- **Closed surveys explain themselves in text, not a tooltip.** A hover tooltip doesn't exist on a
  phone.

### Tests

- **`test_design_tokens.py` guards:**
  - no `uppercase` in `templates/` except `_avatar.html`
  - no `bg-black` or `text-black`
  - no `style="flex`
  - no `onclick=` or `onsubmit=` in `templates/`
  - no `focus:ring` on an `input`
  - no template types `settings.BRAND["meaning"]`
  - `card-link`, `link`, `chip` and `answer` are in the built CSS
- **`test_pages.py`:** each main page, rendered for the role that sees it, has exactly one `h1`.
- **Dashboard:**
  - There is no *Valoración de resultados* and no *Código de referencia* stat; the code appears
    in the subtitle.
  - *Cuestionarios valorados* links to results only with `can_view_insights`.
  - *Tu respuesta* appears only for a viewer who may take surveys.
  - The threshold caption renders.
- **Survey:**
  - Every radio and checkbox in a rendered question sits inside an `answer` label.
  - Errors render through the alert.
  - No module renders an `h3` before its `h2`.
- **Report:**
  - Under *Por categoría* and *Por dominio*, each categoría's and dominio's name appears once per
    block, and *Calificación final* isn't repeated.
  - The results page still labels each stats row.
  - *Despublicar* is a dialog form with no `onsubmit`.
- **Look and layout:** the highlight, tiles, stacking and hover are checked in the browser.

### Out of scope

- **Copy.** The copy pass is Phase 4, including *¡Gracias!* and button wording, except the two
  closed-survey lines, which replace the tooltip.
- **The PDF's layout,** beyond the chart captions.
- **Roster pagination.**
- **Removing the losing palette.**

---

# Phase 3 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: superpowers:executing-plans (native). Steps use
> checkbox (`- [ ]`) syntax. Never commit: the user reviews the uncommitted diff.

**Goal:** Every page uses the Phase 2 components and type roles, plus the five shared pieces in the
brief above.

**Architecture:** Four component classes in `static/css/main.css`'s `@layer components`, one
partial (`components/_page_header.html`), then one task per page group. Guards come last, once
every page passes them. Views change only where the dashboard needs a value it doesn't have.

**Tech Stack:** Django 6 templates, Tailwind v4 (`npm run build:css`), TypeScript (`npm run
build:js`), pytest.

**Spec:** the brief above (`## What changes` and `## Design`).

## Global Constraints

- Colors only from `primary`, `accent`, `neutral`, `series`, `success`, `warning`, `danger`.
- User-facing copy stays as it is (Phase 4), except the two closed-survey lines, the three
  results card titles and the report captions, which the brief names.
- Mobile-first: unprefixed classes describe the phone. Tap targets are 44px on a phone.
- No inline `style` except computed widths and offsets; no inline `on*=` handlers.
- After touching templates or TS: `npm run build:css` / `npm run build:js`.
- Each task ends with `pytest`, `ruff check .` and `ruff format --check .` green.

## Review Focus

1. **A respondent reloads or goes back after answering.** The selected row must stay
   highlighted. `has-[:checked]` reads the restored state, so this needs no script. The test
   asserts the class is on the label holding a `checked` input.
2. **An executive without `can_manage_employees`** (Ejecutivo secundario has it; an Empleado
   doesn't reach the dashboard). The registered stat must be a plain card, not a dead link
   (Task 2).
3. **A company with no NOM-035 assignment.** *Cuestionarios valorados* says *Sin encuestas
   NOM-035* and still renders (Task 2).
4. **A dominio name shared by two categorías.** Its name must still appear once per block, not
   once per page. The test counts within the block (Task 5).
5. **The unpublish dialog without JavaScript.** The dialog never opens, so the form must not be
   reachable by a submit outside it. The submit lives inside the dialog, and the opener is a
   `type="button"` (Task 5).

---

### Task 1: Shared pieces

**Files:**
- Modify: `static/css/main.css` (`@layer components`)
- Create: `templates/components/_page_header.html`
- Test: `apps/core/tests/test_components_css.py`

- [x] **Step 1: Failing test.** Add `"card-link", "link", "chip", "answer"` to `COMPONENTS` in
  `test_components_css.py`. Run `pytest apps/core/tests/test_components_css.py`: four fail.
- [x] **Step 2: Classes.** In `@layer components`:

```css
  /* A card that is wholly a link or a button; the call site adds `group` and a
     trailing chevron (or icon). */
  .card-link {
    @apply flex items-center gap-4 text-left transition-colors hover:border-primary-300;
  }
  /* An inline link inside a sentence. */
  .link {
    @apply font-medium text-primary-700 underline-offset-2 hover:underline;
  }
  /* The label of a visually hidden checkbox or radio (`peer sr-only` before it). */
  .chip {
    @apply inline-flex min-h-11 cursor-pointer items-center gap-1.5 rounded-full border border-neutral-300 bg-white px-4 text-sm text-neutral-700 transition-colors select-none hover:bg-neutral-50 sm:min-h-9;
    @apply peer-checked:border-primary-600 peer-checked:bg-primary-600 peer-checked:text-white peer-checked:hover:bg-primary-700;
    @apply peer-focus-visible:outline-2 peer-focus-visible:outline-offset-2 peer-focus-visible:outline-primary-500;
  }
  /* A survey option. The selected row is a selection, never a status. */
  .answer {
    @apply flex min-h-11 cursor-pointer items-center gap-3 rounded-lg border border-neutral-200 bg-white px-3 py-2.5 transition-colors hover:bg-neutral-50;
    @apply has-[:checked]:border-primary-600 has-[:checked]:bg-primary-50;
  }
  .answer > input {
    @apply size-5 shrink-0 accent-primary-600;
  }
```

- [x] **Step 3: The partial.** `templates/components/_page_header.html`:

```django
{% comment %}
The page's one h1, with an optional subtitle. `{% include "components/_page_header.html" with title=… subtitle=… %}`
{% endcomment %}
<div class="mb-6">
  <h1 class="text-xl font-bold text-neutral-900">{{ title }}</h1>
  {% if subtitle %}<p class="mt-1 text-sm text-neutral-600">{{ subtitle }}</p>{% endif %}
</div>
```

- [x] **Step 4:** `npm run build:css`, then run the test: it passes.

### Task 2: Dashboard

**Files:**
- Modify: `templates/core/company_dashboard.html`
- Modify: `apps/core/views.py` (`CompanyDashboardView`), only if `results_url` or
  `latest_scored_count` is missing for some viewer
- Test: `apps/core/tests/test_dashboard_results_card.py` (rewrite), plus a new
  `apps/core/tests/test_dashboard_page.py`

- [x] **Step 1: Failing tests** in `test_dashboard_page.py`, against the principal-exec dashboard
  (pattern as in `test_app_header.py`'s `dashboard` fixture):
  - `"Valoración de resultados" not in html`
  - The reference code is in the subtitle, not a `dt`: there is no `>Código de referencia</dt>`,
    and `company.reference_code` is inside the `mb-6` header.
  - A user with `can_view_insights` gets the `Cuestionarios valorados` `dt` inside an `<a` whose
    `href` is the results URL. A Secondary Exec gets no `Cuestionarios valorados`.
  - With an `active_assignment` and a viewer in Employees + Principal Exec (who may take
    surveys), `Tu respuesta` and `Responder` render. A viewer without
    `can_take_assigned_surveys` gets no `Tu respuesta`.
  - With a representative threshold, the caption `Mínimo representativo:` renders under the bar.
  - A Secondary Exec without `can_manage_employees`: check `bootstrap_groups`. If every
    dashboard viewer holds it, assert instead that the registered stat is a link for the
    principal exec.
- [x] **Step 2: Rewrite `test_dashboard_results_card.py`** so it asserts the stat card (not the
  removed section) links to results, and is hidden without the permission.
- [x] **Step 3: Rewrite the template** as the brief's *Dashboard* says:
  - the page header with the code subtitle (`subtitle` built with `{% with %}` or a `<p>` the
    partial accepts, using `font-mono` on the code: add an optional `meta_mono` parameter to the
    partial *only if needed*; otherwise render the header inline with the same classes)
  - the `<dl>` stat grid with `card-link`s
  - Cochran's `<button class="card card-link group …" data-dialog-open="cochran-modal">`
  - one card per assignment, with the *Tu respuesta* strip
  - the *Valoración* section removed

  No `style="flex`, no `uppercase`, no `bg-black`, no "→".
- [x] **Step 4:** `npm run build:css`, then run `pytest apps/core`: green.

### Task 3: Roster, employee detail, company list

**Files:**
- Modify: `templates/core/employee_list.html`, `templates/core/employee_detail.html`,
  `templates/core/company_list.html`
- Test: `apps/core/tests/test_roster.py`, `apps/core/tests/test_employee_valuation_panel.py` (as
  they break), plus new assertions in `test_pages.py` (Task 8)

- [x] **Step 1: Roster.**
  - The page header (`title="Colaboradores" subtitle=company.name`).
  - The sort buttons become `min-h-11 sm:min-h-9 px-3 text-sm`.
  - The filter-dialog labels become `class="chip"`.
- [x] **Step 2: Employee detail.**
  - `grid gap-4 lg:grid-cols-2` in place of the `flex` + `style`.
  - Sentence-case `dt`s (`text-sm font-medium text-neutral-600`).
  - Guía I becomes `{% include "components/_alert.html" with tone="danger" body="Usuario positivo a un acontecimiento traumático severo." %}`.
  - Dominio rows get `min-h-11 lg:min-h-0`, without the `focus-visible:outline-*` classes.
  - The module `h3` becomes `text-base font-semibold text-neutral-900`.
  - The section `h2`s follow the ladder.
- [x] **Step 3: Company list.**
  - The page header.
  - Each card is `card card-link group px-6 py-5` holding a `div.min-w-0.flex-1` and a chevron.
  - The `dl` is left-aligned with sentence-case `dt`s.
- [x] **Step 4:** `npm run build:css`, then `pytest apps/core`: green. Fix any test that pinned
  the old markup by asserting the new contract, not by loosening it.

### Task 4: Results page

**Files:**
- Modify: `templates/core/company_results.html`, `templates/core/results/_body.html`,
  `_participation.html`, `_final_distribution.html`, `_final_stats.html`, `_guia1.html`,
  `_group_line.html`, `_dominios_summary.html`
- Test: `apps/core/tests/test_results_views.py`

- [x] **Step 1: Failing test.** The rendered results page has `<h2` around *Empresa* and *Por
  categoría*, and has no `uppercase`. The *Filtros* summary carries `btn btn-secondary`. Every
  filter input is followed by a `class="chip"` label. The titles *Distribución de la calificación
  final* and *Guía I: acontecimientos traumáticos severos* render.
- [x] **Step 2: Implement.**
  - The page header.
  - The summary becomes `btn btn-secondary [&::-webkit-details-marker]:hidden list-none` with
    the funnel icon and a count badge.
  - Each option becomes `<span><input class="peer sr-only" id=… …><label for=… class="chip">…</label></span>`
    in a `flex flex-wrap gap-2` row under a sentence-case `legend`.
  - The section `h2`s follow the ladder.
  - The three titles are retitled.
  - The participation header labels lose `uppercase tracking-wide`.
  - Area links take `link`.
  - The group-line pills become `chip bg-primary-50 border-primary-200 text-primary-700` with
    `{% icon "x-mark" "size-4" %}`.
  - `_dominios_summary.html` loses its hand-drawn outline.
- [x] **Step 3:** Check `static/ts/results_dashboard.ts` still finds its hooks (`data-filter-count`,
  `data-results-link`, the form id). Then `npm run build:css` and `npm run build:js`, then
  `pytest apps/core`: green.

### Task 5: Reports

**Files:**
- Modify: `templates/reports/report_list.html`, `report_detail.html`, `report_form.html`,
  `sections/results/_stats.html`, `_categoria.html`, `_dominio.html`, `_final.html`,
  `static/css/report.css`
- Test: `apps/reports/tests/test_results_sections.py`, `apps/reports/tests/test_admin_views.py`

- [x] **Step 1: Failing tests.**
  - In `test_results_sections.py`, render the report body for `scored_assignment`. In the
    `sec-…categoria…` section, every categoría label appears exactly once inside each
    `report-page-group` block. In the dominio section, every dominio label appears once inside
    its `report-group` block. In the final section, `Calificación final` appears only in the
    `h3`. `Distribución por nivel` and the `report-caption` class render.
  - In `test_admin_views.py`, a published report's detail page has
    `<dialog id="unpublish-dialog"`, the unpublish form inside it, and no `onsubmit`.
- [x] **Step 2: `_stats.html`.**
  - `<span class="report-stats-label">{% firstof label row.label %}</span>`. When the caller
    passes `label=""`, use `{% if label is not None %}` logic via a `with`-supplied flag:
    `hide_label=True` drops the span entirely.
  - The callers become:
    - `_categoria.html`: `<p class="report-caption">Distribución por nivel</p>` before the chart,
      `<p class="report-caption">Calificación</p>` before the stats, which are included with
      `hide_label=True`.
    - `_dominio.html`: the dominio name stays as `report-group-label`, with the same two
      captions, and stats with `hide_label=True`.
    - `_final.html`: a `Calificación` caption, and stats with `hide_label=True`.
- [x] **Step 3: `report.css`:** `.report-caption` uses the `report-small` font size, `color:
  var(--brand-neutral-600)`, and `margin: .5rem 0 .25rem`.
- [x] **Step 4: List and detail.**
  - The list rows become `<a class="group flex … hover:bg-neutral-50">` with a chevron, and
    *Abrir* goes.
  - Detail:
    - The *Despublicar* `btn-danger` becomes a `type="button"` with
      `data-dialog-open="unpublish-dialog"`.
    - `<dialog id="unpublish-dialog" class="dialog" aria-labelledby="unpublish-dialog-title">`
      holds the title *¿Despublicar el reporte?*, the existing sentence, and the actions row:
      *Cancelar* (`data-dialog-close`) and the form with `data-loading` and the `btn-danger`
      submit.
  - The page header goes on the list and detail pages, and the form's `h2`s follow the ladder.
- [x] **Step 5:** `npm run build:css`, then `pytest apps/reports apps/core`: green. Also run the
  PDF test (`test_pdf.py`) to confirm WeasyPrint accepts the caption.

### Task 6: Survey, *Mis encuestas*, confirmation

**Files:**
- Modify: `templates/surveys/_question.html`, `survey_detail.html`, `survey_submitted.html`,
  `templates/core/employee_survey_list.html`
- Test: `apps/surveys/tests/test_answer_controls.py`, `apps/surveys/tests/test_views.py`

- [x] **Step 1: Failing tests.**
  - Every `type="radio"`/`type="checkbox"` in a rendered question sits in a `<label class="answer`.
  - No `focus:ring` in `_question.html`.
  - A POST with a missing answer renders the danger alert (`role="alert"`).
  - The rendered survey has no `<h3` before the first module `<h2`.
  - *Mis encuestas* for a closed assignment shows `La encuesta cerró; ya no puedes ver tus
    respuestas.` and no `bg-black`.
- [x] **Step 2: `_question.html`.**
  - Every option label becomes `class="answer"` (plus `lg:` tile classes for likert and rating:
    `lg:min-h-20 lg:flex-col lg:justify-center lg:gap-2 lg:text-center`, with the containers
    `flex flex-col gap-2 lg:grid lg:grid-cols-5`).
  - Inputs drop their classes, since `.answer > input` styles them.
  - *Sí/No* goes in `grid gap-2 lg:grid-cols-2`.
  - The card becomes `card p-5 mb-6` with `border-danger-300` on error.
  - Likert text becomes `lg:text-sm lg:text-neutral-700`.
- [x] **Step 3: `survey_detail.html`.**
  - The page header.
  - The errors render through `_alert`.
  - The instructions panel becomes `card p-4`.
  - The intro becomes a `p` and the module title an `h2` in `neutral-900`.
  - The progress bar is `bg-primary-600`.
- [x] **Step 4: Confirmation and *Mis encuestas*.**
  - Confirmation: a `size-12` success circle and `p-8 sm:p-10`.
  - *Mis encuestas*: open surveys are `card-link`s with a chevron. Closed ones are plain cards
    with the line, and completed ones say `Ya enviaste tus respuestas.`
- [x] **Step 5:** Check `static/ts/survey_progress.ts` still finds `.question-card`, `legend`,
  `.module-card` and `data-*`; keep those hooks. Then `npm run build:css` and
  `pytest apps/surveys apps/core`: green.

### Task 7: Sign-in, *Acerca de*, footer

**Files:**
- Modify: `templates/accounts/login_request.html`, `login_verify.html`, `login_password.html`,
  `login_setup_access_code.html`, `templates/core/about.html`, `templates/_footer.html`,
  `templates/base_centered.html` (only for a `brand_line` block)
- Test: `apps/accounts/tests` (whichever render the login pages), `apps/core/tests/test_brand.py`

- [x] **Step 1: Failing tests.**
  - The login page has exactly one `<h1` and shows `settings.BRAND["meaning"]`.
  - `about` has no `onclick`.
- [x] **Step 2: Implement.**
  - `base_centered.html` gains `{% block brand_line %}{% endblock %}` under the logo.
  - The login page fills that block with `<p class="-mt-3 mb-4 text-sm text-neutral-600">{{ brand.meaning }}</p>`,
    keeps the one `h1`, and turns the footer options into two stacked `card card-link group px-4 py-4`.
  - The four pages' footer links take `link`.
  - `about.html` extends `base_centered.html` (`container_width` `max-w-xl`) with `text-base`
    prose and a closing `<a class="link" href="{% url 'core:home' %}">Ir al inicio</a>`.
  - Footer: `flex flex-col items-center gap-1 sm:grid sm:grid-cols-12`, keeping each item's
    `sm:` alignment.
- [x] **Step 3:** `npm run build:css`, then `pytest`: green.

### Task 8: Guards and the one-h1 check

**Files:**
- Modify: `apps/core/tests/test_design_tokens.py`
- Create: `apps/core/tests/test_pages.py`

- [x] **Step 1: Guards** in `test_design_tokens.py`, each walking `templates/**/*.html` (the
  file's existing helper):
  - `uppercase` appears only in `_avatar.html`
  - `bg-black` and `text-black` appear nowhere
  - `style="flex` appears nowhere
  - `onclick=` and `onsubmit=` appear nowhere
  - no `<input` tag carries `focus:ring`
  - `settings.BRAND["meaning"]` is typed in no template
- [x] **Step 2: `test_pages.py`.** Parametrize over `(role, url)` for the dashboard, roster,
  employee detail, results, report list, company list (admin), *Mis encuestas*, the survey, the
  confirmation, the four sign-in pages (anonymous) and *Acerca de*. Each response is 200 and
  `html.count("<h1") == 1`. Report detail and form need a report; take
  `apps/reports/tests/conftest.py`'s fixture there if it's simple, otherwise cover them in
  `test_admin_views.py`.
- [x] **Step 3:** `pytest`: green. Any failure is a page Tasks 2–7 missed; fix the page.

### Task 9: Documentation

**Files:**
- Modify: `docs/platform/design-system.md`, `nom-035-results-dashboard.md`,
  `nom-035-report.md`, `survey-model.md`, `responsive-layout.md` (if a page shape it names
  changed), `apps/core/CLAUDE.md`, `apps/surveys/CLAUDE.md`, `apps/reports/CLAUDE.md`,
  `.claude/CLAUDE.md`

- [x] **Step 1:** `design-system.md`, in present tense with no migration wording, gets
  everything the brief's *Live doc sections this makes wrong* lists. *Status* names the new
  partial.
- [x] **Step 2:** The feature docs and CLAUDE.md lines the brief names.
- [x] **Step 3:** `grep -rn "Valoración de resultados\" card\|Mi respuesta" docs apps .claude`
  turns up nothing stale. Then `pytest`, `ruff check .`, `ruff format --check .`, and
  `npm run build:css` and `npm run build:js` with no diff left behind.
- [x] **Step 4:** Hand the user the browser checklist, at 360px and desktop in both palettes.

### Browser-review follow-ups

- [x] Roster *Ordenar por*: label above, three buttons split the width on a phone (no truncation).
- [x] Employee detail dominio and dimension rows: the name wraps instead of pushing the score and
      pill off the card; `pill` no longer wraps.
- [x] Dashboard: *Código de referencia* panel beside the title, large monospace, *Copiar*
      (`static/ts/copy.ts`), one line on what it is for.
- [x] One filter bar: `components/_filter_buttons.html` and `_filter_dialog.html` shared by the
      roster and Resultados; `static/ts/filter_dialog.ts` replaces `roster_filters.ts`; Resultados
      gains the dialog, *Limpiar filtros* and a count of dimensions; sexo un-chooses instead of
      *Todos*; one localidad offers no localidad filter.
