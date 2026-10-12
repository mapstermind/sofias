# Design system

## Status

Current — implemented in `static/css/main.css`, `apps/core` (`brand.py`, `context_processors.py`,
`forms.py`, `styleguide.py`, `templatetags/brand.py`, `templatetags/icons.py`), the partials in
`templates/components/`, `templates/forms/` and `templates/icons/`, the account screens' layout
`templates/base_auth.html`, and the scripts in `static/ts/`.

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

Each recurring pattern has one definition. A button, a form control, a card, a link and a pill
are component classes (`btn btn-primary`, `control`, `card`, `card-link`, `link`, `pill`,
`chip`), and so is a survey's answer row (`answer`). Every page opens with one page-header
partial and follows one heading ladder. Every Django form draws its
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
- **Typography.** Figtree is self-hosted from `static/fonts/figtree/` as two variable fonts,
  upright and italic, with weights 300–900. The browser gets the WOFF2 files: the app declares one
  `@font-face` per file with the weight range and `font-display: swap`, preloads the upright file
  in `base.html`, and sets Figtree as Tailwind's `--font-sans`. The results report uses the TTF
  files beside them for headings, tables and figures and keeps Source Serif 4 for prose. Its
  `@font-face` rules declare one face per weight, because WeasyPrint rejects the range form.
  `npm run build:css` minifies `output.css`.
