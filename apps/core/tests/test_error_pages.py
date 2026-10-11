"""Branded Spanish error pages: see docs/platform/design-system.md (Error pages)."""

from pathlib import Path

import pytest
from django.conf import settings
from django.test import RequestFactory, override_settings

from apps.core.views import server_error

pytestmark = pytest.mark.django_db
TEMPLATES = Path(__file__).resolve().parents[3] / "templates"


@override_settings(DEBUG=False)
def test_an_unknown_address_gets_the_404_page(client):
    response = client.get("/no-existe/")
    html = response.content.decode()
    assert response.status_code == 404
    assert "No encontramos esta página" in html
    assert settings.BRAND["name"] in html
    assert 'href="/"' in html and "Ir al inicio" in html
    assert "Error 404" in html


@override_settings(DEBUG=False)
def test_a_refused_page_gets_the_403_page(
    client, make_user_with_profile, company, bootstrap_groups
):
    viewer = make_user_with_profile(email="exec@example.com", company=company)
    viewer.groups.add(bootstrap_groups["Principal Exec"])
    client.force_login(viewer)
    response = client.get("/empresas/")
    assert response.status_code == 403
    assert "No tienes acceso a esta página" in response.content.decode()


def test_the_500_page_renders_without_the_database(django_assert_num_queries):
    with django_assert_num_queries(0):
        response = server_error(RequestFactory().get("/"))
    html = response.content.decode()
    assert response.status_code == 500
    assert "No pudimos cargar esta página" in html
    assert settings.BRAND["name"] in html
    assert "Ir al inicio" in html


@pytest.mark.parametrize("name", ["404.html", "403.html", "500.html"])
def test_no_error_page_types_the_product_name(name):
    assert "SOFIA" not in (TEMPLATES / name).read_text()
