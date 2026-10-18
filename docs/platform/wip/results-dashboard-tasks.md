# Results dashboard redesign — tasks

## What changes

**Change.** The Resultados page (`/tablero-empresa/resultados/`) takes the layout
proposed at `/propuestas/resultados/`, built on real data, plus the Oct 14 nits
that land on the dashboard. The report, its PDF and its charts are not touched.

**Why.** The current page is eight stacked sections in two long lists; the
question it exists to answer — *which categoría and dominio carry the risk* — is
buried. The proposal puts the final score and the categorías above the fold,
adds a **Ver** selector so one categoría can be read in full, and shows
participation, Guía I and respondent profile as one row of small cards. The
Oct 14 meeting (`docs/internal/meetings/20261014.md`) adds: axes on charts, a
percentage beside each risk level, "…de los colaboradores presenta un nivel…"
copy, and no % respondidos por área.

**Decisions taken** (the proposal's, as confirmed in the session):

1. Each categoría and dominio row carries an *En alto o muy alto* percentage —
   a sum of the distribution, never a verdict. This is also the Oct 14
   grouping ([nulo, bajo] / [medio] / [alto, muy alto]) as far as the dashboard
   is concerned; nothing else on the page groups levels.
2. The main chart's scale ends at the next decena above the largest share, with
   gridlines and axis labels, and says so beneath.
3. The dashboard gets its own chart components; the four shared ones stay as
   they are because the report draws them.
4. Two risk ramps stay: base for the final score and categorías, deeper for
   dominios.
5. The page is one column on a phone, in the order: filter bar, main chart,
   categorías, participation, Guía I, quienes respondieron, por área.
6. A **Ver** selector (calificación final or one categoría) sits beside the
   survey selector. It changes what is measured, not who is counted, so
   participation, Guía I and quienes respondieron do not change with it. With a
   categoría chosen the main box shows its distribution and statistics, the
   right column its dominios, and *Por área* shows that categoría.
7. The proposal's larger type and borderless rounded cards are scoped to this
   page. Promoting them to the design system is a separate change.
8. In *Por área*, the round button adds the área to the filters and the name
   stays a link.
9. The Distribución / Estadísticas toggle and the statistics stay on the
   dashboard (the report's statistics are out of scope for this change).

**Out of scope.** Everything in `apps/reports` and the report's charts; the
Oct 14 items that are not about the results page (Puesto, surveys, report font,
palettes, buttons, registration).

**Sections of `nom-035-results-dashboard.md` this makes wrong:** *Scope*,
*Page layout* (the whole section table and sections 1–8), *On a phone*,
*In-place filtering* (adds the Ver and Distribución/Estadísticas controls and
the selected-level state), *Chart components* (adds the dashboard charts) and
*Results data* (adds per-área categoría distributions). The small-group rule
and the query parameters (plus the new `ver`) stay.

**ADRs.** None is touched; no decision in `docs/adr/` is superseded.

## Plan

Each task is TDD: failing test, then code, then green. Nothing is committed
until the user has reviewed the diff.

- [x] **1. Data: per-área distribution for any categoría.** Extend
  `apps/nom035/results.py` so a participation row carries, besides the final
  distribution, one distribution per categoría (from `GroupScore`), under the
  existing visibility rule (`visible`, `_hide_until_safe`). Add an *En alto o
  muy alto* count to `DistributionRow`. Tests in
  `apps/nom035/tests/` for counts, suppression and the query count staying flat.
- [x] **2. Query: `ver` parameter.** `ResultsQuery.ver` (`final` or a
  categoría key valid for the assignment's variant, else ignored); `params()`,
  `results_url`, `filter_pills` untouched by it except that it is carried
  through. Tests in `test_results_query.py`.
- [x] **3. Chart geometry for the main chart.** Pure functions in
  `apps/core/charts.py`: a variable ceiling (next decena above the largest
  share), gridlines, per-level heights. Tests in `test_charts.py`.
- [x] **4. View context.** `_results_context` builds the page's blocks (hero,
  categorías or dominios, cards, áreas) and the `ver` options. Query-count test
  in `test_results_views.py` stays the same.
- [x] **5. Templates.** `company_results.html` and `results/_body.html`
  restructured to the proposal (toolbar with Ver, hero, aside, cards, áreas),
  reusing the proposal's partials as the starting point, moved under
  `templates/core/results/`. Copy: "de los colaboradores presenta un nivel…",
  percent beside each level, no % respondidos por área, axes shown.
- [x] **6. TypeScript.** `results_dashboard.ts`: Ver change refetches the
  fragment; Distribución/Estadísticas and level selection switch in place
  without a request; the round área button adds the área to the filters.
  `npm run build:js`.
- [x] **7. Frontend design pass.** With `frontend-design`, refine the new page
  within the project's design system (tokens, components, no Tailwind hues);
  `npm run build:css`; check at 360px.
- [x] **8. Remove the proposal.** Delete `results_proposal.py`, its templates,
  view, URL and tests, and its mentions in `apps/core/CLAUDE.md`.
- [x] **9. Documentation (last).** Rewrite `docs/platform/nom-035-results-dashboard.md`
  to describe the new page in present tense, with no migration commentary;
  update `apps/core/CLAUDE.md` and `docs/platform/design-system.md` /
  `responsive-layout.md` where they name the results page.

**Browser checklist for the reviewer** (no JS test runner exists): change Ver
and watch the main box, dominios and Por área; toggle Distribución / Estadísticas;
click each level; apply and clear a filter; press an área's round button; load
at 360px and confirm one column, no horizontal scroll, 44px tap targets; repeat
as an Ejecutivo principal on a small group.
