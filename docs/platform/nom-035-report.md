# NOM-035 Results Report

## Status

Current — implemented in `apps/reports`; aggregates in `apps/nom035/results.py`;
pages at `/empresas/<código>/reportes/` and `/tablero-empresa/reportes/`.

## What this does

An Administrador writes one **Reporte de resultados** per closed NOM-035 survey
assignment of a company: the platform fills every figure, chart, table and
figure-bearing sentence from the survey data, and the Administrador adds the
facts the platform does not hold — the place of issue, the company's main
activities and headcount by work modality, the evaluator and their cédula, the
client's signatories, conclusions and any extra recommendations. Publishing
freezes the figures; from then on the company's Ejecutivo principal reads the
same report on the platform and downloads it as a letter-size PDF, page for
page identical every time. The report states risk as **distributions of
workers across the five Niveles de Riesgo**, never as a single company level,
and draws the results with the same chart components as the results dashboard.

## Why we're building it

The client keeps a formal results document as evidence of having applied the
Guías de Referencia, and the domain expert named its structure the top priority
(`docs/internal/meetings/20260609_00.md`). Hand-assembled reports carry
copy-paste errors — figures in the narrative that disagree with the chart beside
them — which generating every figure-bearing sentence from data removes.

## Scope

**In scope:**

- A `Report` per NOM-035 `SurveyAssignment`: draft / published, a frozen data
  snapshot on publish, Administrador-written fields, and an ordered list of
  client signatories.
- Two `Company` fields: `industry` (actividad principal) and `work_center`
  (centro de trabajo).
- Company-level aggregates in `apps/nom035`: dimensión results, final-score and
  categoría NDR distributions per área, and Guía I outcomes per área — all under
  the small-group rule.
- The report's sections, generated sentences, recommendations matrix and fixed
  text, declared as an ordered section registry.
- Administrador pages to list, preview, edit, publish, unpublish and download a
  report; Ejecutivo principal pages to list, read and download published reports;
  entry points from the company dashboards and the admin results page.
- PDF rendering with WeasyPrint, from the same partials as the screen.

**Out of scope:**

- A per-question (per-item) breakdown.
- The sample prevention policy, the conformity-assessment (audit) table, theory
  chapters and the blank questionnaires as annexes.
- Generating the Plan Bianual de Prevención.
- A named list of workers requiring clinical referral — the platform is
  anonymous.
- Filters (sexo, edad, área, localidad) on the report; it always covers the
  whole assignment.
- A report for any instrument other than NOM-035.
- Ejecutivo secundario access, and unsuppressed reports for Administración (see
  Open questions).
- Editing the generated text, the recommendations matrix or the fixed text from
  the platform; they change in code.

## How it works

### Lifecycle

A report has two states.

- **Borrador.** Until the first save, the report page previews the assignment
  with every Administrador field empty, and nothing is stored. The edit form
  opens prefilled with the evaluator and the signatories of the company's most
  recent other report, when there is one; every other field starts empty.
  Saving it creates the report. A draft computes every figure live from the
  current scores, so the preview always shows what publishing would freeze.
  Executives cannot see it.
- **Publicado.** *Publicar* stores the snapshot, `published_at` and
  `published_by`. The published report renders only from the snapshot, so later
  submissions or a `recompute_nom035_scores` run never change it. Its fields
  cannot be edited: the edit page redirects back with *Despublica el reporte para
  editarlo.* — the Django admin shows a published report and its signatories
  read-only as well. Clicking *Publicar* again on a published report changes
  nothing and says nothing. *Despublicar* first asks the browser to confirm
  (*¿Despublicar el reporte? El contenido congelado se descartará y la empresa
  dejará de verlo hasta que se publique de nuevo.*), then discards the snapshot
  and returns the report to Borrador; executives lose access until it is
  published again.

*Publicar* is refused, with one Spanish message per unmet condition, while any
of these holds:

- the assignment's status is **activa** (only a closed assignment can be
  reported);
- the assignment has no scored questionnaire;
- a required field is empty: lugar de emisión, principales actividades,
  evaluator name, evaluator cédula, conclusiones.

A draft's page lists the same conditions under *Para publicar falta:* above the
report (`publishing.blockers`).

Headcounts, signatories and additional recommendations are optional; an empty
optional block is left out of the report, never printed blank.

