# Design system — foundation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking. **No commits** — per CLAUDE.md, the work stops at a green suite and is handed back uncommitted.

**Goal:** One brand config, Figtree, palette tokens and two live-switchable palettes (Petróleo, Pizarra) applied across every template and the report.

**Architecture:** `static/css/main.css` maps Tailwind `primary/accent/neutral` scales onto `--brand-*` CSS variables that each `[data-palette]` block fills. A context processor in `apps/core` exposes `brand`, the active `palette` (from the `paleta` cookie) and whether to show the switch; `base.html` renders `<html lang="es" data-palette="…">`. Templates swap `indigo-*`→`primary-*`, `gray-*`→`neutral-*`.

**Tech Stack:** Django 6 templates, Tailwind v4 CLI (`@theme inline`), WeasyPrint, pytest.

**Spec:** `docs/platform/design-system.md`

## Global Constraints

- Palette slugs `petrol` (label *Petróleo*) and `slate` (label *Pizarra*); default `petrol`; cookie name `paleta`.
- Switch visible to the Admins group (and superusers) and to everyone when `DEBUG` is on.
- Tokens: `primary-50…900`, `accent-100,200,300,500,700`, `neutral-50…900`.
- Fixed, outside palettes: the NDR risk ramp (`apps/core/templatetags/valuation_extras.py`) and chart categorical colors (`apps/core/templatetags/charts.py`); success `#2F7D4F`, warning text `#8A5A12`, danger `#B3423A`.
- `neutral-500` is the lightest step for text. All user-facing copy Spanish.
- Figtree from `static/fonts/figtree/*.ttf`; report keeps Source Serif 4 for prose.
- Final step of any template/static change: `npm run build:css`.

## Review Focus

1. A tampered or stale `paleta` cookie (`paleta=<script>`, `paleta=durazno`) → default palette, never echoed raw into `data-palette`.
2. The switch's `next` redirect pointing off-site (`next=https://evil.example`) → redirect home instead.
3. Pages rendered without a request (PDF via `render_to_string`) → still get a valid `data-palette` (default when not passed).
4. A non-admin, non-DEBUG visitor → no switch markup at all.
5. The survey page at 360px → the switch must not overlap the fixed phone bar (survey overrides the block with nothing).

---

### Task 1: Brand config, context processor, palette switch, logo

**Files:**
- Modify: `config/settings.py` (BRAND, BRAND_PALETTES, BRAND_PALETTE_DEFAULT, context processor)
- Create: `apps/core/brand.py` (`active_palette(request) -> str`, `can_switch_palette(user) -> bool`)
- Create: `apps/core/context_processors.py` (`brand(request) -> dict`)
- Create: `apps/core/templatetags/brand.py` (`{% brand_logo css_class %}`)
- Modify: `apps/core/views.py` (`PaletteSwitchView`), `apps/core/urls.py` (`paleta/`, name `palette_switch`)
- Create: `templates/_palette_switch.html`
- Modify: `static/img/logo.svg` (clean SVG, `fill="currentColor"`)
- Modify: `templates/base.html`, `base_app.html`, `base_centered.html`, `_footer.html`, `core/about.html`, `accounts/login_request.html`, every `{% block title %}` naming SOFIA-S, `templates/surveys/survey_detail.html` (empty `palette_switch` block), `config/urls.py`, `apps/accounts/admin.py`
- Test: `apps/core/tests/test_brand.py`

**Interfaces:**
- Produces: context vars `brand` (dict: name, short_name, meaning, logo), `palette` (slug), `palettes` (tuple of `(slug, label)`), `show_palette_switch` (lazy bool). `apps.core.brand.active_palette(request)`.

- [ ] **Step 1: Write failing tests** (`apps/core/tests/test_brand.py`)

