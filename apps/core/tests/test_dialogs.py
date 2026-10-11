"""Every dialog is a native <dialog>: see docs/platform/design-system.md (Dialogs)."""

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
TEMPLATES = sorted((ROOT / "templates").rglob("*.html"))


def test_no_template_hand_rolls_an_overlay():
    hits = [
        str(p.relative_to(ROOT)) for p in TEMPLATES if "fixed inset-0" in p.read_text()
    ]
    assert not hits, 'use <dialog class="dialog">:\n' + "\n".join(hits)


def test_every_dialog_is_named_by_its_title():
    found = 0
    for path in TEMPLATES:
        text = path.read_text()
        for tag in re.findall(r"<dialog\b[^>]*>", text):
            found += 1
            label = re.search(r'aria-labelledby="([^"]+)"', tag)
            assert label, f"{path.name}: {tag}"
            assert f'id="{label.group(1)}"' in text, f"{path.name}: {label.group(1)}"
    assert found >= 6


def test_the_dialog_class_is_compiled():
    css = (ROOT / "static/css/output.css").read_text()
    assert re.search(r"\.dialog\s*\{", css) and ".dialog::backdrop" in css


def test_the_expired_session_cannot_be_dismissed():
    html = (ROOT / "templates/surveys/_session_expired_modal.html").read_text()
    assert "data-dialog-static" in html


def test_no_dialog_is_opened_by_inline_script():
    hits = [
        str(p.relative_to(ROOT))
        for p in TEMPLATES
        if re.search(
            r"style\.display\s*=|onclick=\"document\.getElementById", p.read_text()
        )
    ]
    assert not hits, hits
