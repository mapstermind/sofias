# NOM-035 Results Report

## Status

Draft — designed, not yet implemented. Code will live in `apps/reports`, with
its new aggregates in `apps/nom035`.

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
- Two new `Company` fields: `industry` (actividad principal) and `work_center`
  (centro de trabajo).
- Three new company-level aggregates in `apps/nom035`: dimensión results,
  final-score and categoría NDR distributions per área, and Guía I outcomes per
  área — all under the existing small-group rule.
- The report's sections, generated sentences, recommendations matrix and fixed
  text, declared as an ordered section registry.
- Administrador pages to list, preview, edit, publish, unpublish and download a
  report; Ejecutivo principal pages to list, read and download published reports;
  entry points from the company dashboards and the admin results page.
- PDF rendering with WeasyPrint, from the same templates as the screen.

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
  Saving it creates the report. A draft
  computes every figure live from the current scores, so the preview always
  shows what publishing would freeze. Executives cannot see it.
- **Publicado.** *Publicar* stores the snapshot, `published_at` and
  `published_by`. The published report renders only from the snapshot, so later
  submissions or a `recompute_nom035_scores` run never change it. Its fields
  cannot be edited. *Despublicar* discards the snapshot and returns it to
  Borrador; executives lose access until it is published again.

*Publicar* is refused, with a Spanish message naming every unmet condition,
while any of these holds:

- the assignment's status is **activa** (only a closed assignment can be
  reported);
- the assignment has no scored questionnaire;
- a required field is empty: lugar de emisión, principales actividades,
  evaluator name, evaluator cédula, conclusiones.

Headcounts, signatories and additional recommendations are optional; an empty
optional block is left out of the report, never printed blank.

### Pages and routes

Administrador — requires `can_manage_surveys` and `can_view_insights`, the same
guard as the admin results route:

| Route | Purpose |
|---|---|
| `empresas/<reference_code>/reportes/` | The company's NOM-035 assignments, labelled by their answers' date range (`assignment_label`), each with its report state: *Sin iniciar*, *Borrador*, *Publicado* |
| `empresas/<reference_code>/reportes/<assignment>/` | The report — live while a draft, frozen once published — under an action bar: *Editar*, *Publicar*, *Despublicar*, *Descargar PDF* |
| `…/editar/` | One form: lugar de emisión, principales actividades, headcount presencial / home office / híbrido, evaluator and cédula, signatories (ordered rows, addable and removable), additional recommendations, conclusiones |
| `…/publicar/`, `…/despublicar/` | POST only |
| `…/pdf/` | The PDF; a draft carries a *BORRADOR* watermark on every page |

Ejecutivo principal — requires `can_view_insights`, scoped to the viewer's own
company:

| Route | Purpose |
|---|---|
| `tablero-empresa/reportes/` | Published reports only |
| `tablero-empresa/reportes/<assignment>/` | The frozen report |
| `tablero-empresa/reportes/<assignment>/pdf/` | Its PDF |

A draft, a missing report, a non-NOM-035 assignment or another company's
assignment is a 404. Entry points: a *Reporte* link on the Administrador's
company dashboard and admin results page, and a *Reporte de resultados* card on
the company dashboard next to *Valoración de resultados*.

### Report contents

Sections in order. **G** = generated from data, **A** = written by the
Administrador, **F** = fixed text.

1. **Portada** — *Reporte de resultados*, *Guías de referencia*,
   *NOM-035-STPS-2018* on three lines; the company's `legal_name`; lugar de
   emisión and the publication date (the current date on a draft); the provider.
2. **Datos del centro de trabajo** (G) — razón social, domicilio, RFC, centro de
   trabajo, actividad principal.
3. **Objetivo** (F) — placeholder text until the expert supplies it.
4. **Principales actividades** (A) — followed by the headcount by modality and
   its sum, labelled as the figures the company reported.
5. **Selección de la población** (G) — the guías applied (Guía I with Guía II
   for `small`, Guía III for `large`), the application period, activated
   members registered, questionnaires answered and the participation percent.
   It makes no claim about who was invited.
6. **Resultados**
   1. *Perfil de quienes respondieron* — sex and age band.
   2. *Participación por área*.
   3. *Calificación final* — distribution and statistics.
   4. *Resultados por categoría* — distribution and statistics per categoría.
   5. *Resultados por dominio* — distribution and statistics per dominio,
      grouped under its categoría.
   6. *Resultados por dimensión* — per dimensión, grouped under its dominio:
      *n*, minimum, median, mean, maximum and the highest possible score. No
      level: the norm publishes no dimensión thresholds.
   7. *Resultados por área* — final-score distribution per área, then each
      área's categoría distributions.
   8. *Guía I* — the company's three outcomes (sin acontecimiento /
      acontecimiento sin requerir valoración / requiere valoración clínica),
      then the same counts per área.