```python
import pytest
from django.test import RequestFactory, override_settings

from apps.core.brand import active_palette

pytestmark = pytest.mark.django_db
RF = RequestFactory()


def _req(cookie=None):
    r = RF.get("/")
    if cookie is not None:
        r.COOKIES["paleta"] = cookie
    return r


def test_no_cookie_gives_default():
    assert active_palette(_req()) == "petrol"


def test_known_cookie_is_used():
    assert active_palette(_req("slate")) == "slate"


@pytest.mark.parametrize("bad", ["durazno", "<script>", ""])
def test_unknown_cookie_falls_back(bad):
    assert active_palette(_req(bad)) == "petrol"


def test_none_request_gives_default():
    assert active_palette(None) == "petrol"


def test_page_is_spanish_and_painted(client):
    html = client.get("/que-es-sofia/").content.decode()
    assert '<html lang="es" data-palette="petrol">' in html


def test_cookie_repaints_page(client):
    client.cookies["paleta"] = "slate"
    html = client.get("/que-es-sofia/").content.decode()
    assert 'data-palette="slate"' in html


@override_settings(DEBUG=False)
def test_switch_hidden_for_non_admin(client, make_user, bootstrap_groups):
    user = make_user(email="e@x.mx")
    user.groups.add(bootstrap_groups["Employees"])
    client.force_login(user)
    assert "data-palette-switch" not in client.get("/que-es-sofia/").content.decode()


@override_settings(DEBUG=False)
def test_switch_shown_for_admin(client, make_user, bootstrap_groups):
    user = make_user(email="a@x.mx")
    user.groups.add(bootstrap_groups["Admins"])
    client.force_login(user)
    html = client.get("/que-es-sofia/").content.decode()
    assert "data-palette-switch" in html
    assert "Petróleo" in html and "Pizarra" in html


@override_settings(DEBUG=True)
def test_switch_shown_to_anyone_in_debug(client):
    assert "data-palette-switch" in client.get("/que-es-sofia/").content.decode()


def test_switch_view_sets_cookie_and_redirects(client):
    r = client.post("/paleta/", {"paleta": "slate", "next": "/que-es-sofia/"})
    assert r.status_code == 302 and r["Location"] == "/que-es-sofia/"
    assert r.cookies["paleta"].value == "slate"


def test_switch_view_rejects_offsite_next_and_bad_slug(client):
    r = client.post("/paleta/", {"paleta": "durazno", "next": "https://evil.example/"})
    assert r["Location"] == "/"
    assert "paleta" not in r.cookies


def test_logo_partial_inlines_current_color_svg(client):
    html = client.get("/que-es-sofia/").content.decode()
    assert 'fill="currentColor"' in html
    assert "<?xml" not in html
```

(The about page is public — `TemplateView` without login — so it is the cheapest page that renders `base.html`.)

- [ ] **Step 2: Run** `pytest apps/core/tests/test_brand.py` → FAIL (`apps.core.brand` missing).

- [ ] **Step 3: Settings**

```python
# Brand: name, logo and palettes are defined once. See docs/platform/design-system.md.
BRAND = {
    "name": "SOFIA-S",
    "short_name": "SOFIA",
    "meaning": "Sistema de Obtención, Filtrado e Inteligencia Analítica de Sondeos",
    "logo": "img/logo.svg",
}
BRAND_PALETTES = (("petrol", "Petróleo"), ("slate", "Pizarra"))
BRAND_PALETTE_DEFAULT = "petrol"
```
Add `"apps.core.context_processors.brand"` to `TEMPLATES[0]["OPTIONS"]["context_processors"]`.

- [ ] **Step 4: `apps/core/brand.py`**

```python
"""Brand and palette lookups shared by the context processor, the switch view and the PDF."""

from django.conf import settings

COOKIE = "paleta"


def palette_slugs() -> set[str]:
    return {slug for slug, _ in settings.BRAND_PALETTES}


def active_palette(request) -> str:
    """The palette a request asked for by cookie, or the default when it names none we have."""
    chosen = request.COOKIES.get(COOKIE) if request is not None else None
    return chosen if chosen in palette_slugs() else settings.BRAND_PALETTE_DEFAULT


def can_switch_palette(user) -> bool:
    if settings.DEBUG:
        return True
    if not user.is_authenticated:
        return False
    return user.is_superuser or user.groups.filter(name="Admins").exists()
```

