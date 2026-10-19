# NOM-035 report — refinements

## What changes

**One family.** The client wants a sans serif in place of the serif. The report
is set entirely in Figtree, the application's typeface; Source Serif 4 is no
longer bundled. A second sans for prose was rejected: next to Figtree it would
read as an inconsistency rather than a choice. Without the change of face, the
roles are told apart by weight, size and measure:

| Role | Class | Set in |
|---|---|---|
| Prose | `.report-prose` | Figtree 400, 1rem, line-height 1.6, 66ch |
| Finding | `.report-finding` | Figtree 500, 1.25rem, line-height 1.4 — below the 600/700 headings so it reads as a statement |
| Razón social on the cover | `.report-cover-company` | Figtree 700, 2.5rem, line-height 1.1, letter-spacing −0.015em |

Sections of live docs made wrong:

- `docs/platform/nom-035-report.md` — *Visual design* ("set larger in the
  serif"), the **Type** bullet, the `static/fonts/` row of the files table, and
  the fonts clause of the plain-CSS decision under *Decisions*.
- `docs/platform/design-system.md` — **Typography** ("keeps Source Serif 4 for
  prose").
- `apps/reports/CLAUDE.md` — **Fonts**.

No ADR records the font choice.

**Range-strip labels.** Three close values (Prom. 83.3, Mediana 90, Máx. 90)
overprinted: two lanes held only two of them. A crowded label now shifts
aside within its lane, with a leader line to its dot, and a cluster at the end
is pushed back inside the strip. Shared chart geometry (`apps/core/charts.py`),
so the results dashboard benefits too; no doc describes the lane rule.

## Tasks

- [x] Tests: `test_pdf.py` — the URL-fetcher test fetches the Figtree TTF; the
      font test asserts the report CSS names Figtree and no serif family
      (rename it). Run, see it fail.
- [x] `static/css/report.css`: drop the three Source Serif 4 `@font-face`
      rules, restyle `.report-prose`, `.report-finding`,
      `.report-cover-company` per the table, update the header comment.
- [x] Delete `static/fonts/SourceSerif4-Variable.ttf` and `static/fonts/OFL.txt`
      (it licenses only Source fonts).
- [x] `npm run build:css`; full suite green.
- [x] Generate one PDF and look at the cover and a finding (done: only
      Figtree is embedded).
- [ ] Browser check at 360px and wide (user).
- [x] Documentation: rewrite the sections listed above in present tense.
- [x] Range strip: label placement with sideways shift (tests in
      `apps/core/tests/test_charts.py`).