### Pages and routes

Administrador — requires `can_manage_surveys` and `can_view_insights`, the same
guard as the admin results route:

| Route | Purpose |
|---|---|
| `empresas/<reference_code>/reportes/` | The company's NOM-035 assignments, labelled by their answers' date range (`assignment_label`), each with its report state: *Sin iniciar*, *Borrador*, *Publicado*, and its count of scored questionnaires — the frozen count once published |
| `empresas/<reference_code>/reportes/<assignment>/` | The report — live while a draft, frozen once published — under a sticky action bar: *Descargar PDF*, then *Editar* and *Publicar* on a draft or *Despublicar* on a published report |
| `…/editar/` | One form: lugar de emisión, principales actividades, headcount presencial / home office / híbrido, evaluator and cédula, signatories (ordered rows, addable and removable), additional recommendations, conclusiones |
| `…/publicar/`, `…/despublicar/` | POST only |
| `…/pdf/` | The PDF; a draft carries a *BORRADOR* watermark on every page |

Ejecutivo principal — requires `can_view_insights`, scoped to the viewer's own
company (a viewer with no company is sent to profile setup):

| Route | Purpose |
|---|---|
| `tablero-empresa/reportes/` | Published reports only, each with its frozen count of scored questionnaires |
| `tablero-empresa/reportes/<assignment>/` | The frozen report, with *Descargar PDF* |
| `tablero-empresa/reportes/<assignment>/pdf/` | Its PDF |

A draft, a missing report, a non-NOM-035 assignment or another company's
assignment is a 404. Entry points: a *Reporte de resultados* link on the
Administrador's company dashboard and a *Reporte* link on the admin results
page; a *Reporte de resultados* card on the Ejecutivo principal's company
dashboard next to *Valoración de resultados*.

### Report contents

The table of contents (*Contenido*) follows the portada, on screen and in the
PDF. Sections in order, with the numbers the report prints. **G** = generated
from data, **A** = written by the Administrador, **F** = fixed text.

- **Portada** (unnumbered) — *Reporte de resultados*, *Guías de referencia*,
  *NOM-035-STPS-2018* on three lines; the company's `legal_name` (its `name`
  when blank); lugar de emisión and the publication date (the current date on a
  draft); at the foot, *Implementación externa y apoyo logístico* over the
  company's `name`.

1. **Datos del centro de trabajo** (G) — razón social, domicilio, RFC, centro de
   trabajo, actividad principal; a blank fact prints *—*.
2. **Objetivo** (F) — placeholder text until the expert supplies it.
3. **Principales actividades** (A) — followed, when any headcount is filled, by
   *Número de trabajadores*: the filled modalities and their total, labelled as
   the figures the company reported.
4. **Selección de la población** (G) — the guías applied (Guía I with Guía II
   for `small`, Guía III for `large`), the application period, activated
   members registered, questionnaires answered and the participation percent.
   The period is the span of the scored questionnaires' completion dates
   (`period_span`) and is printed only when there is one. It makes no claim
   about who was invited.
5. **Resultados**
   1. *Perfil de quienes respondieron* — sex and age band.
   2. *Participación por área*.
   3. *Calificación final* — distribution and statistics.
   4. *Resultados por categoría* — distribution and statistics per categoría.
   5. *Resultados por dominio* — distribution and statistics per dominio,
      grouped under its categoría.
   6. *Resultados por dimensión* — per dimensión, grouped under its dominio:
      the statistics row with a single neutral band up to the highest possible
      score. No level: the norm publishes no dimensión thresholds.
   7. *Resultados por área* — final-score distribution per área, then each
      visible área's categoría distributions.
   8. *Guía I* — the company's three outcomes (sin acontecimiento /
      acontecimiento sin requerir valoración / requiere valoración clínica),
      then the same counts per área.
6. **Criterios de acción** (F, from `action_text`) — the norm's verbatim action
   criteria, only for the levels that at least one worker reached in the final
   score or in any categoría or dominio.
7. **Recomendaciones según riesgo identificado** — grouped by categoría and
   dominio: for each of Medio, Alto and Muy alto that at least one worker
   reached in a dominio, the share of workers at that level, then the
   recommendations-matrix text for that dominio and level (G); followed by the
   additional recommendations (A).
