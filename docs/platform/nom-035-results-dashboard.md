# NOM-035 Results Dashboard

## Status

Current — implemented in `apps/nom035/results.py` and `apps/core`; the page is
`/tablero-empresa/resultados/`.

## What this does

Roles holding `can_view_insights` open a dedicated **Resultados** page for a
company and read one NOM-035 survey assignment at a time: who answered (by sex,
age band and área), how the final score and every categoría and dominio
distribute across the five Niveles de Riesgo, the average, median and range of
the raw scores against the official threshold bands, and how many respondents
screened positive on Guía I. One filter bar — sexo, edad, área, localidad —
narrows every chart at once without reloading the page. Groups small enough to
identify a person are hidden from company executives. Each chart is a reusable,
server-rendered SVG component that knows nothing about NOM-035, so the future
downloadable report draws the same charts from the same data.

## Why it exists

A NOM-035 analysis starts from three questions — *which categoría and dominio
carry the risk, for whom, and how spread out is it* — and the progress dashboard
answers none of them. The Aug 3 2026 session with the domain expert asked for
results dashboards kept separate from the progress dashboard, built with the
downloadable report in mind (`docs/internal/meetings/20260803.md`).

## Scope

**In scope:**

- A results page per company, one NOM-035 `SurveyAssignment` at a time, chosen
  from a selector.
- A global filter bar (sexo, edad, área, localidad) that re-renders the results
  in place.
- Company-level sections: participation by área, respondent profile by sex and
  by age band, final-score NDR distribution, final-score statistics, Guía I
  outcomes.
- Categoría-level sections: NDR distribution and statistics per categoría, each
  expandable to its dominios.
- The small-group and complement suppression rule for viewers without
  `can_view_small_groups`.
- Three instrument-agnostic chart components (stacked bar, column chart, range
  strip) with their geometry in pure Python.
- A stored `SubmissionScore.guia1_event` column and the `can_view_small_groups`
  permission.
- The company dashboard's "Valoración de resultados" link card.

**Out of scope:**

- The downloadable/PDF report itself (the components are built to be reused by
  it).
- Operator-authored names for survey rounds; rounds are labelled from their data.
- Comparing two assignments side by side, or trends across assignments.
- Statistics or charts at the dimensión level.
- A participation table per localidad (localidad is a filter only).
- CSV/Excel export of the results.
- Any company-level or área-level NDR verdict or "necesidad de acción" text.
- Snapshotting respondent demographics at answer time (see ADR-0005).
- A second survey instrument.
- The employee-detail valuation card (see `nom-035-analytics.md`).

## How it works

### Page and routes

| Route | Name | Serves |
|---|---|---|
| `/tablero-empresa/resultados/` | `core:company_results` | The viewer's own company |
| `/tablero-empresa/resultados/fragmento/` | `core:company_results_fragment` | The results body only, same parameters |
| `/empresas/<reference_code>/resultados/` | `core:company_results_for` | Any company (admin) |
| `/empresas/<reference_code>/resultados/fragmento/` | `core:company_results_fragment_for` | The results body only, same parameters |

`CompanyResultsView` and `CompanyResultsFragmentView` (`apps/core/views.py`)
follow the `reference_code` convention: without it the viewer's own company is
shown; with it, `can_manage_surveys` is required. Both require
`can_view_insights`; a viewer without it gets 403, and a viewer with no company
of their own is sent to `accounts:setup_profile`. The fragment view is the page
view rendering `templates/core/results/_body.html` instead of the whole page;
both build their context in `_results_context`.

### Query parameters

Parsed by `apps/core/results_query.py` into a `ResultsQuery`, the same way
`roster.py` parses the roster: Spanish slugs in, English values out; an absent,
empty, unrecognized or foreign-company value is ignored, never an error.

