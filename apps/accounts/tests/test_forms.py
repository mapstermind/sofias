from apps.accounts.forms import EmailRequestForm, OTPVerifyForm, ProfileSetupForm

# Forms are pure Python — no database access needed for these tests.


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


class TestProfileSetupFormCleanReferenceCode:
    def _form(self, code):
        return ProfileSetupForm(
            data={
                "first_name": "Jane",
                "last_name": "Smith",
                "position": "Engineer",
                "reference_code": code,
            }
        )

    def test_lowercased_input_is_uppercased(self):
        form = self._form("abc12")
        assert form.is_valid(), form.errors
        assert form.cleaned_data["reference_code"] == "ABC12"

    def test_already_uppercase_passes(self):
        form = self._form("XYZ99")
        assert form.is_valid()
        assert form.cleaned_data["reference_code"] == "XYZ99"

    def test_special_characters_rejected(self):
        form = self._form("AB-12")
        assert not form.is_valid()
        assert "reference_code" in form.errors

    def test_too_short_rejected(self):
        form = self._form("AB1")
        assert not form.is_valid()

    def test_empty_rejected(self):
        form = self._form("")
        assert not form.is_valid()


class TestEmailRequestForm:
    def test_valid_email(self):
        form = EmailRequestForm(data={"email": "user@example.com"})
        assert form.is_valid()

    def test_invalid_email_rejected(self):
        form = EmailRequestForm(data={"email": "not-an-email"})
        assert not form.is_valid()
