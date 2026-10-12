# Design system — split-card auth layout

## What changes

**What.** Six account screens move from the narrow centered card (`base_centered.html`) to a
new split-card layout, `templates/base_auth.html`. These are the three ways to sign in
(`login_request`, `login_password`, `login_setup_access_code`), the emailed-code check
(`login_verify`), the required password change (`change_password`) and account activation
(`profile_setup`).

- **The card.** A wide white card holds two columns from `lg`. On the left is `.auth-panel`: a
  layered gradient built from the `--brand-*` variables, with a blurred blob and a film grain.
  The logo sits top left and `{{ brand.meaning }}` at the bottom, wrapping naturally. On the
  right are the logo, the page's `h1` and subtitle, `_messages.html`, the form and whatever
  sits below it.
- **On a phone** the panel is a short band above the form, and the logo in the form column is
  hidden.
- **Other ways in.** The three sign-in screens share one *Otras formas de ingresar* block
  (`accounts/_signin_alternatives.html`), which lists the two methods other than the current
  one.
- **Long variant.** `profile_setup` uses it. The card is wider with a 2:3 split, and the panel
  is sticky and one screen tall.
- **Show/hide password.** Every password field the form renderer draws gets a toggle:
  `templates/forms/field.html` renders the button, and the new `static/ts/password_toggle.ts`
  makes it work.
- **Main button.** The primary submit on these screens gets the `.btn-glow` modifier.

**Why.** It's a visual rework the user asked for, based on a reference image. The design was
approved through the proposal artifact <https://claude.ai/artifact/DRmsCArMZuuxZzeGLrAQ5x>. View
logic, forms, URLs and copy stay as they are, apart from the *Otras formas de ingresar* rows
on the password and first-sign-in screens.

**Live doc sections this makes wrong** (`docs/platform/design-system.md`):

- *Messages*: "`base_app.html` and `base_centered.html` include it".
- *Page header*: "the centered screens draw their title inside a card".
- *Error pages*: "the centered card of the login screens". The error pages keep that card, but
  the login screens no longer use it.
- *Phone shape*: "Error pages are the centered login card".
- *Form fields*: nothing about the password toggle yet.
- *Components*: there's no `auth-panel` or `btn-glow` entry.
- *Enforcement*: there's nothing for the toggle or the auth layout.

Also `apps/core/CLAUDE.md` (lines ~67 and ~139).

**ADRs.** No ADR is touched. ADR-0006 (brand palette) holds: the panel reads only palette
variables.

---

# Auth Split-Card Layout Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Move the six account screens onto a split-card `base_auth.html` and give every
password field a show/hide toggle.

**Architecture:** There's one new layout template with blocks for the form column and an
`auth_variant` switch. One CSS component holds the gradient panel, and one include holds the
sign-in alternatives. The toggle is rendered on the server by the shared field template and
made to work by a tiny delegated TS module loaded from `base.html`.

**Tech Stack:** Django 6 templates, Tailwind v4 (`static/css/main.css`), TypeScript (`npm run build:js`), pytest.

**Spec:** the brief above, plus the approved artifact
<https://claude.ai/artifact/DRmsCArMZuuxZzeGLrAQ5x>.

## Global Constraints

- Colors come only from `primary-*`, `accent-*` and `neutral-*` (or `var(--brand-*)` in `main.css`). No Tailwind hue and no hex in templates.
- The product name, meaning and logo are never typed: use `{{ brand.meaning }}` and `{% include "_logo.html" with css_class=… %}`.
- Layout is mobile-first: unprefixed classes describe the phone and `lg:` adds the split. Nothing is wider than 328px unprefixed.
- Every page has exactly one `h1`, and it sits in the form column.
- No inline `style`, no `on*=` handlers, no `focus:ring`/`focus:outline-none` on links or buttons, and no `uppercase`.
- Widget `attrs` carry no styling classes. The toggle's input padding comes from CSS in `main.css`.
- Copy is Spanish in *tú*. Buttons are verbs.
- After a template or CSS change, run `npm run build:css`. After a TS change, run `npm run build:js`. Commit the built output.
- Never commit without asking: each task stops at a green suite with an uncommitted diff.

## Review Focus

