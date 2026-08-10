"""Project-wide localization guarantees: language, timezone, admin chrome."""

from datetime import datetime
from datetime import timezone as dt_timezone

import pytest
from django.conf import settings
from django.urls import reverse

from apps.accounts.models import Company
from apps.core.permissions import project_app_labels

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


def test_every_project_app_is_covered_by_the_label_guard(assert_explicit_labels):
    """One loop over the derived app set, so a new app cannot opt out silently."""
    for app_label in project_app_labels():
        assert_explicit_labels(app_label)


def test_every_project_permission_name_reads_as_its_spanish_model_label():
    """The whole set, not a sample.

    `User` inherits `AbstractUser`'s lazy `_("user")`, so it is the one model
    where Django's untranslated msgid and the rendered Spanish label differ —
    exactly the case a handful of spot-checks is most likely to miss. The
    expected label is derived here from `str(verbose_name)` rather than read
    back from the receiver, so a receiver that picks the wrong source fails.
    """
    from django.apps import apps as django_apps
    from django.contrib.auth import get_permission_codename
    from django.contrib.auth.models import Permission

    from apps.core.permissions import ACTION_VERBS

    wrong = []
    for app_label in sorted(project_app_labels()):
        for model in django_apps.get_app_config(app_label).get_models():
            opts = model._meta
            verbose_name = str(opts.verbose_name)
            expected = {
                get_permission_codename(action, opts): f"{verb} {verbose_name}"
                for action in opts.default_permissions
                if (verb := ACTION_VERBS.get(action)) is not None
            }
            expected.update(dict(opts.permissions))
            for perm in Permission.objects.filter(
                content_type__app_label=app_label, codename__in=expected
            ):
                if perm.name != expected[perm.codename]:
                    wrong.append(
                        f"{app_label}.{perm.codename}: {perm.name!r} "
                        f"(want {expected[perm.codename]!r})"
                    )

    assert wrong == [], "Wrong permission names: " + "; ".join(sorted(wrong))


@pytest.mark.parametrize(
    "codename,expected",
    [
        # Built-in permissions: Django's "Can %s %s" template is not translated.
        ("add_company", "Puede agregar empresa"),
        ("view_surveyassignment", "Puede ver asignación de encuesta"),
        ("change_submissionscore", "Puede modificar valoración"),
        ("delete_answer", "Puede eliminar respuesta"),
        # `User` is the one model whose verbose_name is Django's lazy `_("user")`,
        # so the name must come from the rendered label, not the raw msgid.
        ("add_user", "Puede agregar usuario"),
        # Custom permissions declared on Role.Meta.
        ("can_view_dashboard", "Puede ver el tablero"),
        ("can_manage_employees", "Puede administrar colaboradores"),
    ],
)
def test_permission_names_in_the_groups_picker_are_spanish(codename, expected):
    from django.contrib.auth.models import Permission

    assert Permission.objects.get(codename=codename).name == expected


def test_permission_renaming_leaves_django_own_apps_alone():
    """Only the project's own apps are rewritten; auth/admin keep Django's names."""
    from django.contrib.auth.models import Permission

    perm = Permission.objects.get(content_type__app_label="auth", codename="add_group")
    assert perm.name == "Can add group"


def test_receiver_survives_a_post_migrate_without_the_apps_kwarg():
    """`manage.py flush` — and the teardown of any `transaction=True` test —
    emits post_migrate with `using` but no `apps`. The receiver must not assume
    it was called by `migrate`."""
    from django.apps import apps as django_apps
    from django.db import DEFAULT_DB_ALIAS
    from django.db.models.signals import post_migrate

    app_config = django_apps.get_app_config("accounts")

    post_migrate.send(
        sender=app_config,
        app_config=app_config,
        verbosity=0,
        interactive=False,
        using=DEFAULT_DB_ALIAS,
    )
