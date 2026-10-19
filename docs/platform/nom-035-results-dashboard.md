# NOM-035 Results Dashboard

## Status

Current — implemented in `apps/nom035/results.py` and `apps/core`; the page is
`/tablero-empresa/resultados/`.

## What this does

Roles holding `can_view_insights` open a dedicated **Resultados** page for a
company and read one NOM-035 survey assignment at a time. A main chart shows how
the final score — or one categoría chosen in **Mostrando** — distributes across
the five Niveles de Riesgo, with its average, median and range against the
official threshold bands one toggle away. Beside it, the categorías (or, with a
categoría chosen, its dominios) each show their distribution and the share in
alto or muy alto. Below sit participation, Guía I outcomes, who answered (by sex
and age band) and one row per área. A sticky strip says at all times what is
shown and for whom: the filters — sexo, edad, área, localidad — are removable
chips there, and the same filters can be applied from the charts (an age
column, an área row). Every change re-renders in place without reloading the
page. Groups small enough to identify a person are hidden from company
executives. The results report (`nom-035-report.md`) reads the same data
(`apps/nom035/results.py`) and draws it with the shared SVG chart components.

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
- **Mostrando**: a second selector that switches the page between the final
  score and one categoría. It changes what is measured, not who is counted.
- A sticky strip with the *Mostrando* chip, the filters as removable chips, the
  size of the group and *Filtros*, and a filter dialog (sexo, edad, área,
  localidad) that re-renders the results in place.
- Filtering from the charts: an age column, an área row.
- The main chart (distribution or statistics), the categoría column, and the
  cards for participation, Guía I and respondent profile.
- A *Por área* list drawn for what *Mostrando* measures.
- The small-group and complement suppression rule for viewers without
  `can_view_small_groups`.
- A stored `SubmissionScore.guia1_event` column and the `can_view_small_groups`
  permission.
- The company dashboard's *Cuestionarios valorados* stat card.

**Out of scope:**

- The results report and its PDF — a feature of its own,
  [`nom-035-report.md`](./nom-035-report.md), which reads the same data and draws
  it with the shared SVG chart components.
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
| `/tablero-empresa/resultados/fragmento/` | `core:company_results_fragment` | The strip's summary and the results body, same parameters |
| `/empresas/<reference_code>/resultados/` | `core:company_results_for` | Any company (admin) |
| `/empresas/<reference_code>/resultados/fragmento/` | `core:company_results_fragment_for` | The strip's summary and the results body, same parameters |

`CompanyResultsView` and `CompanyResultsFragmentView` (`apps/core/views.py`)
follow the `reference_code` convention: without it the viewer's own company is
shown; with it, `can_manage_surveys` is required. Both require
`can_view_insights`; a viewer without it gets 403, and a viewer with no company
of their own is sent to `accounts:setup_profile`. The fragment view is the page
view rendering `templates/core/results/_fragment.html` instead of the whole
page; both build their context in `_results_context`.

### Query parameters

Parsed by `apps/core/results_query.py` into a `ResultsQuery`, the same way
`roster.py` parses the roster: Spanish slugs in, English values out; an absent,
empty, unrecognized or foreign-company value is ignored, never an error.

| Parameter | Values | Repeatable | Meaning |
|---|---|---|---|
| `encuesta` | assignment pk | no | The assignment shown; must be this company's NOM-035 assignment |
| `ver` | a categoría key of the assignment's variant | no | What the page measures: that categoría, or the final score when absent. Not a filter |
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
added; it keeps `encuesta` and `ver`) and `filter_pills` (one `Pill` per active
value, with its dimension — *Sexo*, *Edad*, *Área*, *Localidad* — and the URL
that removes it).

A filter is **active** when any of `sexo`, `edad`, `area` or `localidad` holds a
recognized value. `encuesta` and `ver` are not filters. A `ver` the assignment's
variant does not measure (Entorno organizacional on Guía II) is dropped.

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
- without answers: *"Guía III · creada 12 ene 2026 · sin cuestionarios contestados"*.

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
and age and "Sin área" in *Por área*, and drops out of the group
whenever a filter is active.

