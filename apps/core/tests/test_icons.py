"""`{% icon %}`: Heroicons inlined from templates/icons/. See docs/platform/design-system.md."""

import pytest
from django.template import Context, Template, TemplateSyntaxError
from django.test import override_settings


def render(src, **context):
    return Template("{% load icons %}" + src).render(Context(context))


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


def test_a_label_is_escaped():
    html = render('{% icon "x-mark" label=name %}', name="<b>")
    assert "<b>" not in html and "&lt;b&gt;" in html


@override_settings(DEBUG=True)
def test_an_unknown_icon_raises_in_debug():
    with pytest.raises(TemplateSyntaxError):
        render('{% icon "no-such-icon" %}')


@override_settings(DEBUG=False)
def test_an_unknown_icon_renders_nothing_in_production():
    assert render('{% icon "no-such-icon" %}') == ""


@override_settings(DEBUG=True)
def test_a_name_cannot_leave_the_icon_folder():
    with pytest.raises(TemplateSyntaxError):
        render('{% icon "../base" %}')


def test_every_icon_a_template_names_exists():
    """Tests run with DEBUG off, where an unknown icon renders nothing; catch the typo here."""
    import re
    from pathlib import Path

    root = Path(__file__).resolve().parents[3]
    used = {
        name
        for path in root.glob("templates/**/*.html")
        for name in re.findall(r'\{%\s*icon\s+"([^"]+)"', path.read_text())
    }
    assert used, "no {% icon %} found; did the tag change?"
    missing = sorted(
        n for n in used if not (root / "templates/icons" / f"{n}.svg").is_file()
    )
    assert not missing, missing
