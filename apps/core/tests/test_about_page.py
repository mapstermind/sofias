"""The about page in the split card: see docs/platform/design-system.md."""

import pytest
from django.conf import settings
from django.contrib.messages import constants
from django.urls import reverse

from apps.core.tests.test_alerts import _with_message

pytestmark = pytest.mark.django_db


def _html(client):
    return client.get(reverse("core:about")).content.decode()


def test_the_about_page_is_a_split_card_with_its_title_in_the_panel(client):
    html = _html(client)
    assert "auth-card" in html
    # The panel comes first in the markup, so the title is read before the text;
    # `lg:order-last` moves it to the right column.
    assert (
        html.index("auth-panel") < html.index("<h1") < html.index("es una plataforma")
    )
    assert "lg:order-last" in html
    assert settings.BRAND["meaning"] in html


def test_the_about_page_shows_the_logo_in_both_columns(client):
    assert _html(client).count(f'aria-label="Logo {settings.BRAND["name"]}"') == 2


def test_the_about_page_offers_home_as_its_main_action(client):
    html = _html(client)
    assert f'href="{reverse("core:home")}"' in html
    assert "btn-glow" in html
    assert "Ir al inicio" in html


def test_a_message_shows_on_the_about_page(client):
    _with_message(client, "Sesión cerrada", constants.SUCCESS)
    assert "Sesión cerrada" in _html(client)