Filtering runs in the database through `narrow(queryset, query, today, prefix)`,
which the group, the participation headcount and the sex and age breakdowns
share. Each selected age band becomes a `date_of_birth` range computed from
today by `demographics.birth_date_range`, which gives the same answer as
computing each respondent's age.

### Page layout

One form (`<form id="results-filters">`) wraps a grey board, top to bottom:

1. **The pickers** — a white card holding the survey selector (*Encuesta*) and
   **Mostrando** (*Calificación final* or one categoría of the assignment's
   variant). They scroll away with the page.
2. **The sticky strip** (`#results-strip`) — pinned to the top of the viewport.
   Left, `#results-summary` (`_summary.html`): the *Mostrando* chip, the filters
   as removable chips and the size of the group. Right, *Filtros* with its
   count and, from `sm`, *Limpiar filtros* while any filter is active.
3. **The body** (`#results-body`, `_body.html`) — the blocks below.

`_fragment.html`, the in-place response, is the summary parked in a hidden
element followed by `_body.html`.

| Block | Partial (`templates/core/results/`) | Depends on *Mostrando* |
|---|---|---|
| Main box: the final score or the chosen categoría, as *Distribución* or *Estadísticas* | `_hero.html` | yes |
| Categorías (or, with a categoría chosen, its dominios) | `_column.html` | yes |
| Participación, Guía I, Quienes respondieron | `_cards.html` | no |
| Por área | `_areas.html` | yes |

The main box and the column share a row from `lg` (7 + 5 of 12 columns);
`_level_bar.html` (one thin bar split by level) and `_level_cells.html` (the five
levels as cells) are the small distribution drawings, `_ndr_legend.html` the
five-level legend and `_suppressed.html` the small-group message.
`apps/core/results_page.py` shapes what the templates read from `Results`.

**The strip.** The *Mostrando* chip is dark: it says what is measured, not who is
counted. With the final score it is plain text; with a categoría it is a link
that returns to the final score. Each active filter is a solid primary chip
naming its dimension (*Sexo: Femenino*, *Edad: 25–29*, *Área: Operaciones*) with
an ✕ that removes it. With no filter the group reads *Toda la empresa*. The size
reads *"— 6 de 12 colaboradores"* when a filter narrows the group and
*"— 12 colaboradores"* otherwise. The strip turns pale primary while a filter is
active or a categoría is chosen (`data-active`); *Filtros* turns solid primary
only while a filter is active (`data-filtered`), since a categoría is not one of
its dimensions.

**The main box.** A title (the final score or the categoría) and, once the
script runs, a *Distribución* / *Estadísticas* toggle.

- *Distribución*: one stem per level, Nulo to Muy alto, in a fixed slot each,
  on a 0–ceiling % scale. The ceiling is the next multiple of 10 above the
  largest share (at least 10), so the plot uses its height; it is printed in the
  caption and a labelled gridline marks every 10 %, over a baseline. Under each
  stem a label carries the level's squircle, its name (*M. alto* for Muy alto, so
  all five sit on one line) and its percent. The level holding the most
  colaboradores starts selected: a count above its stem and, beside the chart,
  the share as a figure — *"38 % de los colaboradores presenta un nivel medio."*
  — with *n de N*. Choosing another stem moves the figures. Percents are whole
  numbers that add to 100 (largest remainder). Two charts with different
  ceilings compare by their printed values, not by height.
- *Estadísticas*: *Cuestionarios*, *Promedio*, *Mediana*, *Mínimo* and *Máximo*
  of the raw integer scores, "—" when none, over a range strip that draws the
  threshold bands from 0 to the highest possible score for that row in the
  variant (item count × 4; the Muy alto band runs to that maximum) and four
  labelled points, followed by the five-level legend. No NDR badge is attached to
  any value; the page states no company or área verdict.

