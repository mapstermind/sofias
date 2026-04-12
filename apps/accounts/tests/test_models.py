import pytest
from django.utils import timezone

from apps.accounts.models import EmailOTP
from apps.accounts.utils import generate_unique_username

pytestmark = pytest.mark.django_db


class TestEmailOTPIsValid:
    def _make_otp(self, email="a@example.com", code="123456", **kwargs):
        return EmailOTP.objects.create(
            email=email,
            code=code,
            expires_at=timezone.now() + timezone.timedelta(minutes=10),
            **kwargs,
        )

    def test_fresh_otp_is_valid(self):
        otp = self._make_otp()
        assert otp.is_valid() is True

    def test_used_otp_is_not_valid(self):
        otp = self._make_otp(is_used=True)
        assert otp.is_valid() is False

    def test_expired_otp_is_not_valid(self):
        otp = EmailOTP.objects.create(
            email="b@example.com",
            code="654321",
            expires_at=timezone.now() - timezone.timedelta(seconds=1),
        )
        assert otp.is_valid() is False

    def test_used_and_expired_otp_is_not_valid(self):
        otp = EmailOTP.objects.create(
            email="c@example.com",
            code="000000",
            expires_at=timezone.now() - timezone.timedelta(minutes=5),
            is_used=True,
        )
        assert otp.is_valid() is False


class TestCompanyReferenceCode:
    def test_reference_code_auto_generated_on_create(self, make_company):
        company = make_company()
        assert company.reference_code != ""
        assert len(company.reference_code) == 5
        assert company.reference_code.isalnum()

    def test_reference_code_not_overwritten_on_update(self, make_company):
        company = make_company()
        original = company.reference_code
        company.name = "Updated Name"
        company.save()
        company.refresh_from_db()
        assert company.reference_code == original

    def test_reference_code_unique_across_companies(self, make_company):
        c1 = make_company(name="Company One", legal_name="One SA de CV")
        c2 = make_company(name="Company Two", legal_name="Two SA de CV")
        assert c1.reference_code != c2.reference_code


class TestGenerateUniqueUsername:
    def test_returns_local_part_when_no_collision(self):
        result = generate_unique_username("jane@example.com")
        assert result == "jane"

    def test_appends_counter_on_collision(self, make_user):
        # Create a user that occupies the "john" username
        make_user(email="john@example.com", username="john")
        result = generate_unique_username("john@other.com")
        assert result == "john1"

    def test_handles_multiple_collisions(self, make_user):
        make_user(email="a@example.com", username="bob")
        make_user(email="b@example.com", username="bob1")
        result = generate_unique_username("bob@other.com")
        assert result == "bob2"
