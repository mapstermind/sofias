from smtplib import SMTPException
from unittest.mock import patch

import pytest
from django.test import override_settings
from django.urls import reverse
from django.utils import timezone

from apps.accounts.models import EmailOTP, SetupAccessCode, User, UserProfile

pytestmark = pytest.mark.django_db

REQUEST_OTP_URL = "/cuentas/ingresar/"
PASSWORD_LOGIN_URL = "/cuentas/ingresar-con-contrasena/"
SETUP_ACCESS_CODE_URL = "/cuentas/primer-ingreso/"
VERIFY_OTP_URL = "/cuentas/verificar/"
CHANGE_PASSWORD_URL = "/cuentas/cambiar-contrasena/"
LOGOUT_URL = "/cuentas/cerrar-sesion/"


def _create_setup_access_code(user, code="123456789", used=False):
    access_code = SetupAccessCode.objects.create(user=user, code=code)
    if used:
        access_code.mark_used()
    return access_code


# ── request_otp ───────────────────────────────────────────────────────────────


class TestRequestOTPView:
    def test_get_renders_form(self, client):
        response = client.get(REQUEST_OTP_URL)
        assert response.status_code == 200
        assert "Inicio de sesión por correo".encode() in response.content
        assert "Otras formas de ingresar".encode() in response.content
        assert "Tengo un código temporal de acceso".encode() in response.content
        assert "Ya creé mi contraseña".encode() in response.content
        assert reverse("accounts:setup_access_code_login").encode() in response.content
        assert reverse("accounts:password_login").encode() in response.content

    def test_authenticated_user_is_redirected(self, client, make_user):
        client.force_login(make_user())
        response = client.get(REQUEST_OTP_URL)
        assert response.status_code == 302

    def test_post_valid_email_creates_otp(self, client, make_user):
        make_user(email="known@example.com")
        with patch("apps.accounts.views.send_otp_email"):
            client.post(REQUEST_OTP_URL, {"email": "known@example.com"})

        assert EmailOTP.objects.filter(email="known@example.com").exists()

    def test_post_valid_email_redirects_to_verify(self, client, make_user):
        make_user(email="known@example.com")
        with patch("apps.accounts.views.send_otp_email"):
            response = client.post(REQUEST_OTP_URL, {"email": "known@example.com"})

        assert response.status_code == 302
        assert response["Location"].endswith(reverse("accounts:verify_otp"))

    def test_post_unknown_email_shows_error(self, client):
        response = client.post(REQUEST_OTP_URL, {"email": "unknown@example.com"})
        assert response.status_code == 200
        assert not EmailOTP.objects.filter(email="unknown@example.com").exists()

    def test_post_stores_email_in_session(self, client, make_user):
        make_user(email="session@example.com")
        with patch("apps.accounts.views.send_otp_email"):
            client.post(REQUEST_OTP_URL, {"email": "session@example.com"})

        assert client.session["otp_email"] == "session@example.com"

    def test_post_calls_send_otp_email(self, client, make_user):
        make_user(email="send@example.com")
        with patch("apps.accounts.views.send_otp_email") as mock_send:
            client.post(REQUEST_OTP_URL, {"email": "send@example.com"})

        mock_send.assert_called_once()
        assert mock_send.call_args[0][0] == "send@example.com"

    def test_rate_limit_blocks_second_request(self, client, make_user):
        make_user(email="rate@example.com")
        with patch("apps.accounts.views.send_otp_email"):
            client.post(REQUEST_OTP_URL, {"email": "rate@example.com"})

        with patch("apps.accounts.views.send_otp_email") as mock_send:
            response = client.post(REQUEST_OTP_URL, {"email": "rate@example.com"})

        assert response.status_code == 200  # re-renders with error
        mock_send.assert_not_called()

    def test_smtp_failure_deletes_otp_and_shows_error(self, client, make_user):
        make_user(email="fail@example.com")
        with patch("apps.accounts.views.send_otp_email", side_effect=SMTPException):
            response = client.post(REQUEST_OTP_URL, {"email": "fail@example.com"})

        assert response.status_code == 200
        assert not EmailOTP.objects.filter(email="fail@example.com").exists()

    def test_post_invalid_email_rerenders_form(self, client):
        response = client.post(REQUEST_OTP_URL, {"email": "not-an-email"})
        assert response.status_code == 200


