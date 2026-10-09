# Design system

## Status

Current — implemented in `static/css/main.css` and `apps/core` (`brand.py`, `context_processors.py`, `templatetags/brand.py`).

## What this does

SOFIA-S has one visual foundation that every page draws from. The product's name and logo are
defined once and rendered by one partial. Its typeface is Figtree. Its colors come from a small
set of named token scales: `primary`, `accent` and `neutral`. A palette is the set of values
those tokens take.

Two palettes exist while the client chooses between them. **Petróleo** (`petrol`) is a blue-teal
primary with a periwinkle accent on cool neutrals. **Pizarra** (`slate`) is an ink-slate primary
with a peach accent on warm stone neutrals. An administrator sees a small floating switch on every
page and can flip between them. The choice is kept in a cookie and repaints the whole application,
the results report and its PDF included: the PDF is painted in the palette of whoever downloads
it. Everyone else sees the default palette and no switch.

Every template expresses color through the token scales: `text-primary-600`, `bg-neutral-50`,
`bg-accent-100`. None names a Tailwind hue such as `indigo` or `gray`. Changing a palette's
values, or replacing both palettes with the client's final choice, is an edit to one CSS file.

## Why we're building it

The product's name, logo and palette are placeholders that the client is still choosing, and
may replace later. Each of those changes has to be one edit, and the candidate palettes have to
be compared live on the real screens rather than in a mock-up.

## Scope

**In scope:**

- **Brand configuration.** `settings.BRAND` holds `name`, `short_name`, `meaning` (what the
  name stands for, shown on the about page) and `logo`. A context processor exposes it to every
  template as `brand`. Page titles, the footer, the about page, login copy and the Django admin's
  titles read it; no template types the product name.
- **The logo partial.** `templates/_logo.html` is the only place the logo is drawn. It inlines the
  SVG with `fill="currentColor"`, so it takes the color of its context (`text-primary-700` in the
  header). The favicon points at the same file, so it draws in the browser's default black.
- **Typography.** Figtree is self-hosted from `static/fonts/figtree/` as two variable TrueType
  files, upright and italic, with weights 300–900. The app declares one `@font-face` per file with
  the weight range and `font-display: swap`, preloads the upright file in `base.html`, and sets
  Figtree as Tailwind's `--font-sans`. The results report uses Figtree for headings, tables and
  figures and keeps Source Serif 4 for prose. Its `@font-face` rules declare one face per weight,
  because WeasyPrint rejects the range form.
- **Type scale.** Base 16px. Steps 14 / 16 / 20 / 25 / 31 / 39. Weights: 400 body, 500 labels and
  buttons, 600–700 headings. Line height 1.5 for body, 1.2–1.3 for headings.
- **Color tokens.** `static/css/main.css` declares `primary-50…900`, `accent-100…700`,
  `neutral-50…900` and the chart tokens `series-1` and `series-2` in an `@theme inline` block. Each maps to a `--brand-*` CSS variable.
  Each palette assigns those variables under `[data-palette="<slug>"]`, and `:root` carries the
  default palette's values so a page without the attribute still renders. `static/css/report.css`
  reads the same `--brand-*` variables.
- **The palettes.** The full scales live in `main.css`; the anchor values are:

  | Role | Petróleo (`petrol`) | Pizarra (`slate`) |
  |---|---|---|
  | Primary, actions and links (600) | `#1F5D71` | `#47546C` |
  | Primary, hover (700) | `#1A4C5D` | `#3A455A` |
  | Primary, tint (50) | `#EEF5F7` | `#F3F5F8` |
  | Accent, swatch (300) | `#B3C0FB` periwinkle | `#E5D09A` peach |
  | Chart, first series | `#1F5D71` (primary-600) | `#47546C` (primary-600) |
  | Chart, second series | `#6B79D9` (accent-500) | `#7787A2` (primary-400) |
  | Neutral, page (100) | `#EDF1F2` | `#F3F0EB` |
  | Neutral, headings (900) | `#1A1F21` | `#1D1A17` |