- [ ] **Step 5: `apps/core/context_processors.py`**

```python
from django.conf import settings
from django.utils.functional import SimpleLazyObject

from apps.core.brand import active_palette, can_switch_palette


def brand(request):
    return {
        "brand": settings.BRAND,
        "palette": active_palette(request),
        "palettes": settings.BRAND_PALETTES,
        # Lazy: only base.html asks, and a fragment response must not pay a group query.
        "show_palette_switch": SimpleLazyObject(lambda: can_switch_palette(request.user)),
    }
```
Note: `SimpleLazyObject` wrapping a bool is truthy-safe in `{% if %}` (proxies `__bool__`).

- [ ] **Step 6: Switch view + URL**

```python
class PaletteSwitchView(View):
    """Remembers the palette a visitor picked. Temporary: removed when the client chooses."""

    def post(self, request):
        target = request.POST.get("next", "")
        if not url_has_allowed_host_and_scheme(target, {request.get_host()}, request.is_secure()):
            target = "/"
        response = redirect(target)
        chosen = request.POST.get("paleta")
        if chosen in palette_slugs():
            response.set_cookie(COOKIE, chosen, max_age=60 * 60 * 24 * 365, samesite="Lax")
        return response
```
`path("paleta/", views.PaletteSwitchView.as_view(), name="palette_switch")`.

- [ ] **Step 7: Logo.** Rewrite `static/img/logo.svg` to `<svg xmlns="http://www.w3.org/2000/svg" viewBox="38.5 45.4 154.7 195.5"><path fill="currentColor" d="…same path…"/></svg>`. `apps/core/templatetags/brand.py`:

```python
"""`{% brand_logo "h-8 w-auto" %}` — the only place the logo is drawn, inlined so it takes currentColor."""

from functools import lru_cache

from django import template
from django.conf import settings
from django.contrib.staticfiles import finders
from django.utils.html import format_html
from django.utils.safestring import mark_safe

register = template.Library()


@lru_cache(maxsize=4)
def _svg(path: str) -> str:
    with open(finders.find(path), encoding="utf-8") as fh:
        return fh.read().strip()


@register.simple_tag
def brand_logo(css_class=""):
    svg = _svg(settings.BRAND["logo"])
    attrs = format_html(' class="{}" role="img" aria-label="{}"', css_class, settings.BRAND["name"])
    return mark_safe(svg.replace("<svg", "<svg" + attrs, 1))
```
`templates/_logo.html`: `{% load brand %}{% brand_logo css_class %}` — callers use `{% include "_logo.html" with css_class="h-8 w-auto text-primary-700" %}`.

- [ ] **Step 8: Templates.** `base.html`: `<html lang="es" data-palette="{{ palette }}">`, title default `{{ brand.name }}`, favicon `{% static brand.logo %}`, before `</body>`: `{% block palette_switch %}{% if show_palette_switch %}{% include "_palette_switch.html" %}{% endif %}{% endblock %}`. `survey_detail.html`: `{% block palette_switch %}{% endblock %}`. Replace the `<img>` logos in `base_app.html`, `base_centered.html`, `about.html` with `_logo.html`; every `SOFIA-S` in titles/copy → `{{ brand.name }}`; `¿Qué es SOFIA?` → `¿Qué es {{ brand.short_name }}?`; about's acronym line → `<strong>{{ brand.name }}</strong> ({{ brand.meaning }})`. `config/urls.py` and `apps/accounts/admin.py` read `settings.BRAND["name"]`.

