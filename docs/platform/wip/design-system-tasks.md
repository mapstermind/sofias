# Design system — Phase 2a: core components

## What changes

**What.** The design system gains a component layer and every existing template adopts it:

- CSS component classes for the single-element patterns (buttons, form control, card, pill).
- A project form renderer that draws every Django form field the same way.
- An alert partial, Django messages shown on every page, and a Heroicons icon tag.
- A styleguide page at `/estilos/`.

Navigation, tables on a phone, the dialog, empty and error pages, and pagination are Phase 2b
and stay out of this change.

**Why.** Each pattern exists today in several hand-written variants:

- About 10 button class strings across 12 templates, mixing `rounded-lg`/`xl`, two hover
  directions, a `focus:ring` that shows on mouse clicks, and no disabled or loading state.
- Field markup written out per field (9 times in `profile_setup.html`), with widget classes
  copied between `accounts/forms.py` and `reports/forms.py`.
- Twelve alert boxes in five shapes, with no icons.
- Django messages that only the report pages display.

Phase 3 (the page pass) needs one definition per pattern to assemble pages from.

**Live doc sections this makes wrong** (`docs/platform/design-system.md`):

- *Out of scope → Component partials and a styleguide page*: the 2a half moves into Scope.
- *Out of scope → An icon set*: Heroicons is adopted.
- *Scope*: gains a **Components** entry. *Usage rules* gains the button, field and alert rules.
- *Key decisions* and *Enforcement*: gain the entries listed under **Decisions** and **Tests**
  below.
- *Phone shape*: gains the styleguide's one-column shape.

`.claude/CLAUDE.md`'s Design-system bullet gains the component rule.

**ADRs.** None touched.

## Design

### Atoms: component classes

One `@layer components` block in `static/css/main.css`, built only from tokens with `@apply`.
Utilities sit in a later layer, so a call site adds layout (`w-full sm:w-auto`, `mt-4`) without a
specificity fight.

**Buttons**: `btn` plus one variant, optionally with `btn-sm`.

| Class | Look | Used for |
|---|---|---|
| `btn-primary` | `primary-600` fill, white text; hover `primary-700` | the one main action per view |
| `btn-secondary` | white, `neutral-300` border, `neutral-800` text; hover `neutral-50` | Cancelar, Ver, Descargar PDF, filters |
| `btn-text` | no box, `primary-700` text; hover `primary-50` wash | in-row actions, dismiss |
| `btn-danger` | `danger-600` fill, white text; hover `danger-800` | *Despublicar*, *Eliminar* |

- **Shape and type:** 8px radius (`rounded-lg`), weight 500, 14px text.
- **Size:** 44px tall by default; `btn-sm` is 36px, for dense desktop tables only.
- **Icons:** a leading icon is 20px, with the gap built in.
- **States:**
  - **Focus:** `focus-visible` only, a 2px `primary-500` outline with a 2px offset.
  - **Disabled:** 50% opacity, no hover, `cursor-not-allowed`.
  - **Loading:** `aria-busy="true"` shows a spinner in the leading slot and blocks clicks. A
    small TS module (`static/ts/busy_submit.ts`) sets it on the submitter when a form carrying
    `data-loading` submits. Under `prefers-reduced-motion` the spinner does not spin.
  - **Where loading goes:** the login request (it sends the OTP email), the report's
    publish/unpublish forms, and the report form's save.

**Form control**: `control`.

- **Look:** white fill, `neutral-300` border, 8px radius, 44px tall, 16px text. At 16px iOS
  Safari does not zoom in on focus.
- **Focus:** `primary-500` border plus a 2px ring of the same color.
- **Invalid:** `[aria-invalid="true"]` gives a `danger-600` border and ring.
- **Disabled:** `neutral-50` fill, `neutral-500` text.
- **Where it applies:**
  - Fields drawn by the renderer get these styles from their `field` wrapper, through a
    `.field :is(input…, select, textarea)` rule with the same declarations.
  - `control` itself is for the hand-written inputs outside a Django form (roster search,
    results filters).

**Card**: `card` is white, with a `neutral-200` border, `shadow-sm` and a 12px radius
(`rounded-xl`). Padding is set at the call site.

**Pill**: `pill` is the shared shape (full radius, 12px text, weight 500, `px-2.5 py-0.5`).

- `pill-marker` adds the `rounded-xs` squircle in the current text color.
- The tone stays a utility.
- `ndr_badge` builds on `pill`, and the status pills use `pill pill-marker`.

### Fields: the form renderer

- **Renderer.** `FORM_RENDERER = "apps.core.forms.SofiaFormRenderer"`, a `TemplatesSetting`
  subclass that sets:
  - `form_template_name = "forms/form.html"`
  - `field_template_name = "forms/field.html"`
- **Admin is unaffected.** `django.forms` joins `INSTALLED_APPS` so Django's widget templates
  resolve. No widget template is overridden, so the admin renders as before.
