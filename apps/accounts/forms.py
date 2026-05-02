from django import forms
from django.contrib.auth.password_validation import validate_password

from apps.accounts.models import User


class EmailRequestForm(forms.Form):
    email = forms.EmailField(
        label="Tu correo electrónico",
        widget=forms.EmailInput(
            attrs={
                "autofocus": True,
                "placeholder": "tucorreo@ejemplo.com",
                "autocomplete": "email",
                "class": "block w-full rounded-lg border border-gray-300 px-4 py-3 text-sm focus:border-indigo-500 focus:ring-indigo-500",
            }
        ),
    )


class EmailPasswordLoginForm(forms.Form):
    email = forms.EmailField(
        label="Tu correo electrónico",
        widget=forms.EmailInput(
            attrs={
                "autofocus": True,
                "placeholder": "tucorreo@ejemplo.com",
                "autocomplete": "email",
                "class": "block w-full rounded-lg border border-gray-300 px-4 py-3 text-sm focus:border-indigo-500 focus:ring-indigo-500",
            }
        ),
    )
    password = forms.CharField(
        label="Contraseña",
        strip=False,
        widget=forms.PasswordInput(
            attrs={
                "autocomplete": "current-password",
                "class": "block w-full rounded-lg border border-gray-300 px-4 py-3 text-sm focus:border-indigo-500 focus:ring-indigo-500",
            }
        ),
    )

    error_messages = {
        "invalid_login": "Correo o contraseña inválidos.",
    }

    def clean_email(self):
        return self.cleaned_data["email"].lower()

    def clean(self):
        cleaned_data = super().clean()
        email = cleaned_data.get("email")
        password = cleaned_data.get("password")

        if not email or not password:
            return cleaned_data

        user = User.objects.filter(email=email).first()
        if (
            user is None
            or not user.has_usable_password()
            or not user.check_password(password)
        ):
            raise forms.ValidationError(
                self.error_messages["invalid_login"],
                code="invalid_login",
            )

        if not user.is_active:
            raise forms.ValidationError(
                self.error_messages["invalid_login"],
                code="invalid_login",
            )

        cleaned_data["user"] = user
        return cleaned_data


class RequiredPasswordChangeForm(forms.Form):
    new_password1 = forms.CharField(
        label="Nueva contraseña",
        strip=False,
        widget=forms.PasswordInput(
            attrs={
                "autocomplete": "new-password",
                "class": "block w-full rounded-lg border border-gray-300 px-4 py-3 text-sm focus:border-indigo-500 focus:ring-indigo-500",
            }
        ),
    )
    new_password2 = forms.CharField(
        label="Confirma la nueva contraseña",
        strip=False,
        widget=forms.PasswordInput(
            attrs={
                "autocomplete": "new-password",
                "class": "block w-full rounded-lg border border-gray-300 px-4 py-3 text-sm focus:border-indigo-500 focus:ring-indigo-500",
            }
        ),
    )

    def __init__(self, user, *args, **kwargs):
        self.user = user
        super().__init__(*args, **kwargs)

    def clean_new_password2(self):
        password1 = self.cleaned_data.get("new_password1")
        password2 = self.cleaned_data["new_password2"]

        if password1 and password1 != password2:
            raise forms.ValidationError("Las contraseñas no coinciden.")

        validate_password(password2, self.user)
        return password2

    def save(self):
        self.user.set_password(self.cleaned_data["new_password2"])
        self.user.must_change_password = False
        self.user.save(update_fields=["password", "must_change_password"])
        return self.user


class OTPVerifyForm(forms.Form):
    email = forms.EmailField(widget=forms.HiddenInput())
    code = forms.CharField(
        label="Código de inicio de sesión",
        min_length=6,
        max_length=6,
        widget=forms.TextInput(
            attrs={
                "autofocus": True,
                "inputmode": "numeric",
                "autocomplete": "one-time-code",
                "placeholder": "000000",
                "class": "block w-full rounded-lg border border-gray-300 px-4 py-3 text-center text-2xl tracking-widest focus:border-indigo-500 focus:ring-indigo-500",
            }
        ),
    )

    def clean_code(self):
        code = self.cleaned_data["code"].strip()
        if not code.isdigit():
            raise forms.ValidationError("El código debe contener solo dígitos.")
        return code


class ProfileActivationForm(forms.Form):
    reference_code = forms.CharField(
        label="Código de referencia de la empresa",
        min_length=5,
        max_length=5,
        widget=forms.TextInput(
            attrs={
                "autofocus": True,
                "placeholder": "XXXXX",
                "class": "block w-full rounded-lg border border-gray-300 px-4 py-3 text-sm uppercase tracking-widest focus:border-indigo-500 focus:ring-indigo-500",
            }
        ),
    )

    def clean_reference_code(self):
        code = self.cleaned_data["reference_code"].strip().upper()
        if not code.isalnum():
            raise forms.ValidationError(
                "El código de referencia debe ser alfanumérico."
            )
        return code
