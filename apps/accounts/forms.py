from django import forms
from django.contrib.auth.password_validation import validate_password

from apps.accounts.models import (
    CompanyArea,
    CompanyLocation,
    User,
    normalize_setup_access_code,
)


class UserCSVImportForm(forms.Form):
    csv_file = forms.FileField(
        label="Archivo CSV",
        help_text="Sube un archivo .csv con usuarios para crear.",
        widget=forms.ClearableFileInput(attrs={"accept": ".csv,text/csv"}),
    )

    def clean_csv_file(self):
        csv_file = self.cleaned_data["csv_file"]
        if not csv_file.name.lower().endswith(".csv"):
            raise forms.ValidationError("El archivo debe tener extensión .csv.")
        return csv_file


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


class SetupAccessCodeLoginForm(forms.Form):
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
    setup_access_code = forms.CharField(
        label="Código temporal de acceso",
        widget=forms.TextInput(
            attrs={
                "inputmode": "numeric",
                "autocomplete": "one-time-code",
                "placeholder": "123-456-789",
                "class": "block w-full rounded-lg border border-gray-300 px-4 py-3 text-center text-2xl tracking-widest focus:border-indigo-500 focus:ring-indigo-500",
            }
        ),
    )

    def clean_email(self):
        return self.cleaned_data["email"].lower()

    def clean_setup_access_code(self):
        code = normalize_setup_access_code(self.cleaned_data["setup_access_code"])
        if len(code) != 9 or not code.isdigit():
            raise forms.ValidationError(
                "El código temporal de acceso debe tener 9 dígitos."
            )
        return code


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


_TEXT_CLASSES = (
    "block w-full rounded-lg border border-gray-300 px-4 py-3 text-sm "
    "focus:border-indigo-500 focus:ring-indigo-500"
)
_SELECT_CLASSES = (
    "block w-full rounded-lg border border-gray-300 bg-white px-4 py-3 text-sm "
    "focus:border-indigo-500 focus:ring-indigo-500"
)


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
    # Name and cargo are collected here rather than at import: the admin's roster
    # only has to carry what identifies the account, and the employee is the
    # authority on their own name anyway.
    first_name = forms.CharField(
        label="Nombre(s)",
        max_length=150,
        error_messages={"required": "Escribe tu nombre."},
        widget=forms.TextInput(
            attrs={"autocomplete": "given-name", "class": _TEXT_CLASSES}
        ),
    )
    last_name = forms.CharField(
        label="Apellidos",
        max_length=150,
        error_messages={"required": "Escribe tus apellidos."},
        widget=forms.TextInput(
            attrs={"autocomplete": "family-name", "class": _TEXT_CLASSES}
        ),
    )
    position = forms.CharField(
        label="Cargo",
        max_length=255,
        required=False,
        widget=forms.TextInput(
            attrs={
                "autocomplete": "organization-title",
                "placeholder": "Opcional",
                "class": _TEXT_CLASSES,
            }
        ),
    )
    area = forms.ModelChoiceField(
        queryset=CompanyArea.objects.none(),
        label="Área",
        empty_label="Selecciona tu área",
        error_messages={
            "required": "Selecciona el área a la que perteneces.",
            "invalid_choice": "Selecciona un área válida de tu empresa.",
        },
        widget=forms.Select(attrs={"class": _SELECT_CLASSES}),
    )
    location = forms.ModelChoiceField(
        queryset=CompanyLocation.objects.none(),
        label="Localidad",
        empty_label="Selecciona tu localidad",
        error_messages={
            "required": "Selecciona la localidad en la que trabajas.",
            "invalid_choice": "Selecciona una localidad válida de tu empresa.",
        },
        widget=forms.Select(attrs={"class": _SELECT_CLASSES}),
    )

    def __init__(self, *args, company, **kwargs):
        """Scope the pickers to `company`, which is always required.

        Narrowing the querysets is the security boundary, not just a UX nicety:
        ModelChoiceField resolves a submitted pk *within its queryset*, so a
        foreign company's pk fails as `invalid_choice` before the view sees it.
        """
        super().__init__(*args, **kwargs)
        self.company = company

        self.fields["area"].queryset = CompanyArea.objects.filter(
            company=company, is_active=True
        )
        active_locations = CompanyLocation.objects.filter(
            company=company, is_active=True
        )
        self.active_locations = list(active_locations)
        if len(self.active_locations) > 1:
            self.fields["location"].queryset = active_locations
        else:
            # 0 or 1 localidad: nothing to choose. Dropping the field means a
            # posted pk is structurally ignored rather than trusted.
            del self.fields["location"]

    @property
    def implicit_location(self):
        """The single localidad to auto-assign when the picker isn't shown."""
        return self.active_locations[0] if len(self.active_locations) == 1 else None

    def clean_reference_code(self):
        code = self.cleaned_data["reference_code"].strip().upper()
        if not code.isalnum():
            raise forms.ValidationError(
                "El código de referencia debe ser alfanumérico."
            )
        return code