| Parameter | Values | Repeatable | Meaning |
|---|---|---|---|
| `encuesta` | assignment pk | no | The assignment shown; must be this company's NOM-035 assignment |
| `sexo` | `femenino`, `masculino` | no | First recognized value wins |
| `edad` | `15-19`, `20-24`, `25-29`, `30-34`, `35-39`, `40-44`, `45-49`, `50-54`, `55-59`, `60-mas` | yes | Age band(s) |
| `area` | `CompanyArea` pk | yes | Área(s) of this company |
| `localidad` | `CompanyLocation` pk | yes | Localidad(es) of this company |

Values of one repeatable dimension OR together; dimensions AND with each other.
An invalid value is dropped on its own; its valid neighbours still apply. The
value readers `values`, `valid_pks` and `first_sex`, and `SEX_SLUGS` /
`SEX_SLUGS_TO_LABELS`, live in `apps/core/query_params.py`, shared by `roster.py`
and `results_query.py`. `results_query.py` also builds the links the page
prints: `results_url` (the page URL for a query, with one parameter dropped or
added) and `filter_pills` (one `Pill` per active value, with the URL that removes
it).

A filter is **active** when any of `sexo`, `edad`, `area` or `localidad` holds a
recognized value. `encuesta` is not a filter.

### The survey selector

`assignment_options(company)` (`apps/nom035/results.py`) lists the company's
assignments whose `survey.key == "nom035"`, newest `created_at` first, each as an
`AssignmentOption` carrying its label and its scored-questionnaire count, in one
query. `select_assignment(options, requested_pk)` picks the requested one;
without a valid `encuesta` it picks the most recent assignment with at least one
scored questionnaire, falling back to the most recent assignment. Each option is
labelled from its data by `assignment_label`, with dates in
`America/Mexico_City`:

- with answers: *"Guía III · aplicada 12 ene – 28 feb 2026"* — the variant label
  and the earliest and latest `completed_at` among its scored submissions (both
  years shown when they differ, a single date when they coincide);
- without answers: *"Guía III · creada 12 ene 2026 · sin respuestas"*.

A company with no NOM-035 assignment shows *"Esta empresa aún no tiene encuestas
NOM-035 asignadas."* and no filter bar.

### Who is counted

The **group** is every `SubmissionScore` of the selected assignment whose
respondent matches the active filters. Respondent attributes are read live from
`UserProfile`: age is computed as of today in `America/Mexico_City` (ADR-0005),
and an área counts only when it belongs to the company being viewed — otherwise
the respondent buckets as "Sin área" (`_area_of` in `apps/nom035/results.py`).
The área and localidad filters take only this company's pks, so a respondent
carrying another company's área or localidad never matches one. A submission
whose employee account was deleted (`user` is null) counts as "Sin dato" for sex
and age and "Sin área" in the participation table, and drops out of the group
whenever a filter is active.

Filtering runs in the database through `narrow(queryset, query, today, prefix)`,
which the group, the participation headcount and the sex and age breakdowns
share. Each selected age band becomes a `date_of_birth` range computed from
today by `demographics.birth_date_range`, which gives the same answer as
computing each respondent's age.

### Page layout

A filter bar, then the results body (`#results-body`). Company-level sections
come first under an *Empresa* heading, categoría-level sections second under
*Por categoría*.

| # | Section | Partial (`templates/core/results/`) | Component |
|---|---|---|---|
| 0 | Active-filter pills and group line: *"Femenino · 25–29 · Operaciones — 18 cuestionarios"*, or *"Toda la empresa — 60 cuestionarios"* | `_group_line.html` | text |
| **Empresa** | | | |
| 1 | **Participación por área** — Registrados, Respondieron, Participación, final-NDR distribution | `_participation.html` | `stacked_bar` per row |
| 2 | **Perfil de quienes respondieron — sexo** | `_sex_profile.html` | `stacked_bar` with legend |
| 3 | **Perfil de quienes respondieron — edad** | `_age_profile.html` | `column_chart` |
| 4 | **Calificación final — distribución** | `_final_distribution.html` | `stacked_bar` |
| 5 | **Calificación final — estadística** | `_final_stats.html` | stats row + `range_strip` |
| 6 | **Guía I — acontecimientos traumáticos severos** | `_guia1.html` | headline count + `stacked_bar` with legend |
| **Por categoría** | | | |
| 7 | **Distribución por categoría** | `_categoria_distribution.html` | one `stacked_bar` per categoría, each a `<details>` expanding to its dominios |
| 8 | **Estadística por categoría** | `_categoria_stats.html` | stats row + `range_strip` per categoría, each a `<details>` expanding to its dominios |