# ── verify_otp ────────────────────────────────────────────────────────────────


class TestVerifyOTPView:
    def _set_session_email(self, client, email):
        session = client.session
        session["otp_email"] = email
        session.save()

    def _create_otp(self, email, code="123456", minutes=10):
        return EmailOTP.objects.create(
            email=email,
            code=code,
            expires_at=timezone.now() + timezone.timedelta(minutes=minutes),
        )

    def test_get_without_session_redirects_to_request_otp(self, client):
        response = client.get(VERIFY_OTP_URL)
        assert response.status_code == 302
        assert "ingresar" in response["Location"]

    def test_get_with_session_renders_form(self, client):
        self._set_session_email(client, "user@example.com")
        response = client.get(VERIFY_OTP_URL)
        assert response.status_code == 200

    @override_settings(OTP_EXPIRY_MINUTES=7)
    def test_get_uses_configured_otp_expiry_minutes(self, client):
        self._set_session_email(client, "user@example.com")

        response = client.get(VERIFY_OTP_URL)

        assert response.status_code == 200
        assert "Expira en 7 minutos.".encode() in response.content

    def test_valid_otp_marks_otp_as_used(self, client, make_user):
        email = "markused@example.com"
        make_user(email=email)
        otp = self._create_otp(email)
        self._set_session_email(client, email)

        client.post(VERIFY_OTP_URL, {"email": email, "code": "123456"})

        otp.refresh_from_db()
        assert otp.is_used is True

    def test_valid_otp_returning_user_no_duplicate(
        self, client, make_user_with_profile
    ):
        email = "existing@example.com"
        make_user_with_profile(email=email)
        self._create_otp(email)
        self._set_session_email(client, email)

        client.post(VERIFY_OTP_URL, {"email": email, "code": "123456"})

        assert User.objects.filter(email=email).count() == 1

    def test_mismatched_hidden_email_rerenders_with_error(self, client, make_user):
        session_email = "session@example.com"
        submitted_email = "submitted@example.com"
        make_user(email=session_email)
        make_user(email=submitted_email)
        self._create_otp(submitted_email)
        self._set_session_email(client, session_email)

        response = client.post(
            VERIFY_OTP_URL,
            {"email": submitted_email, "code": "123456"},
        )

        assert response.status_code == 200
        assert "_auth_user_id" not in client.session

    def test_expired_otp_rerenders_with_error(self, client, bootstrap_groups):
        email = "expired@example.com"
        EmailOTP.objects.create(
            email=email,
            code="999999",
            expires_at=timezone.now() - timezone.timedelta(seconds=1),
        )
        self._set_session_email(client, email)

        response = client.post(VERIFY_OTP_URL, {"email": email, "code": "999999"})
        assert response.status_code == 200

    def test_wrong_code_rerenders_with_error(self, client, bootstrap_groups):
        email = "wrong@example.com"
        self._create_otp(email, code="000000")
        self._set_session_email(client, email)

        response = client.post(VERIFY_OTP_URL, {"email": email, "code": "111111"})
        assert response.status_code == 200

    def test_non_activated_user_redirects_to_setup(
        self, client, make_user_with_profile, make_company
    ):
        company = make_company()
        email = "notyet@example.com"
        make_user_with_profile(email=email, company=company)
        self._create_otp(email)
        self._set_session_email(client, email)

        response = client.post(VERIFY_OTP_URL, {"email": email, "code": "123456"})

        assert response.status_code == 302
        assert "completar-perfil" in response["Location"]

    def test_activated_user_skips_setup(
        self, client, make_user_with_profile, make_company
    ):
        company = make_company()
        email = "active@example.com"
        user = make_user_with_profile(email=email, company=company)
        user.profile.is_activated = True
        user.profile.save()
        self._create_otp(email)
        self._set_session_email(client, email)

        response = client.post(VERIFY_OTP_URL, {"email": email, "code": "123456"})

        assert response.status_code == 302
        assert "completar-perfil" not in response["Location"]

    def test_admin_user_skips_setup_profile_redirect(
        self, client, make_user, bootstrap_groups
    ):
        email = "admin@example.com"
        user = make_user(email=email)
        user.groups.add(bootstrap_groups["Admins"])
        self._create_otp(email)
        self._set_session_email(client, email)

        response = client.post(VERIFY_OTP_URL, {"email": email, "code": "123456"})

        assert response.status_code == 302
        assert "completar-perfil" not in response["Location"]

    def test_user_without_profile_redirects_to_setup(self, client, make_user):
        email = "noprofile@example.com"
        make_user(email=email)
        self._create_otp(email)
        self._set_session_email(client, email)

        response = client.post(VERIFY_OTP_URL, {"email": email, "code": "123456"})

        assert response.status_code == 302
        assert "completar-perfil" in response["Location"]