8. **Conclusiones** (A).
9. **Responsables** — the client's signatories, then under *Implementación
   externa y apoyo logístico* the company's `name`, the evaluator and their
   cédula, and the confidentiality notice (F) with the company's `name` filled
   in.
10. **Anexo** — glossary and Ley Federal del Trabajo articles 43 and 473–475
    (F), and *Método utilizado* (G from the scoring constants, for the applied
    guía only): the categoría → dominio → dimensión → ítem table, the item
    scoring-direction table, and the final, categoría and dominio threshold
    tables.

Every statistics row prints *n*, *Prom.*, *Mediana*, *Mín*, *Máx* and *Máx.
posible*, with the range strip below. Each results section that has no scored
questionnaire prints *Aún no hay cuestionarios valorados en esta encuesta.*

Counting follows the results dashboard (*Who is counted*): respondents are the
assignment's scored questionnaires; *registrados* are activated members; age is
computed on the day the data is built and frozen with the snapshot. Statistics,
distributions and percent rounding (largest remainder) are the dashboard's.

### Generated sentences

Pure functions in `apps/reports/text.py`, in Spanish. Every share a sentence
prints is the row's largest-remainder percents summed — the same figures the
chart beside it prints. Ranking and ties are decided on the exact fractions.

- **Calificación final** — *"De los N colaboradores evaluados, el X % presentó
  niveles de riesgo Nulo o Bajo; el Y % restante, Medio, Alto o Muy alto."*
  (*"De 1 colaborador evaluado, …"* for a single worker.)
- **Categoría** — names the categoría with the largest share of workers at Alto
  plus Muy alto, with that share. Tied categorías are named together: with one
  share (*"… cada una"*) when their printed shares match, with each one's share
  when rounding prints them differently. When no categoría has a worker at Alto
  or above, it says so instead.
- **Dominio** — names up to three dominios with the largest Alto plus Muy alto
  share, each with its share, ties at the cut-off included, skipping any at 0 %;
  when none qualifies, it says so instead.

A recommendation's share is the dominio row's largest-remainder percent at that
level. Sentences name categorías and dominios only, never an área.

### Section registry

`apps/reports/sections.py` declares the report as one ordered tuple,
`REGISTRY`. Each `Section` has a key, a title, a partial template, a function
building that section's context from a `ReportContext` (the report, its data,
the draft flag, the issue date and the signatories), and optional children
(*Resultados* holds its eight). Numbers derive from position: every titled
section is numbered, the untitled portada is not. The screen, the PDF and the
table of contents all iterate the registry through `templates/reports/_document.html`,
so reordering, removing or adding a section is a registry change plus a
partial. The screen and the PDF share every partial. A section's
`break_before` flag makes it start a new page in the PDF (see *PDF*).

### Snapshot

The snapshot stores **data**, not rendered output: `ReportData`
(`apps/reports/snapshot.py`) — the company facts printed on the report, the
variant and its label, the period label, registered, responded and
participation, the computation date, the sex and age slices, the participation
rows with their suppression state, the final and categoría distributions and
statistics (dominios as their children), the dimensión groups, the área rows and
the Guía I counts. Strip bands are clamped to the highest possible score, since
JSON holds no infinity. `dump` and `load` round-trip exactly, so a draft and a
published report render through the same dataclasses. Generated sentences, the
levels for *Criterios de acción*, the recommendations matrix and fixed text
render from the snapshot at view time, so a published report's figures never
change while a wording correction in code reaches it too. A change to the
snapshot's shape is not migrated; the report is unpublished and published again.

### Small groups

The report is always computed with the small-group and complement rule
(`shows`, `_hide_until_safe` in `apps/nom035/results.py`), whoever views it,
the Administrador's preview included — so the preview is exactly what the client
receives. It affects only per-área content: the participation rows (5.2), the
per-área distributions (5.7) and the per-área Guía I counts (5.8). A hidden área
keeps its registered and responded counts and shows the dashboard's suppression
message. Company-wide sections use the whole assignment.

### Visual design

**Finding first, chart as evidence.** Each results section with a finding opens
with its generated sentence, set larger in the serif, then the chart, then the
small print (*n*, base, suppression note). The five-level NDR palette is the
only meaning-bearing color and appears only where a risk level is meant. It
has two tiers: categorías and the final score draw in the base tier, dominios
in a deeper variant of the same five levels, so a reader can tell a dominio's
level from a categoría's at a glance.

