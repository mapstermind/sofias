import pytest

from apps.accounts.forms import (
    EmailRequestForm,
    OTPVerifyForm,
    ProfileActivationForm,
    SetupAccessCodeLoginForm,
)

# Most forms are pure Python and need no database. ProfileActivationForm is the
# exception — its área/localidad pickers are company-scoped querysets.


class TestOTPVerifyFormCleanCode:
    def _form(self, code):
        return OTPVerifyForm(data={"email": "user@example.com", "code": code})

    def test_valid_six_digit_code(self):
        form = self._form("123456")
        assert form.is_valid()
        assert form.cleaned_data["code"] == "123456"

    def test_rejects_alphabetic_characters(self):
        form = self._form("12345a")
        assert not form.is_valid()
        assert "code" in form.errors

    def test_rejects_too_short(self):
        form = self._form("12345")
        assert not form.is_valid()

    def test_rejects_empty(self):
        form = self._form("")
        assert not form.is_valid()

    def test_rejects_spaces(self):
        form = self._form("123 56")
        assert not form.is_valid()


@pytest.mark.django_db
class TestProfileActivationFormCleanReferenceCode:
    @pytest.fixture
    def company_with_area(self, make_company, make_area):
        company = make_company()
        return company, make_area(company, name="Ventas")

    def _form(self, code, company_with_area):
        company, area = company_with_area
        return ProfileActivationForm(
            data={
                "reference_code": code,
                "first_name": "Ana",
                "last_name": "López",
                "area": area.pk,
            },
            company=company,
        )

    def test_lowercased_input_is_uppercased(self, company_with_area):
        form = self._form("abc12", company_with_area)
        assert form.is_valid(), form.errors
        assert form.cleaned_data["reference_code"] == "ABC12"

    def test_already_uppercase_passes(self, company_with_area):
        form = self._form("XYZ99", company_with_area)
        assert form.is_valid()
        assert form.cleaned_data["reference_code"] == "XYZ99"

    def test_special_characters_rejected(self, company_with_area):
        form = self._form("AB-12", company_with_area)
        assert not form.is_valid()
        assert "reference_code" in form.errors

    def test_too_short_rejected(self, company_with_area):
        form = self._form("AB1", company_with_area)
        assert not form.is_valid()

    def test_empty_rejected(self, company_with_area):
        form = self._form("", company_with_area)
        assert not form.is_valid()


@pytest.mark.django_db
class TestProfileActivationFormIdentityFields:
    """Name and cargo are collected here, so the CSV import doesn't carry them."""

    @pytest.fixture
    def company_with_area(self, make_company, make_area):
        company = make_company()
        return company, make_area(company, name="Ventas")

    def _data(self, company, area, **overrides):
        data = {
            "reference_code": company.reference_code,
            "first_name": "Ana",
            "last_name": "López",
            "area": area.pk,
        }
        data.update(overrides)
        return data

    def test_name_is_required(self, company_with_area):
        company, area = company_with_area
        form = ProfileActivationForm(
            data=self._data(company, area, first_name="", last_name=""),
            company=company,
        )
        assert not form.is_valid()
        assert "first_name" in form.errors
        assert "last_name" in form.errors

    def test_cargo_is_optional_and_defaults_to_blank(self, company_with_area):
        company, area = company_with_area
        form = ProfileActivationForm(data=self._data(company, area), company=company)
        assert form.is_valid(), form.errors
        assert form.cleaned_data["position"] == ""

    def test_values_are_stripped(self, company_with_area):
        company, area = company_with_area
        form = ProfileActivationForm(
            data=self._data(
                company,
                area,
                first_name="  Ana  ",
                last_name="  López  ",
                position="  Analista  ",
            ),
            company=company,
        )
        assert form.is_valid(), form.errors
        assert form.cleaned_data["first_name"] == "Ana"
        assert form.cleaned_data["last_name"] == "López"
        assert form.cleaned_data["position"] == "Analista"


@pytest.mark.django_db
class TestProfileActivationFormScoping:
    def test_area_choices_limited_to_active_entries_of_the_company(
        self, make_company, make_area
    ):
        company = make_company(name="Cliente A")
        other = make_company(name="Cliente B")
        mine = make_area(company, name="Ventas")
        make_area(company, name="Retirada", is_active=False)
        make_area(other, name="Ajena")

        form = ProfileActivationForm(company=company)
        assert list(form.fields["area"].queryset) == [mine]

    def test_foreign_company_area_is_rejected(self, make_company, make_area):
        company = make_company(name="Cliente A")
        other = make_company(name="Cliente B")
        make_area(company, name="Ventas")
        foreign = make_area(other, name="Ajena")

        form = ProfileActivationForm(
            data={
                "reference_code": company.reference_code,
                "first_name": "Ana",
                "last_name": "López",
                "area": foreign.pk,
            },
            company=company,
        )
        assert not form.is_valid()
        assert "area" in form.errors

    def test_location_field_absent_when_company_has_none(self, make_company, make_area):
        company = make_company()
        make_area(company, name="Ventas")

        form = ProfileActivationForm(company=company)
        assert "location" not in form.fields
        assert form.implicit_location is None

    def test_single_location_is_implicit_not_asked(
        self, make_company, make_area, make_location
    ):
        company = make_company()
        make_area(company, name="Ventas")
        only = make_location(company, name="Matriz")

        form = ProfileActivationForm(company=company)
        assert "location" not in form.fields
        assert form.implicit_location == only

    def test_location_required_when_company_has_several(
        self, make_company, make_area, make_location
    ):
        company = make_company()
        make_area(company, name="Ventas")
        make_location(company, name="Matriz")
        make_location(company, name="Norte")

        form = ProfileActivationForm(company=company)
        assert "location" in form.fields
        assert form.fields["location"].required
        assert form.implicit_location is None


class TestEmailRequestForm:
    def test_valid_email(self):
        form = EmailRequestForm(data={"email": "user@example.com"})
        assert form.is_valid()

    def test_invalid_email_rejected(self):
        form = EmailRequestForm(data={"email": "not-an-email"})
        assert not form.is_valid()


class TestSetupAccessCodeLoginForm:
    def _form(self, email="user@example.com", code="123456789"):
        return SetupAccessCodeLoginForm(
            data={"email": email, "setup_access_code": code}
        )

    def test_valid_nine_digit_code(self):
        form = self._form()
        assert form.is_valid(), form.errors
        assert form.cleaned_data["setup_access_code"] == "123456789"

    def test_hyphenated_code_is_normalized(self):
        form = self._form(code="123-456-789")
        assert form.is_valid(), form.errors
        assert form.cleaned_data["setup_access_code"] == "123456789"

    def test_spaced_code_is_normalized(self):
        form = self._form(code="123 456 789")
        assert form.is_valid(), form.errors
        assert form.cleaned_data["setup_access_code"] == "123456789"

    def test_rejects_non_digits(self):
        form = self._form(code="12345ABCD")
        assert not form.is_valid()
        assert "setup_access_code" in form.errors

    def test_rejects_too_short_code(self):
        form = self._form(code="12345678")
        assert not form.is_valid()
        assert "setup_access_code" in form.errors

    def test_rejects_too_long_code(self):
        form = self._form(code="1234567890")
        assert not form.is_valid()
        assert "setup_access_code" in form.errors

    def test_invalid_email_rejected(self):
        form = self._form(email="not-an-email")
        assert not form.is_valid()
        assert "email" in form.errors
