"""The palette comparison at /propuestas/paletas/ and the navy palette it keeps to itself."""

from pathlib import Path

import pytest
from django.conf import settings
from django.test import override_settings

pytestmark = pytest.mark.django_db

URL = "/propuestas/paletas/"
REPO_ROOT = Path(__file__).resolve().parents[3]


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


def test_it_has_one_h1(admin_page):
    assert admin_page.count("<h1") == 1


@pytest.mark.parametrize("slug", ["petrol", "slate", "navy"])
def test_it_paints_one_specimen_per_palette(admin_page, slug):
    assert f'<section id="{slug}"' in admin_page
    assert f'<div data-palette="{slug}"' in admin_page


def test_ids_stay_unique_across_the_three_specimens(admin_page):
    assert admin_page.count('id="id_petrol-contact_email"') == 1
    assert admin_page.count('id="id_navy-contact_email"') == 1


def test_it_loads_the_navy_stylesheet(admin_page):
    assert "css/proposal-navy.css" in admin_page


def test_no_other_page_loads_the_navy_stylesheet(client, make_user, bootstrap_groups):
    user = make_user(email="admin@example.com")
    user.groups.add(bootstrap_groups["Admins"])
    client.force_login(user)
    with override_settings(DEBUG=False):
        page = client.get("/estilos/").content.decode()
    assert "proposal-navy" not in page


def test_navy_is_not_a_palette_a_visitor_can_pick():
    assert "navy" not in {slug for slug, _ in settings.BRAND_PALETTES}
    main_css = (REPO_ROOT / "static/css/main.css").read_text()
    assert 'data-palette="navy"' not in main_css
    assert (
        'data-palette="navy"'
        in (REPO_ROOT / "static/css/proposal-navy.css").read_text()
    )
