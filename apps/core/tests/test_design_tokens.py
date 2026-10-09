"""Design-system guarantees: see docs/platform/design-system.md (Enforcement).

These read source files, never a rendered page: they prove every declared pair
in both palettes meets WCAG AA and that no template bypasses the tokens. Whether
a page *looks* right in each palette is checked by a human in the browser.
"""

import re
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[3]
MAIN_CSS = (REPO_ROOT / "static/css/main.css").read_text()
PALETTES = ("petrol", "slate")
WHITE = "#FFFFFF"

# (use, foreground, background, minimum ratio). A token names a palette step;
# a hex is fixed. 4.5:1 for text, 3:1 for UI boundaries and chart marks.
PAIRS = [
    ("body text", "neutral-800", "neutral-50", 4.5),
    ("secondary text", "neutral-600", WHITE, 4.5),
    ("secondary text on a light fill", "neutral-600", "neutral-100", 4.5),
    ("lightest text", "neutral-500", WHITE, 4.5),
    ("primary button", WHITE, "primary-600", 4.5),
    ("primary button, hover", WHITE, "primary-700", 4.5),
    ("link", "primary-600", WHITE, 4.5),
    ("link on the page background", "primary-600", "neutral-50", 4.5),
    ("active item / info message", "primary-700", "primary-50", 4.5),
    ("chip on the accent", "primary-900", "accent-200", 4.5),
    ("accent label", "accent-700", "accent-100", 4.5),
    ("input border", "neutral-400", WHITE, 3),
    ("focus ring", "primary-500", WHITE, 3),
    ("primary chart mark", "primary-600", "neutral-100", 3),
    ("first chart series", "series-1", "neutral-100", 3),
    ("second chart series", "series-2", "neutral-100", 3),
]


def _palette(slug):
    match = re.search(r'\[data-palette="%s"\][^{]*\{([^}]*)\}' % slug, MAIN_CSS)
    assert match, f'no [data-palette="{slug}"] block in static/css/main.css'
    return dict(
        re.findall(r"--brand-([a-z]+-\d+):\s*(#[0-9A-Fa-f]{6})", match.group(1))
    )


def _luminance(hex_):
    rgb = [int(hex_[i : i + 2], 16) / 255 for i in (1, 3, 5)]
    lin = [c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4 for c in rgb]
    return 0.2126 * lin[0] + 0.7152 * lin[1] + 0.0722 * lin[2]


def _ratio(a, b):
    hi, lo = sorted((_luminance(a), _luminance(b)), reverse=True)
    return (hi + 0.05) / (lo + 0.05)


@pytest.mark.parametrize("slug", PALETTES)
def test_every_declared_pair_meets_wcag_aa(slug):
    tokens = _palette(slug)
    failures = []
    for use, fg, bg, minimum in PAIRS:
        f = fg if fg.startswith("#") else tokens[fg]
        b = bg if bg.startswith("#") else tokens[bg]
        if (ratio := _ratio(f, b)) < minimum:
            failures.append(f"{use}: {fg} on {bg} = {ratio:.2f}, needs {minimum}")
    assert not failures, "\n".join(failures)


def test_both_palettes_declare_the_same_tokens():
    assert _palette("petrol").keys() == _palette("slate").keys()


def test_every_palette_token_is_exposed_to_tailwind():
    for token in _palette("petrol"):
        assert f"--color-{token}: var(--brand-{token});" in MAIN_CSS, token


# A Tailwind utility on one of its own hue scales, with any variants. Brand color
# comes from the palette tokens, status color from success/warning/danger.
HUE_CLASS = re.compile(
    r"(?<![\w-])(?:[\w-]+:)*[a-z]+(?:-[a-z]+)*-"
    r"(?:gray|indigo|green|yellow|red|amber|orange|emerald|lime|rose)-\d{2,3}\b"
)
# The risk ramp is a fixed data color, outside every palette.
EXEMPT = {"valuation_extras.py"}
SCANNED = [
    path
    for path in (
        *sorted(REPO_ROOT.glob("templates/**/*.html")),
        *sorted(REPO_ROOT.glob("apps/*/forms.py")),
        *sorted(REPO_ROOT.glob("apps/*/templatetags/*.py")),
        *sorted(REPO_ROOT.glob("static/ts/*.ts")),
    )
    if path.name not in EXEMPT
]