`_body.html` assembles them; `_stats_row.html` is the one statistics row sections
5 and 8 share, `_ndr_legend.html` the five-level legend under sections 1, 4, 5, 7
and 8, and `_suppressed.html` the small-group message.

**1 — Participación por área.** One row per área of the company, sorted by name;
a retired área (`is_active=False`) appears only while it still has registered
members or respondents. A "Sin área" row follows, last, when some respondent has
no área of this company. *Registrados* counts **activated** members of the
company in that área (only activated members carry área, sexo and date of
birth); *Respondieron* counts the group's scored questionnaires in that área;
*Participación* is Respondieron ÷ Registrados as a whole percent. The sexo, edad
and localidad filters apply to both counts; the área filter limits which rows
appear. "Sin área" shows "—" for Registrados and Participación, since activation
always assigns an área. A row with no respondents shows "—" in place of its bar.
The área name links to the same page with that área added to the filter, unless
it is already selected. A company with no áreas shows *"Esta empresa no tiene
áreas registradas."*

**2 — Sexo.** One 100 % bar: Femenino, Masculino, Sin dato, with a legend giving
each segment's percent and count of *personas*. Ignores the `sexo` filter, noting
*"Sin filtro de sexo"* when one is set.

**3 — Edad.** One column per band from 15–19 to 60 o más, youngest left, count
labelled above each non-empty column, then a "Sin dato" column. Ignores the
`edad` filter, noting *"Sin filtro de edad"* when one is set.

**4 and 7 — NDR distribution.** A 100 % bar across the five levels Nulo, Bajo,
Medio, Alto, Muy alto, with the row's *n* beside it. Row 4 is the final score;
section 7 has one row per categoría of the assignment's variant (five for
Guía III, four for Guía II, which has no Entorno organizacional), each expanding
to one row per dominio. Empty segments are omitted. Percents are rounded by
largest remainder so a bar always sums to 100. Hovering, focusing or tapping a
segment shows *"Alto · 14 cuestionarios · 23 %"*; a legend under the section
repeats the five levels.

**5 and 8 — Statistics.** Each row shows *n*, *Prom.* (mean, one decimal),
*Mediana* (may end in .5), *Mín* and *Máx* of the raw integer scores, with "—"
when the row has no scores. Each row carries its own *n*: a dominio whose whole
conditional block was skipped has no `GroupScore` row, so a dominio's *n* can be
lower than the final score's. Beside the numbers a range strip draws that row's
NDR threshold bands, from 0 to the highest possible score for that row in the
variant (item count × 4; the Muy alto band is open-ended in the official tables,
so it runs to that maximum), with the two ends labelled, and plots four labelled
points — *Mín*, *Mediana*, *Prom.*, *Máx*. A label near either end anchors to
that end. Points whose labels would collide alternate above and below the strip.
Hovering, focusing or tapping a point shows its value and the band it falls in —
*"Prom.: 45.3 · Medio"*; hovering or tapping a band shows its level. A row with
no scores draws no strip. No NDR badge is attached to any of the four values; the
page states no company or área verdict.

**6 — Guía I.** A headline count — *"4 colaboradores requieren valoración
clínica"* — over a 100 % bar of three outcomes, with a legend giving each
outcome's percent and count: *Sin acontecimiento* (`guia1_event` false),
*Acontecimiento sin requerir valoración* (`guia1_event` true, `guia1_positive`
false), *Requiere valoración clínica* (`guia1_positive` true). No names appear on
this page.

### On a phone