7. **Criterios de acción** (F, from `action_text`) — only for the levels that at
   least one worker reached in the final score or in any categoría or dominio.
8. **Recomendaciones según riesgo identificado** — for each dominio and each of
   Medio, Alto and Muy alto that at least one worker reached in it: the share of
   workers at that level, then the recommendations-matrix text for that dominio
   and level (G); followed by the additional recommendations (A).
9. **Conclusiones** (A).
10. **Responsables** — the client's signatories, the provider, the evaluator and
    their cédula, and the confidentiality notice (F).
11. **Anexo** — glossary and Ley Federal del Trabajo articles 43 and 473–475 (F),
    and *Método utilizado* (G from the scoring constants, for the applied guía
    only): the categoría → dominio → dimensión → ítem table, the item
    scoring-direction table, and the final, categoría and dominio threshold
    tables.

Counting follows the results dashboard (*Who is counted*): respondents are the
assignment's scored questionnaires; *registrados* are activated members; age is
computed at publication and frozen with the snapshot. Statistics, distributions
and percent rounding (largest remainder) are the dashboard's.

### Generated sentences

Pure functions of the snapshot, in Spanish:

- **Calificación final** — *"De los N colaboradores evaluados, el X % presentó
  niveles de riesgo Nulo o Bajo; el Y % restante, Medio, Alto o Muy alto."*
- **Categoría** — names the categoría with the largest share of workers at Alto
  plus Muy alto, ties named together, with that share. When no categoría has a
  worker at Alto or above, it says so instead.
- **Dominio** — names up to three dominios with the largest Alto plus Muy alto
  share, ties at the cut-off included, skipping any at 0 %; when none qualifies,
  it says so instead.

A sentence never names a suppressed área.

### Section registry

`apps/reports/sections.py` declares the report as one ordered list. Each entry
has a key, a title, a partial template, and a function building that section's
context from the snapshot (or from fixed content). The screen, the PDF and the
table of contents all iterate the registry, so reordering, removing or adding a
section is a registry change plus a partial. The screen and the PDF share every
partial.

### Snapshot

The snapshot stores **data**, not rendered output: counts, percents,
statistics, strip geometry inputs, the levels present, the área rows with their
suppression state, and the company and assignment facts printed on the report.
Generated sentences, the recommendations matrix and fixed text render from the
snapshot at view time, so a published report's figures never change while a
wording correction in code reaches it too. A change to the snapshot's shape is
not migrated; the report is unpublished and published again.

### Small groups

The report is always computed with the small-group and complement rule
(`shows`, `_hide_until_safe` in `apps/nom035/results.py`), whoever views it,
the Administrador's preview included — so the preview is exactly what the client
receives. It affects only per-área content: the participation rows (6.2), the
per-área distributions (6.7) and the per-área Guía I counts (6.8). A hidden área
keeps its registered and responded counts and shows the dashboard's suppression
message. Company-wide sections use the whole assignment.

### Visual design

**Finding first, chart as evidence.** Each results section opens with its
generated sentence, set larger in the serif, then the chart, then the small
print (*n*, base, suppression note). The five-level NDR palette (gray, green,
amber, orange, red — `valuation_extras`) is the only meaning-bearing color and
appears only where a risk level is meant.

- **Type.** Source Serif 4 for prose (findings, Administrador text, fixed
  text); Source Sans 3 for data (tables, charts, figures). Body measure about
  65 characters; sentence case; no all-caps labels. Both families are bundled
  under `static/fonts/` (SIL Open Font License) so screen and PDF match — the
  app's system font stack would make the PDF depend on the server's fonts.
- **Color.** White sheet, ink `#111827`, secondary `#4B5563`, rules `#E5E7EB`;
  brand indigo `#4338CA` only for navigational structure — section numbers,
  table of contents, running header.
- **Cover.** Typographic only: the title on three lines, the razón social as the
  largest element, place and date, provider at the foot. No risk colors.

Chart placement reuses the dashboard's template tags and geometry
(`apps/core/templatetags/charts.py`, `apps/core/charts.py`) unchanged, through
report-specific partials — never the dashboard's partials, which carry filter,
disclosure and fragment logic:

| Section | Components |
|---|---|
| 6.1 Perfil | `stacked_bar` (sex), `column_chart` (age), stacked at full width |
| 6.2 Participación | table, `level_columns` per área row |
| 6.3 Calificación final | `level_columns` (lg) and `range_strip` |
| 6.4 Categoría | `level_columns` and `range_strip` per categoría |
| 6.5 Dominio | `level_columns` (sm) and `range_strip` per dominio under its categoría; always expanded |
| 6.6 Dimensión | `range_strip` with a single neutral gray band from 0 to the highest possible score |
| 6.7 Por área | one `stacked_bar` row per área for the final score; then small `level_columns` per categoría under each área |
| 6.8 Guía I | `stacked_bar` for the company; count table per área |
| 7 Criterios de acción | NDR badge and text, with a left rule in the level's color |
| 8 Recomendaciones | per dominio: NDR badge, the share, the matrix text; refers back to 6.5 |
| Anexo, Método | numeric tables; threshold header cells in each level's color |

