"""Brand configuration and the temporary palette switch: see docs/platform/design-system.md.

The about page is public and renders `base.html`, so it is the cheapest page that
carries the brand, the palette attribute and the switch.
"""

import pytest
from django.test import RequestFactory, override_settings

from apps.core.brand import active_palette

pytestmark = pytest.mark.django_db

ABOUT_URL = "/que-es-sofia/"
SWITCH_URL = "/paleta/"


def _request(cookie=None):
    request = RequestFactory().get("/")
    if cookie is not None:
        request.COOKIES["paleta"] = cookie
    return request


def test_no_cookie_gives_the_default_palette():
    assert active_palette(_request()) == "petrol"


def test_a_known_cookie_picks_its_palette():
    assert active_palette(_request("slate")) == "slate"


@pytest.mark.parametrize("bad", ["durazno", '"><script>', ""])
def test_an_unknown_cookie_falls_back_to_the_default(bad):
    assert active_palette(_request(bad)) == "petrol"


def test_no_request_gives_the_default_palette():
    """The PDF renders without a request."""
    assert active_palette(None) == "petrol"


def test_pages_are_spanish_and_carry_the_palette(client):
    html = client.get(ABOUT_URL).content.decode()
    assert '<html lang="es" data-palette="petrol">' in html


def test_the_cookie_repaints_the_page(client):
    client.cookies["paleta"] = "slate"
    assert 'data-palette="slate"' in client.get(ABOUT_URL).content.decode()


@override_settings(DEBUG=False)
def test_the_switch_is_hidden_from_a_non_admin(client, make_user, bootstrap_groups):
    user = make_user(email="empleado@example.com")
    user.groups.add(bootstrap_groups["Employees"])
    client.force_login(user)
    assert "data-palette-switch" not in client.get(ABOUT_URL).content.decode()


@override_settings(DEBUG=False)
def test_the_switch_is_hidden_from_an_anonymous_visitor(client):
    assert "data-palette-switch" not in client.get(ABOUT_URL).content.decode()


@override_settings(DEBUG=False)
def test_the_switch_is_shown_to_an_admin(client, make_user, bootstrap_groups):
    user = make_user(email="admin@example.com")
    user.groups.add(bootstrap_groups["Admins"])
    client.force_login(user)
    html = client.get(ABOUT_URL).content.decode()
    assert "data-palette-switch" in html
    assert "Petróleo" in html and "Pizarra" in html


@override_settings(DEBUG=True)
def test_the_switch_is_shown_to_anyone_in_debug(client):
    assert "data-palette-switch" in client.get(ABOUT_URL).content.decode()


def test_switching_sets_the_cookie_and_returns_to_the_page(client):
    response = client.post(SWITCH_URL, {"paleta": "slate", "next": ABOUT_URL})
    assert response.status_code == 302
    assert response["Location"] == ABOUT_URL
    assert response.cookies["paleta"].value == "slate"


def test_switching_ignores_an_offsite_return_and_an_unknown_palette(client):
    response = client.post(
        SWITCH_URL, {"paleta": "durazno", "next": "https://evil.example/"}
    )
    assert response["Location"] == "/"
    assert "paleta" not in response.cookies


def test_the_logo_is_inlined_so_it_takes_the_text_color(client):
    html = client.get(ABOUT_URL).content.decode()
    assert 'fill="currentColor"' in html
    assert "<?xml" not in html


@override_settings(DEBUG=True)
def test_the_switch_reserves_room_so_the_footer_stays_reachable(client):
    """The pill is fixed to the bottom edge; without a spacer it covers the footer links at 360px."""
    html = client.get(ABOUT_URL).content.decode()
    assert "data-palette-switch-spacer" in html
    assert html.index("data-palette-switch-spacer") < html.index('action="/paleta/"')


def test_palette_hex_reads_a_palette_from_main_css():
    from apps.core.brand import palette_hex

    assert palette_hex("petrol")["primary-600"] == "#1F5D71"
    assert palette_hex("slate")["series-2"] == "#7787A2"