At 360px the page reads as one column with no horizontal scroll. The filter bar
stacks: the survey selector runs full width and the *Filtros (n)* disclosure sits
below it, opening onto one column of fieldsets with a full-width *Aplicar*
button. Participation rows become stacked cards — the área name on its own line,
then Registrados, Respondieron and Participación side by side, each with its
label stacked above the value, then the distribution bar full width; the table's column header is
hidden. The sex and age sections stack in one column (they sit side by side only
from the `lg` breakpoint). Each statistics row puts its label, then its five
numbers, then its range strip below them. Distribution rows put the label above
the bar, and a categoría expands its dominio rows inline, indented beneath it.
The tooltip is shown by tapping a mark and hidden by tapping anywhere else or
scrolling.

### Small-group and complement rule

For a viewer **without** `can_view_small_groups` (Ejecutivo principal — the one
role besides Administrador that holds `can_view_insights`), a set of
questionnaires *S* taken out of a base *B* is shown only when

- *|S|* ≥ `MIN_GROUP_SIZE` (5), **and**
- *|B| − |S|* is 0 or ≥ `MIN_GROUP_SIZE`.

`shows(size, base, *, suppress)` in `apps/nom035/results.py` is the rule. It
applies at two levels, and área rows carry one more rule on top:

- **The group.** When a filter is active, *S* is the group and *B* is every
  scored questionnaire of the assignment. If the rule fails, sections 4–8 are
  replaced by *"Grupo demasiado pequeño para mostrar resultados sin identificar a
  las personas (mínimo 5)"*. Sections 0–3 still render: they count people and
  reveal no scores, and every row with respondents in section 1 shows the same
  message in place of its distribution bar. With no filter active, the whole
  assignment is always shown, whatever its size.
- **Each área row** in section 1, "Sin área" included. *S* is the row's
  respondents and *B* is the group. If the rule fails, the row shows the same
  message in place of its distribution bar — also when no filter is active.
- **The hidden total.** The group's final distribution is shown with exact
  counts, so hidden rows would be recoverable as that distribution minus the
  visible rows. After the per-row rule, when the respondents of the rows with
  respondents that are hidden number from 1 to 4, the smallest visible row with
  respondents is hidden as well (ascending by respondents, ties broken by
  label), one row at a time, until the hidden rows hold at least
  `MIN_GROUP_SIZE` respondents or no visible row with respondents remains. A row
  with no respondents is never hidden and never counts toward that total.

A suppressed participation row keeps its headcounts (Registrados, Respondieron)
and shows no NDR distribution.

A group of zero questionnaires shows, for every viewer and in place of every
section after the group line, *"Ningún cuestionario coincide con los
filtros."* when a filter is active and *"Esta encuesta aún no tiene
cuestionarios contestados."* when none is.

The rule is enforced in the data layer: a suppressed group carries
`suppressed=True` and no distribution, statistics or Guía I data, and a
suppressed participation row carries `suppressed=True` and an empty `counts`,
so no template can print a small group. Differences between two filtered views
remain possible and are recorded as a known limitation in
`nom-035-valoracion-supuestos.md`.

### In-place filtering

The filter bar (`<form id="results-filters">`) holds the survey selector and a
**"Filtros (n)"** disclosure (a native `<details>`) at every width: opening it
reveals radio buttons for sexo (with *Todos*), checkboxes for edad and área, and
checkboxes for localidad when the company has any, plus an **Aplicar** button.
*n* counts the active filter values. It is a plain GET form, so the page works
without JavaScript by reloading.

`static/ts/results_dashboard.ts` enhances it. Changing the survey or pressing
Aplicar fetches the matching `…/fragmento/` URL (the form's
`data-fragment-url`), swaps `#results-body` with the response, closes the
disclosure, refreshes the count in "Filtros (n)", and updates the address bar
with `history.replaceState` — a filtered view is a shareable link and survives a
reload. A newer request aborts one still in flight; `#results-body` carries
`aria-busy` while it loads; a failed request falls back to navigating to the
page URL. After each swap the script copies the new group line
(`[data-group-line]`) into a persistent, visually hidden
`<p id="results-status" aria-live="polite">` outside `#results-body`, so a screen
reader announces the new group once; `#results-body` itself is not a live region.