| Level | Categoría and final | Dominio |
|---|---|---|
| Nulo | `#D1D5DB` | `#9CA3AF` |
| Bajo | `#22C55E` | `#4A8039` |
| Medio | `#F59E0B` | `#CA9429` |
| Alto | `#F97316` | `#B5531F` |
| Muy alto | `#EF4444` | `#7A1010` |

Dominio marks — the 5.5 columns and statistics bands, the recommendation
badges and left rules, the annex's dominio threshold headers — use the dominio
tier; everything else uses the base tier. Categoría badges are tinted; dominio
badges are solid, with white text on Bajo, Alto and Muy alto and `#111827` on
Nulo and Medio. Every block of colored marks closes with the legend of its
tier; 5.5's is headed *Dominios*.

- **Type.** Source Serif 4 for prose (findings, Administrador text, fixed
  text); Source Sans 3 for data (headings, tables, charts, figures). Body
  measure about 65 characters; sentence case; no all-caps labels. Both families
  are bundled under `static/fonts/` (SIL Open Font License, `OFL.txt`) so
  screen and PDF match.
- **Color.** White sheet, ink `#111827`, secondary `#4B5563`, rules `#E5E7EB`;
  brand indigo `#4338CA` only for navigational structure — section numbers,
  table of contents, running header.
- **Cover.** Typographic only: the title on three lines, the razón social as the
  largest element, place and date, the company's `name` at the foot. No risk
  colors.

The report partials carry only `report-*` classes, defined in plain CSS:

| File | Holds |
|---|---|
| `static/css/report.css` | The fonts and every report class, phone first |
| `static/css/report-wide.css` | The wide layout: real tables, two-column people lists, single-row statistics |
| `static/css/report-print.css` | Paged media; the PDF only |

The screen page links `report-wide.css` with `media="print, (min-width: 768px)"`.
The PDF links it unconditionally: WeasyPrint matches no width media feature and
discards a media list that contains one, so no breakpoint applies in the PDF
and the letter page always gets the wide layout. The page chrome around the
report (header, action bar, messages) is the app's Tailwind.

Chart placement reuses the dashboard's template tags and geometry
(`apps/core/templatetags/charts.py`, `apps/core/charts.py`) unchanged, through
report-specific partials in `templates/reports/sections/results/` — never the
dashboard's partials, which carry filter, disclosure and fragment logic:

| Section | Components |
|---|---|
| 5.1 Perfil | `stacked_bar` (sex), `column_chart` (age), stacked at full width |
| 5.2 Participación | table, `level_columns` (sm) per área row |
| 5.3 Calificación final | `level_columns` (lg) and the statistics row with `range_strip` |
| 5.4 Categoría | `level_columns` and the statistics row per categoría |
| 5.5 Dominio | `level_columns` (sm) and the statistics row per dominio under its categoría, in the dominio tier; always expanded; a *Dominios* legend |
| 5.6 Dimensión | the statistics row, `range_strip` with a single neutral gray band from 0 to the highest possible score |
| 5.7 Por área | one `stacked_bar` row per área for the final score; then small `level_columns` per categoría under each visible área |
| 5.8 Guía I | `stacked_bar` for the company; count table per área |
| 6 Criterios de acción | NDR badge and text, with a left rule in the level's color |
| 7 Recomendaciones | per dominio: a solid dominio-tier badge, the share, the matrix text, a left rule in the dominio tier; refers back to 5.5 |
| Anexo, Método | numeric tables; threshold header cells carry a bar in each level's color — the dominio table in the dominio tier |

### On a phone

One column at 360 px. The per-área tables (participation, por área, Guía I)
become stacked rows — one block per área, each value labelled. The two-column
tables (Datos del centro de trabajo, Número de trabajadores) stay tables: they
fit at 360 px. Statistics rows put the label above three figures per line and
the strip below; signatories list in one column; the action bar wraps. The PDF
keeps the letter-page layout.

### PDF