`templates/_palette_switch.html`:
```django
{% comment %}
Temporary: lets an administrator compare the candidate palettes on the real
pages. Bottom-left, because back-to-top owns bottom-right. Removed with the
losing palette — see docs/platform/design-system.md.
{% endcomment %}
<form method="post" action="{% url 'core:palette_switch' %}" data-palette-switch
      class="fixed bottom-[max(1rem,env(safe-area-inset-bottom))] left-4 z-30 flex items-center gap-1 rounded-full border border-neutral-300 bg-white p-1 text-sm shadow-sm print:hidden">
  {% csrf_token %}
  <input type="hidden" name="next" value="{{ request.get_full_path }}">
  <span class="px-2 text-neutral-600">Paleta</span>
  {% for slug, label in palettes %}
    <button type="submit" name="paleta" value="{{ slug }}"
            aria-pressed="{% if slug == palette %}true{% else %}false{% endif %}"
            class="rounded-full px-3 py-1 font-medium {% if slug == palette %}bg-primary-600 text-white{% else %}text-neutral-700 hover:bg-neutral-100{% endif %} focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-primary-500">{{ label }}</button>
  {% endfor %}
</form>
```

- [ ] **Step 9: Run** `pytest apps/core/tests/test_brand.py` → PASS; then `pytest` → whole suite green (fix any test that asserted a literal `SOFIA-S` title or `lang="en"`).

### Task 2: Tokens, fonts and the contrast test

**Files:**
- Modify: `static/css/main.css`
- Test: `apps/core/tests/test_design_tokens.py`

**Interfaces:**
- Produces: utilities `*-primary-{50..900}`, `*-accent-{100,200,300,500,700}`, `*-neutral-{50..900}`, `font-sans` = Figtree. CSS variables `--brand-primary-N`, `--brand-accent-N`, `--brand-neutral-N` (report.css reads these).

- [ ] **Step 1: Failing contrast test**

```python
"""Palette guarantees: see docs/platform/design-system.md (Enforcement)."""

import re
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[3]
MAIN_CSS = (REPO_ROOT / "static/css/main.css").read_text()
PALETTES = ("petrol", "slate")
WHITE = "#FFFFFF"

# (use, foreground token, background token, minimum ratio)
PAIRS = [
    ("body text", "neutral-800", "neutral-50", 4.5),
    ("secondary text", "neutral-600", WHITE, 4.5),
    ("secondary text on fill", "neutral-600", "neutral-100", 4.5),
    ("lightest text", "neutral-500", WHITE, 4.5),
    ("primary button", WHITE, "primary-600", 4.5),
    ("primary hover", WHITE, "primary-700", 4.5),
    ("link", "primary-600", WHITE, 4.5),
    ("link on page", "primary-600", "neutral-50", 4.5),
    ("active / info", "primary-700", "primary-50", 4.5),
    ("accent chip", "primary-900", "accent-200", 4.5),
    ("accent label", "accent-700", "accent-100", 4.5),
    ("input border", "neutral-400", WHITE, 3),
    ("focus ring", "primary-500", WHITE, 3),
    ("primary chart mark", "primary-600", "neutral-100", 3),
]


def _block(slug):
    m = re.search(r'\[data-palette="%s"\][^{]*\{([^}]*)\}' % slug, MAIN_CSS)
    assert m, f"no [data-palette={slug}] block in main.css"
    return dict(re.findall(r"--brand-([a-z]+-\d+):\s*(#[0-9A-Fa-f]{6})", m.group(1)))


def _lum(hex_):
    rgb = [int(hex_[i : i + 2], 16) / 255 for i in (1, 3, 5)]
    lin = [c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4 for c in rgb]
    return 0.2126 * lin[0] + 0.7152 * lin[1] + 0.0722 * lin[2]


def _ratio(a, b):
    hi, lo = sorted((_lum(a), _lum(b)), reverse=True)
    return (hi + 0.05) / (lo + 0.05)


@pytest.mark.parametrize("slug", PALETTES)
def test_every_declared_pair_meets_wcag_aa(slug):
    tokens = _block(slug)
    failures = []
    for use, fg, bg, minimum in PAIRS:
        f = fg if fg.startswith("#") else tokens[fg]
        b = bg if bg.startswith("#") else tokens[bg]
        if _ratio(f, b) < minimum:
            failures.append(f"{use}: {fg} on {bg} = {_ratio(f, b):.2f} < {minimum}")
    assert not failures, "\n".join(failures)


def test_palettes_declare_the_same_tokens():
    assert _block("petrol").keys() == _block("slate").keys()
```

