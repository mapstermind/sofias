# NOM-035 Results Dashboard

## Status

Draft

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

## Why we're building it

The "Valoración de resultados" section on the company dashboard lists counts and
one bar per área; it cannot answer the questions a NOM-035 analysis starts from —
*which categoría and dominio carry the risk, for whom, and how spread out is it*.
The Aug 3 2026 session with the domain expert asked for results dashboards kept
separate from the progress dashboard, built with the downloadable report in mind
(`docs/internal/meetings/20260803.md`).

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
- Replacing the dashboard's "Valoración de resultados" section with a link card.

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
- The employee-detail valuation card, which is unchanged.

## How it works

### Page and routes

| Route | Name | Serves |
|---|---|---|
| `/tablero-empresa/resultados/` | `core:company_results` | The viewer's own company |
| `/tablero-empresa/resultados/fragmento/` | `core:company_results_fragment` | The results body only, same parameters |
| `/empresas/<reference_code>/resultados/` | `core:company_results_for` | Any company (admin) |
| `/empresas/<reference_code>/resultados/fragmento/` | `core:company_results_fragment_for` | The results body only, same parameters |

`CompanyResultsView` and `CompanyResultsFragmentView` (`apps/core/views.py`)
follow the existing `reference_code` convention: without it the viewer's own
company is shown; with it, `can_manage_surveys` is required. Both require
`can_view_insights`; a viewer without it gets 403.

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
The value readers `_values` and `_valid_pks`, and `SEX_SLUGS`, live in
`apps/core/query_params.py`, shared by `roster.py` and `results_query.py`.

A filter is **active** when any of `sexo`, `edad`, `area` or `localidad` holds a
recognized value. `encuesta` is not a filter.

### The survey selector

The selector lists the company's assignments whose `survey.key == "nom035"`,
newest `created_at` first. Without a valid `encuesta`, the page shows the most
recent assignment with at least one scored questionnaire, falling back to the
most recent assignment. Each option is labelled from its data:

- with answers: *"Guía III · aplicada 12 ene – 28 feb 2026"* — the variant label
  and the earliest and latest `completed_at` among its scored submissions;
- without answers: *"Guía III · creada 12 ene 2026 · sin respuestas"*.

A company with no NOM-035 assignment shows *"Esta empresa aún no tiene encuestas
NOM-035 asignadas."* and no filter bar.

### Who is counted

The **group** is every `SubmissionScore` of the selected assignment whose
respondent matches the active filters. Respondent attributes are read live from
`UserProfile`: age is computed as of today in `America/Mexico_City` (ADR-0005),
and área and localidad count only when they belong to the company being viewed —
otherwise the respondent buckets as "Sin área" / "Sin localidad", the guard
`_area_of` already applies. A submission whose employee account was deleted
(`user` is null) counts as "Sin dato" on every dimension and drops out of the
group whenever a filter is active.

Age filtering runs in the database: each selected band becomes a
`date_of_birth` range computed from today.

### Page layout

A filter bar, then the results body (`#results-body`). Company-level
sections come first, categoría-level second.

| # | Section | Component |
|---|---|---|
| 0 | Active-filter pills and group line: *"Femenino · 25–29 · Operaciones — 18 cuestionarios"*, or *"Toda la empresa — 60 cuestionarios"* | text |
| **Empresa** | | |
| 1 | **Participación por área** — Registrados, Respondieron, Participación, final-NDR distribution | table + `stacked_bar` per row |
| 2 | **Perfil de quienes respondieron — sexo** | `stacked_bar` |
| 3 | **Perfil de quienes respondieron — edad** | `column_chart` |
| 4 | **Calificación final — distribución** | `stacked_bar` |
| 5 | **Calificación final — estadística** | stats row + `range_strip` |
| 6 | **Guía I — acontecimientos traumáticos severos** | headline count + `stacked_bar` |
| **Por categoría** | | |
| 7 | **Distribución por categoría** | one `stacked_bar` per categoría, each a `<details>` expanding to its dominios |
| 8 | **Estadística por categoría** | stats row + `range_strip` per categoría, each a `<details>` expanding to its dominios |