1. **Toggle without JS.** If the script doesn't load, the button must not show, and the field still works as a plain password input. The button renders with `hidden`. Test in Task 1.
2. **A password field with an error.** The toggle must sit next to the control, and the error must still follow it with `aria-describedby` intact. Test in Task 1.
3. **Messages on the new layout.** A Django message, such as the one after sign-out, must show in the form column. Test in Task 2 (moves `test_a_message_shows_on_a_centered_page`).
4. **`profile_setup`'s blocked states** (*no empresa*, *no áreas*). The alert renders in place of the form, inside the new layout. Test in Task 3.
5. **Verify page alternatives.** `login_verify` must not offer the other sign-in methods. Test in Task 2.

---

### Task 1: Show/hide password on every password field

**Files:**
- Create: `templates/icons/eye.svg`, `templates/icons/eye-slash.svg` (Heroicons v2 outline 24px)
- Create: `static/ts/password_toggle.ts` → built to `static/js/password_toggle.js`
- Modify: `templates/forms/field.html` (wrap a password control)
- Modify: `templates/base.html` (load the script)
- Modify: `static/css/main.css` (the `.field [data-password-toggle] input` padding)
- Test: `apps/core/tests/test_form_renderer.py`

**Interfaces:**
- Produces: the markup `<div class="relative" data-password-toggle>{{ control }}<button type="button" class="btn btn-text btn-sm absolute …" data-password-toggle-button aria-label="Mostrar contraseña" aria-pressed="false" hidden>{eye}{eye-slash hidden}</button></div>`.

- [x] **Step 1: Write the failing tests** (append to `test_form_renderer.py`)

```python
class PasswordForm(forms.Form):
    password = forms.CharField(label="Contraseña", widget=forms.PasswordInput)

    def clean_password(self):
        raise forms.ValidationError("Revisa tu contraseña.")


def test_a_password_field_gets_a_hidden_show_button():
    html = group(PasswordForm(), "password")
    assert "data-password-toggle" in html
    button = re.search(r"<button[^>]*data-password-toggle-button[^>]*>", html).group(0)
    assert 'type="button"' in button
    assert 'aria-label="Mostrar contraseña"' in button
    assert 'aria-pressed="false"' in button
    assert " hidden" in button  # shown only once the script runs


def test_the_show_button_sits_after_the_control_and_before_errors():
    html = group(PasswordForm(data={"password": "x"}), "password")
    assert html.index("<input") < html.index("data-password-toggle-button")
    assert html.index("data-password-toggle-button") < html.index("Revisa tu contraseña.")
    assert 'aria-describedby="id_password_error"' in html


def test_other_fields_get_no_show_button():
    assert "data-password-toggle" not in group(DemoForm(), "name")


def test_every_page_loads_the_password_toggle(client):
    html = client.get("/cuentas/ingresar/").content.decode()
    assert "js/password_toggle.js" in html
```

- [x] **Step 2: Run them, expect FAIL** — `pytest apps/core/tests/test_form_renderer.py -k "password or show_button" -v`

- [x] **Step 3: Implement.**
  - **Icons.** Download `eye.svg` and `eye-slash.svg` from Heroicons v2 outline into `templates/icons/`, in the same format as `x-mark.svg`.
  - **`field.html`.** Replace the single-control branch `{% else %}{{ field }}{% endif %}` (the non-fieldset one) so that a password widget is wrapped:

```django
{% if field.use_fieldset %}<div class="grid grid-cols-1 gap-3 sm:grid-cols-3">{{ field }}</div>{% elif field.widget_type == "password" %}<div class="relative" data-password-toggle>{{ field }}<button type="button" class="btn btn-text btn-sm absolute top-1/2 right-1 -translate-y-1/2 px-2 text-neutral-500" data-password-toggle-button aria-label="Mostrar contraseña" aria-pressed="false" hidden>{% icon "eye" "size-5" %}{% icon "eye-slash" "hidden size-5" %}</button></div>{% else %}{{ field }}{% endif %}
```

  - **`main.css`** (in the components layer, after the `.field :is(input…)` rule):

```css
  /* Room for the show-password button templates/forms/field.html adds. */
  .field [data-password-toggle] input {
    @apply pr-12;
  }
```

  - **`static/ts/password_toggle.ts`:**

