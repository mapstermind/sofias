"""The styleguide at /estilos/: see docs/platform/design-system.md (Components)."""

from pathlib import Path

import pytest
from django.test import override_settings

pytestmark = pytest.mark.django_db

URL = "/estilos/"
ICON_DIR = Path(__file__).resolve().parents[3] / "templates/icons"


@override_settings(DEBUG=False)
def test_an_anonymous_visitor_gets_a_404(client):
    assert client.get(URL).status_code == 404


@override_settings(DEBUG=False)
def test_an_employee_gets_a_404(
    client, make_user_with_profile, company, bootstrap_groups
):
    user = make_user_with_profile(email="empleado@example.com", company=company)
    user.groups.add(bootstrap_groups["Employees"])
    client.force_login(user)
    assert client.get(URL).status_code == 404


@pytest.fixture
def admin_page(client, make_user, bootstrap_groups):
    user = make_user(email="admin@example.com")
    user.groups.add(bootstrap_groups["Admins"])
    client.force_login(user)
    with override_settings(DEBUG=False):
        response = client.get(URL)
    assert response.status_code == 200
    return response.content.decode()


@override_settings(DEBUG=True)
def test_anyone_sees_it_in_debug(client):
    assert client.get(URL).status_code == 200


@pytest.mark.parametrize(
    "name",
    [
        "btn-primary",
        "btn-secondary",
        "btn-text",
        "btn-danger",
        "btn-sm",
        "card",
        "pill-marker",
    ],
)
def test_it_shows_every_component(admin_page, name):
    assert name in admin_page


def test_it_shows_every_state(admin_page):
    assert 'aria-busy="true"' in admin_page
    assert "disabled" in admin_page
    assert "(opcional)" in admin_page
    assert 'aria-invalid="true"' in admin_page
    assert "<fieldset" in admin_page


@pytest.mark.parametrize("scale", ["success", "primary", "warning", "danger"])
def test_it_shows_every_alert_tone(admin_page, scale):
    assert f"bg-{scale}-50 " in admin_page


def test_it_shows_every_icon_by_name(admin_page):
    for path in ICON_DIR.glob("*.svg"):
        assert path.stem in admin_page


def test_it_shows_the_active_palette_swatches(admin_page):
    assert "#1F5D71" in admin_page