# ── password_login ───────────────────────────────────────────────────────────


class TestPasswordLoginView:
    def test_get_renders_form(self, client):
        response = client.get(PASSWORD_LOGIN_URL)
        assert response.status_code == 200

    def test_unusable_password_cannot_login(self, client, make_user):
        make_user(email="disabled@example.com")

        response = client.post(
            PASSWORD_LOGIN_URL,
            {"email": "disabled@example.com", "password": "TempPass123!"},
        )

        assert response.status_code == 200
        assert "_auth_user_id" not in client.session

    def test_valid_password_logs_user_in(
        self, client, make_user_with_profile, make_company
    ):
        company = make_company()
        user = make_user_with_profile(
            email="password@example.com",
            password="TempPass123!",
            company=company,
        )
        user.profile.is_activated = True
        user.profile.save()

        response = client.post(
            PASSWORD_LOGIN_URL,
            {"email": "password@example.com", "password": "TempPass123!"},
        )

        assert response.status_code == 302
        assert client.session["_auth_user_id"] == str(user.pk)

    def test_temporary_password_redirects_to_change_password(
        self, client, make_user_with_profile, make_company
    ):
        company = make_company()
        make_user_with_profile(
            email="temporary@example.com",
            password="TempPass123!",
            company=company,
            must_change_password=True,
        )

        response = client.post(
            PASSWORD_LOGIN_URL,
            {"email": "temporary@example.com", "password": "TempPass123!"},
        )

        assert response.status_code == 302
        assert "cambiar-contrasena" in response["Location"]

    def test_setup_access_code_cannot_login_as_password(self, client, make_user):
        user = make_user(email="setup-password@example.com")
        _create_setup_access_code(user, code="123456789")

        response = client.post(
            PASSWORD_LOGIN_URL,
            {"email": "setup-password@example.com", "password": "123456789"},
        )

        assert response.status_code == 200
        assert "_auth_user_id" not in client.session


# ── setup_access_code_login ──────────────────────────────────────────────────