**1 — Participación por área.** One row per área of the company plus "Sin área",
sorted by name with "Sin área" last. *Registrados* counts **activated** members
of the company in that área (only activated members carry área, sexo and date of
birth); *Respondieron* counts the group's scored questionnaires in that área;
*Participación* is Respondieron ÷ Registrados as a whole percent. The sexo, edad
and localidad filters apply to both counts; the área filter limits which rows
appear. "Sin área" shows "—" for Registrados and Participación, since
activation always assigns an área. The área name links to the same page with
that área added to the filter.

**2 — Sexo.** One 100 % bar: Femenino, Masculino, Sin dato, each direct-labelled
with percent and count. Ignores the `sexo` filter, noting *"Sin filtro de
sexo"* when one is set.

**3 — Edad.** One column per band from 15–19 to 60 o más, youngest left, count
labelled on each column; a separate "Sin dato" column at the end. Ignores the
`edad` filter, with the same note.

**4 and 7 — NDR distribution.** A 100 % bar across the five levels Nulo, Bajo,
Medio, Alto, Muy alto. Row 4 is the final score; section 7 has one row per
categoría of the assignment's variant (five for Guía III, four for Guía II,
which has no Entorno organizacional), each expanding to one row per dominio.
Empty segments are omitted. Percents are rounded by largest remainder so a bar
always sums to 100. Hovering or tapping a segment shows *"Alto · 14 cuestionarios
· 23 %"*; a legend under the section repeats the five levels.

**5 and 8 — Statistics.** Each row shows *n*, *Prom.* (mean, one decimal),
*Mediana* (may end in .5), *Mín* and *Máx* of the raw integer scores. Each row
carries its own *n*: a dominio whose whole conditional block was skipped has no
`GroupScore` row, so a dominio's *n* can be lower than the final score's. Beside
the numbers (below them on a phone) a range strip draws that row's NDR threshold
bands, from 0 to the highest possible score for that row in the variant (item
count × 4; the Muy alto band is open-ended in the official tables), and plots
four labelled points — *Mín*, *Mediana*, *Prom.*, *Máx*. Points whose labels
would collide alternate above and below the strip. Hovering or tapping a point
shows its value and the band it falls in. No NDR badge is attached to any of the
four values; the page states no company or área verdict.

**6 — Guía I.** A headline *"4 colaboradores requieren valoración clínica"* over a
100 % bar of three outcomes: *Sin acontecimiento* (`guia1_event` false),
*Acontecimiento sin requerir valoración* (`guia1_event` true, `guia1_positive`
false), *Requiere valoración clínica* (`guia1_positive` true). No names appear on
this page.

### Small-group and complement rule

For a viewer **without** `can_view_small_groups` (Ejecutivo principal — the one
role besides Administrador that holds `can_view_insights`), a set
of questionnaires *S* taken out of a base *B* is shown only when

- *|S|* ≥ `MIN_GROUP_SIZE` (5), **and**
- *|B| − |S|* is 0 or ≥ `MIN_GROUP_SIZE`.

The rule applies at two levels:

- **The group.** When a filter is active, *S* is the group and *B* is every
  scored questionnaire of the assignment. If the rule fails, sections 4–8 are
  replaced by *"Grupo demasiado pequeño para mostrar resultados sin identificar a
  las personas (mínimo 5)"*. Sections 0–3 still render: they count people and
  reveal no scores. With no filter active, the whole assignment is always shown,
  whatever its size.
- **Each área row** in section 1. *S* is the row's respondents and *B* is the
  group. If the rule fails, the row keeps its counts and shows the same message
  in place of its distribution bar — also when no filter is active.

A group of zero questionnaires shows *"Ningún cuestionario coincide con los
filtros."* for every viewer.