```ts
/**
 * The show/hide button templates/forms/field.html puts beside every password
 * control. The button ships `hidden` so a page without this script never shows
 * a control that does nothing; this reveals it, and a click flips the input
 * between password and text, its pressed state, its label and its icon.
 */
function toggle(input: HTMLInputElement, button: HTMLButtonElement): void {
  const show = input.type === "password";
  input.type = show ? "text" : "password";
  button.setAttribute("aria-pressed", String(show));
  button.setAttribute("aria-label", show ? "Ocultar contraseña" : "Mostrar contraseña");
  const [eye, eyeSlash] = Array.from(button.querySelectorAll("svg"));
  eye?.classList.toggle("hidden", show);
  eyeSlash?.classList.toggle("hidden", !show);
}

document.querySelectorAll<HTMLButtonElement>("[data-password-toggle-button]").forEach((button) => {
  button.hidden = false;
});

document.addEventListener("click", (event) => {
  const button = (event.target as Element).closest<HTMLButtonElement>("[data-password-toggle-button]");
  const input = button?.closest("[data-password-toggle]")?.querySelector("input");
  if (button && input) toggle(input, button);
});
```

  - **`base.html`.** Add `<script src="{% static 'js/password_toggle.js' %}" defer></script>` after `focus_on_load.js`.
  - **Build.** Run `npm run build:js && npm run build:css`.

- [x] **Step 4: Run the tests, expect PASS** — `pytest apps/core/tests/test_form_renderer.py apps/core/tests/test_icons.py apps/core/tests/test_design_tokens.py`

- [x] **Step 5: Run the full suite** (`pytest`). Stop with an uncommitted diff.

---

### Task 2: `base_auth.html`, the panel component and the four sign-in screens

**Files:**
- Create: `templates/base_auth.html`
- Create: `templates/accounts/_signin_alternatives.html`
- Modify: `templates/accounts/login_request.html`, `login_password.html`, `login_setup_access_code.html`, `login_verify.html`
- Modify: `static/css/main.css` (`.auth-backdrop`, `.auth-panel`, `.btn-glow`)
- Test: `apps/accounts/tests/test_auth_layout.py` (new), `apps/core/tests/test_components_css.py`, `apps/core/tests/test_alerts.py`

**Interfaces:**
- Produces, from `base_auth.html`:
  - blocks `title`, `form_header` (the `h1` and subtitle), `form_body` and `form_footer`;
  - the context value `auth_variant`, passed by a view: empty, or `long`;
  - the hooks `data-auth-panel` on the `<aside>`, and `data-auth-variant="{{ variant }}"` on the card.
- Produces, from `_signin_alternatives.html`: it takes `current` (one of `otp`, `password` or `setup`).

- [x] **Step 1: Write the failing tests.** Create `apps/accounts/tests/test_auth_layout.py`:

```python
"""The split-card auth layout (templates/base_auth.html): see docs/platform/design-system.md."""

import pytest
from django.conf import settings
from django.urls import reverse

pytestmark = pytest.mark.django_db

SIGN_IN = {
    "otp": "accounts:request_otp",
    "password": "accounts:password_login",
    "setup": "accounts:setup_access_code_login",
}


def _html(client, name):
    return client.get(reverse(name)).content.decode()


@pytest.mark.parametrize("name", SIGN_IN.values())
def test_a_sign_in_screen_uses_the_split_card(client, name):
    html = _html(client, name)
    assert "data-auth-panel" in html
    assert settings.BRAND["meaning"] in html
    assert "auth-panel" in html and "btn-glow" in html


@pytest.mark.parametrize("current, name", SIGN_IN.items())
def test_a_sign_in_screen_offers_the_other_two_ways_in(client, current, name):
    html = _html(client, name)
    assert "Otras formas de ingresar" in html
    others = [n for c, n in SIGN_IN.items() if c != current]
    for other in others:
        assert f'href="{reverse(other)}"' in html
    assert f'href="{reverse(name)}"' not in html


def test_the_verify_screen_uses_the_split_card_without_alternatives(client):
    session = client.session
    session["otp_email"] = "ana@empresa.mx"
    session.save()
    html = _html(client, "accounts:verify_otp")
    assert "data-auth-panel" in html
    assert "Otras formas de ingresar" not in html
    assert "pide otro código" in html
```

  Also make these changes in existing tests:
  - Add `"auth-panel"` and `"btn-glow"` to `COMPONENTS` in `test_components_css.py`.
  - Rename `test_a_message_shows_on_a_centered_page` to `test_a_message_shows_on_a_sign_in_page`. Its body is unchanged.