def test_no_template_names_a_tailwind_hue():
    hits = [
        f"{path.relative_to(REPO_ROOT)}: {match.group(0)}"
        for path in SCANNED
        for match in HUE_CLASS.finditer(path.read_text())
    ]
    assert not hits, (
        "use primary-*/neutral-*, or success-*/warning-*/danger-*:\n" + "\n".join(hits)
    )


def test_no_template_types_the_product_name():
    hits = [
        str(path.relative_to(REPO_ROOT))
        for path in REPO_ROOT.glob("templates/**/*.html")
        if "SOFIA" in path.read_text()
    ]
    assert not hits, "use {{ brand.name }} or {{ brand.short_name }}:\n" + "\n".join(
        hits
    )


# A legend swatch: an 8–10px square. Tailwind v4's `rounded-sm` is 4px, which
# turns it into a dot; swatches are 2px-radius squircles (`rounded-xs`).
DOT_SWATCH = re.compile(
    r'class="[^"]*\bsize-2(?:\.5)?\b[^"]*\brounded-(?:sm|full|md)\b'
)


def test_legend_swatches_are_squircles_not_dots():
    hits = [
        str(path.relative_to(REPO_ROOT))
        for path in REPO_ROOT.glob("templates/**/*.html")
        if DOT_SWATCH.search(path.read_text())
    ]
    assert not hits, "use size-2.5 rounded-xs:\n" + "\n".join(hits)


def test_report_badges_carry_the_squircle_marker():
    css = (REPO_ROOT / "static/css/report.css").read_text()
    assert ".report-badge::before" in css


# A pill that names a state. Answer values (Sí/No, choice labels), the "Tú" tag
# and filter links are pills too, but not states, so they carry no marker.
STATUS_LABELS = (
    "Publicado",
    "Borrador",
    "Sin iniciar",
    "Activa",
    "Completada",
    "Cerrada",
    "En progreso",
    "Activado",
    "No activado",
    "Sin activar",
)
PILL = re.compile(
    r'<span class="([^"]*\brounded-full\b[^"]*\btext-xs\b[^"]*)">\s*([^<{]+)'
)


def test_status_pills_carry_the_squircle_marker():
    found, missing = 0, []
    for path in REPO_ROOT.glob("templates/**/*.html"):
        for classes, text in PILL.findall(path.read_text()):
            if not text.strip().startswith(STATUS_LABELS):
                continue
            found += 1
            if "before:rounded-xs" not in classes or "before:bg-current" not in classes:
                missing.append(f"{path.relative_to(REPO_ROOT)}: {text.strip()}")
    assert found >= 20, f"only {found} status pills found; did the markup change?"
    assert not missing, "\n".join(missing)


# Status scales are fixed (the same in every palette) and declared in @theme.
STATUS_PAIRS = [
    ("status text on white", "600", WHITE, 4.5),
    ("status text on its tint", "600", "50", 4.5),
    ("pill text on its tint", "800", "50", 4.5),
    ("pill text on its hover tint", "800", "100", 4.5),
    ("status icon on its tint", "500", "50", 3),
]


def _status(name):
    return dict(re.findall(r"--color-%s-(\d+):\s*(#[0-9A-Fa-f]{6});" % name, MAIN_CSS))


@pytest.mark.parametrize("name", ("success", "warning", "danger"))
def test_status_scales_meet_wcag_aa(name):
    steps = _status(name)
    assert steps.keys() == {"50", "100", "200", "500", "600", "800"}, steps
    failures = []
    for use, fg, bg, minimum in STATUS_PAIRS:
        f = fg if fg.startswith("#") else steps[fg]
        b = bg if bg.startswith("#") else steps[bg]
        if (ratio := _ratio(f, b)) < minimum:
            failures.append(
                f"{name} {use}: {fg} on {bg} = {ratio:.2f}, needs {minimum}"
            )
    assert not failures, "\n".join(failures)


def test_answer_values_carry_no_status_color():
    """A "No" to a psychosocial question is not an error; answers are neutral pills."""
    html = (REPO_ROOT / "templates/core/_answer_row.html").read_text()
    assert not re.search(r"\b(?:green|red|success|warning|danger)-\d", html)