The rule is enforced in the data layer: a suppressed result carries
`suppressed=True` and no numbers, so no template can print a small group.
Differences between two filtered views remain possible and are recorded as a
known limitation in `nom-035-valoracion-supuestos.md`.

### In-place filtering

The filter bar holds the survey selector and a **"Filtros (n)"** disclosure (a
native `<details>`), at every width: opening it reveals checkboxes for edad,
área and localidad, radio buttons for sexo, and an **Aplicar** button. It is a
plain GET form, so the page works without JavaScript by reloading.

`static/ts/results_dashboard.ts` enhances it. Changing the survey or pressing
Aplicar fetches the matching `…/fragmento/` URL, swaps `#results-body` with the
response, closes the disclosure, refreshes the count in "Filtros (n)", and
updates the address bar with `history.replaceState` — a filtered view is a
shareable link and survives a reload. The active-filter pills (each with a ×
that removes that value) and the group line render inside `#results-body`, so
the swap refreshes them; clicking a pill's × or an área name in the
participation table updates the form's controls and runs the same swap. The
company's áreas and localidades do not depend on the assignment, so the filter
bar itself is never re-rendered. The same module drives the tooltip for chart
marks on hover, keyboard focus and tap.

### Chart components

Three components render inline SVG from plain data and know nothing about
NOM-035:

| Tag (`apps/core/templatetags/charts.py`) | Template (`templates/components/charts/`) | Geometry (`apps/core/charts.py`) |
|---|---|---|
| `{% stacked_bar segments %}` | `stacked_bar.html` | `stacked_segments()` — widths, largest-remainder percents, 2px gaps |
| `{% column_chart columns %}` | `column_chart.html` | `columns()` — heights against the tallest column |
| `{% range_strip strip %}` | `range_strip.html` | `range_strip()` — band positions, marker positions, label lanes |

Each input item carries a label, a value and a **color key**; the template turns
the key into Tailwind `fill-*` classes. Every mark carries an `aria-label` and
`data-tooltip` text for the TypeScript tooltip, and is keyboard-focusable. There
is no SVG `<title>`, which would stack a second, native tooltip on the styled
one. SVG numbers render inside `{% localize off %}` so a locale separator can
never reach a coordinate. Every colored mark
has a direct label or a legend entry, so no reading depends on color alone.

Colors:

- **NDR** — the existing ramp in `apps/core/templatetags/valuation_extras.py`
  (Nulo gray-300, Bajo green-500, Medio amber-500, Alto orange-500, Muy alto
  red-500), extended with an `ndr_fill` filter for SVG.
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

`Results` is a tree of frozen dataclasses: the group size and label, the sex and
age breakdowns, the final/categoría/dominio distribution rows, the statistics
rows (each with its band table and scale maximum from `_nom035_scoring.py`), the
Guía I outcome counts, and the participation rows. It issues a fixed number of
queries — one over `SubmissionScore` with the respondent's profile, área and
localidad joined, one over the matching `GroupScore` rows at categoría and
dominio level, and one count of activated members per área — independent of the
number of respondents. `MIN_GROUP_SIZE = 5` lives in `apps/nom035/constants.py`.

`apps/accounts/demographics.py` holds `AGE_BANDS` (label, slug, lower and upper
bound; 60 o más has no upper bound) and `age_band(age)`. It is instrument-agnostic
because it describes `UserProfile`.

### Company dashboard

`templates/core/company_dashboard.html` keeps a compact "Valoración de
resultados" card, gated on `can_view_insights`: the scored-questionnaire count of
the latest NOM-035 assignment and a *"Ver resultados →"* link to the results
page. `CompanyDashboardView` passes that count instead of a company valuation.

## Schema

`nom035.SubmissionScore` gains one column:

| Field | Type | Notes |
|---|---|---|
| `guia1_event` | `BooleanField("acontecimiento traumático severo", default=False)` | `g1-1` answered "Sí". Set by `score_submission`/`materialize`; backfilled by `recompute_nom035_scores`. `guia1_positive` implies `guia1_event`. |

`ScoreResult` gains `guia1_event: bool`.

`accounts.Role.Meta.permissions` gains `("can_view_small_groups", "Puede ver
resultados de grupos pequeños")`, granted to Administrador by
`bootstrap_groups`.

## Where the code lives

| Path | Role |
|---|---|
| `apps/nom035/results.py` | `results_for` and the `Results` dataclasses; small-group rule |
| `apps/nom035/constants.py` | `MIN_GROUP_SIZE` |
| `apps/nom035/scoring.py`, `services.py`, `models.py` | `guia1_event` computed, stored, declared |
| `apps/nom035/aggregates.py` | `employee_valuation` only |
| `apps/accounts/demographics.py` | `AGE_BANDS`, `age_band` |
| `apps/accounts/models.py`, `management/commands/bootstrap_groups.py` | `can_view_small_groups` |
| `apps/core/query_params.py` | Shared GET-parameter readers |
| `apps/core/results_query.py` | `ResultsQuery`, `parse_results_query` |
| `apps/core/charts.py` | Pure chart geometry |
| `apps/core/templatetags/charts.py` | `stacked_bar`, `column_chart`, `range_strip` tags |
| `apps/core/templatetags/valuation_extras.py` | `ndr_fill` added |
| `apps/core/views.py`, `urls.py` | `CompanyResultsView`, `CompanyResultsFragmentView`, four routes |
| `templates/components/charts/` | `stacked_bar.html`, `column_chart.html`, `range_strip.html` |
| `templates/core/company_results.html` | Page: selector, filter bar, `#results-body` |
| `templates/core/results/` | `_body.html` and one partial per section |
| `templates/core/company_dashboard.html` | Link card |
| `static/ts/results_dashboard.ts` | Fragment swap, URL sync, pills, tooltip |

## Key decisions

- Decision: One assignment at a time, chosen from a selector.
  Reason: Guía II and Guía III differ in item count, thresholds and categorías,
  and a repeated round would count the same people twice, so statistics across
  assignments are meaningless.
- Decision: Assignments are labelled from their answers' date range, not a new
  name field.
  Reason: The real application period is already in the data, and a typed label
  could disagree with it; no migration is needed.
- Decision: A separate results page, linked from the dashboard.
  Reason: The expert asked for dashboards separate from the current one, and
  filtering must not re-run the progress queries.
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
- Decision: No NDR label on the mean, median or range, and no área action text.
  Reason: Labelling only the mean reads as a company grade the norm does not
  define; the área rule was an unconfirmed assumption.
- Decision: `guia1_event` is stored, not recomputed from answers.
  Reason: It matches how `guia1_positive` is stored and keeps the page off the
  `Answer` table.

## Open questions

None blocking. Assumptions awaiting confirmation from the domain expert are
tracked in [`nom-035-valoracion-supuestos.md`](./nom-035-valoracion-supuestos.md):
the small-group threshold and its exemption, the complement rule and the
subtraction limitation, the respondent-based demographics and "Sin dato"
buckets, the three Guía I outcomes, and the absence of a company- or área-level
verdict.

## Linked ADRs

- [ADR-0003 — per-instrument survey-processing apps](../adr/adr-0003-per-instrument-survey-processing-apps.md)
  — why results data lives in `apps/nom035` while the chart components stay
  instrument-agnostic in `apps/core`.
- [ADR-0004 — per-company área/localidad catalogs](../adr/adr-0004-per-company-area-and-locality-catalogs.md)
  — the área and localidad pks the filters and the participation table group by.
- [ADR-0005 — two-surname names and profile demographics](../adr/adr-0005-two-surname-names-and-profile-demographics.md)
  — sex and date of birth on `UserProfile`, age derived as of today.
