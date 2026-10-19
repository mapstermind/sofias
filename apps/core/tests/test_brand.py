"""Brand configuration: see docs/platform/design-system.md.

The about page is public and renders `base.html`, so it is the cheapest page that
carries the brand.
"""

import pytest

from apps.core.brand import palette_hex

pytestmark = pytest.mark.django_db

ABOUT_URL = "/que-es-sofia/"


def test_pages_are_spanish(client):
    assert '<html lang="es">' in client.get(ABOUT_URL).content.decode()


def test_the_logo_is_inlined_so_it_takes_the_text_color(client):
    html = client.get(ABOUT_URL).content.decode()
    assert 'fill="currentColor"' in html
    assert "<?xml" not in html


def test_palette_hex_reads_the_palette_from_main_css():
    tokens = palette_hex()
    assert tokens["primary-500"] == "#5D6C87"
    assert tokens["series-2"] == "#7787A2"