**The column.** With the final score chosen it lists the categorías of the
assignment's variant (five for Guía III, four for Guía II, which has no Entorno
organizacional). Each row is a `<details>` — the first open — whose summary shows
the name, a thin distribution bar, a pill with the percent of colaboradores in
**alto o muy alto** (a sum of the distribution, not a verdict) and a chevron.
Opened, a categoría shows its five levels as cells, its average and median
against its maximum, its dominios on the deeper dominio ramp (name, bar, percent
in alto o muy alto) and **Mostrar esta categoría, con sus estadísticas**, which
chooses it in *Mostrando*. With a categoría chosen the column lists its dominios
instead: each opens to its levels, a statistics row and a range strip, on the
dominio ramp, under a *Dominios* legend. A dominio whose whole conditional block
was skipped has no `GroupScore` row, so its *n* can be lower than the
categoría's.

**Participación.** *Cuentas activadas* (activated members in the group's
filtered scope), *Respondieron* (the group's scored questionnaires),
*Pendientes*, the overall percent and a row of marks, one per *k* accounts so
the row never exceeds 45 marks.

**Guía I.** A headline count — *"4 colaboradores requieren valoración
clínica"* — over a bar of three outcomes with a legend giving each outcome's
percent and count: *Sin acontecimiento* (`guia1_event` false), *Acontecimiento
sin requerir valoración* (`guia1_event` true, `guia1_positive` false), *Requiere
valoración clínica* (`guia1_positive` true). No names appear. A suppressed group
has no Guía I card.

**Quienes respondieron.** Sexo as a figure per sex over a two-part bar; *Sin
dato* appears only when someone has no sex on file. Edad as one column per band
from 15–19 to 60 o más with its count above and a baseline beneath, *Sin dato*
only when needed. Each chart ignores its own filter and says so
(*"Esta gráfica no aplica el filtro de sexo."* / *"…de edad"*). Each age column
is a link: *"Toca una columna para filtrar todo el tablero por esa edad; tócala
de nuevo para quitar el filtro."* A column already filtered is tinted and its
link removes the filter.

**Por área.** A level legend, then one row per área of the company, sorted by
name; a retired área (`is_active=False`) appears only while it still has
registered members or respondents. A "Sin área" row follows, last, when some
respondent has no área of this company. Each row shows the área's name (a link
that adds it to the filters, unless it is selected), *"n de N respondieron"*
(*Sin área* has no *N*), a distribution bar for what *Mostrando* measures,
five colour-and-percent pairs beneath it and the percent in alto o muy alto at
the right. A round button at the row's end does what the name does; on a
selected área the row is tinted and the button is a solid ✕ that removes the
filter. A row with no respondents shows "—"; a suppressed row keeps its
headcounts and shows the small-group message. A company with no áreas shows
*"Esta empresa aún no tiene áreas."*

*Cuentas activadas* counts **activated** members of the company in that área
(only activated members carry área, sexo and date of birth); the sexo, edad and
localidad filters apply to it and to *Respondieron*, and the área filter limits
which rows appear. "Sin área" has no *N* since activation always assigns an
área.

Every number on the page is printed as text, and the charts hold nothing a
screen reader or a phone cannot reach: each stem and each age column is a
button or a link with a text description, and no tooltip or hover state carries
a value.

### On a phone

At 360px the page is one column with no horizontal scroll, in this order:
pickers, strip, main box, categorías, participation, Guía I, quienes
respondieron, por área. The pickers stack, each full width. The strip stays one
line: its chips and size scroll sideways inside it, and *Filtros* stays pinned at
its right; *Limpiar filtros* is only in the dialog. The main box puts the figure
above the chart. Stem labels are three short lines, so five fit the width. The
sex and age cards stack in one column from `md`; the age columns are narrow on a
phone but full height. *Por área* rows put the name and its button on one line,
then the headcount, the bar and the percents full width.

### Small-group and complement rule

For a viewer **without** `can_view_small_groups` (Ejecutivo principal — the one
role besides Administrador that holds `can_view_insights`), a set of
questionnaires *S* taken out of a base *B* is shown only when

- *|S|* ≥ `MIN_GROUP_SIZE` (5), **and**
- *|B| − |S|* is 0 or ≥ `MIN_GROUP_SIZE`.

`shows(size, base, *, suppress)` in `apps/nom035/results.py` is the rule. It
applies at two levels, and área rows carry one more rule on top:

