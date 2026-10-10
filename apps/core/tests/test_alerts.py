"""The alert partial and Django messages on every page: see docs/platform/design-system.md."""

from pathlib import Path

import pytest
from django.contrib.messages import constants
from django.contrib.messages.storage.base import Message
from django.contrib.messages.storage.cookie import CookieStorage
from django.template.loader import render_to_string
from django.test import RequestFactory

ICON_DIR = Path(__file__).resolve().parents[3] / "templates/icons"

TONES = {
    "success": ("check-circle", "success", "status"),
    "info": ("information-circle", "primary", "status"),
    "warning": ("exclamation-triangle", "warning", "status"),
    "danger": ("exclamation-circle", "danger", "alert"),
}


def _icon_path(name):
    """The drawing of an icon file, which identifies it in rendered HTML."""
    source = (ICON_DIR / f"{name}.svg").read_text()
    return source[source.index("<path") : source.index("/>") + 2]


def alert(**context):
    return render_to_string("components/_alert.html", context)


@pytest.mark.parametrize("tone", TONES)
def test_each_tone_has_its_icon_scale_and_role(tone):
    icon, scale, role = TONES[tone]
    html = alert(tone=tone, body="Texto")
    assert _icon_path(icon) in html
    assert f"bg-{scale}-50" in html and f"border-{scale}-200" in html
    assert f'role="{role}"' in html


def test_items_render_as_a_list_under_the_title():
    html = alert(tone="warning", title="Para publicar falta:", items=["Uno", "Dos"])
    assert html.index("Para publicar falta:") < html.index("<ul")
    assert html.count("<li>") == 2


def test_a_body_is_escaped():
    assert "&lt;b&gt;" in alert(tone="info", body="<b>x</b>")


def test_an_alert_is_not_dismissible_unless_asked():
    assert "data-dismiss" not in alert(tone="danger", body="x")
    html = alert(tone="success", body="x", dismissible=True)
    assert "data-dismiss" in html and 'aria-label="Cerrar aviso"' in html


def _with_message(client, text, level=constants.SUCCESS):
    request = RequestFactory().get("/")
    storage = CookieStorage(request)
    client.cookies["messages"] = storage._encode([Message(level, text)])


@pytest.mark.django_db
def test_a_message_shows_on_a_centered_page(client):
    _with_message(client, "Revisa tu correo", constants.INFO)
    html = client.get("/cuentas/ingresar/").content.decode()
    assert "Revisa tu correo" in html
    assert "data-dismiss" in html
    assert "bg-primary-50" in html


@pytest.mark.django_db
def test_a_message_shows_on_an_app_page(staff_client):
    _with_message(staff_client, "Guardado", constants.ERROR)
    html = staff_client.get("/empresas/").content.decode()
    assert "Guardado" in html
    assert 'role="alert"' in html


@pytest.mark.django_db
def test_no_messages_render_no_container(staff_client):
    assert "data-messages" not in staff_client.get("/empresas/").content.decode()


@pytest.mark.django_db
def test_every_page_loads_the_busy_submit_script(client):
    assert "js/busy_submit.js" in client.get("/cuentas/ingresar/").content.decode()


@pytest.mark.django_db
def test_the_code_request_marks_its_button_busy(client):
    """It sends an email, so a double tap would send two codes."""
    assert "data-loading" in client.get("/cuentas/ingresar/").content.decode()


@pytest.mark.django_db
def test_every_page_loads_the_dismiss_script(client):
    """The styleguide's demo alerts are dismissible without any message pending."""
    assert "js/dismiss.js" in client.get("/cuentas/ingresar/").content.decode()


@pytest.mark.django_db
def test_a_centered_page_has_a_main_to_return_focus_to(client):
    """dismiss.ts moves focus to #main once the last message is closed."""
    assert (
        '<main id="main" tabindex="-1"'
        in client.get("/cuentas/ingresar/").content.decode()
    )