class TestSetupAccessCodeLoginView:
    def test_get_renders_form(self, client):
        response = client.get(SETUP_ACCESS_CODE_URL)

        assert response.status_code == 200
        assert "código temporal de acceso".encode() in response.content

    def test_authenticated_user_is_redirected(self, client, make_user):
        client.force_login(make_user())

        response = client.get(SETUP_ACCESS_CODE_URL)

        assert response.status_code == 302

    def test_valid_code_redirects_to_password_change(self, client, make_user):
        user = make_user(
            email="first-login@example.com",
            must_change_password=True,
        )
        _create_setup_access_code(user, code="123456789")

        response = client.post(
            SETUP_ACCESS_CODE_URL,
            {"email": "first-login@example.com", "setup_access_code": "123456789"},
        )

        assert response.status_code == 302
        assert "cambiar-contrasena" in response["Location"]
        assert client.session["_auth_user_id"] == str(user.pk)

    def test_valid_code_marks_code_used_and_clears_code(self, client, make_user):
        user = make_user(
            email="consume-view@example.com",
            must_change_password=True,
        )
        access_code = _create_setup_access_code(user, code="123456789")

        client.post(
            SETUP_ACCESS_CODE_URL,
            {"email": "consume-view@example.com", "setup_access_code": "123456789"},
        )

        access_code.refresh_from_db()
        assert access_code.used_at is not None
        assert access_code.code is None

    def test_setup_code_user_must_create_password_before_app_access(
        self, client, make_user
    ):
        user = make_user(email="blocked@example.com", must_change_password=True)
        _create_setup_access_code(user, code="123456789")
        client.post(
            SETUP_ACCESS_CODE_URL,
            {"email": "blocked@example.com", "setup_access_code": "123456789"},
        )

        response = client.get(SETUP_PROFILE_URL)

        assert response.status_code == 302
        assert "cambiar-contrasena" in response["Location"]

    def test_user_can_login_with_created_password_after_setup(self, client, make_user):
        user = make_user(email="future-password@example.com", must_change_password=True)
        _create_setup_access_code(user, code="123456789")
        client.post(
            SETUP_ACCESS_CODE_URL,
            {
                "email": "future-password@example.com",
                "setup_access_code": "123456789",
            },
        )
        client.post(
            CHANGE_PASSWORD_URL,
            {
                "new_password1": "NewStrongPass123!",
                "new_password2": "NewStrongPass123!",
            },
        )
        client.post(LOGOUT_URL)

        response = client.post(
            PASSWORD_LOGIN_URL,
            {
                "email": "future-password@example.com",
                "password": "NewStrongPass123!",
            },
        )

        assert response.status_code == 302
        assert client.session["_auth_user_id"] == str(user.pk)

    def test_unknown_email_is_rejected_with_generic_error(self, client):
        response = client.post(
            SETUP_ACCESS_CODE_URL,
            {"email": "unknown@example.com", "setup_access_code": "123456789"},
        )

        assert response.status_code == 200
        assert "_auth_user_id" not in client.session

    def test_inactive_user_is_rejected_with_generic_error(self, client, make_user):
        user = make_user(
            email="inactive-setup@example.com",
            must_change_password=True,
            is_active=False,
        )
        _create_setup_access_code(user, code="123456789")

        response = client.post(
            SETUP_ACCESS_CODE_URL,
            {"email": "inactive-setup@example.com", "setup_access_code": "123456789"},
        )

        assert response.status_code == 200
        assert "_auth_user_id" not in client.session

    def test_user_without_code_is_rejected_with_generic_error(self, client, make_user):
        make_user(email="no-code@example.com", must_change_password=True)

        response = client.post(
            SETUP_ACCESS_CODE_URL,
            {"email": "no-code@example.com", "setup_access_code": "123456789"},
        )

        assert response.status_code == 200
        assert "_auth_user_id" not in client.session

    def test_code_for_other_user_is_rejected(self, client, make_user):
        make_user(email="target@example.com", must_change_password=True)
        other = make_user(email="other-code@example.com", must_change_password=True)
        _create_setup_access_code(other, code="123456789")

        response = client.post(
            SETUP_ACCESS_CODE_URL,
            {"email": "target@example.com", "setup_access_code": "123456789"},
        )

        assert response.status_code == 200
        assert "_auth_user_id" not in client.session

    def test_used_code_is_rejected(self, client, make_user):
        user = make_user(email="used-view@example.com", must_change_password=True)
        _create_setup_access_code(user, code="123456789", used=True)

        response = client.post(
            SETUP_ACCESS_CODE_URL,
            {"email": "used-view@example.com", "setup_access_code": "123456789"},
        )

        assert response.status_code == 200
        assert "_auth_user_id" not in client.session

    def test_malformed_code_rerenders_form(self, client, make_user):
        make_user(email="malformed@example.com", must_change_password=True)

        response = client.post(
            SETUP_ACCESS_CODE_URL,
            {"email": "malformed@example.com", "setup_access_code": "not-a-code"},
        )

        assert response.status_code == 200
        assert "_auth_user_id" not in client.session

    def test_hyphenated_code_is_accepted(self, client, make_user):
        user = make_user(email="hyphenated@example.com", must_change_password=True)
        _create_setup_access_code(user, code="123456789")

        response = client.post(
            SETUP_ACCESS_CODE_URL,
            {
                "email": "hyphenated@example.com",
                "setup_access_code": "123-456-789",
            },
        )

        assert response.status_code == 302
        assert "cambiar-contrasena" in response["Location"]