- **The group.** When a filter is active, *S* is the group and *B* is every
  scored questionnaire of the assignment. If the rule fails, the main box, the
  column and the Guía I card are replaced by *"Grupo muy pequeño: ocultamos sus
  resultados para no identificar a nadie (mínimo 5 personas)."* Participación,
  Quienes respondieron and Por área still render: they count people and reveal
  no scores, and every área row with respondents shows the same message in place
  of its distribution. With no filter active, the whole assignment is always
  shown, whatever its size.
- **Each área row**, "Sin área" included. *S* is the row's respondents and *B* is
  the group. If the rule fails, the row shows the same message in place of its
  distribution — also when no filter is active, and for whatever *Mostrando*
  measures.
- **The hidden total.** The group's final distribution is shown with exact
  counts, so hidden rows would be recoverable as that distribution minus the
  visible rows. After the per-row rule, when the respondents of the rows with
  respondents that are hidden number from 1 to 4, the smallest visible row with
  respondents is hidden as well (ascending by respondents, ties broken by
  label), one row at a time, until the hidden rows hold at least
  `MIN_GROUP_SIZE` respondents or no visible row with respondents remains. A row
  with no respondents is never hidden and never counts toward that total.

A suppressed participation row keeps its headcounts (Cuentas activadas,
Respondieron) and shows no NDR distribution, final or per categoría.

A group of zero questionnaires shows, for every viewer and in place of the
whole body (the strip stays), *"Ningún cuestionario coincide con los
filtros."*, with a *Limpiar filtros* action, when a filter is active and *"Esta
encuesta aún no tiene cuestionarios contestados."* when none is.

The rule is enforced in the data layer: a suppressed group carries
`suppressed=True` and no distribution, statistics or Guía I data, and a
suppressed participation row carries `suppressed=True`, an empty `counts` and
an empty `categoria_counts`, so no template can print a small group. Differences between two views —
including a filtered view subtracted from the unfiltered page — remain
possible and are recorded as a known limitation in
`nom-035-valoracion-supuestos.md`.

### In-place filtering

The page is one GET form, so it works without JavaScript by reloading. The
pickers (*Encuesta*, *Mostrando*) are fields of it. The strip's *Filtros* opens
the shared filter dialog (`components/_filter_dialog.html`,
`static/ts/filter_dialog.ts`; see `design-system.md`): chips for sexo (picking the
chosen one again clears it), edad and área, and for localidad when the company
has more than one, over *Limpiar filtros* and *Aplicar filtros*. The view builds
the groups as `filter_groups` and the link that clears the filters while keeping
the survey and *Mostrando* as `clear_url`.

`static/ts/results_dashboard.ts` enhances it. Changing a picker or pressing
*Aplicar filtros* fetches the matching `…/fragmento/` URL (the form's
`data-fragment-url`), moves the response's parked summary into `#results-summary`,
swaps `#results-body` with the rest, closes the dialog, refreshes the count on
*Filtros*, shows or hides *Limpiar filtros*, sets the strip's `data-filtered` and
`data-active`, and updates the address bar with `history.replaceState` — a
filtered view is a shareable link and survives a reload. A newer request aborts
one still in flight; `#results-body` carries `aria-busy` while it loads, which
dims it; a failed request falls back to navigating to the page URL. After each
swap the script copies the new group line (`[data-group-line]`) into a
persistent, visually hidden `<p id="results-status" aria-live="polite">`, so a
screen reader announces the new group once; `#results-body` itself is not a live
region.

Filter chips, the *Mostrando* chip, the área names and buttons, the age columns
and the categorías' *Mostrar esta categoría* links carry `data-results-link`:
clicking one sets the form's controls from the link's query string — a control
whose parameter is absent returns to its empty option, which is how ✕ on
*Mostrando* returns to the final score — and runs the same swap, as does any
other link inside the body back to this page (the empty state's *Limpiar
filtros*). The link is gone after the swap, so focus moves to the group line
(`tabindex="-1"`). The bar's *Limpiar filtros* clears the chips and applies,
keeping whichever survey and *Mostrando* are selected. The company's áreas and
localidades do not depend on the assignment, so the dialog is never re-rendered.