- [ ] **Step 2: Run** → FAIL (no palette blocks).

- [ ] **Step 3: main.css additions** (after the `@source` lines):

```css
/* ── Figtree ── Variable TrueType, weights 300–900 (SIL OFL, fonts/figtree/OFL.txt). */
@font-face {
  font-family: "Figtree";
  src: url("../fonts/figtree/Figtree-VariableFont_wght.ttf") format("truetype");
  font-weight: 300 900; font-style: normal; font-display: swap;
}
@font-face {
  font-family: "Figtree";
  src: url("../fonts/figtree/Figtree-Italic-VariableFont_wght.ttf") format("truetype");
  font-weight: 300 900; font-style: italic; font-display: swap;
}

/* ── Tokens ── Templates name these scales, never a Tailwind hue. `inline` makes each
   utility read the variable at use time, so a [data-palette] block repaints the page. */
@theme inline {
  --font-sans: "Figtree", ui-sans-serif, system-ui, sans-serif;
  --color-primary-50: var(--brand-primary-50);  /* … through 900 */
  --color-accent-100: var(--brand-accent-100);  /* 100, 200, 300, 500, 700 */
  --color-neutral-50: var(--brand-neutral-50);  /* … through 900 */
}

/* ── Palettes ── `:root` carries the default so a page without the attribute renders. */
:root, [data-palette="petrol"] { /* Petróleo */
  --brand-primary-50:#EEF5F7; --brand-primary-100:#D4E7EC; --brand-primary-200:#AACFD9; --brand-primary-300:#77B0C0; --brand-primary-400:#458EA3;
  --brand-primary-500:#2B7389; --brand-primary-600:#1F5D71; --brand-primary-700:#1A4C5D; --brand-primary-800:#173E4C; --brand-primary-900:#13323D;
  --brand-accent-100:#E3E8FD; --brand-accent-200:#C9D2FC; --brand-accent-300:#B3C0FB; --brand-accent-500:#6B79D9; --brand-accent-700:#444C97;
  --brand-neutral-50:#F6F8F8; --brand-neutral-100:#EDF1F2; --brand-neutral-200:#DDE3E5; --brand-neutral-300:#C5CED1; --brand-neutral-400:#8A979B;
  --brand-neutral-500:#6B777B; --brand-neutral-600:#525D61; --brand-neutral-700:#3E474A; --brand-neutral-800:#2A3133; --brand-neutral-900:#1A1F21;
}
[data-palette="slate"] { /* Pizarra */
  --brand-primary-50:#F3F5F8; --brand-primary-100:#E3E7EE; --brand-primary-200:#C8D0DC; --brand-primary-300:#A3AFC2; --brand-primary-400:#7787A2;
  --brand-primary-500:#5D6C87; --brand-primary-600:#47546C; --brand-primary-700:#3A455A; --brand-primary-800:#2F3849; --brand-primary-900:#252C3A;
  --brand-accent-100:#F5EDD3; --brand-accent-200:#EEDFB6; --brand-accent-300:#E5D09A; --brand-accent-500:#B8974A; --brand-accent-700:#6F5A2E;
  --brand-neutral-50:#FAF8F5; --brand-neutral-100:#F3F0EB; --brand-neutral-200:#E7E2DA; --brand-neutral-300:#D3CCC1; --brand-neutral-400:#999082;
  --brand-neutral-500:#7A7367; --brand-neutral-600:#5C564C; --brand-neutral-700:#443F37; --brand-neutral-800:#2E2A25; --brand-neutral-900:#1D1A17;
}
```
(The `@theme inline` block is written out in full — every step listed, no ellipses.) The test regex reads the `[data-palette="petrol"]` block even though it shares its selector with `:root`. `base.html` adds `<link rel="preload" href="{% static 'fonts/figtree/Figtree-VariableFont_wght.ttf' %}" as="font" type="font/ttf" crossorigin>`.