The active-filter pills (each with a × that removes that value) and the group
line render inside `#results-body`, so the swap refreshes them. Pills and área
links carry `data-results-link`: clicking one sets the form's controls from the
link's query string and runs the same swap. The company's áreas and localidades
do not depend on the assignment, so the filter bar itself is never re-rendered.
The same module drives the tooltip (`#chart-tooltip`) for any `[data-tooltip]`
mark on hover, keyboard focus and tap, placed above the mark (below it when there
is no room) and kept inside the viewport.

### Chart components

Three components render inline SVG from plain data and know nothing about
NOM-035:

| Tag (`apps/core/templatetags/charts.py`) | Template (`templates/components/charts/`) | Geometry (`apps/core/charts.py`) |
|---|---|---|
| `{% stacked_bar items unit="cuestionario" legend=False %}` | `stacked_bar.html` | `stacked_segments()` — widths, largest-remainder percents; 2px white gaps between segments |
| `{% column_chart items unit="persona" %}` | `column_chart.html` | `columns()` — heights against the tallest column |
| `{% range_strip bands scale_max points %}` | `range_strip.html` | `range_strip()` — band positions, marker positions, label lanes |

Each input item carries a key, a label, a value and a **color key**; the tag
library turns the key into Tailwind `fill-*` (and legend `bg-*`) classes, so the
data layer names no class. `unit` picks the counted noun for tooltips
(*cuestionario* or *persona*). Each tag also takes an optional `label` for the
SVG's own `aria-label`, which otherwise joins every mark's text.

Bar segments, columns and strip markers carry an `aria-label` and `data-tooltip`
text and are keyboard-focusable. Strip bands carry an `aria-label` and
`data-tooltip` with their level but are not focusable — the markers are the marks
a keyboard reaches. There is no SVG `<title>`, which would stack a second, native
tooltip on the styled one. SVG numbers render inside `{% localize off %}` so a
locale separator can never reach a coordinate. Every colored mark has a direct
label or a legend entry, so no reading depends on color alone.

Colors:

- **NDR** — the ramp in `apps/core/templatetags/valuation_extras.py` (Nulo
  gray-300, Bajo green-500, Medio amber-500, Alto orange-500, Muy alto red-500):
  `ndr_fill` for SVG marks, `ndr_bar` for legend swatches.
- **Sex** — Femenino violet-600 (`#7c3aed`), Masculino sky-600 (`#0284c7`), Sin
  dato gray-300. The pair passes the dataviz palette validator on a light
  surface (deutan ΔE 9.2, normal-vision ΔE 19.8). Neither reuses a risk color.
- **Age** — every band indigo-500; "Sin dato" gray-300. Position encodes the
  band and height the count, so one hue suffices.
- **Guía I** — Sin acontecimiento gray-300, Acontecimiento sin requerir
  valoración amber-500, Requiere valoración clínica red-500.

### Results data

`apps/nom035/results.py` builds everything the page shows:

```python
results_for(assignment, query: ResultsQuery, *, suppress_small_groups: bool) -> Results
```

`Results` is a tree of frozen dataclasses: the group `size` and the assignment's
`whole_size`, whether the query is `filtered` and the group `suppressed`, the
`sex` and `age` breakdowns (`Slice`s), the participation rows
(`ParticipationRow`), the final and per-categoría distribution rows
(`DistributionRow`, dominios as `children`), the final and per-categoría
statistics rows (`StatsRow`, each with its band table from
`_nom035_scoring.thresholds_for` and its scale maximum from the variant's item
count), and the Guía I outcome counts (`Guia1`). Distribution and participation
rows turn their per-level counts into slices through one helper, `_ndr_slices`.
The group line and pills are built by the view from the query, not stored in
`Results`.

