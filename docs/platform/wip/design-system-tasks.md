# Design system — about page in the split card

## What changes

**What.** The about page (`/que-es-sofia/`, `templates/core/about.html`) moves into the account
screens' split card, with the columns swapped:

- **Left column:** the logo, centered and shown from `lg`, then the three paragraphs, then
  *Ir al inicio* as `btn btn-primary btn-glow`.
- **Right column:** an `auth-panel` holding the logo and the page's `h1` (*¿Qué es
  {{ brand.short_name }}?*) at `text-xl`, rising to `text-2xl` at `lg` and `text-3xl` at `xl`,
  with `brand.meaning` under it.
- **On a phone:** the panel is the top band.

`base_centered.html` loses its last user and is deleted. `about.html` extends `base.html`
directly. The card frame (white, radius, ring, tinted shadow, grid) becomes a component,
`.auth-card`, and `base_auth.html` uses it too.

**Why.** The user asked for the about page to match the sign-in screens. The design was approved
in <https://claude.ai/artifact/TXUc15ZHC924W9JEMuvAis>, with these choices: option A (fold the
layout into the page), the larger panel title, and the button. The logo above the paragraphs was
added at sign-off.

**Live doc sections this makes wrong** (`docs/platform/design-system.md`):

- *Messages*: names `base_centered.html`.
- *Page header*: "the about page draw[s] their title inside a card".
- *Account screens*: describes the card shell inline, with no `.auth-card`, and the panel's
  display text only as `brand.meaning`.
- *Phone shape*: says nothing about the about page.

Also affected: `apps/core/CLAUDE.md` (lines ~67 and ~139) and the comment in
`templates/_messages.html`.

**ADRs.** None touched.

---

# About Page Split-Card Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Render the about page in the split card, and remove `base_centered.html`.

**Architecture:** One CSS component (`.auth-card`) is shared by `base_auth.html` and
`core/about.html`. The about page owns its whole body and reuses `auth-backdrop`, `auth-panel`
and `btn-glow`.

**Tech Stack:** Django templates, Tailwind v4, pytest.

**Spec:** the brief above, and the artifact.

## Global Constraints

- Color comes only from palette scales or `var(--brand-*)`. No typed product name, meaning or
  logo.
- Layout is mobile-first. There is one `h1` per page. No inline style or handlers.
- Run `npm run build:css` after a template or CSS change.
- Each task stops at a green suite with an uncommitted diff. Never commit without asking.

## Review Focus

1. **A message on the about page.** It still shows, in the text column. Test in Task 2.
2. **Heading order.** The panel is first in the markup, so the `h1` comes before the
   paragraphs. Test in Task 2.
3. **Template inheritance.** Nothing still extends the deleted layout. Rendering it would fail, so the page tests cover this.
4. **Sign-in screens unchanged.** After the extraction they render the same structure; the
   existing auth-layout tests cover this (Task 1).

---

### Task 1: Extract the card frame to `.auth-card`

**Files:** `static/css/main.css`, `templates/base_auth.html`, `apps/core/tests/test_components_css.py`

- [x] Add `"auth-card"` to `COMPONENTS` in `test_components_css.py`. Run it and expect a FAIL.
- [x] Add this to `main.css`, next to `.auth-panel`:

```css
  /* The white split card of the account screens and the about page: one
     column on a phone, two from `lg` (the page sets the column split). */
  .auth-card {
    @apply grid w-full grid-cols-1 rounded-[20px] bg-white p-2 lg:rounded-3xl lg:p-3;
    box-shadow:
      0 0 0 1px var(--brand-neutral-200),
      0 30px 60px -24px color-mix(in srgb, var(--brand-primary-900) 35%, transparent);
  }
```

- [x] In `base_auth.html`, replace the card `div`'s frame classes
  (`grid w-full grid-cols-1 rounded-[20px] bg-white p-2 shadow-[…] lg:rounded-3xl lg:p-3`)
  with `auth-card`. Keep the variant classes (`max-w-*`, `lg:grid-cols-*`, `lg:min-h-[620px]`).
- [x] Run `npm run build:css`, then `pytest`. Expect green.

### Task 2: The about page in the split card; delete `base_centered.html`

**Files:** `templates/core/about.html`, delete `templates/base_centered.html`,
`templates/_messages.html` (its comment), and a new test file `apps/core/tests/test_about_page.py`.

- [x] Write the failing tests:

```python
"""The about page in the split card: see docs/platform/design-system.md."""

from pathlib import Path

import pytest
from django.conf import settings
from django.contrib.messages import constants
from django.urls import reverse

from apps.core.tests.test_alerts import _with_message

pytestmark = pytest.mark.django_db
REPO_ROOT = Path(__file__).resolve().parents[3]


def _html(client):
    return client.get(reverse("core:about")).content.decode()


def test_the_about_page_is_a_split_card_with_its_title_in_the_panel(client):
    html = _html(client)
    panel = html.index("auth-panel")
    assert "auth-card" in html
    assert panel < html.index("<h1") < html.index("es una plataforma")
    assert settings.BRAND["meaning"] in html
    assert "lg:order-last" in html


def test_the_about_page_shows_the_logo_in_both_columns(client):
    assert _html(client).count(f'aria-label="Logo {settings.BRAND["name"]}"') == 2


def test_the_about_page_offers_home_as_its_main_action(client):
    html = _html(client)
    assert f'href="{reverse("core:home")}"' in html
    assert "btn-glow" in html and "Ir al inicio" in html


def test_a_message_shows_on_the_about_page(client):
    _with_message(client, "Sesión cerrada", constants.SUCCESS)
    assert "Sesión cerrada" in _html(client)

```

- [x] Run them and expect a FAIL.
- [x] Rewrite `about.html` so it extends `base.html`, following the markup in the artifact's
  spec, with the left column's logo added: `{% include "_logo.html" with
  css_class="mx-auto mb-8 hidden h-10 w-auto text-primary-600 lg:block" %}`. It's hidden on a
  phone, where the band above already shows the logo, the same as the account screens. The
  first paragraph keeps `<strong>{{ brand.name }}</strong>` but drops the bracketed meaning,
  which the panel now shows.
- [x] Delete `templates/base_centered.html`, and fix the comment in `_messages.html`.
- [x] Run `npm run build:css`, then `pytest`. Expect green.

### Task 3: Documentation

- [x] In `design-system.md`, rewrite these sections in the present tense:
  - *Messages*: the layouts that include it are `base_app.html`, `base_auth.html` and the about
    page.
  - *Page header*: the about page's title is in its panel.
  - *Account screens*: describe the `.auth-card` component.
  - Add an **About page** entry next to *Account screens*.
  - *Phone shape*: add the about page.
  - *Enforcement*: add the about-page tests.
  - Styleguide: no change. `.auth-card` is a frame, not a demo-able component; it renders on
    every account screen.
- [x] In `apps/core/CLAUDE.md`, update lines ~67 and ~139.
- [x] Run `pytest`, `ruff check .` and `ruff format --check .`.
