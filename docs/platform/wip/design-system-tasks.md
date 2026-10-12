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

---

# Design system — Phase 4: copy and UX

## What changes

Phase 4 makes the product read as one voice and work for a keyboard, a screen reader and a
flaky connection. The design system's *Out of scope: Copy* becomes a **Voz** section in
`docs/platform/design-system.md`; every user-visible string is checked against it (the copy list
below, reviewed before it is applied); the survey gets the fixes a respondent meets 61–87 times;
and the app gains an accessibility floor it does not have today.

Why: the audit found English on screens and in the sign-in email, placeholder instructions shown
to every respondent, three meanings of *registrado*, three overlapping names for codes, silent
autosave failures, a survey read in the wrong order, and no skip link.

Live docs this makes wrong (rewritten in the plan's last task, not before):

- `design-system.md` — *Out of scope: Copy*; a new *Voz* section and glossary; skip link, busy
  default, alerts; the dashboard panel's *Código de referencia*.
- `survey-model.md` — the save-state line, error handling (Spanish, values kept, focus), reading
  order, instructions.
- `auth-and-onboarding.md`, `setup-access-codes.md` — *código de empresa* / *código de acceso*;
  `next` after sign-in; the Spanish email; the CSRF page; *quien te invitó*.
- `nom-035-report.md`, `apps/reports/CLAUDE.md` — *Retirar publicación*; fields needed to publish.
- `localization.md` — its glossary: *puesto*, not *cargo*; the Voz glossary links to it rather
  than repeating it. `employee-roster.md`, `auth-and-onboarding.md`, `csv-user-import.md`,
  `docs/internal/user-guides/user-onboarding.md`, `apps/accounts/CLAUDE.md` — *puesto*.
- `nom-035-results-dashboard.md` — empty results offer *Limpiar filtros*; the dimmed body while
  loading; the sex/age captions.

ADRs: none touched. Metadata-only migrations (no column changes): `accounts`
(`UserProfile.position` → *puesto*) and `reports` (`ReportSignatory.title` → *puesto*, and row
89's *teletrabajo*).

## Design

### Voz (the rules the copy list applies)

- **Tú, always.** The NOM-035 questions keep the norm's own wording, which speaks *usted*; the
  instructions say they are the official questions.
- **Buttons are verbs**, in sentence case, naming what happens: *Guardar reporte*, *Enviar
  respuestas*, *Retirar publicación*. The confirmation reuses the button's word: *Reporte
  guardado.*, *Respuestas enviadas*, *Publicación retirada.* One action keeps one name through a
  flow (*Seguir respondiendo*, never also *Seguir editando*).
- **No ¡…!, no *por favor*, no *lo sentimos*, no *exitosamente*.** Thanks are said once, plainly.
- **An error says what happened and how to fix it**: *El código no es correcto o ya venció.
  Revisa los 6 dígitos o pide uno nuevo.* Never *Error* or *inválido* alone.
- **An empty screen offers the next step** when the reader has one; otherwise it says when the
  space fills.
- **Plain words over system words**: no *valorado*, *vinculado*, *configurado*, *congelado*,
  *sesión* as a technical term, *usuario*, *UserProfile*.
- **Punctuation**: full sentences in messages end with a period; buttons, labels and headings do
  not. A space before `%`. Tab titles are `Página | Contexto | Marca`. A year range takes an en
  dash. Opening `¿`.
- **Glossary** (one word per concept):

  | Concept | Word |
  |---|---|
  | A person in the company, whatever their role | *colaborador*; the `Employees` role stays *Empleado* |
  | What is assigned and answered | *encuesta* |
  | One person's completed survey, counted | *cuestionario contestado*, where the count was called *respuestas*; *cuestionarios valorados* stays where it counts scored ones |
  | Account state | *activar*: *Cuenta activada* / *Sin activar* |
  | 5-character company code | *código de empresa* |
  | 9-digit first-login code | *código de acceso* |
  | 6-digit emailed code | *código de inicio de sesión* (short: *código*) |
  | Signing in | *iniciar sesión*; the first-login path stays *Primer ingreso* |
  | Who hands out codes | *quien te invitó* |
  | Job title, for a colaborador and a report signatory | *puesto* (never *cargo*) |
  | Back to the survey form | *Seguir respondiendo* |
  | Removing a report's publication | *Retirar publicación* |
  | Remote staff | *teletrabajo* |
  | The NOM-035 result | *valoración* (as in `localization.md`); Guía I keeps *valoración clínica* |

### The survey

- **Reading order.** The form comes before the sidebar in the HTML (it already does on screen):
  title, questions, then progress and *Pendientes*. Headings run h1 → h2.
- **The bar never hides the focused question.** Below `lg`, the page's scroll padding clears the
  fixed action bar, so a question tabbed into stays above it.
- **Save state.** Under the progress bar, a polite live line: *Guardando…* → *Cambios guardados*;
  on a network error, a 5xx or a 403 for a stale token, *No se pudo guardar. Revisa tu conexión y
  presiona Guardar progreso.* in the danger tone; on a closed survey, *La encuesta cerró; ya no se
  guardan cambios.* A 401 keeps the session-expired dialog.
- **Errors after *Guardar*.** Spanish messages; the values just posted are rendered back rather
  than the stored answers; each question in error carries `aria-invalid` and `aria-describedby`
  to its message; the danger alert at the top says how many answers need fixing, links to the
  first, and takes focus on load.
- ***Progreso guardado*** opens with focus on *Seguir respondiendo*.
- ***Pendientes*** jumps without smooth scrolling under `prefers-reduced-motion`.
- **Instructions** — the norm's own points (Guía II/III, *cómo aplicarse*, item 5); the YouTube
  link stays as it is:

  > Este cuestionario identifica los factores de riesgo psicosocial en tu trabajo, como lo pide la
  > NOM-035. Sus preguntas son las oficiales de la norma.
  >
  > - Responde pensando en las condiciones de tu trabajo durante los dos últimos meses.
  > - No hay respuestas correctas ni incorrectas. Tu opinión es lo más importante, así que
  >   contesta con sinceridad.
  > - Contesta todas las preguntas. Algunas aparecen según lo que respondas antes.
  > - Tus datos se manejan con privacidad y confidencialidad, y se usan solo para mejorar el
  >   ambiente de trabajo.
  > - Cada respuesta se guarda al elegirla. Puedes salir y volver cuando quieras; al terminar,
  >   presiona *Enviar respuestas*.

  It does not promise the company sees only group results: an executive with
  `can_view_submissions` sees a colaborador's answers.

### Across the app

- **Skip link** *Saltar al contenido*: the first tab stop on every layout, visible on focus,
  targeting `#main`.
- **Busy by default.** Every POST form's submit shows the spinner and blocks a second press;
  a form opts out with `data-no-busy`. (Today four forms opt in.)
- **Sign back in where you were.** The login views honour `next` when
  `url_has_allowed_host_and_scheme` accepts it; the session-expired dialog passes the survey's
  URL as `next`.
- **Expired security token** — a Spanish CSRF-failure page (`CSRF_FAILURE_VIEW`) on the centered
  card: the page was open too long or in another tab; reload it and try again.
- **Forms.** The date of birth's three selects get labels (*Día*, *Mes*, *Año*); after a failed
  submit, autofocus moves to the first field in error.
- **Results.** While a swap loads, `#results-body[aria-busy]` dims; after a chip or área link,
  focus moves to the group line; the filtered empty state offers *Limpiar filtros*.
- **A closed or completed survey link** redirects home with a message saying which.
- **The sign-in email** is Spanish and names the product.
- **Performance.** Figtree is served to browsers as WOFF2 (the PDF keeps the TTFs); `output.css`
  is built with `--minify`.

### Decisions

- Decision: copy is reviewed as a list before it is applied. Reason: the words are the product's
  voice and some rows depend on facts only the owner knows.
- Decision: *quien te invitó*, not a named department. Reason: the client decides who runs the
  rollout; the invitation is the one thing every colaborador received.
- Decision: the NOM-035 questions stay verbatim, including the Guía I question's missing `¿`.
  Reason: `Guias de Referencia.md` is the authority and prints it that way.
- Decision: the report's required-to-publish fields stay optional on save; only their labels
  change. Reason: a draft is saved half-written on purpose.
- Decision: no Lighthouse gate. Reason: no runner in the repo; a keyboard and screen-reader
  checklist goes in the PR.

### Out of scope

- **Account enumeration** on *Iniciar sesión* (*No hay ninguna cuenta con este correo*) — a
  security change with its own route. Its wording is still fixed here.
- **The charts' 10px value labels** — shared with the PDF; a PDF pass.
- **The report screen's second `h1`** — the cover's, which the PDF needs.
- **The Django admin's own chrome**; the CSV import page's copy is in the list because an
  operator reads it.
- **Removing the losing palette; roster pagination.**

### Copy list

Strike a row to keep the current text, or edit *Proposed*. `—` in *Now* means an addition.

#### Sign-in and onboarding

| # | Where | Now | Proposed |
|---|---|---|---|
| 1 | accounts/login_request.html (title) | Inicio Sesión | Iniciar sesión |
| 2 | accounts/login_request.html (h1) | Inicio de sesión por correo | Iniciar sesión con un código por correo |
| 3 | accounts/login_request.html | Usa esta opción si puedes recibir correos de {{ brand.name }}. Te enviaremos un código a tu correo institucional. | Te enviaremos un código de 6 dígitos a tu correo de trabajo. |
| 4 | accounts/login_request.html | Usa esta opción si tu administrador o RH te entregó un código de 9 dígitos. | Usa esta opción si quien te invitó te entregó un código de acceso de 9 dígitos. |
| 5 | accounts/login_request.html | Ingresar con contraseña | Iniciar sesión con contraseña |
| 6 | accounts/login_request.html (button) | Enviar código de inicio de sesión | Enviarme un código |
| 7 | accounts/login_password.html (title, h1) | Inicio con contraseña | Iniciar sesión con contraseña |
| 8 | accounts/login_password.html (button) | Ingresar | Iniciar sesión |
| 9 | accounts/login_password.html | ¿Puedes recibir el código por correo? | ¿Prefieres recibir un código por correo? |
| 10 | accounts/login_password.html | Ingresa con código | Inicia sesión con un código |
| 11 | accounts/login_setup_access_code.html | Ingresa tu correo institucional y el código temporal de acceso que te entregó tu administrador. | Escribe tu correo de trabajo y el código de acceso de 9 dígitos que te entregó quien te invitó. |
| 12 | accounts/login_setup_access_code.html | Ingresa con contraseña | Inicia sesión con contraseña |
| 13 | accounts/login_verify.html (title) | Ingresa tu código | Revisa tu correo |
| 14 | accounts/login_verify.html (button) | Verificar código | Iniciar sesión |
| 15 | accounts/login_verify.html | ¿Correo electrónico incorrecto? / Usa una dirección diferente | ¿No es tu correo? / Usa otro correo |
| 16 | accounts/login_verify.html | — | ¿No te llegó? Revisa tu correo no deseado o *pide otro código* (link to the request page). |
| 17 | accounts/profile_setup.html (title) | Activar cuenta — {{ brand.name }} | Activar cuenta \| {{ brand.name }} |
| 18 | accounts/profile_setup.html | Confirma el código de referencia de tu empresa y completa tus datos. | Escribe el código de tu empresa y completa tus datos. |
| 19 | accounts/profile_setup.html | Tu cuenta no está vinculada a ninguna empresa. Contacta a tu administrador. | Tu cuenta aún no tiene una empresa asignada. Avisa a quien te invitó. |
| 20 | accounts/profile_setup.html | Tu empresa aún no tiene áreas configuradas. Contacta a tu administrador para continuar. | Tu empresa aún no da de alta sus áreas, así que todavía no puedes activar tu cuenta. Avisa a quien te invitó. |
| 21 | accounts/forms.py | Correo o contraseña inválidos. | El correo o la contraseña no son correctos. Revísalos e intenta de nuevo. |
| 22 | accounts/forms.py (label) | Código temporal de acceso | Código de acceso |
| 23 | accounts/forms.py | El código temporal de acceso debe tener 9 dígitos. | El código de acceso tiene 9 dígitos. Revisa que no falte ninguno. |
| 24 | accounts/forms.py (label) | Confirma la nueva contraseña | Repite la nueva contraseña |
| 25 | accounts/forms.py | Las contraseñas no coinciden. | Las dos contraseñas no coinciden. Escríbelas otra vez. |
| 26 | accounts/forms.py | El código debe contener solo dígitos. | El código lleva solo números, sin letras ni espacios. |
| 27 | accounts/forms.py (label) | Código de referencia de la empresa | Código de empresa |
| 28 | accounts/forms.py (help) | El código de 5 caracteres proporcionado por tu administrador. | Son 5 letras y números. Te lo da quien te invitó. |
| 29 | accounts/forms.py, accounts/models.py (label, help) | Cargo / El puesto que ocupas en tu empresa. | Puesto / El puesto que ocupas en tu empresa. |
| 30 | accounts/forms.py | Selecciona una opción válida. (sexo) | Selecciona Masculino o Femenino. |
| 31 | accounts/forms.py | Escribe una fecha de nacimiento válida. | Esa fecha no existe. Revisa el día y el mes. |
| 32 | accounts/forms.py | Las opciones de localidad cambiaron mientras llenabas el formulario. Revisa tus datos y confirma tu selección. | La lista de localidades cambió mientras llenabas el formulario. Revisa tus datos y vuelve a enviarlo. |
| 33 | accounts/forms.py | El código de referencia debe ser alfanumérico. | El código de empresa lleva solo letras y números. |
| 34 | accounts/forms.py | Escribe tu fecha de nacimiento. | Selecciona tu fecha de nacimiento. |
| 35 | accounts/forms.py | La fecha de nacimiento debe corresponder a una edad entre 15 y 99 años. | Revisa el año: la edad debe estar entre 15 y 99 años. |
| 36 | accounts/views.py | Un código fue enviado recientemente. Por favor, espera 30 segundos antes de solicitar uno nuevo. | Ya te enviamos un código hace unos segundos. Revisa tu correo o espera 30 segundos para pedir otro. |
| 37 | accounts/views.py | No se encontró una cuenta con este correo electrónico. Si esto es un error, por favor contacta a tu administrador. | No hay ninguna cuenta con este correo. Revisa que esté bien escrito o avisa a quien te invitó. |
| 38 | accounts/views.py | No pudimos enviar el correo. Por favor, intenta de nuevo. | No pudimos enviar el código a tu correo. Intenta de nuevo en unos minutos. |
| 39 | accounts/views.py | El código temporal de acceso es inválido. | El correo y el código de acceso no coinciden, o el código ya se usó. Revisa ambos o pide uno nuevo a quien te invitó. |
| 40 | accounts/views.py (×2) | El código es inválido o ha expirado. | El código no es correcto o ya venció. Revisa los 6 dígitos o pide uno nuevo. |
| 41 | accounts/views.py | El código no coincide con tu empresa asignada. Por favor, verifica con tu administrador. | Ese código no corresponde a tu empresa. Revísalo o pídelo de nuevo a quien te invitó. |
| 42 | accounts/emails.py (subject) | Your login code | Tu código para iniciar sesión en {{ brand.name }} |
| 43 | accounts/emails.py (body) | Your one-time login code is: … / This code expires in N minutes. / If you didn't request this code, you can safely ignore this email. | Tu código de inicio de sesión en {{ brand.name }} es: … / Vence en N minutos. / Si no lo pediste, ignora este correo: nadie puede entrar a tu cuenta sin el código. |

#### Dashboard and company pages

| # | Where | Now | Proposed |
|---|---|---|---|
| 44 | core/company_list.html | Selecciona una empresa para ver su tablero con análisis. | Selecciona una empresa para ver su tablero. |
| 45 | core/company_list.html | Respuestas | Cuestionarios contestados |
| 46 | core/company_list.html (empty) | No hay empresas creadas aún. | Aún no hay empresas. Dalas de alta en el panel de administración. (action to the admin's *Agregar empresa*) |
| 47 | core/company_dashboard.html (panel) | Código de referencia | Código de empresa |
| 48 | core/company_dashboard.html (stat) | Colaboradores registrados | Cuentas activadas |
| 49 | core/company_dashboard.html (stat, 0 members) | Sin datos | Sin colaboradores |
| ~~50~~ | core/company_dashboard.html (stat) | Cuestionarios valorados | *dropped: valoración stays (localization.md glossary)* |
| 51 | core/company_dashboard.html (stat) | Sin encuestas NOM-035 | Sin encuestas NOM-035 asignadas |
| 52 | core/company_dashboard.html (Cochran) | …con un 95% de confianza y un 5% de margen de error | …con un 95 % de confianza y un 5 % de margen de error |
| 53 | core/company_dashboard.html (Cochran) | Donde N es el total de colaboradores registrados y n es el número mínimo de respuestas requeridas. | Donde N es el total de colaboradores de la empresa y n es el número mínimo de cuestionarios contestados. (**factual fix**: N counts every member) |
| 54 | core/company_dashboard.html | Activa, fecha límite dd/mm/aaaa | Activa · Fecha límite: dd/mm/aaaa |
| 55 | core/company_dashboard.html | Mínimo representativo: N respuestas | Mínimo representativo: N cuestionarios |
| 56 | core/company_dashboard.html | Tu respuesta | Tus respuestas |
| 57 | core/company_dashboard.html, core/employee_survey_list.html | La encuesta cerró; ya no puedes ver tus respuestas. | La encuesta cerró antes de que enviaras tus respuestas. |
| 58 | core/company_dashboard.html, core/employee_detail.html (×2) | No hay encuestas asignadas a esta empresa. | Aún no hay encuestas asignadas a esta empresa. |

#### Roster and employee detail

| # | Where | Now | Proposed |
|---|---|---|---|
| ~~59~~ | accounts/roles.py | Empleado | *dropped: colaborador names every person on the roster, so it can't name a role (localization.md, employee-roster.md)* |
| 60 | core/employee_list.html, core/employee_detail.html | {{ percent }}% | {{ percent }} % |
| 61 | core/employee_list.html (empty, narrowed) | Ningún colaborador coincide con la búsqueda. | Ningún colaborador coincide con la búsqueda o los filtros. |
| 62 | core/employee_list.html (empty) | Aún no hay colaboradores vinculados a {{ company }}. | Aún no hay colaboradores en {{ company }}. |
| 63 | core/employee_detail.html (Puesto, Área, Localidad) | Sin asignar | Sin capturar |
| 64 | core/employee_detail.html (dt) | Cargo | Puesto |
| 65 | core/employee_detail.html (pills) | Activado / No activado | Activada / Sin activar |
| ~~66~~ | core/employee_detail.html (h2) | Valoración de resultados | *dropped: valoración stays* |
| 67 | core/employee_detail.html (alert) | Usuario positivo a un acontecimiento traumático severo. | Requiere valoración clínica: reportó un acontecimiento traumático severo (Guía I). |
| 68 | core/employee_detail.html (empty) | La valoración se genera al completar la encuesta. | La valoración aparece cuando el colaborador envía la encuesta. |
| 69 | core/employee_detail.html | Este colaborador aún no ha iniciado esta encuesta. | Aún no empieza esta encuesta. |

#### Results

| # | Where | Now | Proposed |
|---|---|---|---|
| 70 | core/results/_body.html (empty, filtered) | Ningún cuestionario coincide con los filtros. | same, plus a *Limpiar filtros* action |
| 71 | core/results/_age_profile.html | Sin filtro de edad | Esta gráfica no aplica el filtro de edad. |
| 72 | core/results/_sex_profile.html | Sin filtro de sexo | Esta gráfica no aplica el filtro de sexo. |
| 73 | core/results/_participation.html (column) | Registrados | Cuentas activadas |
| 74 | core/results/_participation.html (column) | Distribución (final) | Nivel de riesgo final |
| 75 | core/results/_participation.html (empty) | Esta empresa no tiene áreas registradas. | Esta empresa aún no tiene áreas. |
| 76 | core/results/_stats_row.html | Prom. · Mín · Máx | Prom. · Mín. · Máx. |
| 77 | core/results/_categoria_stats.html, _final_stats.html | Estadística por categoría / Estadística de la calificación final | Estadísticas por categoría / Estadísticas de la calificación final |
| 78 | core/results/_suppressed.html | Grupo demasiado pequeño para mostrar resultados sin identificar a las personas (mínimo 5) | Grupo muy pequeño: ocultamos sus resultados para no identificar a nadie (mínimo 5 personas). |
| 79 | nom035/results.py (survey picker) | … · sin respuestas | … · sin cuestionarios contestados |

#### Reports

| # | Where | Now | Proposed |
|---|---|---|---|
| 80 | reports/report_list.html (empty, executive) | Aún no hay reportes publicados. | Aún no hay reportes publicados. Aquí aparecerán cuando estén listos. |
| ~~81~~ | reports/report_list.html | N cuestionario(s) valorado(s) | *dropped: valoración stays* |
| 82 | reports/report_list.html | Sin iniciar | Sin borrador |
| 83 | reports/report_detail.html, reports/views.py | Despublicar / ¿Despublicar el reporte? / Despublica el reporte para editarlo. / Reporte despublicado. | Retirar publicación / ¿Retirar la publicación del reporte? / Retira la publicación del reporte para editarlo. / Publicación retirada. |
| 84 | reports/report_detail.html (dialog) | El contenido congelado se descartará y la empresa dejará de verlo hasta que se publique de nuevo. | Se descartará la versión publicada y la empresa dejará de ver el reporte hasta que lo publiques de nuevo. |
| 85 | reports/report_detail.html | Para publicar falta: | Antes de publicar, falta: |
| 86 | reports/report_form.html (button) | Guardar | Guardar reporte |
| 87 | reports/report_form.html (row checkbox) | Eliminar | Quitar |
| 88 | reports/models.py (five `publishing.REQUIRED` fields) | (opcional) | no *(opcional)*; help *Necesario para publicar.* |
| 89 | reports/models.py | personal en home office | personal en teletrabajo |
| 89b | reports/models.py, report form, admin (signatory) | cargo | puesto |
| 90 | reports/views.py | El reporte se guardó desde otra sesión; revísalo antes de editarlo de nuevo. | Alguien más guardó este reporte al mismo tiempo. Revisa lo que quedó guardado antes de editarlo de nuevo. |
| ~~91~~ | reports/publishing.py | La encuesta no tiene cuestionarios valorados. | *dropped: valoración stays* |

#### Survey and *Mis encuestas*

| # | Where | Now | Proposed |
|---|---|---|---|
| 92 | surveys/_instrucciones_content.html | Lorem ipsum… (two paragraphs) | the instructions above; the YouTube paragraph stays |
| 93 | surveys/survey_detail.html (title) | {{ survey.title }} | {{ survey.title }} \| {{ brand.name }} |
| 94 | surveys/survey_detail.html | Ir a la siguiente ↓ | Ir a la siguiente pendiente ↓ |
| 95 | surveys/survey_detail.html (alert) | Favor de corregir las preguntas resaltadas abajo antes de enviar. | Corrige N respuestas para poder guardar. *Ir a la primera* |
| 96 | surveys/_progress_saved_modal.html | Tus respuestas han sido guardadas. Puedes continuar respondiendo ahora o en otro momento — tu progreso estará aquí cuando regreses. | Guardamos tus respuestas. Puedes seguir ahora o volver después; tu avance te estará esperando. |
| 97 | surveys/_progress_saved_modal.html, _submit_confirm_modal.html | Continuar respondiendo / Seguir editando | Seguir respondiendo |
| 98 | surveys/_submit_confirm_modal.html | Tu progreso ya está guardado, así que puedes revisarlas antes de enviar. | Tus respuestas ya están guardadas, así que puedes revisarlas antes de enviar. |
| 99 | surveys/_session_expired_modal.html (title) | Sesión expirada | Tu sesión se cerró |
| 100 | surveys/_session_expired_modal.html | Tu sesión ha expirado por inactividad. Tu progreso guardado está a salvo — inicia sesión de nuevo para continuar. | Se cerró por inactividad. Las respuestas que ya guardaste están a salvo; inicia sesión de nuevo para continuar. |
| 101 | surveys/survey_submitted.html (title, h1) | ¡Gracias! — {{ survey.title }} / ¡Gracias! | Respuestas enviadas \| {{ brand.name }} / Respuestas enviadas |
| 102 | surveys/survey_submitted.html | Tu respuesta a {{ survey.title }} ha sido registrada. | Enviaste tus respuestas a {{ survey.title }}. Gracias por participar. |
| 103 | core/employee_survey_list.html (title) | Mis Encuestas | Mis encuestas |
| 104 | core/employee_survey_list.html (empty) | No hay encuestas asignadas a tu empresa aún. | Aún no tienes encuestas por responder. Cuando tu empresa te asigne una, aparecerá aquí. |
| 105 | surveys/views.py | Please enter a whole number. / Please enter a number. / Please select a valid option. | Escribe un número entero, sin decimales. / Escribe un número; usa punto para los decimales. / Elige una de las opciones. |
| 106 | surveys/views.py (redirect home) | — | Esta encuesta ya cerró. / Ya enviaste tus respuestas a esta encuesta. |
| 107 | surveys/survey_detail.html (save line) | — | Guardando… / Cambios guardados / No se pudo guardar. Revisa tu conexión y presiona Guardar progreso. / La encuesta cerró; ya no se guardan cambios. |

#### Errors, footer, about, admin import

| # | Where | Now | Proposed |
|---|---|---|---|
| 108 | 403.html | …Si la necesitas, pide acceso a tu administrador. | …Si la necesitas, pide acceso a quien te invitó. |
| 109 | (new) CSRF failure page | Django's English 403 | La página estuvo abierta mucho tiempo o se usó en otra pestaña. Recárgala e intenta de nuevo. / *Recargar* |
| 110 | base layouts (new) | — | Saltar al contenido |
| 111 | _footer.html | 2024 - {{ year }} | 2024–{{ year }} |
| 112 | core/about.html (title) | ¿Qué es …? — {{ brand.name }} | ¿Qué es …? \| {{ brand.name }} |
| 113 | core/about.html | A través de encuestas configurables, … | A través de cuestionarios como los de la NOM-035, … |
| 114 | core/about.html | …se presentan en tableros y reportes dinámicos, facilitando la toma de decisiones basada en datos reales del clima organizacional. | …se presentan en tableros y reportes que ayudan a decidir con datos sobre los riesgos psicosociales y el entorno de trabajo. |
| 115 | employee_list.html, employee_detail.html (titles) | X — {{ company }} \| … | X \| {{ company }} \| … |
| 116 | admin import_csv.html | Sube un CSV para crear usuarios, asignar un grupo y crear su UserProfile vinculado a una empresa existente. | Sube un archivo CSV para crear cuentas de colaboradores, asignarles un rol y vincularlas a una empresa existente. |
| 117 | admin import_csv.html, change_list.html | Importar CSV / Importar usuarios desde CSV / Importar usuarios | Importar colaboradores |
| 118 | accounts/forms.py (CSV help) | Sube un archivo .csv con usuarios para crear. | Un archivo .csv con las cuentas que quieres crear. |
| 119 | admin import_csv.html, setup-code pages | código temporal de acceso | código de acceso |
| 120 | admin import_csv.html | El colaborador captura su nombre, cargo, área y localidad al activar su cuenta. | El colaborador captura su nombre, puesto, área y localidad al activar su cuenta. |
| 121 | accounts/models.py (`Company.reference_code`, `SetupAccessCode` Meta), admin | código de referencia / código temporal de acceso | código de empresa / código de acceso — *added in implementation: the operator copies the code from the admin, so it carries the name employees see* |

---

# Phase 4 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this
> plan task-by-task (native execution, as in Phase 3). Steps use checkbox (`- [ ]`) syntax.

**Goal:** apply the Voz rules and the approved copy list, fix the survey's order, errors and save
state, and give the app an accessibility floor.

**Architecture:** copy lives where it is today (templates, forms, views, `roles.py`, `emails.py`);
behaviour changes stay server-rendered, with the survey's save line and the results focus handled
in the existing TypeScript. New pieces: a skip link in `base.html`, a CSRF-failure view in
`apps/core/views.py`, a `LabelledSelectDateWidget`, an error-focus mixin, and a session-stored
`next`.

**Tech Stack:** Django 6 templates and forms, Tailwind v4, TypeScript (no JS runner), pytest.

**Spec:** the Phase 4 brief above (*What changes*, *Design*, *Copy list*).

## Global Constraints

- Text follows the copy list row for row; a row not in the list keeps its wording.
- Tú throughout; NOM-035 question text untouched.
- No `focus:ring`, `uppercase`, inline `on*=` or inline layout `style` (the design-token guards).
- Every template or TS edit ends with `npm run build:css` / `npm run build:js`.
- Never commit; the suite runs with `pytest --maxfail=50` to see every break at once.

## Review Focus

1. A survey POST with one bad number and other good answers → the good answers and the bad text
   both come back, nothing is saved, the alert names the count. (Task 4 test.)
2. `?next=https://evil.example/` on any login page → ignored; home after sign-in. (Task 5 test.)
3. `next` given to a user who must change password or activate → that step first; `next` kept
   for after. (Task 5 test.)
4. A GET form (roster, results) never gets a busy spinner stuck on its button. (Task 5: busy
   applies only to `method="post"`; checked in the browser list.)
5. A puesto left blank at activation → employee detail shows *Sin capturar*, not an empty
   `dd`. (Task 2: covered by the existing detail tests once the string changes.)

---

### Task 1: Sign-in, onboarding and email (rows 1–43)

**Files:** `templates/accounts/*.html`, `apps/accounts/forms.py`, `apps/accounts/views.py`,
`apps/accounts/emails.py`, `apps/accounts/roles.py`; tests in `apps/accounts/tests/`,
`apps/core/tests/` that pin old strings.

- [x] **Step 1: Failing tests** — `apps/accounts/tests/test_copy.py`:

```python
from django.core import mail
from apps.accounts.emails import send_otp_email
from apps.accounts.roles import ROLES


def test_the_login_email_is_spanish_and_names_the_product(settings):
    send_otp_email("a@x.mx", "123456")
    msg = mail.outbox[-1]
    assert msg.subject == f"Tu código para iniciar sesión en {settings.BRAND['name']}"
    assert "Tu código de inicio de sesión" in msg.body and "Vence en" in msg.body
    assert "code" not in msg.body.lower().replace("código", "")


```

- [x] **Step 2:** `pytest apps/accounts/tests/test_copy.py` — FAIL.
- [x] **Step 3:** Apply rows 1–43 exactly (row 29 also renames `UserProfile.position`'s `verbose_name`; `makemigrations accounts`). `emails.py` builds subject and body from
  `settings.BRAND["name"]`; minutes pluralised in Spanish (`minuto`/`minutos`).
- [x] **Step 4:** `pytest --maxfail=50` — update every test that pinned an old string to the new
  row text (no behaviour change).
- [x] **Step 5:** `npm run build:css`.

### Task 2: Dashboard, company list, roster, employee detail, results (rows 44–79)

**Files:** `templates/core/company_list.html`, `company_dashboard.html`, `employee_list.html`,
`employee_detail.html`, `employee_survey_list.html` (row 57), `templates/core/results/*.html`,
`apps/nom035/results.py` (row 79); tests pinning old strings.

- [x] **Step 1: Failing tests** in `apps/core/tests/test_dashboard_page.py`:

```python
def test_the_cochran_note_counts_every_member(client, viewer):
    viewer("Principal Exec")
    html = _get(client)
    assert "N es el total de colaboradores de la empresa" in html
    assert "Código de empresa" in html and "Cuentas activadas" in html
```

  and in `test_results_views.py`:

```python
def test_a_filtered_empty_group_offers_to_clear(client, setup, make_user_with_profile):
    add_respondents(setup, make_user_with_profile, 6)
    client.force_login(setup["exec"])
    body = client.get(
        reverse("core:company_results") + f"?area={setup['area'].pk}"
    ).content.decode()
    empty = body[body.index("Ningún cuestionario coincide") :]
    assert "Limpiar filtros" in empty[:600]
```

- [x] **Step 2:** run — FAIL.
- [x] **Step 3:** apply rows 44–79. Row 46's action links to `admin:accounts_company_add`.
  Row 70 passes `action_url=clear_url action_label="Limpiar filtros"` to `_empty.html` in
  `results/_body.html` (the fragment view shares `_results_context`, so `clear_url` is there);
  `_empty.html` gains an optional `action_attrs` flag so this link carries `data-results-link`
  and the script swaps in place.
- [x] **Step 4:** `pytest --maxfail=50`; update pinned strings.
- [x] **Step 5:** `npm run build:css`.

### Task 3: Reports (rows 80–91)

**Files:** `templates/reports/report_list.html`, `report_detail.html`, `report_form.html`,
`apps/reports/views.py`, `apps/reports/publishing.py`, `apps/reports/forms.py`,
`apps/reports/models.py` + a generated migration.

- [x] **Step 1: Failing test** in `apps/reports/tests/test_admin_views.py`:

```python
def test_fields_needed_to_publish_say_so(admin_client_for_report):  # existing fixtures
    html = admin_client_for_report.get(edit_url).content.decode()
    label = html[html.index('for="id_issued_in"') :]
    assert "(opcional)" not in label[: label.index("</label>")]
    assert "Necesario para publicar." in html
```

  (use the fixtures the file's `test_the_report_form_has_one_title` already uses).
- [x] **Step 2:** run — FAIL.
- [x] **Step 3:** apply rows 80–91. In `ReportForm.__init__`, for each `name` in
  `publishing.REQUIRED`: `field.shown_as_required = True`, `field.help_text =
  "Necesario para publicar."`. Row 89 edits the model's `verbose_name`;
  `python manage.py makemigrations reports`.
- [x] **Step 4:** `pytest --maxfail=50`; update pinned strings (*Despublicar* tests).
- [x] **Step 5:** `npm run build:css`.

### Task 4: The survey

**Files:** `apps/surveys/views.py`, `templates/surveys/survey_detail.html`, `_question.html`,
`_instrucciones_content.html`, `_progress_saved_modal.html`, `_submit_confirm_modal.html`,
`_session_expired_modal.html`, `survey_submitted.html`, `static/ts/survey_progress.ts`,
`static/css/main.css`; tests in `apps/surveys/tests/`.

- [x] **Step 1: Failing tests** — `apps/surveys/tests/test_views.py`, class
  `TestSurveyErrors` (reuse the module's integer-question fixture, or create an INTEGER question
  in the assignment's module):

```python
def test_a_bad_number_keeps_what_was_posted(self, client, ...):
    resp = client.post(url, {f"question_{q_int.id}": "doce", f"question_{q_likert.id}": "2"})
    html = resp.content.decode()
    assert 'value="doce"' in html
    assert re.search(rf'name="question_{q_likert.id}" value="2"[^>]*checked', html)
    assert "Escribe un número entero, sin decimales." in html
    assert 'aria-invalid="true"' in html
    assert f'aria-describedby="question_{q_int.id}_error"' in html
    assert "Corrige 1 respuesta para poder guardar." in html
    assert not Answer.objects.exists()

def test_the_form_comes_before_the_sidebar(self, client, ...):
    html = client.get(url).content.decode()
    assert html.index('id="survey-form"') < html.index('id="survey-actions"')
    assert html.index("<h1") < html.index("<h2")

def test_a_closed_survey_link_says_so(self, client, ...):
    assignment.status = SurveyAssignment.Status.CLOSED; assignment.save()
    resp = client.get(url, follow=True)
    assert "Esta encuesta ya cerró." in resp.content.decode()

def test_instructions_are_not_placeholder(self, client, ...):
    html = client.get(url).content.decode()
    assert "Lorem" not in html and "dos últimos meses" in html
```

  and in `test_survey_page_contract.py`: `id="save-status"` with `aria-live="polite"` inside
  `#survey-actions`.
- [x] **Step 2:** run — FAIL.
- [x] **Step 3: View.** On errors, render posted values:
  `existing_answers = {**existing_answers, **answer_values, **raw_errors}` where `raw_errors`
  maps an errored question id to `request.POST.get(form_key, "").strip()`. Spanish messages
  (row 105). Closed → `messages.info(request, "Esta encuesta ya cerró.")`; completed →
  `messages.info(request, "Ya enviaste tus respuestas a esta encuesta.")` before each redirect.
  Pass `error_count = len(errors)` and `first_error_id`.
- [x] **Step 4: Templates.** Move the sidebar block after the form column, drop `order-last`.
  `_question.html`: give the card `id="q-{{ question.id }}"`; on error the fieldset gets
  `aria-invalid="true" aria-describedby="question_{{ question.id }}_error"` and the message
  `id="question_{{ question.id }}_error"`. The alert (`_alert.html` gains optional `focus` →
  `tabindex="-1" data-focus-on-load`, and `link_url`/`link_label`): *Corrige {{ n }}
  respuesta{{ n|pluralize }} para poder guardar.* with *Ir a la primera* → `#q-<id>`. Save line
  under the progress: `<p id="save-status" aria-live="polite" class="min-h-5 text-sm
  text-neutral-600"></p>`. Copy rows 92–104. *Progreso guardado*: `autofocus` on *Seguir
  respondiendo*. Session-expired link: `{% url 'accounts:request_otp' %}?next={{
  request.get_full_path|urlencode }}`.
- [x] **Step 5: CSS.** In `main.css`:
  `@media (width < 64rem) { html:has(#survey-actions) { scroll-padding-bottom: 10rem; } }`
  and `[data-focus-on-load]:focus { outline: none }` is **not** added (the base outline shows
  where focus went).
- [x] **Step 6: TS.** `survey_progress.ts`: `autoSave` sets the save line — *Guardando…* before
  the fetch, *Cambios guardados* on 2xx, *La encuesta cerró; ya no se guardan cambios.* on a 403
  whose JSON `error` is `closed`, otherwise (403/5xx/network) *No se pudo guardar. Revisa tu
  conexión y presiona Guardar progreso.* with `text-danger-700`; 401 keeps the dialog. The
  Pendientes jump uses `behavior: matchMedia("(prefers-reduced-motion: reduce)").matches ?
  "auto" : "smooth"`. A small `focus_on_load.ts` (loaded from `base.html`, deferred) focuses the
  first `[data-focus-on-load]`.
- [x] **Step 7:** `pytest --maxfail=50`; `npm run build:css && npm run build:js`.

### Task 5: Across the app

**Files:** `templates/base.html`, `static/ts/busy_submit.ts`, `apps/accounts/views.py`,
`apps/accounts/forms.py`, `apps/core/views.py`, `config/settings.py`,
`templates/403_csrf.html`, `static/ts/results_dashboard.ts`, `static/css/main.css`; tests.

- [x] **Step 1: Failing tests.** `apps/core/tests/test_pages.py`:

```python
def test_every_layout_opens_with_a_skip_link(client):
    html = client.get(reverse("accounts:request_otp")).content.decode()
    body = html[html.index("<body") :]
    first_link = re.search(r"<a [^>]*>", body).group(0)
    assert 'href="#main"' in first_link
    assert "Saltar al contenido" in body[: body.index("</a>")]

def test_a_csrf_failure_is_a_spanish_page(client):
    from django.test import Client
    strict = Client(enforce_csrf_checks=True)
    resp = strict.post(reverse("accounts:request_otp"), {"email": "a@x.mx"})
    assert resp.status_code == 403
    assert "Recárgala e intenta de nuevo." in resp.content.decode()
```

  `apps/accounts/tests/test_views.py`, class `TestNext`:

```python
def test_next_survives_the_otp_round_trip(client, make_user_with_profile):
    user = make_user_with_profile(email="a@x.mx")  # activated
    client.get(reverse("accounts:request_otp") + "?next=/encuestas/5/")
    client.post(reverse("accounts:request_otp"), {"email": "a@x.mx"})
    code = EmailOTP.objects.get(email="a@x.mx").code
    resp = client.post(reverse("accounts:verify_otp"), {"email": "a@x.mx", "code": code})
    assert resp.url == "/encuestas/5/"

def test_an_offsite_next_is_ignored(client, make_user):
    make_user(email="b@x.mx", password="pw-12345678")  # password login enabled
    client.get(reverse("accounts:password_login") + "?next=https://evil.example/")
    resp = client.post(reverse("accounts:password_login"), {"email": "b@x.mx", "password": "pw-12345678"})
    assert "evil" not in resp.url

def test_next_waits_for_activation(client, make_user):  # inactive profile
    ...  # GET with ?next=/x/, sign in → redirect to setup_profile; session still holds next
```

  `apps/accounts/tests/test_forms.py`: a bound `ProfileActivationForm` with only the date
  missing → `form["date_of_birth"]` widget subwidgets carry `aria-label` *Día*/*Mes*/*Año*;
  the first errored field carries `autofocus` and the email field does not.
- [x] **Step 2:** run — FAIL.
- [x] **Step 3: Skip link** first in `<body>` of `base.html`:
  `<a href="#main" class="sr-only focus:not-sr-only focus:fixed focus:top-2 focus:left-2
  focus:z-50 btn btn-secondary">Saltar al contenido</a>`. Every layout already has
  `<main id="main" tabindex="-1">`.
- [x] **Step 4: Busy by default.** `busy_submit.ts`: applies to forms whose `method` is `post`
  and that lack `data-no-busy`; drop `data-loading` from the four templates and the docs.
- [x] **Step 5: `next`.** In `apps/accounts/views.py`: `_remember_next(request)` on every login
  view's GET stores `request.GET["next"]` in `session["login_next"]` when
  `url_has_allowed_host_and_scheme(next, {request.get_host()}, request.is_secure())`;
  `_redirect_after_login(user, request)` sends unfinished users to their step as today and
  otherwise pops `login_next` (falling back to `LOGIN_REDIRECT_URL`); `change_password` and
  `setup_profile` end through it, so `next` waits for them.
- [x] **Step 6: CSRF page.** `apps/core/views.py`: `def csrf_failure(request, reason=""):` render
  `403_csrf.html` (extends `base_error.html`; row 109) with status 403;
  `CSRF_FAILURE_VIEW = "apps.core.views.csrf_failure"`. *Recargar* is
  `<a href="{{ request.get_full_path }}">`.
- [x] **Step 7: Forms.** `apps/core/forms.py` gains `ErrorFocusMixin` (`full_clean` → when
  `self.errors`, remove `autofocus` from every widget and set it on the first field named in
  `self.errors`) and `LabelledSelectDateWidget(SelectDateWidget)` (`get_context` adds
  `aria-label` Día/Mes/Año to subwidgets by name suffix). Every `apps/accounts/forms.py` form
  with autofocus mixes it in; the activation form uses the widget.
- [x] **Step 8: Results.** `main.css`: `#results-body[aria-busy="true"] { @apply opacity-50
  transition-opacity; }`. `results_dashboard.ts`: after a swap started from a
  `[data-results-link]` click, focus `[data-group-line]` (given `tabindex="-1"` in
  `_group_line.html`).
- [x] **Step 9:** `pytest --maxfail=50`; `npm run build:css && npm run build:js`.

### Task 6: Errors, footer, about, admin import, titles (rows 108–119)

**Files:** `templates/403.html`, `_footer.html`, `core/about.html`, `employee_list.html`,
`employee_detail.html`, `templates/admin/accounts/user/*.html`, `apps/accounts/forms.py`.

- [x] **Step 1: Failing test** in `apps/core/tests/test_design_tokens.py`:

```python
def test_tab_titles_use_the_pipe_separator():
    for path in TEMPLATES.rglob("*.html"):
        m = re.search(r"{% block title %}(.*?){% endblock %}", path.read_text(), re.S)
        if m:
            assert " — " not in m.group(1), path
```

- [x] **Step 2:** run — FAIL.
- [x] **Step 3:** apply rows 108–119.
- [x] **Step 4:** `pytest --maxfail=50`; `npm run build:css`.

### Task 7: Fonts and CSS size

**Files:** `static/fonts/figtree/*.woff2`, `static/css/main.css`, `templates/base.html`,
`package.json`.

- [x] **Step 1:** One-off conversion (not a project dependency):
  `pip install --target $SCRATCH/ft fonttools brotli` and
  `PYTHONPATH=$SCRATCH/ft python -m fontTools.ttLib.woff2 compress -o <out>.woff2 <in>.ttf` for
  both faces.
- [x] **Step 2:** `main.css` `@font-face` `src` → the `.woff2` files, `format("woff2")`;
  `base.html` preload → `.woff2`, `type="font/woff2"`. The TTFs stay for the PDF.
- [x] **Step 3:** `package.json` `build:css` adds `--minify`; `npm run build:css`.
- [x] **Step 4:** `pytest --maxfail=50` (the PDF tests still render with the TTFs).

### Task 8: Documentation

- [x] `design-system.md`: *Voz* section and glossary (from the brief); *Out of scope* drops
  *Copy*; skip link, busy-by-default (`data-no-busy`), alerts with `focus`, the dashboard
  panel's *Código de empresa*; WOFF2 and minified CSS; an enforcement line for the new guards.
- [x] `survey-model.md`: reading order, save line, errors, instructions, closed/completed
  messages.
- [x] `auth-and-onboarding.md`, `setup-access-codes.md`: code names, *quien te invitó*, `next`,
  the Spanish email, the CSRF page.
- [x] `nom-035-report.md`, `apps/reports/CLAUDE.md`: *Retirar publicación*, *Necesario para
  publicar.*
- [x] `nom-035-results-dashboard.md`: dimmed body, focus to the group line, empty state's
  *Limpiar filtros*, sex/age captions.
- [x] `employee-roster.md`, `.claude/CLAUDE.md`, `apps/accounts/CLAUDE.md`, `apps/core/CLAUDE.md`,
  `apps/surveys/CLAUDE.md`: role label *Colaborador*, new files and conventions.
- [x] Full `pytest`, `ruff check .`, `ruff format --check .`, both builds; then the browser and
  keyboard checklist for the PR.