Report partials use breakpoints up to `md:` only: WeasyPrint lays the letter
page out at about 816 px, where `lg:` never applies.

### On a phone

One column at 360 px. Every table becomes stacked rows — one block per
categoría, dominio or área with its level shares — and the action bar wraps. The
PDF keeps the letter-page layout.

### PDF

`render_report_pdf(report)` renders the registry's partials inside a standalone
`base_report.html` (no app chrome, no action bar) and passes it to WeasyPrint
with a URL fetcher that resolves fonts, CSS and images through Django's static
finders — no HTTP request to the app itself. The response is `application/pdf`,
an attachment named `reporte-nom035-<reference_code>-<yyyy-mm>.pdf`, generated
synchronously per request without caching.

Paged media:

- letter size; a running header with the razón social from page 2; footer
  *Página N de M*;
- a table of contents with page numbers from `target-counter()`;
- a page break before the cover, before *Resultados* and before the annex;
- finding blocks and table rows never split; table headers repeat;
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
| | `headcount_in_person`, `headcount_home_office`, `headcount_hybrid` | nullable positive integers |
| | `evaluator_name`, `evaluator_license` | evaluator and cédula |
| | `additional_recommendations`, `conclusions` | text |
| `reports.ReportSignatory` | `report`, `title`, `name`, `order` | the client's signatories |

The provider's identity, the confidentiality notice, the recommendations matrix
(keyed by the engine's dominio keys, covering both variants), the glossary, the
Ley Federal del Trabajo articles and the Objetivo placeholder are constants in
`apps/reports`.

## Where the code will live

| Path | Holds |
|---|---|
| `apps/nom035/results.py` | dimensión, per-área distribution and per-área Guía I aggregates |
| `apps/reports/models.py` | `Report`, `ReportSignatory` |
| `apps/reports/snapshot.py` | building the snapshot from the aggregates |
| `apps/reports/sections.py` | the section registry |
| `apps/reports/text.py` | generated sentences |
| `apps/reports/content.py` | recommendations matrix, provider, confidentiality notice, glossary, LFT, Objetivo |
| `apps/reports/pdf.py` | `render_report_pdf`, the static URL fetcher |
| `apps/reports/views.py`, `urls.py`, `forms.py` | pages, publish/unpublish, the edit form and signatory formset |
| `templates/reports/` | `base_report.html`, report page, section partials |
| `static/fonts/` | Source Serif 4 and Source Sans 3 |

`apps/reports` is registered as `apps.reports` with a short label and Spanish
model metadata.

## Key decisions

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
  `Company`; headcount, signatories and evaluator on `Report`; provider identity
  in code.
  Reason: Round-specific facts on `Company` would rewrite older reports.
- Decision: Only the Ejecutivo principal reads reports, through
  `can_view_insights`.
  Reason: The report holds the results page's data, so it shares its audience.
- Decision: The small-group rule always applies, preview included.
  Reason: One frozen version per report, and the Administrador writes against
  the figures the client sees.
- Decision: WeasyPrint renders the PDF server-side from the screen templates.
  Reason: A real download, identical every time, with paged-media headers,
  footers and page numbers, without shipping a browser.
- Decision: Reuse the dashboard's chart tags and geometry, not its partials.
  Reason: The dashboard and the report can evolve independently.
- Decision: Recommendations matrix, fixed text and provider identity are code
  constants.
  Reason: They are consultancy content shared by every report, revised by
  developers.

## Open questions

- Whether WeasyPrint renders Tailwind v4's compiled CSS (`oklch()`, cascade
  layers, custom properties) and the SVG charts correctly. Settled by the
  plan's first task, a throwaway spike: if it does, the PDF uses `output.css`
  plus a page stylesheet; if not, the PDF uses a plain report stylesheet with
  hex colors.
- Where the reference material the fixed text is transcribed from lives once
  this branch merges (`docs/temporal/` is untracked).
- Domain points awaiting the expert are tracked in
  [`nom-035-valoracion-supuestos.md`](./nom-035-valoracion-supuestos.md):
  unsuppressed reports for Administración, the Objetivo text, and stating each
  level in the final-score sentence.

## Linked ADRs

- [ADR-0003 — per-instrument survey-processing apps](../adr/adr-0003-per-instrument-survey-processing-apps.md)
  — the report is NOM-035-specific and its aggregates belong to `apps/nom035`.
