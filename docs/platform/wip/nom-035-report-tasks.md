# NOM-035 report — no statistics

## What changes

**The report prints no statistics.** The mean, median, minimum and maximum of a
group's scores are not shared with the client; they stay on the results
dashboard. Every statistics row leaves the report and its PDF: the
*Calificación* block (n, Prom., Mediana, Mín., Máx., Máx. posible and the range
strip) under 5.3 *Calificación final*, each categoría in 5.4 and each dominio
in 5.5. The distribution by level, the generated findings and each section's
*n* line stay.

**5.6 *Resultados por dimensión* is removed.** It was statistics rows only (the
norm publishes no dimensión thresholds, so it has no levels to show).
*Resultados por área* becomes 5.6 and *Guía I* 5.7. The annex's
categoría → dominio → dimensión → ítem table stays: it explains the method.

**Data.** `ReportData` drops `final_stats`, `categoria_stats` and
`dimensions`; `apps/nom035`'s report-only dimensión aggregates
(`_dimensions`, `DimensionGroup`, `NEUTRAL_BAND_LABEL`,
`ReportResults.dimensions`) go with them. The dashboard's statistics
(`Results.final_stats`, `categoria_stats`) are untouched. `load` reads named
keys, so a snapshot published before the change still loads; its extra keys
are ignored.

**Recommendations sit with their dominio.** Section 7 *Recomendaciones según
riesgo identificado* stops listing the matrix text at the end of the report.
In 5.5, each dominio block opens with its recommendations (caption
*Recomendaciones*), one per level among Medio, Alto and Muy alto that at least
one worker reached, shown with the dominio-tier badge and the text but no
share (the chart directly below prints it). Then comes *Distribución por
nivel* and the chart. A dominio with no worker at those levels shows only its
chart. 5.4 is unchanged: the matrix has no categoría-level text. The
one-group-per-page rule in 5.4 and 5.5 stays.

**Section 7 becomes *Recomendaciones adicionales*:** only the Administrador's
text, and the section is left out (with the later sections renumbered) when
that text is empty. The registry gains a per-section `shown` predicate for
this. `text.recommendations` takes one dominio row and returns its
(level, label, text); the share and grouping fields go.

Sections of `docs/platform/nom-035-report.md` made wrong: *Scope* (dimensión
results among the `apps/nom035` aggregates), the section list (5.3–5.8 and the
paragraph on captions and statistics rows), "Every statistics row prints…",
"Statistics, distributions…", the per-área section numbers, *Snapshot*, the
dominio-tier note ("statistics bands"), the charts table (5.3–5.6), the phone
layout's statistics rows, the page-break list, the section list's item 7 and
*Generated sentences* where it covers recommendations. No ADR records it.

## Tasks

- [x] Tests first: no statistics in any results section, no
      `resultados.dimension` in the registry or the document, page-break and
      palette tests bounded by `resultados.area`, the snapshot carries no
      statistics, `report_results` has no dimensiones. See them fail.
- [x] Templates: drop `_stats.html` and `_dimension.html`; remove the
      *Calificación* block from `_final.html`, `_categoria.html`,
      `_dominio.html`.
- [x] `sections.py`: drop the dimensión section and the stats pairing.
- [x] `snapshot.py`: drop the three fields, `_clamped`, `_stats`.
- [x] `apps/nom035/results.py`: drop the report-only dimensión aggregates.
- [x] CSS: drop `report-stats*` (report.css, report-wide.css,
      report-print.css) and the PDF's range-strip tick rule.
- [x] Recommendations: tests for a dominio block's recommendations above
      its chart (badge, text, no share), none for a dominio below Medio,
      section 7 *Recomendaciones adicionales* present only with text and the
      numbering closing up without it. Then `Section.shown`, `_dominio`,
      `text.recommendations`, `_dominio.html`, `_recomendaciones.html`.
- [x] Suite green; render one PDF and look at 5.3–5.7 and 7.
- [x] Documentation: rewrite the sections above in present tense;
      `apps/reports/CLAUDE.md` and `apps/nom035/CLAUDE.md` where they mention
      statistics or dimensiones in the report.