- **`forms/field.html`, in order:**
  1. **Label:** 14px, weight 500, `neutral-800`. An optional field (`not field.field.required`)
     adds a quiet *(opcional)*.
  2. **Help text:** 14px, `neutral-600`, above the control.
  3. **The control,** inside the `field` wrapper.
  4. **Every error:** an `exclamation-circle` icon and `danger-600` text, below the control.
- **Accessibility.** Django 6 sets `aria-invalid` and `aria-describedby` on the widget. The
  template keeps the ids Django points at.
- **Multi-widgets.** A multi-widget (`field.use_fieldset`, e.g. date of birth) renders a
  `<fieldset>` with a `<legend>`, carrying `m-0 p-0 border-0 min-w-0` like
  `surveys/_question.html`.
- **Checkboxes and radios** render as full-width 44px rows, with `accent-color` from `primary-600`.
- **`forms/form.html`:**
  - non-field errors as a danger alert with `items`
  - hidden fields
  - the visible fields in a `space-y-6` stack
- **Custom arrangements.** A page that needs its own layout (the report form's grid and
  formset) places fields one by one with `{{ field.as_field_group }}`.
- **Widget classes go away.** Widget `attrs` lose every styling `class`: `_TEXT_CLASSES`,
  `_SELECT_CLASSES` and `_DATE_SELECT_CLASSES` in `accounts/forms.py`, and `INPUT_CLASS` in
  `reports/forms.py`, are deleted. `attrs` keep only real extras (autocomplete, inputmode, the
  OTP code's centered digits).
- **Adopted by:** `profile_setup`, `login_request`, `login_verify`, `login_password`,
  `login_setup_access_code`, `change_password` and `report_form`.
- **Not touched:**
  - the survey question widgets (`surveys/_question.html`), which are their own component
  - the admin CSV import, which keeps the admin's look

### Alerts, messages and icons

**Icons.** `{% icon "name" "css classes" %}` in `apps/core/templatetags/icons.py`.

- **Files:** it reads `templates/icons/<name>.svg`: Heroicons v2.2.0 outline, 24px,
  `stroke="currentColor"`, downloaded once, with Heroicons' MIT `LICENSE` beside them.
- **Accessibility:** the default is `aria-hidden="true"`. `label="…"` renders `role="img"` and
  an `aria-label` instead.
- **Unknown names** raise `TemplateSyntaxError` when DEBUG is on and render nothing otherwise.
- **The set** is only the icons in use:
  - `check-circle`, `information-circle`, `exclamation-triangle`, `exclamation-circle`, `x-mark`
  - the replacements for the hand-drawn icons in the survey modals, `survey_submitted`,
    `company_dashboard`, `employee_list`, `employee_detail` and `_dominios_summary`

  The chart SVGs and the back-to-top ring are drawings, not icons, and stay.

**Alert.** `templates/components/_alert.html`.

- **Parameters:** `tone` (`success` | `info` | `warning` | `danger`), an optional `title`, and
  either `body` (one string) or `items` (a list).
- **Look:** 50 fill, 200 border, 12px radius. The icon is the tone's 500, and the title and text
  its 800. `info` uses `primary`, because information is not a status.
- **Icon and role per tone:**

  | Tone | Icon | Role |
  |---|---|---|
  | `success` | `check-circle` | `status` |
  | `info` | `information-circle` | `status` |
  | `warning` | `exclamation-triangle` | `status` |
  | `danger` | `exclamation-circle` | `alert` |

- **Replaces** the twelve hand-written boxes: the profile notices, the non-field errors, the
  publish blockers and the report form's errors.
- **Not an alert:** the survey's pending-questions panel is an interactive widget. It keeps its
  markup, re-cut with `card` and `btn`.

**Messages.** `templates/_messages.html`.

- **Where:** included once by `base_app.html` and once by `base_centered.html`, above the page
  content. `templates/reports/_messages.html` and its includes go away.
- **Tones:** `error` → `danger`, `debug` → `info`; the others map by name.
- **Dismissing:** each message has an `x-mark` `btn-text` (`aria-label="Cerrar aviso"`) that
  `static/ts/dismiss.ts` removes; without JS, the message stays.
- **Nothing auto-hides.** Inline alerts are not dismissible.

### The styleguide

- **View and access.** `/estilos/`, `StyleguideView` in `apps/core`. It is gated by
  `brand.can_switch_palette`: Admins, superusers, or anyone when DEBUG is on. Everyone else
  gets a 404.
- **Layout.** `core/styleguide.html` extends `base_app.html`.
- **Sections,** in order, with the app's own copy:
  1. **Color.** The active palette's scales and the status scales, as labelled swatches.
  2. **Type.** The six-step scale and the weights.
  3. **Buttons.** Every variant by size; default, disabled and loading.
  4. **Fields.** A demo form (`apps/core/styleguide.py`) rendered by the real renderer, unbound
     and bound with errors: text with help, an optional field, a select, the date multi-widget,
     a checkbox.
  5. **Alerts and messages.** Every tone, with a title, with items, and dismissible.
  6. **Pills.** Status pills, risk badges from `ndr_badge`, answer pills.
  7. **Cards.**
  8. **Icons.** Every icon in `templates/icons/` with its name.
- **Phone shape:** one column; button and pill rows wrap.

### Decisions

- Single-element patterns are CSS classes, and patterns with structure are partials or Django's
  renderer. A button needs any element and any attribute, which an include cannot pass through.
- Help text sits above the control, read before typing and clear of a phone keyboard.
- Optional fields are marked *(opcional)*, and required ones carry no mark: nearly every field
  is required, so an asterisk on each is noise.
- Cards are 12px, one radius step above the 8px controls inside them.
- Field text is 16px, so iOS does not zoom on focus.
- Messages never hide on a timer, because a timed message fails slow readers.
- Inline alerts cannot be dismissed, because the error is still there.

### Tests

- **Renderer:**
  - label, help, control and errors render in that order
  - every error shows, and *(opcional)* appears only on optional fields
  - `aria-invalid` and `aria-describedby` reach the widget
  - a multi-widget renders a `fieldset` with a `legend`
  - an admin change page still renders
- **Icon tag:**
  - the default is `aria-hidden`
  - a label renders `role="img"`
  - an unknown name raises
- **Alert:** each tone renders its icon and role; `items` render as a list.
- **Messages:** a message shows on a non-report page, inside both layouts.
- **Styleguide:** returns 404 to an employee, 200 to an admin, and 200 to anyone in DEBUG.
- **`test_design_tokens.py` additions:**
  - a template element with an unprefixed `primary`, `danger` or `success` 600 fill plus a
    `hover:` fill on the same scale, and no `btn` class, fails: a hand-rolled button. State
    variants such as the roster filter's `peer-checked:bg-primary-600` and the palette switch's
    neutral hover are not buttons and pass
  - `focus:ring` and `focus:outline-none` fail
  - a styling `class` (border, rounded or padding) in a widget's `attrs` in `apps/**/forms.py`
    fails
- **Checked by hand,** from the PR's click list:
  - the loading state, the message dismiss, hover and keyboard focus
  - every changed page at 360px and on desktop, in both palettes

---

# Phase 2a Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** One definition per button, field, alert, message, pill and card, adopted by every
existing template, and shown on `/estilos/`.

**Architecture:** Component classes in an `@layer components` block in `static/css/main.css`;
a `TemplatesSetting` form renderer with `forms/form.html` and `forms/field.html`; an `{% icon %}`
tag over Heroicons SVG files; `components/_alert.html` and `_messages.html` partials; a
gated styleguide view in `apps/core`.

**Tech Stack:** Django 6.0 templates and form renderer, Tailwind v4 CLI (`@apply`, `@layer`),
TypeScript compiled by `tsc` (no bundler, no test runner), pytest-django.

**Spec:** the brief above (`## What changes` and `## Design`).

## Global Constraints

- Color only from `primary-*`, `accent-*`, `neutral-*`, `series-*`, `success-*`, `warning-*`, `danger-*`.
- Every user-facing string is Spanish; code, comments and identifiers English.
- Unprefixed classes describe the phone; breakpoint prefixes add the wider layout.
- No new npm or Python dependency. Heroicons files are copied, not installed.
- Never commit without asking: each task ends at a green suite with an uncommitted diff.
- After any change to `templates/` or `static/`: `npm run build:css`; after `static/ts/`: `npm run build:js`.
- Focus indication is `focus-visible` only: 2px `primary-500` outline, 2px offset.

## Review Focus

- A field that is `required=False` but validated as required (`date_of_birth`) must not show *(opcional)*.
- A field whose widget is `HiddenInput` (OTP verify's `email`) must render without a label or wrapper.
- A bound form that re-renders after an error keeps its submitted values and the OTP code keeps its large centered digits.
- A message whose text contains HTML characters is escaped, and a page with no messages renders no empty `<ul>`.
- A double-tapped submit on a slow connection sends one request (the busy state disables the submitter after the first submit), and the browser's back button does not leave the button stuck busy (`pageshow` clears it).

---

### Task 1: Component classes and the focus default

**Files:**
- Modify: `static/css/main.css` (new `@layer base` focus rule and `@layer components` block after the `@theme` blocks)
- Test: `apps/core/tests/test_components_css.py` (new)
- Modify: `apps/core/tests/test_design_tokens.py` (new contrast pairs)

**Interfaces:**
- Produces: classes `btn`, `btn-primary`, `btn-secondary`, `btn-text`, `btn-danger`, `btn-sm`, `control`, `field`, `card`, `pill`, `pill-marker`; `[aria-busy="true"]` styling on `.btn`.

- [x] **Step 1: Write the failing tests.** `test_components_css.py` reads `static/css/output.css` and asserts each class above has a rule (`.btn-primary` followed by `{` or a selector list), that the base `:focus-visible` rule is present, and that `.btn[aria-busy="true"]` has a rule. In `test_design_tokens.py` add `test_danger_button_meets_wcag_aa`: white on `danger-600` and on `danger-800` (its hover) ≥ 4.5.
- [x] **Step 2: Run** `pytest apps/core/tests/test_components_css.py -v` — FAIL (classes absent).
- [x] **Step 3: Implement** in `main.css`:

```css
@layer base {
  :where(a, button, summary, [role="button"], input[type="checkbox"], input[type="radio"]):focus-visible {
    outline: 2px solid var(--color-primary-500);
    outline-offset: 2px;
  }
}

@layer components {
  .btn {
    @apply inline-flex h-11 items-center justify-center gap-2 rounded-lg px-4 text-sm font-medium
      whitespace-nowrap transition-colors duration-150 ease-out
      focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-primary-500
      disabled:cursor-not-allowed disabled:opacity-50
      aria-disabled:cursor-not-allowed aria-disabled:opacity-50;
  }
  .btn > svg { @apply size-5 shrink-0; }
  .btn-sm { @apply h-9 px-3; }
  .btn-primary { @apply bg-primary-600 text-white enabled:hover:bg-primary-700; }
  a.btn-primary { @apply hover:bg-primary-700; }
  .btn-secondary { @apply border border-neutral-300 bg-white text-neutral-800 enabled:hover:bg-neutral-50; }
  a.btn-secondary { @apply hover:bg-neutral-50; }
  .btn-text { @apply px-3 text-primary-700 enabled:hover:bg-primary-50; }
  a.btn-text { @apply hover:bg-primary-50; }
  .btn-danger { @apply bg-danger-600 text-white enabled:hover:bg-danger-800; }
  a.btn-danger { @apply hover:bg-danger-800; }
  .btn[aria-busy="true"] { @apply pointer-events-none cursor-progress; }
  .btn[aria-busy="true"]::before {
    content: "";
    @apply size-4 shrink-0 animate-spin rounded-full border-2 border-current border-r-transparent
      motion-reduce:animate-none;
  }

  .control,
  .field :is(input:not([type="checkbox"], [type="radio"], [type="hidden"], [type="file"]), select, textarea) {
    @apply block min-h-11 w-full rounded-lg border border-neutral-300 bg-white px-4 py-2.5 text-base
      text-neutral-900 placeholder:text-neutral-500
      focus:border-primary-500 focus:ring-2 focus:ring-primary-500 focus:outline-none
      aria-invalid:border-danger-600 aria-invalid:focus:ring-danger-600
      disabled:bg-neutral-50 disabled:text-neutral-500;
  }

  .card { @apply rounded-xl border border-neutral-200 bg-white shadow-sm; }

  .pill { @apply inline-flex items-center gap-1.5 rounded-full px-2.5 py-0.5 text-xs font-medium; }
  .pill-marker::before { content: ""; @apply size-2 shrink-0 rounded-xs bg-current; }
}
```

  The status scales stop at 800, so the danger hover is `danger-800`. A text control keeps a focus ring on click on purpose — a text field matches `:focus-visible` on click in every browser anyway.
- [x] **Step 4: Run** `npm run build:css && pytest apps/core/tests/ -q` — PASS.

### Task 2: The icon tag and the Heroicons files

**Files:**
- Create: `apps/core/templatetags/icons.py`, `templates/icons/*.svg`, `templates/icons/LICENSE`
- Test: `apps/core/tests/test_icons.py`

**Interfaces:**
- Produces: `{% load icons %}{% icon "name" "css classes" label="…" %}` → safe SVG string.

- [x] **Step 1: Download** `heroicons@2.2.0/24/outline/<name>.svg` from `https://unpkg.com/` into `templates/icons/` for: `check-circle`, `information-circle`, `exclamation-triangle`, `exclamation-circle`, `x-mark`, plus each icon Task 7 needs (decided there by reading the hand-drawn SVG; add them in Task 7). Save `heroicons@2.2.0/LICENSE` as `templates/icons/LICENSE`.
- [x] **Step 2: Write the failing tests:**

```python
from django.template import Context, Template, TemplateSyntaxError
from django.test import override_settings
import pytest

def render(src):
    return Template("{% load icons %}" + src).render(Context())

def test_an_icon_is_decorative_by_default():
    html = render('{% icon "check-circle" "size-5 text-success-500" %}')
    assert html.startswith("<svg")
    assert 'class="size-5 text-success-500"' in html
    assert 'aria-hidden="true"' in html
    assert 'stroke="currentColor"' in html

def test_a_labelled_icon_is_an_image():
    html = render('{% icon "x-mark" "size-5" label="Cerrar aviso" %}')
    assert 'role="img"' in html and 'aria-label="Cerrar aviso"' in html
    assert "aria-hidden" not in html

@override_settings(DEBUG=True)
def test_an_unknown_icon_raises_in_debug():
    with pytest.raises(TemplateSyntaxError):
        render('{% icon "no-such-icon" %}')

@override_settings(DEBUG=False)
def test_an_unknown_icon_renders_nothing_in_production():
    assert render('{% icon "no-such-icon" %}') == ""

def test_a_name_cannot_leave_the_icon_folder():
    with pytest.raises(TemplateSyntaxError):
        with override_settings(DEBUG=True):
            render('{% icon "../base" %}')
```

- [x] **Step 3: Run** `pytest apps/core/tests/test_icons.py -v` — FAIL (no library `icons`).
- [x] **Step 4: Implement** `icons.py`: `ICON_DIR = Path(settings.BASE_DIR) / "templates" / "icons"`; `NAME = re.compile(r"^[a-z0-9-]+$")`; `@lru_cache _source(name)` reads `ICON_DIR / f"{name}.svg"` and strips the root's `aria-hidden`/`data-slot` attributes Heroicons ships; `@register.simple_tag def icon(name, css_class="", label="")` builds the attrs with `format_html` (`class`, then `aria-hidden="true"` or `role="img" aria-label=…`) and injects them after `<svg`, as `brand_logo` does. A name failing `NAME` or a missing file: raise `TemplateSyntaxError` when `settings.DEBUG`, else return `""`.
- [x] **Step 5: Run** the tests — PASS.

### Task 3: The alert partial and messages on every page

**Files:**
- Create: `templates/components/_alert.html`, `templates/_messages.html`, `static/ts/dismiss.ts`
- Modify: `templates/base_app.html`, `templates/base_centered.html`, `templates/reports/report_detail.html`, `templates/reports/report_form.html`, `templates/reports/report_list.html`, `templates/accounts/profile_setup.html`
- Delete: `templates/reports/_messages.html`
- Test: `apps/core/tests/test_alerts.py`

**Interfaces:**
- Consumes: `{% icon %}` (Task 2).
- Produces: `{% include "components/_alert.html" with tone="danger" title="…" body="…" items=list %}`.

- [x] **Step 1: Write the failing tests:** render `_alert.html` through `render_to_string` for each tone and assert its icon's path fragment is present (`check-circle` → compare against the file's `<path d=` value), `role="alert"` for `danger` and `role="status"` otherwise, `bg-<scale>-50 border-<scale>-200` with `primary` for `info`; `items=["a","b"]` renders two `<li>`; `body="<b>x</b>"` is escaped. A view test: log a `messages.success(request, "Guardado")` on a page using `base_app.html` that is not a report (use `RequestFactory` + `MessageMiddleware`, or post to `/paleta/`? — use a test-only view: add a message via the `client` session and GET the about page), asserting "Guardado" and `data-dismiss` render; GET the about page with no message asserts `data-messages` is absent. Also on a `base_centered` page (the login request page).
- [x] **Step 2: Run** — FAIL.
- [x] **Step 3: Implement** `_alert.html`:

```django
{% load icons %}
{% comment %}
A message box for one tone: success, info, warning or danger. Takes `tone`, an
optional `title`, and `body` (one sentence) or `items` (a list). `dismissible`
adds a close button that static/ts/dismiss.ts wires up. Info uses the primary
scale: information is not a status.
{% endcomment %}
<div {% if tone == "danger" %}role="alert"{% else %}role="status"{% endif %} data-alert
     class="flex items-start gap-3 rounded-xl border px-4 py-3 text-sm
            {% if tone == "success" %}border-success-200 bg-success-50 text-success-800
            {% elif tone == "warning" %}border-warning-200 bg-warning-50 text-warning-800
            {% elif tone == "danger" %}border-danger-200 bg-danger-50 text-danger-800
            {% else %}border-primary-200 bg-primary-50 text-primary-800{% endif %}">
  {% if tone == "success" %}{% icon "check-circle" "mt-px size-5 shrink-0 text-success-500" %}
  {% elif tone == "warning" %}{% icon "exclamation-triangle" "mt-px size-5 shrink-0 text-warning-500" %}
  {% elif tone == "danger" %}{% icon "exclamation-circle" "mt-px size-5 shrink-0 text-danger-500" %}
  {% else %}{% icon "information-circle" "mt-px size-5 shrink-0 text-primary-500" %}{% endif %}
  <div class="min-w-0 flex-1">
    {% if title %}<p class="font-semibold">{{ title }}</p>{% endif %}
    {% if items %}<ul class="{% if title %}mt-1 {% endif %}list-disc space-y-1 pl-5">{% for item in items %}<li>{{ item }}</li>{% endfor %}</ul>
    {% elif body %}<p{% if title %} class="mt-1"{% endif %}>{{ body }}</p>{% endif %}
  </div>
  {% if dismissible %}
    <button type="button" class="btn btn-text btn-sm -my-1.5 -mr-2 px-2 text-current" data-dismiss>
      {% icon "x-mark" "size-5" label="Cerrar aviso" %}
    </button>
  {% endif %}
</div>
```

  `_messages.html` loops `messages` into `<div class="mb-6 space-y-3" data-messages>` with each message's tone (`error`→`danger`, `debug`→`info`, else the tag) and `dismissible=True`, then `<script src="{% static 'js/dismiss.js' %}" defer></script>`. Include it at the top of `<main>` in `base_app.html` and at the top of the card in `base_centered.html`. `dismiss.ts`: one listener on `document` for `click` on `[data-dismiss]` → `closest("[data-alert]")?.remove()`, and move focus to `#main` so focus is not lost. Remove the three `reports/_messages.html` includes and the file. Replace `profile_setup.html`'s two notice boxes and `report_detail.html`'s blockers box with the alert partial (`tone="warning" title="Para publicar falta:" items=blockers`).
- [x] **Step 4: Run** `npm run build:js && npm run build:css && pytest -q` — PASS.

### Task 4: The form renderer

**Files:**
- Create: `apps/core/forms.py`, `templates/forms/form.html`, `templates/forms/field.html`
- Modify: `config/settings.py` (`INSTALLED_APPS` += `"django.forms"`, `FORM_RENDERER`)
- Test: `apps/core/tests/test_form_renderer.py`

**Interfaces:**
- Consumes: `_alert.html` (Task 3), `{% icon %}` (Task 2).
- Produces: `SofiaFormRenderer`; a field attribute `shown_as_required: bool` that a form sets on a field that is `required=False` but validated as required.

- [x] **Step 1: Write the failing tests** with a local demo form (`name` required with `help_text`, `nickname` optional, `born` a `DateField(required=False, widget=SelectDateWidget)` with `shown_as_required = True`, `agree` a `BooleanField(required=False)`, `secret` a `CharField(widget=HiddenInput)`):
  - `str(form["name"].as_field_group())`: the label's index < help's index < `<input`'s index < first error's index (bind with `{}` for errors); every error of a two-error field appears (add a `clean_name` raising two `ValidationError`s in a list).
  - `(opcional)` appears in `nickname`'s group and not in `name`'s or `born`'s.
  - bound with errors: the `<input` for `name` carries `aria-invalid="true"` and `aria-describedby` naming the help id and the error id, both of which exist in the HTML.
  - `born`'s group renders `<fieldset` and `<legend`.
  - `str(form)` renders the hidden `secret` without a label, and non-field errors through `data-alert` with `role="alert"`.
  - `agree` renders the checkbox before its label text inside a `<label`.
  - The admin: log in a superuser and GET `/admin/accounts/user/add/` — 200, and `class="field` does not appear in the page.
- [x] **Step 2: Run** — FAIL.
- [x] **Step 3: Implement.** `apps/core/forms.py`:

```python
"""The project form renderer: every Django form draws its fields through
templates/forms/field.html. See docs/platform/design-system.md (Components)."""

from django.forms.renderers import TemplatesSetting


class SofiaFormRenderer(TemplatesSetting):
    form_template_name = "forms/form.html"
    field_template_name = "forms/field.html"
```

  `settings.py`: `"django.forms"` in `INSTALLED_APPS` (after the contrib apps), `FORM_RENDERER = "apps.core.forms.SofiaFormRenderer"`.

  `forms/field.html` (ids follow Django's: help `<id>_helptext`, errors `<id>_error`):

```django
{% load icons %}
{% with optional=field.field.required|yesno:",1" %}
{% if field.is_hidden %}{{ field }}{% else %}
<div class="field">
  {% if field.use_fieldset %}<fieldset class="m-0 min-w-0 border-0 p-0"{% if field.help_text %} aria-describedby="{{ field.auto_id }}_helptext"{% endif %}>
    <legend class="mb-1.5 text-sm font-medium text-neutral-800">{{ field.label }}{% if optional and not field.field.shown_as_required %} <span class="font-normal text-neutral-500">(opcional)</span>{% endif %}</legend>
  {% elif field.widget_type == "checkbox" %}
  {% else %}
    <label for="{{ field.id_for_label }}" class="mb-1.5 block text-sm font-medium text-neutral-800">{{ field.label }}{% if optional and not field.field.shown_as_required %} <span class="font-normal text-neutral-500">(opcional)</span>{% endif %}</label>
  {% endif %}
  {% if field.help_text %}<p id="{{ field.auto_id }}_helptext" class="mb-2 text-sm text-neutral-600">{{ field.help_text|safe }}</p>{% endif %}
  {% if field.widget_type == "checkbox" %}
    <label for="{{ field.id_for_label }}" class="flex min-h-11 cursor-pointer items-center gap-3 text-sm text-neutral-800">{{ field }}<span>{{ field.label }}</span></label>
  {% elif field.use_fieldset %}<div class="grid grid-cols-3 gap-2">{{ field }}</div>
  {% else %}{{ field }}{% endif %}
  {% if field.errors %}<div id="{{ field.auto_id }}_error" class="mt-2 space-y-1">{% for error in field.errors %}<p class="flex items-start gap-1.5 text-sm text-danger-600">{% icon "exclamation-circle" "mt-px size-4 shrink-0" %}<span>{{ error }}</span></p>{% endfor %}</div>{% endif %}
  {% if field.use_fieldset %}</fieldset>{% endif %}
</div>
{% endif %}
{% endwith %}
```

  Check Django 6's `BoundField.build_widget_attrs` for the exact `aria-describedby` ids before finalizing; match them. `optional` uses `yesno` to avoid a custom filter; if that reads poorly, add a `field_is_optional` filter in `apps/core/templatetags/forms_extras.py` instead. Checkbox styling: add to the components layer `.field input[type="checkbox"], .field input[type="radio"] { @apply size-5 shrink-0 accent-primary-600; }`.

  `forms/form.html`:

```django
{% if form.non_field_errors %}<div class="mb-6">{% include "components/_alert.html" with tone="danger" items=form.non_field_errors %}</div>{% endif %}
{% for field in form.hidden_fields %}{{ field }}{% endfor %}
<div class="space-y-6">{% for field in form.visible_fields %}{{ field.as_field_group }}{% endfor %}</div>
```

- [x] **Step 4: Run** `npm run build:css && pytest -q` — PASS.

### Task 5: Forms adopt the renderer

**Files:**
- Modify: `apps/accounts/forms.py`, `apps/reports/forms.py`
- Modify: `templates/accounts/{login_request,login_verify,login_password,login_setup_access_code,change_password,profile_setup}.html`, `templates/reports/report_form.html`
- Modify: `apps/core/tests/test_design_tokens.py` (widget-class guard)
- Tests: existing `apps/accounts/tests/test_views.py`, `test_forms.py`, `apps/reports/tests/test_admin_views.py`

- [x] **Step 1: Write the failing guard** in `test_design_tokens.py`: for each `apps/*/forms.py`, find every `"class": "…"` and every module constant named `*_CLASS*`; fail when the value contains `border`, `rounded` or a `px-`/`py-` utility.
- [x] **Step 2: Run** — FAIL (accounts and reports forms).
- [x] **Step 3: Implement.**
  - Delete `_TEXT_CLASSES`, `_SELECT_CLASSES`, `_DATE_SELECT_CLASSES`, `INPUT_CLASS`; strip `class` from every widget `attrs`, keeping only `text-center text-2xl tracking-widest` (OTP code, setup access code) and `uppercase tracking-widest` (reference code) as extras.
  - Drop the `"placeholder": "Opcional"` attrs: the label says it now.
  - `ProfileActivationForm.__init__`: `self.fields["date_of_birth"].shown_as_required = True`.
  - Align form labels with the copy each template prints today (e.g. `login_request` prints *Correo electrónico*), so no visible copy changes: read each template's hand-written `<label>` and set the form field's `label` to it.
  - Each template: replace the non-field-error box and the hand-written field blocks with `{{ form }}`, keeping the submit button (now `btn btn-primary w-full`) and any help paragraph that sat outside a field (move it into `help_text` when it describes one field). `profile_setup.html` renders its fields in the order the template uses today; use `{{ form }}` if the form's declared order matches, else a list of `{{ form.x.as_field_group }}` lines.
  - `report_form.html`: the grid keeps its layout, each cell becomes `{{ field.as_field_group }}`; signatory rows likewise.
- [x] **Step 4: Run** `npm run build:css && pytest -q` — PASS. Fix any view test that asserted old markup by asserting the behavior (field present, error text present) instead.

### Task 6: Buttons, focus and the busy state everywhere

**Files:**
- Create: `static/ts/busy_submit.ts`
- Modify: every template with a hand-rolled button or a `focus:ring` on an `<a>`/`<button>` (from the inventory: accounts/*, base_app, core/company_dashboard, company_list, company_results, employee_list, employee_survey_list, employee_detail, reports/report_detail, report_form, report_list, surveys/survey_detail, the four survey modals, survey_submitted, _palette_switch)
- Modify: `apps/core/tests/test_design_tokens.py` (two guards)

- [x] **Step 1: Write the failing guards:**
  - `HANDMADE_BUTTON`: for each `<a` or `<button` tag's `class` value, fail when it holds an unprefixed `bg-(primary|danger|success)-600` and a `hover:bg-` on the same scale, and no `btn` token.
  - `CLICK_RING`: fail when an `<a` or `<button` tag's `class` holds `focus:ring` or `focus:outline-none`.
- [x] **Step 2: Run** — FAIL with the inventory list.
- [x] **Step 3: Implement.** Map each button to a variant: the page's main submit → `btn btn-primary`; Cancelar/Ver/Descargar/filter openers → `btn btn-secondary`; small inline actions (*Limpiar*, sort toggles' outer controls, modal close) → `btn btn-text`; *Despublicar*, *Eliminar* → `btn btn-danger`. Layout utilities (`w-full`, `sm:w-auto`, `flex-1`) stay. Remove every `focus:outline-none focus:ring-*` from links and buttons; the base focus rule draws the ring. Survey answer inputs (`surveys/_question.html`) are not links or buttons and are not touched. The login page's two option cards become `card` links with `hover:border-…` kept. `busy_submit.ts`:

```ts
/**
 * Marks a form's submitter busy so a second tap does not send it twice.
 * Applies to forms carrying `data-loading`. The busy state is cleared on
 * `pageshow`, so a page restored from the back/forward cache is usable.
 */
function markBusy(event: SubmitEvent): void {
  const form = event.target as HTMLFormElement;
  if (!form.matches("form[data-loading]")) return;
  const button = event.submitter as HTMLButtonElement | null;
  if (!button) return;
  if (button.getAttribute("aria-busy") === "true") {
    event.preventDefault();
    return;
  }
  button.setAttribute("aria-busy", "true");
}

function clearBusy(): void {
  document.querySelectorAll('[aria-busy="true"]').forEach((el) => el.removeAttribute("aria-busy"));
}

document.addEventListener("submit", markBusy);
window.addEventListener("pageshow", clearBusy);
```

  Load it once from `base.html` with `defer`. Add `data-loading` to: the login request form, the report publish/unpublish forms, the report form.
- [x] **Step 4: Run** `npm run build:js && npm run build:css && pytest -q` — PASS.

### Task 7: Cards, pills and icons adopted

**Files:**
- Modify: templates with `rounded-2xl … border … bg-white` cards (inventory: 30 files), `base_centered.html`, status pills (the `PILL` matches), `apps/core/templatetags/valuation_extras.py` (`_MARKER` → `pill pill-marker`), templates with hand-drawn icon SVGs (survey modals, `survey_submitted`, `company_dashboard`, `employee_list`, `employee_detail`, `results/_dominios_summary`)
- Modify: `apps/core/tests/test_design_tokens.py` (`test_status_pills_carry_the_squircle_marker` accepts `pill-marker`), `templates/icons/` (new icons)

- [x] **Step 1: Update the tests first:** status pills must carry `pill pill-marker`; a new guard fails a white `rounded-2xl` box with a `border-neutral-200` (the old card) anywhere in `templates/`; `valuation_extras` tests expect `pill` and `pill-marker` in `ndr_badge`'s output.
- [x] **Step 2: Run** — FAIL.
- [x] **Step 3: Implement.** Swap `rounded-2xl border border-neutral-200 bg-white shadow-sm` (any order) for `card`, keeping padding and layout utilities; `shadow-md` cards become `card` too. Status pills become `pill pill-marker` plus their tone. `ndr_badge` returns its tone + `pill pill-marker` (+ the level's `before:bg-…` override for the tinted tier). Answer pills, filter pills and *Tú* become `pill` without the marker. For each hand-drawn icon, find the Heroicon that draws the same thing, add its file to `templates/icons/`, and replace the inline `<svg>` with `{% icon %}`, keeping size and color classes.
- [x] **Step 4: Run** `npm run build:css && pytest -q` — PASS.

### Task 8: The styleguide

**Files:**
- Create: `apps/core/styleguide.py`, `templates/core/styleguide.html`
- Modify: `apps/core/views.py` (`StyleguideView`), `apps/core/urls.py` (`path("estilos/", …, name="styleguide")`)
- Test: `apps/core/tests/test_styleguide.py`

- [x] **Step 1: Write the failing tests:** `DEBUG=False`: anonymous → 404 (not a login redirect), employee → 404, Admins member → 200; `DEBUG=True` anonymous → 200. The 200 page contains every component class name (`btn-primary`, `btn-danger`, `btn-sm`, `pill-marker`, `card`), `aria-busy="true"`, one `data-alert` per tone, `(opcional)`, an `aria-invalid="true"`, and the name of every file in `templates/icons/`.
- [x] **Step 2: Run** — FAIL.
- [x] **Step 3: Implement.** `styleguide.py`: `DemoForm` (Nombre(s) with help, Apellido materno optional, Sexo select, Fecha de nacimiento `SelectDateWidget` with `shown_as_required`, *Acepto el aviso de privacidad* checkbox) and `palette_swatches(slug)` → list of `(scale, [(step, hex)])` from `brand.palette_hex`, plus the status steps parsed from `main.css`. `StyleguideView(TemplateView)`: `dispatch` raises `Http404` unless `brand.can_switch_palette(request.user)`; context: `form=DemoForm()`, `invalid=DemoForm(data={})` (validated), `swatches`, `icons=sorted(stem of templates/icons/*.svg)`, `ndr_levels` (the five levels for `ndr_badge`). The template walks the eight sections from the brief; it is one column, rows `flex flex-wrap gap-3`.
- [x] **Step 4: Run** `npm run build:css && pytest -q` — PASS.

### Task 9: Documentation

**Files:**
- Modify: `docs/platform/design-system.md`, `.claude/CLAUDE.md`, `apps/core/CLAUDE.md`, `apps/reports/CLAUDE.md` (messages partial moved)

- [x] **Step 1:** Rewrite `design-system.md` in present tense: Status line names the new files; Scope gains **Components** (atoms, the renderer and field shape, alerts, messages, icons, the styleguide); Usage rules gain the button-variant, field and alert rules; Out of scope keeps 2b's list and drops *An icon set*; Phone shape adds the styleguide; Key decisions add the seven from the brief; Enforcement adds the new guards. No migration commentary.
- [x] **Step 2:** `.claude/CLAUDE.md` Design-system bullet: use `btn`/`control`/`card`/`pill` and `components/_alert.html`, forms render through the project renderer (no widget classes), `{% icon %}` for icons; a pattern repeated in three or more places with no component gets one proposed before markup is copied.
- [x] **Step 3:** `apps/core/CLAUDE.md`: the renderer, icon tag, styleguide view. `apps/reports/CLAUDE.md`: drop any mention of its own messages partial.
- [x] **Step 4:** `pytest -q && ruff check . && ruff format --check .` — PASS.
