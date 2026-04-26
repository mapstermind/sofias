from smtplib import SMTPException
from unittest.mock import patch

import pytest
from django.urls import reverse
from django.utils import timezone

from apps.accounts.models import EmailOTP, User, UserProfile

pytestmark = pytest.mark.django_db

REQUEST_OTP_URL = "/cuentas/ingresar/"
VERIFY_OTP_URL = "/cuentas/verificar/"
LOGOUT_URL = "/cuentas/cerrar-sesion/"


# ── request_otp ───────────────────────────────────────────────────────────────


class TestRequestOTPView:
    def test_get_renders_form(self, client):
        response = client.get(REQUEST_OTP_URL)
        assert response.status_code == 200

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

    def test_valid_otp_marks_otp_as_used(self, client, make_user):
        email = "markused@example.com"
        make_user(email=email)
        otp = self._create_otp(email)
        self._set_session_email(client, email)

        client.post(VERIFY_OTP_URL, {"email": email, "code": "123456"})

        otp.refresh_from_db()
        assert otp.is_used is True

    def test_valid_otp_returning_user_no_duplicate(self, client, make_user_with_profile):
        email = "existing@example.com"
        make_user_with_profile(email=email)
        self._create_otp(email)
        self._set_session_email(client, email)

        client.post(VERIFY_OTP_URL, {"email": email, "code": "123456"})

        assert User.objects.filter(email=email).count() == 1

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

    def test_non_activated_user_redirects_to_setup(self, client, make_user_with_profile, make_company):
        company = make_company()
        email = "notyet@example.com"
        make_user_with_profile(email=email, company=company)
        self._create_otp(email)
        self._set_session_email(client, email)

        response = client.post(VERIFY_OTP_URL, {"email": email, "code": "123456"})

        assert response.status_code == 302
        assert "completar-perfil" in response["Location"]

    def test_activated_user_skips_setup(self, client, make_user_with_profile, make_company):
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


# ── setup_profile ─────────────────────────────────────────────────────────────

SETUP_PROFILE_URL = "/cuentas/completar-perfil/"


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
        self, client, make_user_with_profile, make_company
    ):
        company = make_company()
        user = make_user_with_profile(email="activate@example.com", company=company)
        client.force_login(user)

        response = client.post(
            SETUP_PROFILE_URL, {"reference_code": company.reference_code}
        )

        user.profile.refresh_from_db()
        assert user.profile.is_activated is True
        assert response.status_code == 302
        assert "completar-perfil" not in response["Location"]

    def test_wrong_code_shows_error(
        self, client, make_user_with_profile, make_company
    ):
        company = make_company()
        user = make_user_with_profile(email="wrongcode@example.com", company=company)
        client.force_login(user)

        response = client.post(SETUP_PROFILE_URL, {"reference_code": "ZZZZZ"})

        user.profile.refresh_from_db()
        assert user.profile.is_activated is False
        assert response.status_code == 200

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