The main box's behavior is client-only and holds nothing the server does not also
render: both its views and every level's figures are in the HTML, and the script
shows or hides them. The toggle is hidden until the script runs. Which view is
open survives a swap; the chosen level does not, since a new group has a new
largest level.

### Chart components

The page's main chart, distribution bars, age columns and cards are HTML and
CSS drawn from `apps/core/results_page.py` and `apps/core/charts.py`:

- **Stem chart** (`charts.stem_chart`) — one stem per level with its percent,
  the ceiling (next multiple of 10 above the largest share, at least 10), the
  gridlines at every 10 % and the stem a reader starts on. A stem's height is its
  share ÷ ceiling.
- **Level bar and cells** (`_level_bar.html`, `_level_cells.html`) — a thin bar
  whose segment widths are the levels' shares, and the five levels as cells, both
  from `Group.levels` / `AreaRow.levels`: name, count, share and a whole percent
  from `largest_remainder`.
- **Range strip** — the SVG component below.

Four instrument-agnostic SVG components know nothing about NOM-035; the report
draws all but the range strip:

| Tag (`apps/core/templatetags/charts.py`) | Template (`templates/components/charts/`) | Geometry (`apps/core/charts.py`) |
|---|---|---|
| `{% stacked_bar items unit="cuestionario" legend=False %}` | `stacked_bar.html` | `stacked_segments()` — widths, largest-remainder percents; 2px white gaps between segments |
| `{% column_chart items unit="persona" %}` | `column_chart.html` | `columns()` — heights against the tallest column |
| `{% level_columns items unit="cuestionario" size="md" %}` | `level_columns.html` | `level_columns()` — one slot per item, empty ones included; heights as shares of a fixed 0–100 % scale, at least `LEVEL_MIN_HEIGHT` (4 %) when non-empty; largest-remainder percents |
| `{% range_strip bands scale_max points %}` | `range_strip.html` | `range_strip()` — band positions, boundary ticks, marker positions, label lanes |

Each input item carries a key, a label, a value and a **color key**; the tag
library turns the key into Tailwind `fill-*` (and swatch `bg-*`) classes, so the
data layer names no class. `{{ key|swatch }}` gives the background class of a
color key for the page's own bars and legends. `unit` picks the counted noun
(*cuestionario* or *persona*) for the SVG's `aria-label` and screen-reader
text. Each tag also takes an optional `label` for that `aria-label`, which
otherwise joins every mark's description (*"Alto · 14 cuestionarios · 23 %"*; a
range strip adds each band's span, *"Medio: 75 a 99"*).

`level_columns` draws the slots — each column 72 % of its slot — with faint
gridlines at 0, 50 and 100 %, and beneath them a `<dl>` with one equal-width
column per item: the item's name with its swatch, its percent, and its count.
`size` is the plot height: `sm` (72px), `md` (112px) or `lg` (160px); `md` and
`lg` also label the gridlines on a scale at the left, which the `<dl>` is
indented to match.

Each SVG is one `role="img"` element with an `aria-label`; its marks carry no
`aria-label`, `tabindex`, `data-tooltip` or SVG `<title>`, and no mark reacts
to hover. SVG numbers render inside `{% localize off %}` so a locale separator
can never reach a coordinate. Every colored mark has a direct label or a legend
entry, so no reading depends on color alone.

Colors:

- **NDR** — the ramp in `apps/core/templatetags/valuation_extras.py`, in two
  tiers. Categorías and the final score use the base tier (Nulo gray-300, Bajo
  green-500, Medio amber-500, Alto orange-500, Muy alto red-500); dominio rows
  and their statistics bands use the deeper dominio tier (Nulo `#9CA3AF`, Bajo
  `#4A8039`, Medio `#CA9429`, Alto `#B5531F`, Muy alto `#7A1010`), so a dominio
  never reads as a categoría. The data layer chooses the tier through the color
  key (`ndr-<level>` / `dom-<level>`); `ndr_fill` gives SVG marks and `ndr_bar`
  legend swatches, each taking `"dominio"` for the deeper tier. The dominio tier
  is validated: adjacent levels at least ΔE 16.5 apart in normal vision and
  11.4 under protan/deutan simulation.
