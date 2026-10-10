# Design system

## Status

Current — implemented in `static/css/main.css`, `apps/core` (`brand.py`, `context_processors.py`,
`forms.py`, `styleguide.py`, `templatetags/brand.py`, `templatetags/icons.py`) and the partials in
`templates/components/`, `templates/forms/` and `templates/icons/`.

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

Each recurring pattern has one definition. A button, a form control, a card and a pill are
component classes (`btn btn-primary`, `control`, `card`, `pill`). Every Django form draws its
fields through one field template, alerts and Django's messages through one partial, and icons
through one tag. A styleguide page at `/estilos/` shows every component in every state, in
whichever palette is active.

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
- **Type scale.** Tailwind's size classes carry the scale's values, declared as `--text-*`
  tokens in `main.css`. The sizes are in `rem`, so a reader who raises their browser's or phone's
  text size scales every step. Each class names a role:

  | Class | Size | Line height | Role |
  |---|---|---|---|
  | `text-xs` | 13px | 1.4 | A label on a graphic or a badge: a pill, a legend entry, a chart caption, a stat's caption, a count |
  | `text-sm` | 14px | 1.5 | Secondary text: table cells, metadata, dates, help, errors, field labels |
  | `text-base` | 16px | 1.5 | Body copy, form controls, the survey's questions and answers |
  | `text-lg` | 20px | 1.4 | Section headings, modal titles |
  | `text-xl` | 25px | 1.25 | Page titles (`h1`) |
  | `text-2xl` | 31px | 1.2 | Stat numbers, the 6-digit login code |
  | `text-3xl` | 39px | 1.15 | Not used by a page |

  `text-xs` is never a sentence. Weights: 400 body, 500 labels and buttons, 600–700 headings.
  The styleguide lists the seven steps with their roles.
- **The survey's type.** Questions, answers, instructions and the modals' text are 16px. Errors,
  the progress and *Pendientes* panels, and the side panel's headings are 14px. A question is 16px at weight 600 in `neutral-900`, and its answers are
  16px in `neutral-800`: on a page holding many questions, a question stands out by weight, not
  size, so a module stays short to scroll. Answer rows keep their 44px minimum. The likert labels
  under the radios on desktop are 14px. The survey's text, number and date inputs are `control`.
  The 9-digit setup code on *Primer ingreso* is 25px, so its eleven characters fit the login card
  at 360px.
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
  - Legend swatches, and the markers that open risk-level badges and status pills
    (`pill-marker`), are 2px-radius squircles (`rounded-xs`), never dots. A tinted risk badge's marker takes its
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

