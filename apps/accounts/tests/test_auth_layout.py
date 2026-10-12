"""The split-card account layout (templates/base_auth.html): see docs/platform/design-system.md."""

import pytest
from django.conf import settings
from django.urls import reverse

pytestmark = pytest.mark.django_db

SIGN_IN = {
    "otp": "accounts:request_otp",
    "password": "accounts:password_login",
    "setup": "accounts:setup_access_code_login",
}


def _html(client, name):
    return client.get(reverse(name)).content.decode()


@pytest.mark.parametrize("name", SIGN_IN.values())
def test_a_sign_in_screen_uses_the_split_card(client, name):
    html = _html(client, name)
    assert "data-auth-panel" in html
    assert 'data-auth-variant=""' in html
    assert settings.BRAND["meaning"] in html
    assert "btn-glow" in html


@pytest.mark.parametrize("current, name", SIGN_IN.items())
def test_a_sign_in_screen_offers_the_other_two_ways_in(client, current, name):
    html = _html(client, name)
    assert "Otras formas de ingresar" in html
    for other, other_name in SIGN_IN.items():
        link = f'href="{reverse(other_name)}"'
        assert (link in html) is (other != current), other


def test_the_verify_screen_uses_the_split_card_without_other_ways_in(client):
    session = client.session
    session["otp_email"] = "ana@empresa.mx"
    session.save()
    html = _html(client, "accounts:verify_otp")
    assert "data-auth-panel" in html
    assert "ana@empresa.mx" in html
    assert "Otras formas de ingresar" not in html
    assert "pide otro código" in html


def test_the_password_change_uses_the_split_card(client, make_user):
    client.force_login(make_user(must_change_password=True))
    html = _html(client, "accounts:change_password")
    assert "data-auth-panel" in html
    assert 'data-auth-variant=""' in html
    assert html.count("data-password-toggle-button") == 2
    assert "Otras formas de ingresar" not in html


def test_activation_uses_the_long_split_card(
    client, make_user_with_profile, make_company, make_area
):
    company = make_company()
    make_area(company=company)
    client.force_login(make_user_with_profile(company=company, is_activated=False))
    html = _html(client, "accounts:setup_profile")
    assert "data-auth-panel" in html
    assert 'data-auth-variant="long"' in html
    assert "Activar cuenta" in html


def test_activation_blocked_by_missing_areas_keeps_the_long_split_card(
    client, make_user_with_profile, make_company
):
    company = make_company()
    client.force_login(make_user_with_profile(company=company, is_activated=False))
    html = _html(client, "accounts:setup_profile")
    assert 'data-auth-variant="long"' in html
    assert "todavía no puedes activar tu cuenta" in html