# ── change_password ──────────────────────────────────────────────────────────


class TestChangePasswordView:
    def test_requires_password_change_before_other_pages(self, client, make_user):
        user = make_user(
            email="mustchange@example.com",
            password="TempPass123!",
            must_change_password=True,
        )
        client.force_login(user)

        response = client.get(SETUP_PROFILE_URL)

        assert response.status_code == 302
        assert "cambiar-contrasena" in response["Location"]

    def test_post_changes_password_and_clears_required_flag(self, client, make_user):
        user = make_user(
            email="change@example.com",
            password="TempPass123!",
            must_change_password=True,
        )
        client.force_login(user)

        response = client.post(
            CHANGE_PASSWORD_URL,
            {
                "new_password1": "NewStrongPass123!",
                "new_password2": "NewStrongPass123!",
            },
        )

        user.refresh_from_db()
        assert response.status_code == 302
        assert user.must_change_password is False
        assert user.check_password("NewStrongPass123!")


# ── setup_profile ─────────────────────────────────────────────────────────────

SETUP_PROFILE_URL = "/cuentas/completar-perfil/"


def _activation_post(company, **overrides):
    """A complete activation body. Name is required, so every POST carries it."""
    payload = {
        "reference_code": company.reference_code,
        "first_name": "Ana",
        "last_name": "López",
    }
    payload.update(overrides)
    return payload


