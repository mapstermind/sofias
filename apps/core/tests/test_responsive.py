"""Project-wide responsive guarantees: see docs/platform/responsive-layout.md.

This module is a floor, not a guarantee. It reads class names, never a rendered
page, so it cannot see a width that only overflows when repeated, a row that
wraps into nonsense, or whether a control is comfortable to tap. Those are
verified by a human at 360px.
"""

import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]

# 360px, less the page shell's `px-4` on each side.
PHONE_CONTENT_BOX_PX = 328

REM_PX = 16
TAILWIND_UNIT_PX = 4  # w-1 == 0.25rem == 4px

# An *unprefixed* width class. The lookbehind does two jobs: it rejects a
# breakpoint prefix, because `lg:w-96` does not apply at 360px, and it rejects a
# longer token ending in the same letters — `max-w-lg` is a cap that shrinks,
# and `autocomplete="new-password"` is not a class at all.
WIDTH = re.compile(r"(?<![-\w:])(?:min-)?w-(\[[^\]\s]+\]|[a-z0-9./]+)")

# The documented places a Tailwind class may live (static/css/main.css).
SCANNED = (
    *sorted(REPO_ROOT.glob("templates/**/*.html")),
    *sorted(REPO_ROOT.glob("apps/*/forms.py")),
    *sorted(REPO_ROOT.glob("apps/*/templatetags/*.py")),
    *sorted(REPO_ROOT.glob("static/ts/*.ts")),
)


def _width_px(value: str) -> float | None:
    """Rendered width of a Tailwind width value, or None when it cannot overflow.

    `full`, `auto`, `screen`, fractions and viewport-relative `calc()` widths all
    shrink with their container, so none of them can push a page sideways.
    """
    if "/" in value:
        return None
    if value.startswith("["):
        literal = value[1:-1]
        if literal.endswith("rem"):
            return float(literal[:-3]) * REM_PX
        if literal.endswith("px"):
            return float(literal[:-2])
        return None
    try:
        return float(value) * TAILWIND_UNIT_PX
    except ValueError:
        return None


def test_no_unprefixed_width_exceeds_the_phone_content_box():
    """A fixed width wider than the phone refuses to shrink and pushes the page.

    `w-96 shrink-0` on a flex child is the shape of the failure: the sibling
    column is squeezed toward zero and the page scrolls sideways. Widen it under
    a breakpoint instead, so the phone keeps a width it can actually fit.
    """
    offenders = []
    for path in SCANNED:
        for line_no, line in enumerate(path.read_text().splitlines(), start=1):
            for value in WIDTH.findall(line):
                px = _width_px(value)
                if px is not None and px >= PHONE_CONTENT_BOX_PX:
                    rel = path.relative_to(REPO_ROOT)
                    offenders.append(f"{rel}:{line_no} w-{value} ({px:g}px)")

    assert offenders == [], (
        f"Unprefixed widths at or above {PHONE_CONTENT_BOX_PX}px "
        "(the 360px phone content box): " + ", ".join(offenders)
    )