- **Voice.** How the product speaks, under **Voz** below.
- **Type scale.** Tailwind's size classes carry the scale's values, declared as `--text-*`
  tokens in `main.css`. The sizes are in `rem`, so a reader who raises their browser's or phone's
  text size scales every step. Each class names a role:

  | Class | Size | Line height | Role |
  |---|---|---|---|
  | `text-xs` | 13px | 1.4 | A label on a graphic or a badge: a pill, a legend entry, a chart caption, a count |
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
  - **Headings.** A page's one `h1` is `text-xl` bold, from the page header (below). A page
    section is an `h2` at `text-lg` weight 600 in `neutral-900`, 40px below what precedes it and
    16px above its content. A card's title is an `h3` at `text-base` weight 600. Headings run in
    order: nothing skips a level.
  - **Labels are sentence case.** A label for a value (a stat's caption, a `dt`, a filter's
    legend) is `text-sm` weight 500 in `neutral-600`. No label is set in capitals or tracked out;
    only the avatar's initials are capitals.
  - **Layout is classes.** An inline `style` carries only a computed value (a bar's width, a
    tick's offset, a ring's dash), never layout. No template carries an inline `on*=` handler;
    behaviour lives in `static/ts/`.
  - **Skip link.** `base.html` opens every page with *Saltar al contenido*, hidden until it has
    keyboard focus, pointing at the layout's `<main id="main" tabindex="-1">`.
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
    states (*Completada*, *Publicado*, *Activada*) `success`; notices and states that need an
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
      (`danger-600` fill, white text, hover `danger-800`) undoes or removes: *Retirar publicación*. Buttons
      have an 8px radius, weight 500 and 14px text, and are 44px tall; `btn-sm` is 36px, for dense
      desktop rows. A leading icon is 20px. A disabled button is at half opacity and ignores hover.
      A busy button (`aria-busy="true"`) shows a spinner and ignores clicks;
      `static/ts/busy_submit.ts` sets it on the submit button of every `method="post"` form, unless
      the form carries `data-no-busy`, and clears it when the back button restores the page from
      the browser's cache. A GET form (a search, the filters) is never marked. A submit another handler cancelled
      is left alone. Under `prefers-reduced-motion` the spinner does not spin.
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
    - **The card link:** `card-link` makes a whole `card` a link or a button: a flex row whose
      `neutral-200` border turns `primary-300` on hover, with no hover shadow. The call site adds
      `group` and a trailing 20px `chevron-right` in `neutral-400` that turns `primary-600` on
      hover, or another icon where the card opens something else (the dashboard's *Mínimo
      representativo* opens the Cochran dialog behind a `calculator`). The card's own title says
      where it goes; no "Ver …" text follows it. A card that leads nowhere is a plain `card`.
    - **The link:** `link` is a link inside a sentence: weight 500, `primary-700`, underlined on
      hover.
    - **The chip:** `chip` is the label of a visually hidden checkbox or radio (`peer sr-only`,
      just before it): a pill-shaped choice with a `neutral-300` border, 44px tall on a phone and
      36px from `sm`, filled `primary-600` with white text when chosen, with the base rule's focus
      outline when its input has keyboard focus. The roster's and the results page's filters are
      chips. The removable filters above the results are chip-shaped links in `primary-50` with an
      `x-mark`.
    - **The filter bar:** a list a person narrows (the roster, the results page) has one bar: its
      field (the search box, the survey picker), then *Filtros*, then *Limpiar filtros* while
      anything is narrowed, all from `components/_filter_buttons.html`. *Filtros* carries a count
      of the dimensions in use and opens `components/_filter_dialog.html`: a dialog of chips, one
      group per dimension, over *Limpiar filtros* and *Aplicar filtros*. Both live inside the
      page's GET form, so applying is a submit and the narrowing lives in the URL.
      `static/ts/filter_dialog.ts` puts the chips back when the dialog is dismissed and lets a
      chosen radio be un-chosen, which is how sexo returns to "either". On a phone the results
      picker has its own row, its survey names being long; the roster's bar is sticky, so its
      search keeps *Filtros* beside it.
    - **The answer row:** `answer` is a survey option's `<label>` wrapping its input: a 44px row
      with a `neutral-200` border, a `neutral-50` hover and a 20px radio or checkbox in
      `primary-600`. The chosen row takes a `primary-600` border and a `primary-50` fill from
      `:has(:checked)`, with no script, so a reload or the back button shows it too. It is a
      selection, never a status: every answer is marked the same way. *Sí/No*, single and
      multiple choice are rows, *Sí/No* side by side from `lg`. Likert and rating are rows on a
      phone and five equal tiles from `lg`, the radio above its label.
  - **The page header.** `templates/components/_page_header.html` takes `title` and an optional
    `subtitle`: the page's one `h1` and a `text-sm` `neutral-600` line under it, 24px above the
    content. The company pages, the report pages, *Mis encuestas* and the styleguide open with
    it, and the survey draws the same shape with its description at body size. The dashboard sets
    the company name beside a `primary-50` panel holding the *Código de empresa*: large
    monospace, so 0/O and 1/I stay apart, with a *Copiar* button (`static/ts/copy.ts`, shown only
    where the Clipboard API exists) and one line saying colaboradores type it to activate. Employee detail, the confirmation page and the about page draw their
    title inside a card, and the account screens in their form column. The report sheet keeps its
    cover's own title.
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
    A password control carries a show/hide button inside its right edge: a `btn-text btn-sm` with
    `eye`, then `eye-slash`, labelled *Mostrar contraseña* or *Ocultar contraseña* and marked with
    `aria-pressed`. The field template renders it `hidden`, and `static/ts/password_toggle.ts`,
    loaded on every page, reveals it and flips the input between hidden and plain text, so without
    JavaScript the control is a plain password field.
    A field that is `required=False` for a widget's sake but validated as required, or one a draft
    may leave blank but publishing needs (the report's, with *Necesario para publicar.* as help),
    sets `shown_as_required = True` to drop *(opcional)*. A form that autofocuses a field mixes in
    `apps.core.forms.ErrorFocusMixin`, which moves the autofocus to the first field in error after
    a failed submit. A date as three selects is `LabelledSelectDateWidget`, which names each part
    (*Día*, *Mes*, *Año*) for a screen reader. Widget `attrs` carry no styling classes, only
    real extras such as the large centered digits of a login code. A page that lays fields out
    itself (the report form's grid and signatory rows) places each with
    `{{ field.as_field_group }}`. The Django admin keeps its own markup.
  - **Alerts.** `templates/components/_alert.html` takes `tone` (`success`, `info`, `warning`,
    `danger`), an optional `title`, and `body` or `items`. It draws a 50 fill, a 200 border and a
    12px radius, the tone's icon in its 500 and the text in its 800. `info` takes `primary`.
    `danger` is `role="alert"`, the rest `role="status"`. An inline alert is never dismissible.
    `link_url` with `link_label` adds one link after the body (*Ir a la primera*). `focus` makes
    the alert take keyboard focus on load (`static/ts/focus_on_load.ts`), for an error a form
    reloaded to report: a role read out on load is not announced reliably, focus is.
  - **Messages.** `templates/_messages.html` draws Django's messages as dismissible alerts at the
    top of every page; `base_app.html`, `base_auth.html` and `base_centered.html` include it. `error` maps to
    `danger` and `debug` to `info`. The close button (*Cerrar aviso*) is wired by
    `static/ts/dismiss.ts`, loaded on every page, which moves focus to the next message or to
    `#main`, which every layout has. Without
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
    tone, the status pills and risk badges, cards, the account screens' panel and `btn-glow`, a card link, a link and chips, a likert
    question's answer rows, a dialog, and every icon by name. It is shown to whoever
    may switch palettes (`brand.can_switch_palette`); everyone else gets a 404.
  - **Navigation.** Every signed-in page has one header row (`base_app.html`): the logo, the
    company's sections, and the user menu. It is 56px on a phone and 60px from `lg`.
    - **Sections.** `{% company_nav %}` (`apps/core/templatetags/navigation.py`) lists the
      sections the viewer may open: *Tablero*, *Colaboradores*, *Resultados* and *Reportes*. Each
      is offered only when the viewer holds the permissions its view checks, as an Administrador
      on any company or as an executive on their own, so an Ejecutivo secundario sees two. A
      child page lights its parent: an employee lights *Colaboradores*, a report or the report
      form lights *Reportes*. The active section carries `aria-current="page"`. Fewer than two
      sections render nothing.
    - **Rendering.** The same list renders twice (`templates/_company_nav.html`). Below `lg` it
      is a switcher: a `<details>` whose 44px summary names the current section and opens a
      panel of 48px links, the current one tinted `primary-50` with a squircle marker. From
      `lg` it is inline tabs: 14px links at weight 500, the active one `neutral-900` over a 2px
      `primary-600` rule. The panel is a disclosure of links, not an ARIA menu.
    - **The user menu** (`templates/_user_menu.html`). The avatar is the summary of a second
      `<details>`, whose panel holds the viewer's name, role label and email, and a *Cerrar
      sesión* button that posts to logout.
    - **Pages without sections.** A respondent's pages and every survey page have no sections,
      so the header offers *Mis encuestas* instead, except on that page itself.
    - **Panel behaviour.** Both panels open and close without JavaScript.
      `static/ts/disclosure.ts` closes an open one on Esc (returning focus to its summary) or on
      a click outside, keeps one open at a time, and closes them when the back button restores
      the page.
    - **Page context.** Company context lives in the page, not the header. `base_app.html`
      opens its content with `{% block page_context %}`, which by default shows an
      Administrador *Empresas / {company}* (`_page_context.html`). A child page replaces it with
      one back link, a `btn-text btn-sm` at every width: *← Colaboradores* (keeping the roster's
      filters), *← Reportes*, *← Reporte*.
  - **Dialogs.** Every dialog is a native `<dialog>` with the `dialog` class, opened with
    `showModal()`, which supplies the focus trap, the inert page behind, Esc and the return of
    focus to the opener.
    - **Look.** `dialog` is white, with a 12px radius, 24px padding and `shadow-xl`, at most
      28rem wide and `calc(100% − 2rem)` on a phone. Taller content scrolls inside it. The
      backdrop is `neutral-900` at 40%. It fades and scales in over 150ms, and appears at once
      under `prefers-reduced-motion`.
    - **Structure.** Each template follows one shape: an optional 48px icon circle, a `text-lg`
      title that the dialog names with `aria-labelledby`, the body, and an actions row
      (`flex-col-reverse sm:flex-row sm:justify-end`), so the main action sits on top on a
      phone and on the right on desktop.
    - **Behaviour** (`static/ts/dialog.ts`). It reads data attributes, so no template carries
      inline script: `data-dialog-open="<id>"` opens, `data-dialog-close` closes,
      `data-open-on-load` opens when the page loads (the survey's confirmation and
      saved-progress dialogs), a click on the backdrop closes, and `data-dialog-static` ignores
      Esc and the backdrop (*Tu sesión se cerró*, which only offers to sign in again).
    - **Confirmations.** A destructive action asks inside a dialog that holds the form itself:
      *Retirar publicación* on a report opens `unpublish-dialog`, whose own `btn-danger` submits. Without
      JavaScript the dialog never opens, so nothing is undone unconfirmed.
  - **Empty states.** `templates/components/_empty.html` takes `body`, and optionally `icon`,
    `title`, `action_url` with `action_label`, and `compact`. It draws a dashed `neutral-300`
    card holding:
    - a 20px `neutral-500` icon on a 40px `neutral-100` tile
    - a 16px title at weight 600
    - the body at 14px in `neutral-600`
    - a `btn-secondary` action

    The empty roster offers *Limpiar filtros* when it is filtered.
  - **Account screens.** The ways to sign in (*Código por correo*, *Revisa tu correo*,
    *Contraseña*, *Primer ingreso*), *Cambia tu contraseña* and *Activa tu cuenta* extend
    `templates/base_auth.html`: a white card on `auth-backdrop`, the page's `neutral-100` tinted by
    a `primary-100` glow at the top left and an `accent-100` glow at the bottom right. The card has
    a 24px radius, a `neutral-200` ring and one large shadow tinted `primary-900`, and splits into
    two columns from `lg`.
    - **The panel:** `auth-panel` is the left column, inset 12px with a 16px radius. Its gradient
      is layered from the palette's variables, with a `primary-900` pool at the bottom left under
      the white text, `accent-300` and `accent-500` glows, a blurred `primary-700` shape and a
      faint film grain, so it repaints with the palette. It holds the logo in white at the top
      left and `brand.meaning` at the bottom, at `text-2xl` weight 600, `text-3xl` from `xl`,
      wrapping in balanced lines.
    - **The form column:** the logo in `primary-600` from `lg`, then the page's `h1` at
      `text-xl` with a `text-sm` subtitle, the messages, the form and whatever follows it. The
      blocks are `form_header`, `form_body` and `form_footer`. The main action is
      `btn btn-primary btn-glow`: `btn-glow` adds a soft `primary-600` shadow beneath it and is
      used only here.
    - **Other ways in:** the three sign-in forms end with *Otras formas de ingresar*
      (`accounts/_signin_alternatives.html`, given `current`). This is a heading between two
      `neutral-200` rules over compact `card card-link shadow-none` rows for the other two
      methods, each with a `primary-50` icon tile (`envelope`, `ticket`, `key`), a title, a line
      and a chevron. *Revisa tu correo* offers *pide otro código* and *Usa otro correo* instead.
    - **The long variant:** a view passes `auth_variant="long"` for a tall form (*Activa tu
      cuenta*). The card widens to `max-w-6xl` with a 2:3 split, the form column to `max-w-lg`
      starting at the top, and the panel becomes one screen tall and sticky, so the logo and the
      name stay in view while the form scrolls.
  - **Error pages.** `templates/404.html`, `403.html` and `500.html` extend `base_error.html`,
    a centered card. Each holds:
    - the logo
    - a `text-xl` title and one sentence (*No encontramos esta página*, *No tienes acceso a esta
      página*, *No pudimos cargar esta página*)
    - *Ir al inicio*
    - the code as a `text-sm` footnote for support

    Django renders the 404 and 403 pages with the request
    context. The 500 page comes from `handler500 = "apps.core.views.server_error"`, which renders
    with only the brand and the default palette and makes no database query, since the database
    may be what failed.
  - **The three-places rule.** A pattern that appears in three or more places with no component
    gets one proposed before its markup is copied again.

**Out of scope:**

- **Tables and pagination.** No page has a table outside the report, and the list rows stack on a
  phone, so there is no table component. Nothing paginates; paginating the roster is a feature of
  its own, with its queries, addresses and filters.
- **A loading skeleton.** The one asynchronous swap, the results filters, marks itself
  `aria-busy`, which dims the body while it loads.
- **The NOM-035 questions' wording.** They are the norm's text, verbatim, and speak *usted*.
- **Dark mode.** The token layer makes it a later addition of one more variable block.
- **The Django admin.** It keeps Django's own styling.
- **Final name, logo and palette.** They stay placeholders until the client confirms them.

## Voz

How the product speaks, on every screen, message and email. The words are the
product's voice, so a wording change is reviewed like a layout change.

- **Tú, always.** The NOM-035 questions keep the norm's own wording, which speaks *usted*; the
  survey's instructions say they are the official questions.
- **Buttons are verbs** in sentence case, naming what happens: *Guardar reporte*, *Enviar
  respuestas*, *Retirar publicación*. The confirmation reuses the button's word: *Reporte
  guardado.*, *Respuestas enviadas*, *Publicación retirada.* One action keeps one name through a
  flow: *Seguir respondiendo* in every dialog that returns to the survey.
- **No ¡…!, no *por favor*, no *lo sentimos*, no *exitosamente*.** Thanks are said once, plainly.
- **An error says what happened and how to fix it**: *El código no es correcto o ya venció.
  Revisa los 6 dígitos o pide uno nuevo.* Never *Error* or *inválido* alone.
- **An empty screen offers the next step** when the reader has one (*Limpiar filtros*, *Agregar
  empresa*); otherwise it says when the space fills.
- **Plain words over system words**: no *vinculado*, *configurado*, *congelado*, *usuario* for a
  person, or an identifier such as *UserProfile*.
- **Punctuation.** A full sentence in a message ends with a period; a button, label or heading
  does not. A space goes before `%`. Tab titles read `Página | Contexto | Marca`. A year range
  takes an en dash. A question opens with `¿`.
- **One word per concept.** The glossary is in [`localization.md`](localization.md). The names
  of the three codes are *código de empresa* (5 characters, typed at activation), *código de
  acceso* (9 digits, the first sign-in) and *código de inicio de sesión* (6 digits, emailed). A
  colaborador who needs a code or access is sent to *quien te invitó*.

## Phone shape

Nothing in this doc sets a page layout. The palette switch is a small pill fixed to the
bottom-left corner, clear of the back-to-top control at bottom-right. The survey form does not
render it, because the form's phone bar spans the whole bottom edge. Buttons and controls are
44px tall, the tap target on a phone; a button that should span the phone's width says so at the
call site (`w-full sm:w-auto`). The styleguide is one column, with its button and pill rows
wrapping.

The header is one 56px row on a phone: the logo, the section switcher, the user menu. Its panels
open below it; the section panel is 14rem wide and aligned to the switcher's left edge. The logo
is a 44px target. Company context and
back links sit at the top of the page, not in the header. A dialog keeps a 16px gutter on each
side and scrolls inside itself when it is taller than 85% of the screen. Error pages are a
centered card.

The account screens are one card on a phone: the panel is a short band at the top holding the
logo and `brand.meaning` as one `text-sm` paragraph, and the form follows below it. The form
column's own logo shows only from `lg`, where the panel becomes the left column. The *Otras
formas de ingresar* rows are full width and at least 44px tall.

The dashboard's stat cards sit two to a row on a phone and four from `lg`. Each survey on it is
one card: its progress on top and, for a viewer who answers it, a *Tus respuestas* strip under a
divider, its action full-width on a phone. A closed survey says why in a line of text, never in a
hover tooltip. The survey's answers are full-width rows on a phone; likert and rating become five
tiles from `lg`. Filter chips wrap. The footer stacks its three items, centered, on a phone, and
spreads them across one row from `sm`.

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
- Decision: Figtree ships to the browser as WOFF2 and to the PDF as TTF.
  Reason: WOFF2 halves each file (about 28 KB against 62 KB) on the first page a respondent opens;
  WeasyPrint reads the TTFs from disk, where size costs nothing.
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
- Decision: The header is one row at every width: a section switcher on a phone, tabs from `lg`.
  Reason: Stacked tabs take a fifth of a phone screen on every page. A collapsible menu hides
  where you are. The switcher names the current section and reaches any other in two taps.
- Decision: The sections come from one tag that mirrors the views' permission checks.
  Reason: A section a viewer cannot open is never offered, and the switcher and the tabs cannot
  disagree.
- Decision: Company context and back links live in the page body.
  Reason: The header holds only navigation, so it stays one row.
- Decision: Every dialog is a native `<dialog>`, and the header's panels are `<details>`.
  Reason: The browser supplies the focus trap, Esc, the inert background and focus restore, and
  a `<details>` opens without JavaScript; the scripts only add polish.
- Decision: The 500 page renders through its own view, without the request context.
  Reason: Django renders it without context anyway, and the database may be what failed.
- Decision: Labels are sentence case.
  Reason: A tracked capitals label is slower to read and reads as template chrome.
- Decision: A chosen survey answer marks its whole row in `primary`.
  Reason: Respondents may struggle with devices, and a 20px dot is easy to miss; one color for
  every answer keeps an answer from reading as right or wrong.
- Decision: The dashboard does not repeat the header's navigation.
  Reason: Every section is one tap away from every page. A dashboard card earns its place with a
  figure, as *Cuestionarios valorados* does.
- Decision: A report names a subject once and captions each chart by what it shows.
  Reason: In the report every chart sits under its own heading, so a label on the chart repeats
  it. The results page lists statistics rows together, so there each keeps its name.
- Decision: A closed survey explains itself in text, not a tooltip.
  Reason: A hover tooltip does not exist on a phone.
- Decision: The password's show/hide button is rendered by the field template and revealed by a
  script.
  Reason: Every password field gets it with no per-form code, and a page whose script fails never
  shows a button that does nothing.
- Decision: The account panel's gradient is built from the palette's variables, not an image.
  Reason: It repaints with the palette, and replacing the palette stays one edit to one CSS file.
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
- Tests check that each role is offered exactly the sections it may open, that every offered
  section opens for that role, and which section each page lights. Only `base_app.html` draws a
  `<header>`, and no template hand-rolls an overlay (`fixed inset-0`), opens a
  dialog with inline script, or draws a dashed empty card outside the partial. Every `<dialog>`
  names a title that exists. The survey opens its confirmation dialog on load only when asked.
  The error pages render in Spanish with the brand, and the 500 page renders with no database
  query.
- Guards fail a template that writes a label in capitals (`uppercase`, outside the avatar),
  uses black, lays out with an inline `style`, carries an inline `on*=` handler, draws a focus
  ring on an `input`, or types the brand's meaning. A test renders each main page for the role
  that sees it and fails a second `h1`. Tests check the dashboard's cards and *Tus respuestas*
  strip, that every survey option is an `answer` row, that the report names each categoría,
  dominio and the final score once, and that *Retirar publicación* is a dialog. A guard fails a
  tab title that separates with `—` instead of `|`. Tests check the skip link, the Spanish CSRF
  page, the autofocus move and the date parts' labels, and that no template opts into the busy
  state by hand.
- Tests cover the component classes in the built CSS, the field template (order, every error,
  *(opcional)*, the ARIA wiring, the fieldset, the admin left alone), the icon tag, each alert
  tone and messages on the layouts, and the styleguide's access and contents. Tests check that
  each account screen renders in `base_auth.html` with its panel, that the long variant is
  activation's (its blocked states included), which other ways in each sign-in form offers, and
  that a password field, and only a password field, renders its show/hide button `hidden`, after
  the control and before the errors. The busy, dismiss, focus-on-load and password-toggle scripts
  have no test runner and are checked in the browser. No test reads the
  copy against **Voz**; wording is checked in review.
- Tests cover the context processor and the switch: cookie validation and the fallback, the
  switch rendered for admins only and never on the survey form, the return-address check, and
  `lang="es"`.
- No test can see color on screen. Every change to `templates/` or `static/` is checked in a
  browser at 360px and on desktop, in both palettes.

## Open questions

None.

## Linked ADRs

None.
