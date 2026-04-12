from smtplib import SMTPException
from unittest.mock import patch

import pytest
from django.urls import reverse
from django.utils import timezone

from apps.accounts.models import EmailOTP, User

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

    def test_post_valid_email_creates_otp(self, client):
        with patch("apps.accounts.views.send_otp_email"):
            client.post(REQUEST_OTP_URL, {"email": "new@example.com"})

        assert EmailOTP.objects.filter(email="new@example.com").exists()

    def test_post_valid_email_redirects_to_verify(self, client):
        with patch("apps.accounts.views.send_otp_email"):
            response = client.post(REQUEST_OTP_URL, {"email": "new@example.com"})

        assert response.status_code == 302
        assert response["Location"].endswith(reverse("accounts:verify_otp"))

    def test_post_stores_email_in_session(self, client):
        with patch("apps.accounts.views.send_otp_email"):
            client.post(REQUEST_OTP_URL, {"email": "session@example.com"})

        assert client.session["otp_email"] == "session@example.com"

    def test_post_calls_send_otp_email(self, client):
        with patch("apps.accounts.views.send_otp_email") as mock_send:
            client.post(REQUEST_OTP_URL, {"email": "send@example.com"})

        mock_send.assert_called_once()
        assert mock_send.call_args[0][0] == "send@example.com"

    def test_rate_limit_blocks_second_request(self, client):
        with patch("apps.accounts.views.send_otp_email"):
            client.post(REQUEST_OTP_URL, {"email": "rate@example.com"})

        with patch("apps.accounts.views.send_otp_email") as mock_send:
            response = client.post(REQUEST_OTP_URL, {"email": "rate@example.com"})

        assert response.status_code == 200  # re-renders with error
        mock_send.assert_not_called()

    def test_smtp_failure_deletes_otp_and_shows_error(self, client):
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

    def test_valid_otp_first_login_creates_user(self, client, bootstrap_groups):
        email = "brandnew@example.com"
        self._create_otp(email)
        self._set_session_email(client, email)

        client.post(VERIFY_OTP_URL, {"email": email, "code": "123456"})

        assert User.objects.filter(email=email).exists()

    def test_valid_otp_first_login_adds_to_employees_group(
        self, client, bootstrap_groups
    ):
        email = "employee@example.com"
        self._create_otp(email)
        self._set_session_email(client, email)

        client.post(VERIFY_OTP_URL, {"email": email, "code": "123456"})

        user = User.objects.get(email=email)
        assert user.groups.filter(name="Employees").exists()

    def test_valid_otp_marks_otp_as_used(self, client, bootstrap_groups):
        email = "markused@example.com"
        otp = self._create_otp(email)
        self._set_session_email(client, email)

        client.post(VERIFY_OTP_URL, {"email": email, "code": "123456"})

        otp.refresh_from_db()
        assert otp.is_used is True

    def test_valid_otp_returning_user_no_duplicate(
        self, client, make_user_with_profile, bootstrap_groups
    ):
        email = "existing@example.com"
        make_user_with_profile(email=email, position="Dev")
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

    def test_successful_login_with_incomplete_profile_redirects_to_setup(
        self, client, bootstrap_groups
    ):
        email = "noprofile@example.com"
        self._create_otp(email)
        self._set_session_email(client, email)

        response = client.post(VERIFY_OTP_URL, {"email": email, "code": "123456"})
        assert response.status_code == 302
        assert "completar-perfil" in response["Location"]


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