- [x] **Step 2: Run them, expect FAIL** — `pytest apps/accounts/tests/test_auth_layout.py apps/core/tests/test_components_css.py -v`

- [x] **Step 3: Implement.**

  `static/css/main.css`, in the components layer:

```css
  /* The split-card auth layout (templates/base_auth.html). The page tint and the
     panel read only palette variables, so both repaint with the palette. */
  .auth-backdrop {
    background:
      radial-gradient(60% 50% at 15% 0%, var(--brand-primary-100) 0%, transparent 70%),
      radial-gradient(50% 45% at 100% 100%, var(--brand-accent-100) 0%, transparent 70%),
      var(--brand-neutral-100);
  }
  .auth-panel {
    @apply relative isolate flex flex-col justify-between gap-4 overflow-hidden rounded-[14px] p-5 text-white lg:rounded-2xl lg:p-8 xl:p-10;
    background:
      radial-gradient(90% 70% at 0% 100%, var(--brand-primary-900) 15%, transparent 65%),
      radial-gradient(55% 45% at 88% 8%, var(--brand-accent-300) 0%, transparent 70%),
      radial-gradient(60% 55% at 35% 38%, var(--brand-primary-500) 0%, transparent 72%),
      radial-gradient(45% 40% at 95% 72%, var(--brand-accent-500) 0%, transparent 70%),
      linear-gradient(165deg, var(--brand-primary-300), var(--brand-primary-800));
  }
  /* The soft blurred shape. */
  .auth-panel::before {
    content: "";
    @apply absolute -z-10 aspect-square w-[70%] rounded-full opacity-70 blur-[60px];
    left: -10%;
    top: 30%;
    background: var(--brand-primary-700);
  }
  /* Film grain: keeps the gradient from banding. */
  .auth-panel::after {
    content: "";
    @apply absolute inset-0 -z-10 opacity-20 mix-blend-overlay;
    background-image: url("data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' width='160' height='160'><filter id='n'><feTurbulence type='fractalNoise' baseFrequency='.9' numOctaves='2' stitchTiles='stitch'/></filter><rect width='100%' height='100%' filter='url(%23n)'/></svg>");
  }
  /* The main action's soft glow, on the auth screens only. */
  .btn-glow {
    box-shadow: 0 10px 22px -12px var(--brand-primary-600);
  }
```

  `templates/base_auth.html`. The variant comes from a context value the view passes, `auth_variant`, the same pattern `container_width` uses, because a template can't read a block's value. `setup_profile` passes `"auth_variant": "long"`:

```django
{% extends "base.html" %}
{% comment %}
The account screens' layout: a white card split into the brand panel and the
form column from `lg`; on a phone the panel is a short band above the form. A
page fills `form_header` (its h1 and subtitle), `form_body` and `form_footer`.
A view passes `auth_variant="long"` for a tall form: a wider card with a
narrower panel that stays in view while the form scrolls.
{% endcomment %}

{% block body_class %}min-h-screen auth-backdrop{% endblock %}

{% block body %}
<main id="main" tabindex="-1" class="flex flex-1 items-center justify-center px-4 py-6 focus:outline-none lg:px-8 lg:py-12">
  <div data-auth-variant="{{ auth_variant|default:"" }}"
       class="grid w-full grid-cols-1 rounded-[20px] bg-white p-2 shadow-[0_0_0_1px_var(--color-neutral-200),0_30px_60px_-24px_color-mix(in_srgb,var(--color-primary-900)_35%,transparent)] lg:rounded-3xl lg:p-3 {% if auth_variant == "long" %}max-w-6xl lg:grid-cols-[2fr_3fr]{% else %}max-w-5xl lg:min-h-[620px] lg:grid-cols-2{% endif %}">

    <aside data-auth-panel aria-label="{{ brand.name }}"
           class="auth-panel{% if auth_variant == "long" %} lg:sticky lg:top-6 lg:h-[calc(100dvh-3rem)] lg:max-h-[760px] lg:self-start{% endif %}">
      {% include "_logo.html" with css_class="h-9 w-auto text-white lg:h-10" %}
      <p class="max-w-[40ch] text-sm font-medium text-white/90 lg:max-w-[18ch] lg:text-2xl lg:font-semibold lg:text-balance lg:text-white{% if auth_variant != "long" %} xl:text-3xl{% endif %}">{{ brand.meaning }}</p>
    </aside>

    <div class="min-w-0 px-4 pt-7 pb-6 lg:flex lg:px-10 lg:py-12 {% if auth_variant == "long" %}lg:items-start{% else %}lg:items-center{% endif %}">
      <div class="mx-auto w-full {% if auth_variant == "long" %}max-w-lg{% else %}max-w-sm{% endif %}">
        {% include "_logo.html" with css_class="mb-5 hidden h-8 w-auto text-primary-600 lg:block" %}
        {% block form_header %}{% endblock %}
        <div class="mt-6">{% include "_messages.html" %}</div>
        <div class="mt-8">{% block form_body %}{% endblock %}</div>
        {% block form_footer %}{% endblock %}
      </div>
    </div>

  </div>
</main>
{% include "_footer.html" %}
{% endblock %}
```

  (Check whether `_messages.html` renders an empty container when there are no messages. If it does, drop the `mt-6` wrapper and give the include's own container the spacing. `test_no_messages_render_no_container` fixes the expected behavior.)

  `templates/accounts/_signin_alternatives.html`:

```django
{% load icons %}
{% comment %}
The other ways to sign in, under each sign-in form. `current` (otp, password,
setup) names the screen it sits on, which is left out.
{% endcomment %}
<div class="mt-8">
  <h2 class="flex items-center gap-3 text-sm font-semibold text-neutral-700 before:h-px before:flex-1 before:bg-neutral-200 after:h-px after:flex-1 after:bg-neutral-200">Otras formas de ingresar</h2>
  <div class="mt-3 space-y-2">
    {% if current != "otp" %}
      <a href="{% url 'accounts:request_otp' %}" class="card card-link group px-4 py-3 shadow-none">
        <span class="grid size-9 shrink-0 place-items-center rounded-lg bg-primary-50 text-primary-700">{% icon "envelope" "size-5" %}</span>
        <span class="min-w-0 flex-1"><span class="block text-sm font-semibold text-neutral-900">Código por correo</span><span class="block text-sm text-neutral-600">Te enviamos un código de 6 dígitos.</span></span>
        {% icon "chevron-right" "size-5 shrink-0 text-neutral-400 transition-colors group-hover:text-primary-600" %}
      </a>
    {% endif %}
    {% if current != "setup" %}
      <a href="{% url 'accounts:setup_access_code_login' %}" class="card card-link group px-4 py-3 shadow-none">
        <span class="grid size-9 shrink-0 place-items-center rounded-lg bg-primary-50 text-primary-700">{% icon "ticket" "size-5" %}</span>
        <span class="min-w-0 flex-1"><span class="block text-sm font-semibold text-neutral-900">Primer ingreso</span><span class="block text-sm text-neutral-600">Tengo un código de acceso de 9 dígitos.</span></span>
        {% icon "chevron-right" "size-5 shrink-0 text-neutral-400 transition-colors group-hover:text-primary-600" %}
      </a>
    {% endif %}
    {% if current != "password" %}
      <a href="{% url 'accounts:password_login' %}" class="card card-link group px-4 py-3 shadow-none">
        <span class="grid size-9 shrink-0 place-items-center rounded-lg bg-primary-50 text-primary-700">{% icon "key" "size-5" %}</span>
        <span class="min-w-0 flex-1"><span class="block text-sm font-semibold text-neutral-900">Iniciar sesión con contraseña</span><span class="block text-sm text-neutral-600">Ya creé mi contraseña.</span></span>
        {% icon "chevron-right" "size-5 shrink-0 text-neutral-400 transition-colors group-hover:text-primary-600" %}
      </a>
    {% endif %}
  </div>
</div>
```

  Download the Heroicons `envelope.svg`, `ticket.svg` and `key.svg` into `templates/icons/`.

  **Each sign-in template** now extends `base_auth.html`. Its `card_header` content goes in
  `form_header`, minus the `brand_line` block. `card_body` becomes `form_body`, with the form's
  `mt-8` dropped because the layout supplies it and `btn-glow` added to the submit.
  `form_footer` includes `accounts/_signin_alternatives.html` with `current="otp"`,
  `"password"` or `"setup"`. `login_verify.html` keeps its two existing `<p>` links in
  `form_footer`, with no alternatives.

  **Build.** Run `npm run build:css`.

- [x] **Step 4: Run, expect PASS** — `pytest apps/accounts apps/core/tests/test_components_css.py apps/core/tests/test_alerts.py apps/core/tests/test_pages.py apps/core/tests/test_design_tokens.py apps/core/tests/test_responsive.py apps/core/tests/test_icons.py`

- [x] **Step 5: Run the full suite.** Stop with an uncommitted diff.

---

### Task 3: `change_password` and `profile_setup` on the auth layout (long variant)

**Files:**
- Modify: `templates/accounts/change_password.html`, `templates/accounts/profile_setup.html`
- Modify: `apps/accounts/views.py` (`setup_profile`: add `"auth_variant": "long"` to each render context)
- Test: `apps/accounts/tests/test_auth_layout.py`

- [x] **Step 1: Write the failing tests** (append):

```python
def test_the_password_change_uses_the_split_card(client, make_user):
    user = make_user(must_change_password=True)
    client.force_login(user)
    html = client.get(reverse("accounts:change_password")).content.decode()
    assert "data-auth-panel" in html
    assert html.count("data-password-toggle-button") == 2
    assert 'data-auth-variant=""' in html


def test_activation_uses_the_long_split_card(client, make_user):
    # Use the same fixtures test_views.py's setup_profile tests use for a
    # non-admin user with a company and areas.
    ...
```

  Write the activation tests with the fixtures from the existing `setup_profile` tests in
  `apps/accounts/tests/test_views.py`. Copy their setup for:

  1. a user with a company and areas: assert `data-auth-variant="long"`, `data-auth-panel` and
     `Activar cuenta`;
  2. a company with no áreas: assert `data-auth-variant="long"` and the *no áreas* alert copy
     (`"todavía no puedes activar tu cuenta"`).

  Check `make_user`'s signature in `conftest.py` for `must_change_password` before using it.

- [x] **Step 2: Run, expect FAIL.**

- [x] **Step 3: Implement.**
  - **`change_password.html`.** It extends `base_auth.html`. `form_header` holds the `h1`, and
    the subtitle moves from `text-neutral-500` to `text-neutral-600`, matching the other
    screens. `form_body` holds the form, with `btn-glow` on the submit. There's no footer.
  - **`profile_setup.html`.** It extends `base_auth.html` and drops the `container_width` block
    and its comment. `form_body` holds the existing alert/form branches unchanged, with
    `btn-glow` on the submit.
  - **`setup_profile`.** Add `"auth_variant": "long"` to every `render(...)` context in the
    view (lines ~294–344). There are five calls. One local dict, `ctx = {"auth_variant": "long"}`,
    is merged into each, matching how the view builds its contexts today.
  - **Build.** Run `npm run build:css`.

- [x] **Step 4: Run, expect PASS.** Run the full suite. Stop with an uncommitted diff.

---

### Task 4: Documentation

**Files:**
- Modify: `docs/platform/design-system.md`
- Modify: `apps/core/CLAUDE.md`

- [x] **Step 1.** Rewrite the affected `design-system.md` sections in present tense, with no
  migration commentary:
  - Add an **Auth layout** entry under the components:
    - `base_auth.html`'s blocks and the `auth_variant` context value;
    - `.auth-panel` (a gradient from palette variables, a blob and grain; the logo, then
      `brand.meaning`);
    - `.auth-backdrop` and `.btn-glow`;
    - the form-column logo, hidden below `lg`;
    - `_signin_alternatives.html`;
    - the long variant, with its sticky panel.
  - **Form fields:** add the password toggle (server-rendered and `hidden`, revealed by
    `password_toggle.ts`).
  - **Messages:** say it's included by `base_app.html`, `base_centered.html` (the about page)
    and `base_auth.html`.
  - **Page header:** "the account screens draw their title in the form column".
  - **Error pages:** they extend `base_error.html`'s centered card, with no reference to the
    login screens.
  - **Phone shape:** add a paragraph on the account screens (the band, then the form).
  - **Enforcement:** add the auth-layout and toggle tests, and note that the toggle script is
    checked in the browser.
  - **Status:** add `templates/base_auth.html` and `static/ts/password_toggle.ts`.
- [x] **Step 2.** Update `apps/core/CLAUDE.md` lines ~67 and ~139 to name `base_auth.html`.
- [x] **Step 3.** Run `pytest`, `ruff check .` and `ruff format --check .`. Stop with an
  uncommitted diff.