`render_report_pdf(report)` (`apps/reports/pdf.py`) renders the registry inside
the standalone `templates/reports/base_report.html` via `report_pdf.html` (no
app chrome, no action bar). The document links `output.css`, `report.css`,
`report-wide.css` and `report-print.css` relative to a fictitious `BASE_URL`;
`ReportURLFetcher` resolves those links through Django's static finders and
refuses every other URL — no network, no request to the app itself. One
`FontConfiguration` is passed to `write_pdf`, so the `@font-face` rules apply
and both families are embedded as subsets. The response is `application/pdf`,
an attachment named `reporte-nom035-<reference_code>-<yyyy-mm>.pdf` (the month
of publication, or the current month for a draft), generated synchronously per
request without caching. WeasyPrint loads only when a PDF is requested.

WeasyPrint ignores Tailwind's `fill-*` classes, so the chart components also
carry each mark's color as a hex `fill` attribute and give their `<text>` a
`font-family` attribute; on screen the classes win.

Paged media (`report-print.css`):

- letter size; a running header with the razón social, set from the cover, and a
  footer *Página N de M*, both from page 2;
- the portada alone on page 1, the table of contents from page 2, with dotted
  leaders and page numbers from `target-counter()`;
- a new page after the portada and after the table of contents;
- a new page for every section whose registry entry sets `break_before`:
  *Resultados*, 5.5 to 5.8, and sections 6 to 10 (*Criterios de acción*,
  *Recomendaciones*, *Conclusiones*, *Responsables*, *Anexo*);
- inside 5.4, 5.5 and 5.6, each repeated group — a categoría, a categoría's
  dominios, a dominio's dimensiones — is a `report-page-group`, and every group
  after the first starts a new page, so the first follows its section heading;
- finding blocks, charts, statistics rows, criteria and table rows never split;
  table headers repeat;
- drafts carry a fixed-position *BORRADOR* watermark, repeated on every page.

A WeasyPrint failure surfaces as a logged 500.

## Schema

| Model | Field | Notes |
|---|---|---|
| `accounts.Company` | `industry` | actividad principal; blank allowed |
| | `work_center` | centro de trabajo; blank allowed |
| `reports.Report` | `assignment` | OneToOne → `SurveyAssignment` |
| | `status` | `draft` / `published` |
| | `snapshot` | JSON; null while a draft |
| | `published_at`, `published_by` | null while a draft |
| | `issued_in` | lugar de emisión |
| | `activities_summary` | principales actividades |
| | `headcount_in_person`, `headcount_home_office`, `headcount_hybrid` | nullable positive integers; `headcount_total` sums the filled ones |
| | `evaluator_name`, `evaluator_license` | evaluator and cédula |
| | `additional_recommendations`, `conclusions` | text |
| | `created_at`, `updated_at` | |
| `reports.ReportSignatory` | `report`, `title`, `name`, `order` | the client's signatories, ordered by `order` |

