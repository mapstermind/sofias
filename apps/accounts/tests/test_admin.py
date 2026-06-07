import pytest
from django.urls import reverse
from django.utils import timezone

from apps.accounts.models import SetupAccessCode

pytestmark = pytest.mark.django_db


def test_setup_access_code_admin_requires_staff(client, make_user):
    user = make_user(email="regular-admin-view@example.com", password="Pass12345!")
    client.force_login(user)

    response = client.get(reverse("admin:accounts_setupaccesscode_changelist"))

    assert response.status_code == 302


def test_setup_access_code_admin_shows_unused_code(client, make_user):
    staff = make_user(
        email="staff@example.com",
        password="Pass12345!",
        is_staff=True,
        is_superuser=True,
    )
    fallback_user = make_user(email="fallback-admin@example.com")
    SetupAccessCode.objects.create(user=fallback_user, code="123456789")
    client.force_login(staff)

    response = client.get(reverse("admin:accounts_setupaccesscode_changelist"))

    assert response.status_code == 200
    assert b"123456789" in response.content


def test_setup_access_code_admin_does_not_show_used_code_value(client, make_user):
    staff = make_user(
        email="staff-used@example.com",
        password="Pass12345!",
        is_staff=True,
        is_superuser=True,
    )
    fallback_user = make_user(email="used-admin@example.com")
    SetupAccessCode.objects.create(
        user=fallback_user,
        code=None,
        used_at=timezone.now(),
    )
    client.force_login(staff)

    response = client.get(reverse("admin:accounts_setupaccesscode_changelist"))

    assert response.status_code == 200
    assert b"123456789" not in response.content
