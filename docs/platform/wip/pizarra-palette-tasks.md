# Pizarra palette — tasks

## What changes

The client chose **Pizarra** (2026-10-18), with primary buttons on slate-500
(`#5D6C87`, hover slate-600). Petróleo, the palette switch, the `/propuestas/`
comparison pages, the navy palette and `docs/branding/` go. With one palette
there is nothing to select, so every piece of palette-selection logic goes too:
the `paleta` cookie, `data-palette` on `<html>`, `BRAND_PALETTES` /
`BRAND_PALETTE_DEFAULT`, the per-slug lookups in the chart tags and the PDF.

Live docs this makes wrong: `docs/platform/design-system.md` (palettes, switch,
styleguide gate, decisions), `apps/core/CLAUDE.md` (Brand and palette,
Components, charts), `docs/internal/user-guides/rebranding.md` (the palette),
`docs/platform/nom-035-report.md` and `nom-035-results-dashboard.md` (PDF/series
"active palette"), `docs/README.md` (ADR status, branding folder),
`.claude/CLAUDE.md` (design-system bullet). ADR-0006 is accepted with the
approved wording.

## Tasks

- [x] Tests first: rewrite `test_brand.py`, `test_design_tokens.py`,
      `test_chart_components.py`, `test_pdf.py`, `test_styleguide.py`,
      `surveys/tests/test_views.py` for one palette on `:root`, no cookie, no
      switch, button on primary-500; delete `test_palette_proposal.py`.
- [x] `static/css/main.css`: Pizarra's values on `:root`, Petróleo block gone,
      `.btn-primary` on 500 / hover 600; delete `static/css/proposal-navy.css`.
- [x] `apps/core/brand.py` reduced to `palette_hex()` (reads `:root`);
      styleguide gate moves to `styleguide.can_view_styleguide`.
- [x] Context processor, settings, views, urls, chart tags, reports PDF/view.
- [x] Templates: `base.html`, `base_error.html`, `survey_detail.html`,
      `reports/base_report.html`, `core/styleguide.html`; delete
      `_palette_switch.html`, `core/palette_proposal.html`, `core/proposal/`.
- [x] Delete `apps/core/palette_proposal.py`, `docs/branding/`.
- [x] `npm run build:css`; `pytest`; `ruff check .`; leftover grep.
- [x] Docs: ADR-0006 accepted; rewrite the live docs listed above in present
      tense with Pizarra as the only palette.