The confidentiality notice (with the company's `name` filled in at render),
the recommendations matrix (keyed by the engine's dominio keys, covering both
variants), the glossary, the Ley Federal del Trabajo articles and the Objetivo
placeholder are constants in `apps/reports/content.py`, transcribed from the
reference material in `docs/internal/report-references/`.

## Where the code lives

| Path | Holds |
|---|---|
| `apps/nom035/results.py` | `report_results` and its dataclasses (`ReportResults`, `DimensionGroup`, `AreaResults`); `period_span`, `local_date` |
| `apps/nom035/_nom035_scoring.py` | `action_text`, the norm's action criteria |
| `apps/reports/models.py` | `Report`, `ReportSignatory` |
| `apps/reports/snapshot.py` | `ReportData`, building it from the aggregates, `dump`/`load`, `data_for` |
| `apps/reports/publishing.py` | `blockers`, `publish`, `unpublish` |
| `apps/reports/sections.py` | the section registry, `context_for`, `render_sections`, the annex's method tables |
| `apps/reports/text.py` | generated sentences, action criteria, recommendations |
| `apps/reports/content.py` | recommendations matrix, confidentiality notice, glossary, LFT, Objetivo |
| `apps/reports/pdf.py` | `render_report_pdf`, `ReportURLFetcher`, the filename |
| `apps/reports/views.py`, `urls.py`, `forms.py`, `admin.py` | pages, publish/unpublish, the edit form and signatory formset, the Django admin |
| `templates/reports/` | the list, detail and form pages, `_document.html`, `base_report.html`, `report_pdf.html`, `sections/` partials |
| `static/css/report.css`, `report-wide.css`, `report-print.css` | the report's plain CSS |
| `static/fonts/` | Source Serif 4 and Source Sans 3 variable TTFs, `OFL.txt` |
| `docs/internal/report-references/` | the report template and the risk-interpretation note the fixed text and sentences follow |

`apps/reports` is registered as `apps.reports` (label `reports`, *Reportes* in
the admin) with Spanish model metadata.

## Key decisions

- Decision: Dominios draw in a deeper tier of the risk palette; categorías and
  the final score in the base tier.
  Reason: Readers move between categoría and dominio charts constantly, and the
  tier tells them which one they are reading. The dominio hexes are validated
  (OKLab ΔE ×100): adjacent dominio levels at least 16.5 apart in normal vision
  and 11.4 under protan/deutan simulation, every mark at least 2.5:1 on white.
  Medio is the closest pair across tiers (ΔE 7.8), so the tier is never carried
  by color alone: the legend names it and dominio badges are solid.

- Decision: Risk is stated as the distribution of workers across levels; the
  mean is a plain number with no level attached, and there is no company verdict.
  Reason: The norm assigns levels to workers only, and the results dashboard
  already decided against labelling the mean.
- Decision: Criterios de acción and recommendations appear for every level any
  worker reached, with the share stated.
  Reason: The norm's analysis is per worker; a minimum share would hide
  individual workers at Muy alto.
- Decision: Rankings in generated sentences use Alto plus Muy alto.
  Reason: The norm calls for a categoría and dominio analysis at both levels.
- Decision: A sentence prints the chart's largest-remainder percents and ranks
  on exact fractions.
  Reason: The sentence must never disagree with the chart beside it, and
  rounding must not decide which categoría or dominio leads.
- Decision: Figure-bearing text is generated and not editable; the
  Administrador writes separate fields.
  Reason: Hand-edited figures drift from the data beside them.
- Decision: Publishing freezes a data snapshot, and only a closed assignment can
  be published.
  Reason: A delivered report must not change when submissions arrive or scores
  are recomputed.
- Decision: The snapshot stores data, not rendered HTML.
  Reason: The report's structure is expected to be revised; data can be
  re-rendered through new templates.
- Decision: Facts are stored where they stay true — industry and work centre on
  `Company`; headcount, signatories and evaluator on `Report`.
  Reason: Round-specific facts on `Company` would rewrite older reports.
- Decision: Only the Ejecutivo principal reads reports, through
  `can_view_insights`.
  Reason: The report holds the results page's data, so it shares its audience.
- Decision: The small-group rule always applies, preview included.
  Reason: One frozen version per report, and the Administrador writes against
  the figures the client sees.
- Decision: WeasyPrint renders the PDF server-side from the screen partials.
  Reason: A real download, identical every time, with paged-media headers,
  footers and page numbers, without shipping a browser.
- Decision: The report is styled by plain CSS — `report.css`, `report-wide.css`
  and the PDF-only `report-print.css` — and charts carry hex `fill` attributes;
  the PDF also loads `output.css` for the chart components' layout. Fonts are
  the Source Serif 4 and Source Sans 3 variable TTFs, declared with one
  `@font-face` per weight.
  Reason: WeasyPrint ignores Tailwind's `fill-*` utilities, matches no width
  media query, and rejects a `font-weight` range; bundled fonts keep the PDF
  independent of the server's installed fonts.
- Decision: Reuse the dashboard's chart tags and geometry, not its partials.
  Reason: The dashboard and the report can evolve independently.
- Decision: Where the template names the implementing business, the report
  prints the client company's `name`.
  Reason: Decided with the product owner; the platform already shows that name
  everywhere.
- Decision: Recommendations matrix and fixed text are code constants.
  Reason: They are consultancy content shared by every report, revised by
  developers.

## Open questions

- Domain points awaiting the expert are tracked in
  [`nom-035-valoracion-supuestos.md`](./nom-035-valoracion-supuestos.md):
  unsuppressed reports for Administración, the Objetivo text, and stating each
  level in the final-score sentence.

## Linked ADRs

- [ADR-0003 — per-instrument survey-processing apps](../adr/adr-0003-per-instrument-survey-processing-apps.md)
  — the report is NOM-035-specific and its aggregates belong to `apps/nom035`.
