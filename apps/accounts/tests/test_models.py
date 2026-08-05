import pytest
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.utils import timezone

from apps.accounts.models import (
    CompanyArea,
    CompanyLocation,
    EmailOTP,
    SetupAccessCode,
)
from apps.accounts.utils import generate_unique_username

pytestmark = pytest.mark.django_db


class TestCompanyCatalogs:
    """CompanyArea / CompanyLocation share an abstract base, so both are covered."""

    @pytest.mark.parametrize("model", [CompanyArea, CompanyLocation])
    def test_duplicate_name_in_same_company_is_rejected_case_insensitively(
        self, make_company, model
    ):
        company = make_company()
        model.objects.create(company=company, name="Ventas")
        with pytest.raises(IntegrityError):
            model.objects.create(company=company, name="ventas")

    @pytest.mark.parametrize("model", [CompanyArea, CompanyLocation])
    def test_same_name_allowed_across_companies(self, make_company, model):
        first = make_company(name="Cliente A")
        second = make_company(name="Cliente B")
        model.objects.create(company=first, name="Operaciones")
        model.objects.create(company=second, name="Operaciones")
        assert model.objects.filter(name="Operaciones").count() == 2

    @pytest.mark.parametrize("model", [CompanyArea, CompanyLocation])
    def test_str_is_the_name(self, make_company, model):
        entry = model.objects.create(company=make_company(), name="Almacén")
        assert str(entry) == "Almacén"

    @pytest.mark.parametrize("model", [CompanyArea, CompanyLocation])
    def test_default_ordering_is_alphabetical(self, make_company, model):
        company = make_company()
        model.objects.create(company=company, name="Ventas")
        model.objects.create(company=company, name="Almacén")
        assert [e.name for e in model.objects.all()] == ["Almacén", "Ventas"]

    @pytest.mark.parametrize("model", [CompanyArea, CompanyLocation])
    def test_clean_strips_whitespace_and_rejects_blank(self, make_company, model):
        company = make_company()
        entry = model(company=company, name="  Ventas  ")
        entry.clean()
        assert entry.name == "Ventas"

        with pytest.raises(ValidationError):
            model(company=company, name="   ").clean()

    def test_deleting_company_cascades_both_catalogs(
        self, make_company, make_area, make_location
    ):
        company = make_company()
        make_area(company, name="Ventas")
        make_location(company, name="Matriz")
        company.delete()
        assert CompanyArea.objects.count() == 0
        assert CompanyLocation.objects.count() == 0


class TestUserProfileCatalogLinks:
    def test_deleting_area_nulls_the_profile_but_keeps_it(
        self, make_company, make_area, make_user_with_profile
    ):
        company = make_company()
        area = make_area(company, name="Ventas")
        user = make_user_with_profile(email="a@x.mx", company=company, area=area)

        area.delete()

        user.profile.refresh_from_db()
        assert user.profile.pk is not None
        assert user.profile.area is None
        assert user.profile.company == company

    def test_full_clean_rejects_area_from_another_company(
        self, make_company, make_area, make_user_with_profile
    ):
        own = make_company(name="Cliente A")
        other = make_company(name="Cliente B")
        foreign_area = make_area(other, name="Ventas")
        user = make_user_with_profile(email="b@x.mx", company=own)

        profile = user.profile
        profile.area = foreign_area
        with pytest.raises(ValidationError) as exc:
            profile.full_clean()
        assert "area" in exc.value.message_dict

    def test_full_clean_rejects_location_from_another_company(
        self, make_company, make_location, make_user_with_profile
    ):
        own = make_company(name="Cliente A")
        other = make_company(name="Cliente B")
        foreign_location = make_location(other, name="Matriz")
        user = make_user_with_profile(email="c@x.mx", company=own)

        profile = user.profile
        profile.location = foreign_location
        with pytest.raises(ValidationError) as exc:
            profile.full_clean()
        assert "location" in exc.value.message_dict


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


class TestSetupAccessCode:
    def test_setup_access_code_is_valid_when_unused(self, make_user):
        user = make_user(email="setup@example.com", must_change_password=True)
        access_code = SetupAccessCode.objects.create(user=user, code="123456789")

        assert access_code.is_valid("123456789") is True

    def test_setup_access_code_is_invalid_when_used(self, make_user):
        user = make_user(email="used@example.com", must_change_password=True)
        access_code = SetupAccessCode.objects.create(
            user=user,
            code=None,
            used_at=timezone.now(),
        )

        assert access_code.is_valid("123456789") is False

    def test_setup_access_code_does_not_expire(self, make_user):
        user = make_user(email="old@example.com", must_change_password=True)
        access_code = SetupAccessCode.objects.create(user=user, code="987654321")
        SetupAccessCode.objects.filter(pk=access_code.pk).update(
            created_at=timezone.now() - timezone.timedelta(days=365)
        )
        access_code.refresh_from_db()

        assert access_code.is_valid("987654321") is True

    def test_mark_used_sets_used_at_and_clears_code(self, make_user):
        user = make_user(email="consume@example.com", must_change_password=True)
        access_code = SetupAccessCode.objects.create(user=user, code="111222333")

        access_code.mark_used()
        access_code.refresh_from_db()

        assert access_code.used_at is not None
        assert access_code.code is None


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