- [ ] **Step 4: Run** `pytest apps/core/tests/test_design_tokens.py` → PASS. `npm run build:css` → succeeds; `grep -c "brand-primary-600" static/css/output.css` > 0.

### Task 3: Rename the classes, and guard against regressions

**Files:**
- Modify: every file listed by `grep -rlE "(gray|indigo)-[0-9]" templates apps/*/forms.py`, plus `templates/_back_to_top.html`, and `base.html`/`base_centered.html` body class.
- Modify: `apps/core/templatetags/charts.py` — **no change** (exempt, see Global Constraints)
- Test: `apps/core/tests/test_design_tokens.py` (add guard tests)

- [ ] **Step 1: Failing guard tests**

```python
HUE_CLASS = re.compile(r"(?<![\w-])(?:[a-z-]+:)*[a-z]+(?:-[a-z]+)*-(?:gray|indigo)-\d{2,3}\b")
# The risk ramp and the chart palette are fixed data colors, outside every palette.
EXEMPT = {"valuation_extras.py", "charts.py"}
SCANNED = [
    p
    for p in (
        *REPO_ROOT.glob("templates/**/*.html"),
        *REPO_ROOT.glob("apps/*/forms.py"),
        *REPO_ROOT.glob("apps/*/templatetags/*.py"),
        *REPO_ROOT.glob("static/ts/*.ts"),
    )
    if p.name not in EXEMPT
]


def test_no_template_names_a_tailwind_gray_or_indigo():
    hits = [
        f"{p.relative_to(REPO_ROOT)}: {m.group(0)}"
        for p in SCANNED
        for m in HUE_CLASS.finditer(p.read_text())
    ]
    assert not hits, "use primary-*/neutral-* instead:\n" + "\n".join(hits)


def test_no_template_types_the_product_name():
    hits = [str(p.relative_to(REPO_ROOT)) for p in REPO_ROOT.glob("templates/**/*.html") if "SOFIA" in p.read_text()]
    assert not hits, "use {{ brand.name }}:\n" + "\n".join(hits)
```

- [ ] **Step 2: Run** → FAIL listing every file.

- [ ] **Step 3: Rename.** `sed -i -E 's/(text|bg|border|ring|outline|fill|stroke|divide|placeholder|from|to|decoration|accent|shadow)-gray-400/…/'` is too clever to review; instead run, over the scanned files except the exempt ones:
  1. `sed -i -E 's/\btext-gray-400\b/text-neutral-500/g'` (contrast: gray-400 text fails AA);
  2. `sed -i -E 's/(-)gray-([0-9]{2,3})\b/\1neutral-\2/g; s/(-)indigo-([0-9]{2,3})\b/\1primary-\2/g'`.
  Then `git diff --stat` and read the diff for anything outside a class attribute.

- [ ] **Step 4: Run** `pytest` → PASS. `npm run build:css`.

### Task 4: Report — Figtree and palette variables

**Files:**
- Modify: `static/css/report.css` (+ `report-wide.css`, `report-print.css` if they hold hex), `templates/reports/base_report.html`, `apps/reports/pdf.py`, `apps/reports/views.py`
- Delete: `static/fonts/SourceSans3-Variable.ttf` (once no rule references it)
- Test: `apps/reports/tests/test_pdf.py`

- [ ] **Step 1: Failing tests** (add to `apps/reports/tests/test_pdf.py`, reusing its existing `scored_assignment` fixture):

```python
def test_report_html_paints_the_default_palette(scored_assignment):
    html = pdf.report_html(Report(assignment=scored_assignment))
    assert '<html lang="es" data-palette="petrol">' in html


def test_report_html_paints_a_chosen_palette(scored_assignment):
    html = pdf.report_html(Report(assignment=scored_assignment), palette="slate")
    assert 'data-palette="slate"' in html


def test_report_css_uses_figtree_not_source_sans():
    css = (REPO_ROOT / "static/css/report.css").read_text()
    assert "Figtree" in css and "SourceSans3" not in css
```