- **Sex** — Femenino `series-1`, Masculino `series-2`, Sin dato `neutral-300`.
  The two series tokens come from the palette (`design-system.md`), and
  neither reuses a risk color.
- **Age** — every band `series-1`; "Sin dato" `neutral-300`. Position encodes the
  band and height the count, so one hue suffices.
- **Guía I** — Sin acontecimiento `neutral-300`, Acontecimiento sin requerir
  valoración `#CA9429`, Requiere valoración clínica `#7A1010`: fixed colors taken
  from the risk ramp, outside the palette.

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
A `DistributionRow` also reports `at_risk` and `at_risk_percent`: the colaboradores
in the levels of `AT_RISK` (Alto and Muy alto). A `ParticipationRow` carries
`categoria_counts` — one distribution per categoría, empty while the row is
suppressed — read through `categoria_slices(key)`; it is excluded from equality
and from a report's frozen snapshot. `categoria_options(assignment)` lists the
(key, label) of the categorías the assignment's variant measures, for
*Mostrando*. The chips and group line are built by the view from the query, not
stored in `Results`.

`apps/core/results_page.py` turns a `Results` into what the templates draw:
`Group` pairs a distribution row with its statistics row (and its dominios) and
carries `levels` and the `view_url` that chooses it in *Mostrando*; `hero_for`
picks the main box and the column for a `ver`; `area_rows`, `participation_card`,
`sex_card`, `age_card` and `guia1_card` shape the rest; `with_valid_ver` drops a
`ver` the variant does not measure.

It issues a fixed number of queries, independent of the number of respondents:
the assignment's scored count, the group's `SubmissionScore` rows with the
respondent's profile, área and localidad joined, one count of activated members
per área, the company's áreas, and one query over the group's `GroupScore` rows
at categoría and dominio level (skipped when the group is empty or suppressed),
and one over the visible áreas' `GroupScore` rows at categoría level for their
per-categoría distributions. A sex or edad filter adds one query each, since
that breakdown ignores its own filter. `MIN_GROUP_SIZE = 5` lives in `apps/nom035/constants.py`.

`apps/accounts/demographics.py` holds `AGE_BANDS` (slug, label, lower and upper
bound; 60 o más has no upper bound), `band_by_slug`, `age_on(date_of_birth,
today)`, `age_band(age)` and `birth_date_range(band, today)`.
`UserProfile.age` is `age_on` against today. The module is instrument-agnostic
because it describes `UserProfile`.

### Company dashboard

`templates/core/company_dashboard.html` shows a *Cuestionarios valorados* stat
card, gated on `can_view_insights`: the scored-questionnaire count of the
assignment the results page opens on
(`select_assignment(assignment_options(company), None)` in
`CompanyDashboardView`). The whole card links to the results page. A company
with no NOM-035 assignment reads *Sin encuestas NOM-035 asignadas* instead of a count. The
page itself is also the *Resultados* section of the company navigation.

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
| `apps/core/results_query.py` | `ResultsQuery` (with `ver`), `parse_results_query`, `results_url`, `filter_pills` |
| `apps/core/results_page.py` | `Group`, `hero_for`, `area_rows` and the card builders: what the templates draw |
| `apps/core/charts.py` | Pure chart geometry, including `stem_chart` |
| `apps/core/templatetags/charts.py` | `stacked_bar`, `column_chart`, `level_columns`, `range_strip` tags, the `swatch` filter; the chart palette |
| `apps/core/templatetags/valuation_extras.py` | `ndr_fill` |
| `apps/core/views.py`, `urls.py` | `CompanyResultsView`, `CompanyResultsFragmentView`, `_results_context`, four routes; the dashboard card's count in `CompanyDashboardView` |
| `templates/components/charts/` | `stacked_bar.html`, `column_chart.html`, `level_columns.html`, `range_strip.html` |
| `templates/core/company_results.html` | Page: pickers, sticky strip, filter dialog, `#results-status`, `#results-body` |
| `templates/core/results/` | `_fragment.html`, `_summary.html`, `_body.html` and the partials of each block |
| `templates/core/company_dashboard.html` | Link card |
| `static/ts/results_dashboard.ts` | Fragment swap, URL sync, chips, strip state, main-box toggle and level choice, *Limpiar filtros*, status line (compiled to `static/js/results_dashboard.js`) |