class TestSetupProfileView:
    def test_admin_get_redirects_to_home(self, client, make_user, bootstrap_groups):
        user = make_user(email="admin2@example.com")
        user.groups.add(bootstrap_groups["Admins"])
        client.force_login(user)

        response = client.get(SETUP_PROFILE_URL)

        assert response.status_code == 302
        assert "completar-perfil" not in response["Location"]

    def test_admin_post_redirects_to_home(self, client, make_user, bootstrap_groups):
        user = make_user(email="admin3@example.com")
        user.groups.add(bootstrap_groups["Admins"])
        client.force_login(user)

        response = client.post(SETUP_PROFILE_URL, {"reference_code": "XXXXX"})

        assert response.status_code == 302
        assert "completar-perfil" not in response["Location"]

    def test_non_admin_unauthenticated_redirects_to_login(self, client):
        response = client.get(SETUP_PROFILE_URL)
        assert response.status_code == 302
        assert "ingresar" in response["Location"]

    def test_correct_code_activates_and_redirects(
        self, client, make_user_with_profile, make_company, make_area
    ):
        company = make_company()
        area = make_area(company, name="Ventas")
        user = make_user_with_profile(email="activate@example.com", company=company)
        client.force_login(user)

        response = client.post(
            SETUP_PROFILE_URL, _activation_post(company, area=area.pk)
        )

        user.profile.refresh_from_db()
        assert user.profile.is_activated is True
        assert user.profile.area == area
        assert response.status_code == 302
        assert "completar-perfil" not in response["Location"]

    def test_wrong_code_shows_error(
        self, client, make_user_with_profile, make_company, make_area
    ):
        company = make_company()
        area = make_area(company, name="Ventas")
        user = make_user_with_profile(email="wrongcode@example.com", company=company)
        client.force_login(user)

        response = client.post(
            SETUP_PROFILE_URL,
            _activation_post(company, reference_code="ZZZZZ", area=area.pk),
        )

        user.profile.refresh_from_db()
        assert user.profile.is_activated is False
        assert user.profile.area is None
        assert response.status_code == 200

    def test_foreign_company_area_is_rejected(
        self, client, make_user_with_profile, make_company, make_area
    ):
        company = make_company(name="Cliente A")
        other = make_company(name="Cliente B")
        make_area(company, name="Ventas")
        foreign = make_area(other, name="Ajena")
        user = make_user_with_profile(email="foreign@example.com", company=company)
        client.force_login(user)

        response = client.post(
            SETUP_PROFILE_URL, _activation_post(company, area=foreign.pk)
        )

        user.profile.refresh_from_db()
        assert response.status_code == 200
        assert user.profile.is_activated is False
        assert user.profile.area is None

    def test_missing_area_shows_field_error(
        self, client, make_user_with_profile, make_company, make_area
    ):
        company = make_company()
        make_area(company, name="Ventas")
        user = make_user_with_profile(email="noarea@example.com", company=company)
        client.force_login(user)

        response = client.post(SETUP_PROFILE_URL, _activation_post(company))

        user.profile.refresh_from_db()
        assert response.status_code == 200
        assert user.profile.is_activated is False
        assert "area" in response.context["form"].errors

    def test_company_without_areas_blocks_activation(
        self, client, make_user_with_profile, make_company
    ):
        company = make_company()
        user = make_user_with_profile(email="noareas@example.com", company=company)
        client.force_login(user)

        response = client.get(SETUP_PROFILE_URL)

        assert response.status_code == 200
        assert response.context["no_areas"] is True

    def test_inactive_area_is_not_selectable(
        self, client, make_user_with_profile, make_company, make_area
    ):
        company = make_company()
        make_area(company, name="Ventas")
        retired = make_area(company, name="Retirada", is_active=False)
        user = make_user_with_profile(email="retired@example.com", company=company)
        client.force_login(user)

        response = client.post(
            SETUP_PROFILE_URL, _activation_post(company, area=retired.pk)
        )

        user.profile.refresh_from_db()
        assert response.status_code == 200
        assert user.profile.is_activated is False

    def test_single_location_is_auto_assigned_and_not_rendered(
        self, client, make_user_with_profile, make_company, make_area, make_location
    ):
        company = make_company()
        area = make_area(company, name="Ventas")
        only = make_location(company, name="Matriz")
        user = make_user_with_profile(email="oneloc@example.com", company=company)
        client.force_login(user)

        page = client.get(SETUP_PROFILE_URL)
        assert 'name="location"' not in page.content.decode()

        client.post(SETUP_PROFILE_URL, _activation_post(company, area=area.pk))

        user.profile.refresh_from_db()
        assert user.profile.is_activated is True
        assert user.profile.location == only

    def test_posted_location_ignored_when_field_hidden(
        self, client, make_user_with_profile, make_company, make_area, make_location
    ):
        company = make_company()
        area = make_area(company, name="Ventas")
        only = make_location(company, name="Matriz")
        other_company = make_company(name="Cliente B")
        foreign_location = make_location(other_company, name="Ajena")
        user = make_user_with_profile(email="ignoreloc@example.com", company=company)
        client.force_login(user)

        client.post(
            SETUP_PROFILE_URL,
            _activation_post(company, area=area.pk, location=foreign_location.pk),
        )

        user.profile.refresh_from_db()
        assert user.profile.location == only

    def test_several_locations_require_a_choice(
        self, client, make_user_with_profile, make_company, make_area, make_location
    ):
        company = make_company()
        area = make_area(company, name="Ventas")
        make_location(company, name="Matriz")
        norte = make_location(company, name="Norte")
        user = make_user_with_profile(email="multiloc@example.com", company=company)
        client.force_login(user)

        # The picker must actually render, or the page is unsubmittable.
        page = client.get(SETUP_PROFILE_URL)
        assert 'name="location"' in page.content.decode()

        response = client.post(
            SETUP_PROFILE_URL, _activation_post(company, area=area.pk)
        )
        assert response.status_code == 200
        assert "location" in response.context["form"].errors

        client.post(
            SETUP_PROFILE_URL,
            _activation_post(company, area=area.pk, location=norte.pk),
        )
        user.profile.refresh_from_db()
        assert user.profile.location == norte

    def test_zero_locations_activates_with_null_location(
        self, client, make_user_with_profile, make_company, make_area
    ):
        company = make_company()
        area = make_area(company, name="Ventas")
        user = make_user_with_profile(email="zeroloc@example.com", company=company)
        client.force_login(user)

        client.post(SETUP_PROFILE_URL, _activation_post(company, area=area.pk))

        user.profile.refresh_from_db()
        assert user.profile.is_activated is True
        assert user.profile.location is None

    def test_activation_saves_name_and_cargo(
        self, client, make_user_with_profile, make_company, make_area
    ):
        company = make_company()
        area = make_area(company, name="Ventas")
        user = make_user_with_profile(email="identity@example.com", company=company)
        client.force_login(user)

        client.post(
            SETUP_PROFILE_URL,
            _activation_post(
                company,
                area=area.pk,
                first_name="Ana",
                last_name="López",
                position="Analista",
            ),
        )

        user.refresh_from_db()
        user.profile.refresh_from_db()
        assert user.first_name == "Ana"
        assert user.last_name == "López"
        assert user.profile.position == "Analista"

    def test_missing_name_blocks_activation(
        self, client, make_user_with_profile, make_company, make_area
    ):
        company = make_company()
        area = make_area(company, name="Ventas")
        user = make_user_with_profile(email="noname@example.com", company=company)
        client.force_login(user)

        response = client.post(
            SETUP_PROFILE_URL,
            _activation_post(company, area=area.pk, first_name="", last_name=""),
        )

        user.profile.refresh_from_db()
        assert response.status_code == 200
        assert user.profile.is_activated is False
        assert "first_name" in response.context["form"].errors

    def test_activation_without_cargo_leaves_it_blank(
        self, client, make_user_with_profile, make_company, make_area
    ):
        company = make_company()
        area = make_area(company, name="Ventas")
        user = make_user_with_profile(email="nocargo@example.com", company=company)
        client.force_login(user)

        client.post(SETUP_PROFILE_URL, _activation_post(company, area=area.pk))

        user.profile.refresh_from_db()
        assert user.profile.is_activated is True
        assert user.profile.position == ""

    def test_form_prefills_details_already_on_record(
        self, client, make_user_with_profile, make_company, make_area
    ):
        """An admin who filled a user in by hand shouldn't make them retype it."""
        company = make_company()
        make_area(company, name="Ventas")
        user = make_user_with_profile(email="prefill@example.com", company=company)
        user.first_name = "Ana"
        user.last_name = "López"
        user.save(update_fields=["first_name", "last_name"])
        user.profile.position = "Analista"
        user.profile.save(update_fields=["position"])
        client.force_login(user)

        form = client.get(SETUP_PROFILE_URL).context["form"]

        assert form.initial["first_name"] == "Ana"
        assert form.initial["last_name"] == "López"
        assert form.initial["position"] == "Analista"

    def test_name_is_not_saved_when_activation_fails(
        self, client, make_user_with_profile, make_company, make_area
    ):
        """A rejected reference code must leave the user row untouched."""
        company = make_company()
        area = make_area(company, name="Ventas")
        user = make_user_with_profile(email="atomic@example.com", company=company)
        client.force_login(user)

        client.post(
            SETUP_PROFILE_URL,
            _activation_post(company, reference_code="ZZZZZ", area=area.pk),
        )

        user.refresh_from_db()
        assert user.first_name == ""
        assert user.profile.is_activated is False

    def test_already_activated_redirects_to_home(
        self, client, make_user_with_profile, make_company
    ):
        company = make_company()
        user = make_user_with_profile(email="alreadyon@example.com", company=company)
        user.profile.is_activated = True
        user.profile.save()
        client.force_login(user)

        response = client.get(SETUP_PROFILE_URL)

        assert response.status_code == 302
        assert "completar-perfil" not in response["Location"]

    def test_no_company_linked_shows_error_page(self, client, make_user):
        user = make_user(email="nocompany@example.com")
        UserProfile.objects.create(user=user, company=None)
        client.force_login(user)

        response = client.get(SETUP_PROFILE_URL)

        assert response.status_code == 200
        assert response.context["no_company"] is True


# ── logout_view ───────────────────────────────────────────────────────────────


class TestLogoutView:
    def test_get_returns_405(self, client, make_user):
        client.force_login(make_user())
        response = client.get(LOGOUT_URL)
        assert response.status_code == 405

    def test_post_logs_out_and_redirects(self, client, make_user):
        user = make_user()
        client.force_login(user)
        response = client.post(LOGOUT_URL)
        assert response.status_code == 302
        assert "_auth_user_id" not in client.session