- **Components.** The patterns that repeat across pages, each defined once:
  - **Component classes** in an `@layer components` block of `main.css`, built with `@apply` from
    the tokens. Utilities sit in a later layer, so a call site adds layout (`w-full sm:w-auto`,
    `mt-4`) on top of them.
    - **Buttons:** `btn` plus one variant. `btn-primary` (`primary-600` fill, white text, hover
      `primary-700`) is the one main action of a view. `btn-secondary` (white, `neutral-300`
      border, `neutral-800` text, hover `neutral-50`) is every other action: *Cancelar*,
      *Descargar PDF*, *Filtros*. `btn-text` (no box, `primary-700` text, hover `primary-50`) is an
      action inside a row or a dialog: *Limpiar filtros*, a close button. `btn-danger`
      (`danger-600` fill, white text, hover `danger-800`) undoes or removes: *Despublicar*. Buttons
      have an 8px radius, weight 500 and 14px text, and are 44px tall; `btn-sm` is 36px, for dense
      desktop rows. A leading icon is 20px. A disabled button is at half opacity and ignores hover.
      A busy button (`aria-busy="true"`) shows a spinner and ignores clicks;
      `static/ts/busy_submit.ts` sets it on the submit button of a form carrying `data-loading`
      (the login code request, publish and unpublish, the report form) and clears it when the
      back button restores the page from the browser's cache. A submit another handler cancelled, such as the unpublish confirmation, is left
      alone. Under `prefers-reduced-motion` the spinner does not spin.
    - **The form control:** white, a `neutral-300` border, an 8px radius, 44px tall, 16px text.
      Focus draws a `primary-500` border and ring, keeping a transparent outline that
      high-contrast modes paint; `aria-invalid="true"` draws them in
      `danger-600`; disabled is `neutral-50` with `neutral-500` text. Fields drawn by the form
      renderer get these styles from their `field` wrapper; `control` is for an input outside a
      Django form, such as the roster search, the results filter and the survey's typed answers.
    - **The card:** `card` is white, with a `neutral-200` border, `shadow-sm` and a 12px radius.
      Padding is set where it is used. An empty state is a card with `shadow-none border-dashed
      border-neutral-300`.
    - **The pill:** `pill` is the shape (full radius, 12px text, weight 500). `pill-marker` adds the
      squircle marker in the pill's ink, or in the color a `before:bg-*` utility names. The tone is
      a utility.
  - **Keyboard focus.** A base rule draws a 2px `primary-500` outline with a 2px offset on
    `:focus-visible` for every link, button, summary, checkbox and radio, so no template draws its
    own and a mouse click draws nothing.
  - **Form fields.** `settings.FORM_RENDERER` is `apps.core.forms.SofiaFormRenderer`, which draws
    every Django form through `templates/forms/form.html` (the form's errors, a hidden field's included, as a danger alert,
    hidden fields, then the fields in a `space-y-6` stack) and every field through
    `templates/forms/field.html`, in this order:
    1. the label (14px, weight 500, `neutral-800`), with a quiet *(opcional)* after it when the
       field is not required;
    2. the help text (14px, `neutral-600`), above the control;
    3. the control;
    4. every error, each with an `exclamation-circle` icon, in `danger-600`.

    Django points the control's `aria-describedby` at the help and error ids, and sets
    `aria-invalid`. A multi-widget (the date of birth) is a `fieldset` with a `legend`, its parts
    stacked on a phone and side by side from `sm`. A checkbox sits before its label in a 44px row.
    A field that is `required=False` for a widget's sake but validated as required sets
    `shown_as_required = True` to drop *(opcional)*. Widget `attrs` carry no styling classes, only
    real extras such as the large centered digits of a login code. A page that lays fields out
    itself (the report form's grid and signatory rows) places each with
    `{{ field.as_field_group }}`. The Django admin keeps its own markup.
  - **Alerts.** `templates/components/_alert.html` takes `tone` (`success`, `info`, `warning`,
    `danger`), an optional `title`, and `body` or `items`. It draws a 50 fill, a 200 border and a
    12px radius, the tone's icon in its 500 and the text in its 800. `info` takes `primary`.
    `danger` is `role="alert"`, the rest `role="status"`. An inline alert is never dismissible.
  - **Messages.** `templates/_messages.html` draws Django's messages as dismissible alerts at the
    top of every page; `base_app.html` and `base_centered.html` include it. `error` maps to
    `danger` and `debug` to `info`. The close button (*Cerrar aviso*) is wired by
    `static/ts/dismiss.ts`, loaded on every page, which moves focus to the next message or to
    `#main`, which both layouts have. Without
    JavaScript a message stays. Nothing hides on a timer.
  - **Icons.** `{% icon "name" "classes" %}` (`{% load icons %}`) inlines
    `templates/icons/<name>.svg`: Heroicons v2 outline, 24px, MIT (the `LICENSE` sits beside
    them), copied in rather than installed, and only the icons in use. An icon is `aria-hidden`
    unless it gets `label="…"`, which makes it an image with that name. An unknown name raises
    under `DEBUG` and renders nothing otherwise. An icon-only button carries its own
    `aria-label`.
  - **The styleguide.** `/estilos/` (`StyleguideView`) shows, in the active palette: the color
    scales with their hex values, the type sizes in use, every button variant and size (default,
    disabled, busy), a demo form (`apps/core/styleguide.py`) empty and with errors, every alert
    tone, the status pills and risk badges, cards, and every icon by name. It is shown to whoever
    may switch palettes (`brand.can_switch_palette`); everyone else gets a 404.
  - **The three-places rule.** A pattern that appears in three or more places with no component
    gets one proposed before its markup is copied again.

**Out of scope:**

- **Navigation, tables, the dialog, empty and error pages, pagination.** The top bar's responsive
  collapse and user menu, tables on a phone, a shared `<dialog>` component, the empty-state and
  loading patterns, the 404 and 500 pages, and pagination are not components yet; each page keeps
  its own markup for them.
- **Page-by-page layout and copy changes.** Pages keep their current structure; only their tokens
  change.
- **Dark mode.** The token layer makes it a later addition of one more variable block.
- **The Django admin.** It keeps Django's own styling.
- **Final name, logo and palette.** They stay placeholders until the client confirms them.

## Phone shape

Nothing in this doc sets a page layout. The palette switch is a small pill fixed to the
bottom-left corner, clear of the back-to-top control at bottom-right. The survey form does not
render it, because the form's phone bar spans the whole bottom edge. Buttons and controls are
44px tall, the tap target on a phone; a button that should span the phone's width says so at the
call site (`w-full sm:w-auto`). The styleguide is one column, with its button and pill rows
wrapping.

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
- Decision: Single-element patterns are CSS component classes; patterns with structure are
  partials or Django's form renderer.
  Reason: A button is sometimes a link and sometimes a submit carrying `name`, `value`, `form` or
  `data-*` attributes, which an `{% include %}` cannot pass through.
- Decision: Help text sits between the label and the control.
  Reason: It is read before typing, and a phone keyboard cannot cover it.
- Decision: Optional fields are marked *(opcional)*; required ones carry no mark.
  Reason: Nearly every field is required, so a mark on each would be noise.
- Decision: Cards have a 12px radius, one step above the 8px controls inside them.
  Reason: The radius ladder (8 controls, 12 cards, full pills) reads as one family.
- Decision: Field text is 16px.
  Reason: iOS Safari zooms in on focus below 16px.
- Decision: Messages never hide on a timer, and inline alerts cannot be dismissed.
  Reason: A timed message fails slow readers, and a dismissed error is still an error.
- Decision: Tailwind's size classes keep their names and take the scale's values; each use names
  its role.
  Reason: Shifting every class up a step would make a page title 31px, three lines or more on a
  360px phone. Moving each use to its role keeps titles and figures their size and spends the
  larger steps where reading needs them.
- Decision: The survey's questions and answers are 16px, the question set apart by weight.
  Reason: 16px is the floor for reading text on a phone, and the survey's modules hold dozens of
  questions; larger questions would add screens of scrolling. A reader who needs larger text gets
  it from their own text-size setting, which the `rem` sizes honor.
- Decision: 13px is for a label on a graphic or a badge, never a sentence.
  Reason: Small text that is read rather than glanced at is where readability fails first.
- Decision: Heroicons are copied in as SVG files, not installed.
  Reason: The app uses about ten icons; a file per icon needs no npm dependency, and the tag
  inlines it so it takes the text color.

## Enforcement

- A test fails when a class on one of Tailwind's own hue scales (`gray`, `indigo`, `green`,
  `yellow`, `red`, `amber`, `orange`, `emerald`, `lime`, `rose`) appears in `templates/`,
  `apps/**/forms.py`, `apps/**/templatetags/*.py` or `static/ts/`, or when a template types the
  product name. The risk-ramp module is exempt.
