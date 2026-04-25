from django import forms


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


class ProfileSetupForm(forms.Form):
    first_name = forms.CharField(
        label="Nombre",
        max_length=150,
        widget=forms.TextInput(
            attrs={
                "autofocus": True,
                "placeholder": "Tu Nombre",
                "autocomplete": "given-name",
                "class": "block w-full rounded-lg border border-gray-300 px-4 py-3 text-sm focus:border-indigo-500 focus:ring-indigo-500",
            }
        ),
    )
    last_name = forms.CharField(
        label="Apellido",
        max_length=150,
        widget=forms.TextInput(
            attrs={
                "placeholder": "Tu Apellido",
                "autocomplete": "family-name",
                "class": "block w-full rounded-lg border border-gray-300 px-4 py-3 text-sm focus:border-indigo-500 focus:ring-indigo-500",
            }
        ),
    )
    position = forms.CharField(
        label="Puesto",
        max_length=255,
        widget=forms.TextInput(
            attrs={
                "placeholder": "Tu Puesto",
                "class": "block w-full rounded-lg border border-gray-300 px-4 py-3 text-sm focus:border-indigo-500 focus:ring-indigo-500",
            }
        ),
    )
    reference_code = forms.CharField(
        label="Código de referencia de la empresa",
        min_length=5,
        max_length=5,
        widget=forms.TextInput(
            attrs={
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
