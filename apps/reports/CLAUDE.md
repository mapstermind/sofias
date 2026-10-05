# reports

The **NOM-035 results report**: one `Report` per NOM-035 `SurveyAssignment`,
drafted and published by an Administrador, read by the company's Ejecutivo
principal, and downloadable as a letter-size PDF. It reads its figures from
`apps/nom035` (`report_results`) and draws them with `apps/core`'s chart
components. Registered as `apps.reports` (label `reports`, admin heading
*Reportes*). Full design: `docs/platform/nom-035-report.md`.

## What lives here

- `models.py` — `Report` (status `draft`/`published`, `snapshot` JSON, the
  Administrador-written fields, `headcount_total`) and `ReportSignatory` (the
  client's signatories, ordered by `order`).
- `snapshot.py` — `ReportData` and `CompanyFacts`, the report's data as frozen
  dataclasses. `build_report_data(assignment)` builds it live from
  `apps.nom035.results.report_results`; `dump`/`load` turn it into JSON and back,
  round-tripping exactly; `data_for(report)` loads a published report's snapshot
  and builds a draft's data live.
- `text.py` — the generated sentences (`final_sentence`, `categoria_sentence`,
  `dominio_sentence`), `action_criteria` (the norm's `action_text` for each level
  reached) and `recommendations`. Pure functions of `ReportData`. Shares are the
  row's largest-remainder percents, as the charts print them; ranking and ties
  use exact fractions.
- `content.py` — fixed consultancy text as constants: `RECOMMENDATIONS` (dominio
  key → level → text), `CONFIDENTIALITY_NOTICE` (formatted with the company's
  `name`), `GLOSSARY`, `LFT_ARTICLES`, `OBJECTIVE_PLACEHOLDER`. Transcribed from
  `docs/internal/report-references/`. The norm's own action criteria stay in
  `apps/nom035/_nom035_scoring.py`.
- `sections.py` — **the report's structure.** `REGISTRY` is one ordered tuple of
  `Section(key, title, template, build, children)`; `context_for(report)` makes
  the `ReportContext` and `render_sections(ctx)` numbers the registry by position
  and builds each section's context. `method_tables` builds the annex's tables
  from the scoring constants.
- `publishing.py` — `blockers(report)` (the Spanish reasons *Publicar* is
  refused), `publish(report, user)` (stores the snapshot) and `unpublish(report)`
  (discards it).
- `pdf.py` — `render_report_pdf(report)` renders `reports/report_pdf.html` with
  WeasyPrint; `ReportURLFetcher` serves only static files; `filename(report)`.
- `views.py`, `urls.py` — Administrador views (`AdminMixin`: `can_manage_surveys`
  and `can_view_insights`, any company, under `empresas/<código>/reportes/`) and
  Ejecutivo principal views (`ExecutiveMixin`: `can_view_insights`, own company,
  published only, under `tablero-empresa/reportes/`). The URLs are included at the
  site root.
- `forms.py` — `ReportForm` and `SignatoryFormSet` (rows keep the order shown;
  an untouched blank row is skipped).
- `admin.py` — `Report` with its signatories inline; status and snapshot read-only.

Templates are in `templates/reports/`: the list, detail and form pages,
`_document.html` (the registry loop, with the TOC right after the portada —
shared by screen and PDF), `base_report.html` and `report_pdf.html` (the PDF
document), and `sections/` (one partial per section; `sections/results/` holds
the results partials and the shared statistics row, `_stats.html`).

## Conventions & gotchas

- **Change the report's structure in the registry.** Reordering, removing or
  adding a section is an edit to `REGISTRY` in `sections.py` plus a partial;
  numbering, the TOC, the screen and the PDF all follow from it. Never hardcode
  a section number in a partial (`s.number` carries it).
- **A snapshot shape change means republishing.** `ReportData` (and the
  `apps/nom035` dataclasses inside it) is stored as JSON in published reports.
  Adding, removing or renaming a field changes the shape; there is no data
  migration — unpublish and publish again. Keep `load` in step with the
  dataclasses (`tests/test_snapshot.py` checks the round trip). Wording, fixed
  text and the recommendations matrix render at view time and need no
  republish.
- **The report's CSS is plain CSS on purpose.** `static/css/report.css` (fonts and
  every `report-*` class, phone first), `report-wide.css` (the wide layout) and
  `report-print.css` (paged media, PDF only) are not Tailwind, and report partials
  use only `report-*` classes. WeasyPrint matches no width media query, so the
  wide layout is a separate file: the screen links it with
  `media="print, (min-width: 768px)"`, the PDF links it unconditionally. A
  breakpoint written inside a report stylesheet never applies in the PDF.
  `npm run build:css` does not touch these files.
- **WeasyPrint limits.** It ignores Tailwind `fill-*` classes (charts carry hex
  `fill` attributes — see `apps/core/CLAUDE.md`, Charts), collapses
  `minmax()` grid tracks (`.report-stats` is flex in the wide layout), and
  ignores `background-size`, flex `margin-top: auto` (the cover foot is
  absolutely positioned), the `translate` property and `position: sticky`. Check a layout change in the PDF, not only on screen.
- **Fonts.** Source Serif 4 and Source Sans 3 variable TTFs in `static/fonts/`
  (OFL). One `@font-face` per weight, each with a single `font-weight`:
  WeasyPrint rejects the range form and silently falls back to a system font. A
  new weight needs its own `@font-face`. `_write_pdf` passes one
  `FontConfiguration` to `write_pdf`.
- **The PDF fetches static files only.** The document lives under the fictitious
  `pdf.BASE_URL`; its stylesheets, fonts and images are relative links that
  `ReportURLFetcher` resolves through Django's static finders. Any other URL
  raises — no network, no request to the app. Reference new assets as relative
  `static/...` paths in `base_report.html` or the CSS.
- **WeasyPrint loads lazily.** `views._pdf_response` imports `pdf` inside the
  function; keep `weasyprint` out of module-level imports elsewhere. Pango is a
  system dependency (`.claude/CLAUDE.md`, *PDF rendering setup*).
- **Small groups always apply**, preview included: the rule lives in
  `apps/nom035/results.py`, never in a report template.

## Tests

`tests/` — `conftest.py` (`scored_assignment`: a closed Guía III assignment with
two áreas and one respondent without área), `test_models.py`,
`test_snapshot.py` (build and JSON round trip), `test_text.py` (sentences),
`test_content.py` (matrix covers every dominio, fixed text present), `test_sections.py` (registry, numbering,
section contexts), `test_results_sections.py` (results partials),
`test_publishing.py`, `test_admin_views.py`, `test_executive_views.py` and
`test_pdf.py` (a real WeasyPrint render, the fetcher, the filename, the
watermark). The suite asserts the rendered HTML and that a PDF is produced; the
PDF's layout is checked by eye.