It issues a fixed number of queries, independent of the number of respondents:
the assignment's scored count, the group's `SubmissionScore` rows with the
respondent's profile, área and localidad joined, one count of activated members
per área, the company's áreas, and one query over the group's `GroupScore` rows
at categoría and dominio level (skipped when the group is empty or suppressed).
A sex or edad filter adds one query each, since that breakdown ignores its own
filter. `MIN_GROUP_SIZE = 5` lives in `apps/nom035/constants.py`.

`apps/accounts/demographics.py` holds `AGE_BANDS` (slug, label, lower and upper
bound; 60 o más has no upper bound), `band_by_slug`, `age_on(date_of_birth,
today)`, `age_band(age)` and `birth_date_range(band, today)`.
`UserProfile.age` is `age_on` against today. The module is instrument-agnostic
because it describes `UserProfile`.

### Company dashboard

`templates/core/company_dashboard.html` shows a compact "Valoración de
resultados" card, gated on `can_view_insights`: under *Cuestionarios valorados*,
the scored-questionnaire count of the assignment the results page opens on
(`select_assignment(assignment_options(company), None)` in
`CompanyDashboardView`), and a *"Ver resultados →"* link to the results page.
A company with no NOM-035 assignment reads *"Esta empresa aún no tiene encuestas
NOM-035 asignadas."* on the card instead of a count.

## Schema

`nom035.SubmissionScore.guia1_event`:

| Field | Type | Notes |
|---|---|---|
| `guia1_event` | `BooleanField("acontecimiento traumático severo", default=False)` | `g1-1` answered "Sí". Set by `score_submission`/`materialize`; `recompute_nom035_scores` refreshes it for stored submissions. `guia1_positive` implies `guia1_event`. |

`ScoreResult` carries `guia1_event: bool`.

`accounts.Role.Meta.permissions` holds `("can_view_small_groups", "Puede ver
resultados de grupos pequeños")`, granted to Administrador by
`bootstrap_groups`.

## Where the code lives

| Path | Role |
|---|---|
| `apps/nom035/results.py` | `assignment_options`, `select_assignment`, `results_for` and the `Results` dataclasses; `narrow`, `shows` (small-group rule), `_hide_until_safe` (hidden-total rule for área rows), `_area_of` |
| `apps/nom035/constants.py` | `MIN_GROUP_SIZE` |
| `apps/nom035/scoring.py`, `services.py`, `models.py` | `guia1_event` computed, stored, declared |
| `apps/nom035/aggregates.py` | `employee_valuation` only |
| `apps/accounts/demographics.py` | `AGE_BANDS`, `band_by_slug`, `age_on`, `age_band`, `birth_date_range` |
| `apps/accounts/models.py`, `management/commands/bootstrap_groups.py` | `can_view_small_groups` |
| `apps/core/query_params.py` | Shared GET-parameter readers |
| `apps/core/results_query.py` | `ResultsQuery`, `parse_results_query`, `results_url`, `filter_pills` |
| `apps/core/charts.py` | Pure chart geometry |
| `apps/core/templatetags/charts.py` | `stacked_bar`, `column_chart`, `range_strip` tags; the chart palette |
| `apps/core/templatetags/valuation_extras.py` | `ndr_fill` |
| `apps/core/views.py`, `urls.py` | `CompanyResultsView`, `CompanyResultsFragmentView`, `_results_context`, four routes; the dashboard card's count in `CompanyDashboardView` |
| `templates/components/charts/` | `stacked_bar.html`, `column_chart.html`, `range_strip.html` |
| `templates/core/company_results.html` | Page: selector, filter bar, `#results-status`, `#results-body`, `#chart-tooltip` |
| `templates/core/results/` | `_body.html` and one partial per section |
| `templates/core/company_dashboard.html` | Link card |
| `static/ts/results_dashboard.ts` | Fragment swap, URL sync, pills, status line, tooltip (compiled to `static/js/results_dashboard.js`) |