- [ ] **Step 2: Run** → FAIL.

- [ ] **Step 3: Implement.** `report_html(report, palette=None)` and `render_report_pdf(report, palette=None)` pass `palette=palette or settings.BRAND_PALETTE_DEFAULT` into the context; `_pdf_response(report, palette)` receives `active_palette(request)` from both PDF views. `base_report.html`: `<html lang="es" data-palette="{{ palette }}">`. `report.css`: replace the two Source Sans 3 `@font-face` rules with one Figtree rule per weight the report uses (400, 600, 700 — single values, WeasyPrint rejects ranges), rename the family in its font stacks, and replace hex values that are brand colors with `var(--brand-…)`: ink `#111827`→`var(--brand-neutral-900)`, secondary `#4B5563`→`var(--brand-neutral-600)`, rules `#E5E7EB`→`var(--brand-neutral-200)`, indigo `#4338CA`→`var(--brand-primary-600)`. NDR hex values stay. Update the file's header comment to match.

- [ ] **Step 4: Run** `pytest apps/reports` → PASS (the existing PDF render test proves WeasyPrint accepts the variables and fonts).

### Task 5: Documentation

**Files:**
- Modify: `docs/platform/design-system.md` (Status → `Current — implemented in static/css/main.css and apps/core`; add chart categorical colors to Out of scope)
- Modify: `CLAUDE.md` (Cross-cutting concepts: a **Design system** bullet), `apps/core/CLAUDE.md` (brand context processor, switch view, `brand_logo` tag), `apps/reports/CLAUDE.md` (Figtree + palette in PDF)

- [ ] **Step 1:** Write the doc changes in present tense, no migration commentary.
- [ ] **Step 2:** `ruff format . && ruff check . && pytest` → green. `npm run build:css` run last.
- [ ] **Step 3:** Hand back: list of changed files, proposed commit message, and the browser checklist (both palettes, 360px + desktop: header logo color, survey page has no switch, login page, results dashboard, report screen + PDF download).

---

## Extension: squircle markers and palette-driven chart series

