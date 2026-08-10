"""Project-wide localization guarantees: language, timezone, admin chrome."""

from datetime import datetime
from datetime import timezone as dt_timezone

import pytest
from django.conf import settings
from django.urls import reverse

from apps.accounts.models import Company

pytestmark = pytest.mark.django_db


def test_project_language_is_mexican_spanish():
    assert settings.LANGUAGE_CODE == "es-mx"


def test_project_timezone_is_mexico_city_and_storage_stays_utc():
    assert settings.TIME_ZONE == "America/Mexico_City"
    assert settings.USE_TZ is True


def test_admin_login_page_is_branded_and_in_spanish(client):
    response = client.get(reverse("admin:login"))

    body = response.content.decode()
    assert "Administración SOFIA-S" in body
    assert "Django administration" not in body


def _empty_inline_management_form(prefix):
    """CompanyAdmin has two inlines; a POST without their management forms 500s."""
    return {
        f"{prefix}-TOTAL_FORMS": "0",
        f"{prefix}-INITIAL_FORMS": "0",
        f"{prefix}-MIN_NUM_FORMS": "0",
        f"{prefix}-MAX_NUM_FORMS": "1000",
    }


def test_django_validation_messages_render_in_spanish(staff_client):
    """Layer 1: Django's own strings, bought with LANGUAGE_CODE alone."""
    response = staff_client.post(
        reverse("admin:accounts_company_add"),
        {
            "name": "",
            "legal_name": "",
            "rfc": "",
            "address": "",
            **_empty_inline_management_form("areas"),
            **_empty_inline_management_form("locations"),
        },
    )

    assert response.status_code == 200
    assert "Este campo es obligatorio." in response.content.decode()


def test_admin_renders_timestamps_in_mexico_city_time(staff_client, make_company):
    """21:00 UTC is 15:00 in Mexico City, which has no DST since 2022."""
    company = make_company()
    Company.objects.filter(pk=company.pk).update(
        created_at=datetime(2026, 8, 9, 21, 0, tzinfo=dt_timezone.utc)
    )

    response = staff_client.get(reverse("admin:accounts_company_changelist"))

    body = response.content.decode()
    # Django's es_MX catalog capitalizes month names.
    assert "9 de Agosto de 2026 a las 15:00" in body
    assert "21:00" not in body


@pytest.mark.parametrize(
    "app_label,expected",
    [
        ("accounts", "Cuentas"),
        ("surveys", "Encuestas"),
        ("responses", "Respuestas"),
        ("nom035", "NOM-035"),
    ],
)
def test_admin_index_groups_apps_under_spanish_names(app_label, expected):
    from django.apps import apps as django_apps

    assert django_apps.get_app_config(app_label).verbose_name == expected
