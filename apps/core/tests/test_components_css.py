"""The component classes compile: see docs/platform/design-system.md (Components).

These read the built `static/css/output.css`, so they also fail when
`npm run build:css` was not run after `main.css` changed.
"""

import re
from pathlib import Path

import pytest

OUTPUT_CSS = (Path(__file__).resolve().parents[3] / "static/css/output.css").read_text()

COMPONENTS = (
    "btn",
    "btn-primary",
    "btn-secondary",
    "btn-text",
    "btn-danger",
    "btn-sm",
    "control",
    "field",
    "card",
    "pill",
    "pill-marker",
)


@pytest.mark.parametrize("name", COMPONENTS)
def test_the_component_class_is_compiled(name):
    assert re.search(r"\.%s(?![\w-])[^{]*\{" % re.escape(name), OUTPUT_CSS), name


def test_keyboard_focus_draws_one_ring_by_default():
    assert re.search(r":where\([^)]*\bbutton\b[^)]*\):focus-visible", OUTPUT_CSS)


def test_a_busy_button_has_a_rule():
    assert (
        '.btn[aria-busy="true"]' in OUTPUT_CSS or ".btn[aria-busy=true]" in OUTPUT_CSS
    )