Tests: `apps/nom035/tests/test_results.py` (the data layer, including a query
cap), `apps/core/tests/test_results_views.py` (routes, authorization, rendering, no
interactive content inside a `<summary>`, and a query count that does not grow with respondents),
`test_results_query.py`, `test_results_page.py`, `test_charts.py`, `test_chart_components.py`,
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
- Decision: One set of filters for the whole page, kept in a sticky strip.
  Reason: The page always describes one group, which is how a reader and a
  report read it, and a filter that scrolls out of view is easy to lose track
  of. The strip also holds what is measured, so "what" and "for whom" are both
  in view wherever the page is scrolled.
- Decision: What is measured (*Mostrando*) is separate from who is counted (the
  filters), and is not a filter.
  Reason: A filter changes the group; *Mostrando* changes the question asked of
  the same group. Participación, Guía I and Quienes respondieron do not change
  with it. The strip marks both, but only a real filter turns *Filtros* solid.
- Decision: Filters can be applied from the charts (an área row, an age column),
  and a filtered item offers to remove its filter.
  Reason: A reader who spots a group in a chart should not have to reopen the
  dialog to look at it.
- Decision: Small-group and complement suppression below 5 for everyone without
  `can_view_small_groups`; the unfiltered assignment is always shown.
  Reason: The executives who see results also see the roster by sexo and área,
  so a small filtered group names its members; the employer is entitled to the
  whole-workplace result.
- Decision: A dedicated `can_view_small_groups` permission.
  Reason: Authorization is by codename, and "manages surveys" is a different
  right from "may see a group of two".
- Decision: Demographic charts count respondents of the selected assignment.
  Reason: They describe who stands behind the results; *Por área* and Participación
  carry the registered headcount alongside.
- Decision: The main chart draws five fixed level stems, one slot each, on a
  scale that ends at the next multiple of 10 above the largest share.
  Reason: An empty level keeps its slot, so every level stays in place, and the
  scale uses the plot's height instead of leaving a distribution concentrated in
  one level squeezed under a 0–100 % axis. Two charts with different scales are
  compared by their printed percents. The categoría and área rows are thin
  segmented bars with a printed percent per level. Sexo and Guía I keep a
  two- or three-part bar: each is one whole split into named parts, not a scale.
- Decision: The page shows the percent in alto o muy alto beside each categoría,
  dominio and área.
  Reason: It lets a reader see where the risk concentrates at a glance. It is a
  sum of a distribution, never a company or área level, so the page still states
  no verdict.
- Decision: The main chart, bars and cards are HTML and CSS; only the range
  strip is shared SVG.
  Reason: The page needs states the SVG components do not have (a chosen level,
  a toggle, links); the report keeps the SVG components because the PDF renderer
  paints them.
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
- Decision: Every value is printed as text; no chart mark has a tooltip or a
  hover state, the controls inside a chart (a stem, an age column, an área
  button) are real buttons and links, and a `<summary>` holds only text.
  Reason: Hover does not exist on a phone, and a focusable element nested in a
  `<summary>` is not reliably reachable by keyboard or announced by a screen
  reader.

## Open questions

None blocking. The small-group threshold and its exemption, the complement rule
and the subtraction limitation await confirmation from the domain expert and are
tracked in [`nom-035-valoracion-supuestos.md`](./nom-035-valoracion-supuestos.md).

## Linked ADRs

- [ADR-0003 — per-instrument survey-processing apps](../adr/adr-0003-per-instrument-survey-processing-apps.md)
  — why results data lives in `apps/nom035` while the chart components stay
  instrument-agnostic in `apps/core`.
- [ADR-0004 — per-company área/localidad catalogs](../adr/adr-0004-per-company-area-and-locality-catalogs.md)
  — the área and localidad pks the filters and *Por área* groups by,
  and why the catalog is per company and curated by an admin.
- [ADR-0005 — two-surname names and profile demographics](../adr/adr-0005-two-surname-names-and-profile-demographics.md)
  — sex and date of birth on `UserProfile`, age derived as of today.