- **The palette switch.** `settings.BRAND_PALETTES` lists the palette slugs with their Spanish
  labels, and `settings.BRAND_PALETTE_DEFAULT` names the default (`petrol`). A context processor
  reads the `paleta` cookie, falls back to the default when the cookie is missing or names an
  unknown palette, and exposes the result as `palette`. `base.html` and the PDF template render it
  as `<html data-palette="…">`. `templates/_palette_switch.html` renders a floating control,
  labelled *Paleta*, for members of the Admins group and superusers, and for every visitor when
  `DEBUG` is on. It posts to `/paleta/`, which sets the cookie for a known palette and redirects
  back to the page, or to the home page when the return address is not on this site. A spacer
  after the footer keeps the footer's links clear of the pill.
- **Usage rules** (enforced where noted under **Enforcement**):
  - Color in templates comes from the token scales or the fixed colors below, never from a
    Tailwind hue name or an arbitrary hex value.
  - Page background `neutral-100`; cards white with a `neutral-200` border; headings and primary
    text `neutral-900`; body copy `neutral-700`; secondary text `neutral-600`. `neutral-500` is the
    lightest step used for text, for captions, hints and placeholders.
  - Primary buttons and links use `primary-600`, with `primary-700` on hover; text on a primary fill
    is white. Focus rings are 2px `primary-500` with a 2px offset, shown on keyboard focus.
  - The accent marks highlights, avatars and chips. It never appears as text on white.
  - Chart series that are not a risk level take `series-1` and `series-2`: the sex profile uses
    both, the age profile `series-1`. A chart's empty baseline is `neutral-300`. The chart tags
    read each series' hex for the active palette from `main.css`, because the PDF paints a chart
    mark from its `fill` attribute rather than from a stylesheet.
  - Legend swatches, and the markers that open risk-level badges and status pills, are
    2px-radius squircles (`rounded-xs`), never dots. A tinted risk badge's marker takes its
    level's bar color, so the badge and the chart legend show the same mark; a solid dominio
    badge's marker, and every status pill's (*Publicado*, *Borrador*, *Completada*, *Sin
    activar*…), takes the pill's ink. Pills that hold a value rather than a state (answers,
    filters, the *Tú* tag) carry no marker.
  - Status takes the `success`, `warning` and `danger` scales: confirmations and finished
    states (*Completada*, *Publicado*, *Activado*) `success`; notices and states that need an
    action (*Borrador*, *Sin activar*, the pending-questions panel) `warning`; errors and field
    validation `danger`. Pills use the 50 or 100 fill with 800 ink, messages a 50 fill, 200
    border and 800 ink, field errors 600 text, icons 500. Status colors are always paired with an
    icon or text.
  - An amount is not a status. Meters and progress (the registration rate, a respondent's
    progress bar and ring) are `primary`, whatever their value; *Activa* is `primary` too.
  - An answer is not a status. A respondent's *Sí*, *No* and choices share one `primary` pill,
    with no color that suggests a right or wrong answer.
  - A frequency answer (*Siempre* … *Nunca*) is its label followed by one `rounded-xs` squircle
    per option, the answer's filled in `primary-600` and the rest `neutral-300`
    (`templates/core/_frequency_answer.html`). On a NOM-035 survey the squares run from the lowest
    score to the highest (0 to 4) and the answer fills its score's square: NOM-035 reverses the
    scoring on some items, so the same *Siempre* sits at the low-risk end of one question and the
    high-risk end of another, and the module header reads *Menor → mayor riesgo*. A frequency
    question with no scoring engine behind it keeps its options' own order, and its module header
    names that order. One color either way: the strip shows where an answer falls, never a verdict
    on the person. The stored value is a position in the list, not a score, and is never printed.
    Screen readers hear the label and the score ("Siempre, puntaje 4 de 4") or the position. On a
    phone the answer drops under its question.
- **Status scales.** `main.css` declares `success`, `warning` and `danger` at steps 50, 100, 200,
  500, 600 and 800 in a plain `@theme` block. They are the same in every palette and muted to sit
  beside either one; their contrast is tested like the palettes'.
