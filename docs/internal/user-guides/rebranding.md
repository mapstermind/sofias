# Rebranding: name, logo, palette and typeface

> Draft. It is refined once the client confirms the name and logo.

The product's identity is defined in a handful of places, and no template types
any of it. Replacing one piece is an edit to that place, a rebuild, and a check
in the browser. The design rules each piece has to respect are in
[`docs/platform/design-system.md`](../../platform/design-system.md).

## The name

1. Edit `BRAND` in `config/settings.py`:
   - `name` — the full product name (page titles, header, footer, the sign-in
     email's subject, the Django admin's header).
   - `short_name` — the short form (*¿Qué es …?* on the about page).
   - `meaning` — what the name stands for, shown under the logo on the sign-in
     page and on the about page. Leave it empty if the new name is not an acronym.
2. Run `pytest`. `apps/core/tests/test_design_tokens.py` fails a template that
   types the name instead of reading `brand`, so a green suite means nothing
   else needs changing.
3. Search the docs for the old name if they should follow
   (`grep -rn "SOFIA-S" docs`); the code needs nothing more.

## The logo

1. Replace the file `BRAND["logo"]` names (`static/img/logo.svg`), or point
   `logo` at a new file under `static/`.
2. The file must be a bare `<svg>` whose shapes use `fill="currentColor"`: it is
   inlined by `{% brand_logo %}` (`apps/core/templatetags/brand.py`) and takes the
   color of where it sits (`text-primary-700` in the header). A logo with fixed
   colors keeps them everywhere, including on dark surfaces.
3. The same file is the favicon (`templates/base.html`), so check it at 16px.
4. Check the header (28px tall), the sign-in card and the error pages (32px).

## The palette

The palette is the `:root` block of `--brand-*` variables in
`static/css/main.css`: `primary` (50–900), `accent` (100–700), `neutral`
(50–900) and `series` (1–2). Templates, the report's `static/css/report.css` and
the PDF's chart fills (`apps/core/brand.py`, `palette_hex`) all read those
variables, so the palette is defined once.

1. Write the new hex values into the block, full scales.
2. Keep the brand away from the green, amber, orange and red hue bands: they
   mean a risk level (*Bajo*, *Medio*, *Alto*, *Muy alto*). The risk ramp and the
   status colors are outside the palette and do not change.
3. Run `pytest apps/core/tests/test_design_tokens.py`: it checks every declared
   text/background pair against WCAG AA.
4. Update the palette table in `docs/platform/design-system.md`; a new direction
   gets an ADR superseding `docs/adr/adr-0006-brand-palette.md`.
5. `npm run build:css`, then check `/estilos/`, the dashboard, the results page
   and a report's PDF in the browser.

## The typeface

Figtree lives in `static/fonts/figtree/`: WOFF2 for the browser, TTF for the
PDF. A new face needs:

1. Its files in `static/fonts/` (WOFF2 and TTF), with its licence.
2. The `@font-face` rules in `static/css/main.css` (one per file, weight range)
   and `static/css/report.css` (one per weight: WeasyPrint rejects the range
   form), and `--font-sans` in `main.css`.
3. The preload in `templates/base.html`, and the `font-family` the chart
   components name in their SVG `<text>`.
4. `npm run build:css`, and a check of the PDF.