User request after Task 5: legends and risk badges take the palette preview's squircle marker
(Tailwind v4's `rounded-sm` is 4px, which turns an 8px swatch into a circle); sex and age chart
series follow the palette on screen and in the PDF. Decision (user): Pizarra's second series is
its lighter slate, `primary-400`.

### Task 6: Squircle swatches and badge markers

**Files:**
- Modify: `templates/components/charts/stacked_bar.html`, `level_columns.html`, `templates/core/results/_ndr_legend.html`, `_ndr_columns.html` — every legend swatch becomes `size-2.5 rounded-xs`.
- Modify: `apps/core/templatetags/valuation_extras.py` — every `ndr_badge` class string gains a marker: `inline-flex items-center gap-1.5 before:size-2 before:shrink-0 before:rounded-xs` plus `before:bg-<level bar color>` on the tinted tier and `before:bg-current` on the solid dominio tier and the neutral badge.
- Modify: `static/css/report.css` — `.report-badge::before`, an 0.5rem square with a 2px radius; tinted levels use their swatch hex, dominio levels `currentColor`.
- Test: `apps/core/tests/test_valuation_extras.py`, `apps/core/tests/test_chart_components.py`, `apps/core/tests/test_design_tokens.py`

- [ ] Failing tests: every `ndr_badge(level, tier)` contains `before:rounded-xs`; tinted `ndr_badge("bajo")` contains `before:bg-green-500`; no template under `templates/` pairs a `size-2`/`size-2.5` swatch with `rounded-sm`; `report.css` defines `.report-badge::before`.
- [ ] Implement; `pytest` green; `npm run build:css`.

### Task 7: Chart series follow the palette

**Files:**
- Modify: `static/css/main.css` — `--brand-series-1` / `--brand-series-2` in both palettes (Petróleo `#1F5D71` / `#6B79D9`; Pizarra `#47546C` / `#7787A2`), exposed as `--color-series-1/2`.
- Modify: `apps/core/brand.py` — `palette_hex(slug) -> dict[str, str]`, the `--brand-*` values of one palette, read once from `static/css/main.css`.
- Modify: `apps/core/templatetags/charts.py` — `sex-female` → `series-1`, `sex-male` → `series-2`, `age` → `series-1`, `none`/`guia1-none`/fallback → `neutral-300`, as `fill-*`/`bg-*` classes; their hex comes from `palette_hex(palette)` at paint time (`_PALETTE_TOKENS`), fixed keys keep `_HEX`. Chart tags become `takes_context=True` and read `context.get("palette")`. Remove `charts.py` from the guard's exemptions.
- Test: `apps/core/tests/test_brand.py`, `test_chart_components.py`, `test_design_tokens.py`

- [ ] Failing tests: `palette_hex("slate")["series-2"] == "#7787A2"`; a stacked bar of the sex profile rendered with `palette="slate"` carries `fill="#47546C"` and `fill-series-1`; every chart color key resolves to a hex in both palettes; contrast pairs `series-1`/`series-2` on `neutral-100` ≥ 3:1; the hue guard scans `charts.py`.
- [ ] Implement; `pytest` green; `npm run build:css`.
- [ ] Docs: `design-system.md` (series tokens, markers; resolve the open question), `apps/core/CLAUDE.md` (charts section: palette-driven keys), root `CLAUDE.md` design-system bullet (charts no longer exempt).

### Task 9: Status color scales, and every template off Tailwind's status hues

User-approved: fixed `success` / `warning` / `danger` scales (50, 100, 200, 500, 600, 800) in
`main.css`'s theme, the same in both palettes. Mapping: Tailwind 50→50, 100→100, 200/300→200,
400/500→500, 600→600, 700/800/900→800. Amount meters (registration rate, roster progress bar,
completion ring) and the "Activa" text use `primary`; Sí/No answer pills are neutral. The hue
guard extends to green, yellow, red, amber, orange, emerald, lime and rose; only the risk-ramp
module is exempt.

- [ ] Failing tests: guard over the new hues; contrast for each status pair (600 on white and on
      50, 800 on 50 and 100); Sí/No pills render without a status hue.
- [ ] Implement; `pytest`; `npm run build:css`; `npm run build:js` (survey_progress.ts).

### Task 10: Guía I takes the risk ramp's colors

- [ ] Failing test: `_HEX["guia1-event"] == "#CA9429"`, `_HEX["guia1-positive"] == "#7A1010"`, with
      matching `fill-[…]`/`bg-[…]` classes, as the dominio keys do.
- [ ] Implement; docs (`design-system.md`, root `CLAUDE.md`, `apps/core/CLAUDE.md`).

### Task 11: Answer display

User-approved: Sí/No take the choice answers' primary pill; a frequency answer is its label plus
a squircle strip of the scale's options, the chosen one filled (`_frequency_answer.html`), with the
stored position never printed and the module header naming the scale's direction
(`first_of_type` filter). Answer rows stack on a phone.

- [x] Tests: `apps/core/tests/test_answer_row.py`.
- [x] Implement; `pytest`; `npm run build:css`; doc rule in `design-system.md`.

### Task 12: Frequency answers in risk order

User-approved (option D): on a NOM-035 assignment each frequency answer's strip runs from score 0
to 4 and fills the answer's score (`apps.nom035.scoring.answer_score`); the module key reads
"Menor → mayor riesgo". Unscored instruments keep the answer-order strip.

- [x] Tests: `answer_score` in `apps/nom035/tests/test_scoring_primitives.py`; strip ordering in
      `apps/core/tests/test_answer_row.py`; page-level in `test_views.py`.
- [x] Implement; `pytest`; `npm run build:css`; docs.