- **Fixed colors, outside every palette.** The NOM-035 risk ramp
  (`apps/core/templatetags/valuation_extras.py`): gray, green, amber, orange and red for *Nulo*
  through *Muy alto*. Guía I's chart marks, which take the ramp's dominio *Medio* (`#CA9429`) for
  a traumatic event and *Muy alto* (`#7A1010`) for a referral, so every risk color comes from one
  ramp. The chart labels' hex `fill` attributes, which only the PDF reads.
- **Language.** `base.html` declares `<html lang="es">`.

**Out of scope:**

- **Component partials and a styleguide page.** Buttons, fields, alerts, tables and dialogs as
  reusable partials come in a later extension of this doc. This doc fixes their colors and type,
  not their markup.
- **Page-by-page layout and copy changes.** Pages keep their current structure; only their tokens
  change.
- **Dark mode.** The token layer makes it a later addition of one more variable block.
- **The Django admin.** It keeps Django's own styling.
- **Final name, logo and palette.** They stay placeholders until the client confirms them.
- **An icon set.** None is adopted yet; the few inline icons stay as they are.

## Phone shape

Nothing in this doc sets a layout. The palette switch is a small pill fixed to the bottom-left
corner, clear of the back-to-top control at bottom-right. The survey form does not render it,
because the form's phone bar spans the whole bottom edge.

## Key decisions

- Decision: Templates name brand scales (`primary`, `accent`, `neutral`), not role tokens
  (`surface`, `ink`, `muted`).
  Reason: A scale step maps one-to-one onto a class and reads the same in every template. Role
  names need a judgment call per use and belong with the component work.
- Decision: Templates never use Tailwind's own hue scales (`gray`, `indigo` and the rest) for
  brand color, and the theme does not redefine them.
  Reason: A class named after one hue that renders another misleads every reader.
- Decision: Brand colors avoid the green, amber, orange and red hue bands.
  Reason: Those hues already mean a risk level. A green brand color reads as *Bajo*, and an
  orange one reads as *Alto*.
- Decision: Pizarra's second chart series is its lighter slate (`primary-400`), not a new hue.
  Reason: Peach cannot carry a series, and a chart-only color would add a hue to the palette for
  one chart; the legend labels carry the difference in lightness.
- Decision: Pizarra's peach accent appears only as a surface (`accent-100` to `accent-300`
  backgrounds), never as a chart series or a small mark.
  Reason: Peach shares the amber *Medio* hue band, and its darker steps fail 3:1 against chart
  tracks.
- Decision: Both palettes ship together behind one attribute, on one branch.
  Reason: The client compares them on the real application. Retiring one is a small deletion
  rather than a branch to keep in sync.
- Decision: Figtree ships as TrueType variable files, not WOFF2.
  Reason: The two files are 62 KB each, WeasyPrint reads them directly, and one format serves both
  the browser and the PDF.
- Decision: The palette switch is a cookie read by a context processor, not a per-company or
  per-user setting.
  Reason: The switch exists only for the decision period and must not need a migration.

## Enforcement

- A test fails when a class on one of Tailwind's own hue scales (`gray`, `indigo`, `green`,
  `yellow`, `red`, `amber`, `orange`, `emerald`, `lime`, `rose`) appears in `templates/`,
  `apps/**/forms.py`, `apps/**/templatetags/*.py` or `static/ts/`, or when a template types the
  product name. The risk-ramp module is exempt.
- Contrast tests check the status scales (600 on white and on its 50 fill, 800 on its 50 and 100
  fills, 500 icons on the 50 fill) alongside the palettes.
- A contrast test reads both palette blocks from `static/css/main.css` and fails when any declared
  text/background pair falls below WCAG AA: 4.5:1 for text, 3:1 for UI boundaries and chart marks.
- Tests cover the context processor and the switch: cookie validation and the fallback, the
  switch rendered for admins only and never on the survey form, the return-address check, and
  `lang="es"`.
- No test can see color on screen. Every change to `templates/` or `static/` is checked in a
  browser at 360px and on desktop, in both palettes.

## Open questions

None.

## Linked ADRs

None.