- Contrast tests check the status scales (600 on white and on its 50 fill, 800 on its 50 and 100
  fills, 500 icons on the 50 fill) alongside the palettes.
- A contrast test reads both palette blocks from `static/css/main.css` and fails when any declared
  text/background pair falls below WCAG AA: 4.5:1 for text, 3:1 for UI boundaries and chart marks.
- Guards fail a link or button that hand-rolls a filled button (a `primary`, `danger` or
  `success` 600 fill with a hover on the same scale and no `btn`), a link or button that draws a
  click ring (`focus:ring`, `focus:outline-none`), a hand-made pill or white `rounded-2xl` card,
  a status pill without `pill-marker`, and a widget `attrs` class in `apps/**/forms.py` that styles
  the control (border, radius or padding).
- A test checks each `--text-*` size and line height against the type scale. A guard fails a
  `text-xs` element whose literal text reads as a sentence: five words or more, or ending in a
  period. It reads the element's text past tags and template logic, counting a variable as one
  word, and skips containers of blocks, whose children are separate labels. It is a heuristic;
  classes TypeScript assembles are checked in review. The survey's tests check its question, answer and input
  classes.
- Tests cover the component classes in the built CSS, the field template (order, every error,
  *(opcional)*, the ARIA wiring, the fieldset, the admin left alone), the icon tag, each alert
  tone and messages on both layouts, and the styleguide's access and contents. The busy and
  dismiss scripts have no test runner and are checked in the browser.
- Tests cover the context processor and the switch: cookie validation and the fallback, the
  switch rendered for admins only and never on the survey form, the return-address check, and
  `lang="es"`.
- No test can see color on screen. Every change to `templates/` or `static/` is checked in a
  browser at 360px and on desktop, in both palettes.

## Open questions

None.

## Linked ADRs

None.