Tests: `apps/nom035/tests/test_results.py` (the data layer, including a query
cap), `apps/core/tests/test_results_views.py` (routes, authorization, rendering,
and a query count that does not grow with respondents),
`test_results_query.py`, `test_charts.py`, `test_chart_components.py`,
`test_responsive.py` and `test_dashboard_results_card.py` in `apps/core/tests/`,
and `apps/accounts/tests/test_demographics.py`. The TypeScript has no test
runner; its behavior is checked in the browser.

## Key decisions

- Decision: One assignment at a time, chosen from a selector.
  Reason: Guía II and Guía III differ in item count, thresholds and categorías,
  and a repeated round would count the same people twice, so statistics across
  assignments are meaningless.
- Decision: Assignments are labelled from their answers' date range, not a name
  field.
  Reason: The real application period is already in the data, and a typed label
  could disagree with it.
- Decision: A separate results page, linked from the dashboard.
  Reason: The expert asked for dashboards separate from the progress dashboard,
  and filtering must not re-run the progress queries.
- Decision: Server-rendered SVG with fragment swapping, no chart library.
  Reason: The same components render in a PDF without a JavaScript engine,
  they are testable from Python, and no dependency is added.
- Decision: Aggregation happens on the server; the browser receives only totals.
  Reason: Sending per-respondent rows to the browser would expose individuals
  and bypass the small-group rule.
- Decision: One global filter bar for every section.
  Reason: The page always describes one group, which is how a reader and a
  report read it.
- Decision: Small-group and complement suppression below 5 for everyone without
  `can_view_small_groups`; the unfiltered assignment is always shown.
  Reason: The executives who see results also see the roster by sexo and área,
  so a small filtered group names its members; the employer is entitled to the
  whole-workplace result.
- Decision: A dedicated `can_view_small_groups` permission.
  Reason: Authorization is by codename, and "manages surveys" is a different
  right from "may see a group of two".
- Decision: Demographic charts count respondents of the selected assignment.
  Reason: They describe who stands behind the results; the participation table
  carries the registered headcount alongside.
- Decision: Sex and age as bars and columns, not pies.
  Reason: A two-slice pie compares angles poorly, and ten ordered age bands lose
  their order in a pie.
- Decision: Distribution rows for final, categoría and dominio together, with
  five levels including Nulo.
  Reason: Categorías are compared side by side, and the norm calls for a
  categoría-and-dominio analysis at Alto and Muy alto.
- Decision: No NDR label on the mean, median or range, and no área or company
  action text.
  Reason: Labelling only the mean reads as a company grade the norm does not
  define, and the norm gives no rule for summarizing an área in one level.
- Decision: `guia1_event` is stored, not recomputed from answers.
  Reason: It matches how `guia1_positive` is stored and keeps the page off the
  `Answer` table.
- Decision: A polite live region outside the swapped body announces the group
  line; the body is not a live region.
  Reason: Announcing the whole swapped body would read every chart aloud; the
  group line says what changed in one sentence.

## Open questions

None blocking. Assumptions awaiting confirmation from the domain expert are
tracked in [`nom-035-valoracion-supuestos.md`](./nom-035-valoracion-supuestos.md):
the small-group threshold and its exemption, the complement rule and the
subtraction limitation, the respondent-based demographics and "Sin dato"
buckets, the three Guía I outcomes, and how a company- or área-level rating
should be obtained, if at all.

## Linked ADRs

- [ADR-0003 — per-instrument survey-processing apps](../adr/adr-0003-per-instrument-survey-processing-apps.md)
  — why results data lives in `apps/nom035` while the chart components stay
  instrument-agnostic in `apps/core`.
- [ADR-0004 — per-company área/localidad catalogs](../adr/adr-0004-per-company-area-and-locality-catalogs.md)
  — the área and localidad pks the filters and the participation table group by,
  and why the catalog is per company and curated by an admin.
- [ADR-0005 — two-surname names and profile demographics](../adr/adr-0005-two-surname-names-and-profile-demographics.md)
  — sex and date of birth on `UserProfile`, age derived as of today.
