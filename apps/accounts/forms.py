from django import forms


class EmailRequestForm(forms.Form):
    email = forms.EmailField(
        label="Your email address",
        widget=forms.EmailInput(attrs={
            "autofocus": True,
            "placeholder": "you@example.com",
            "autocomplete": "email",
            "class": "block w-full rounded-lg border border-gray-300 px-4 py-3 text-sm focus:border-indigo-500 focus:ring-indigo-500",
        }),
    )


class OTPVerifyForm(forms.Form):
    email = forms.EmailField(widget=forms.HiddenInput())
    code = forms.CharField(
        label="Login code",
        min_length=6,
        max_length=6,
        widget=forms.TextInput(attrs={
            "autofocus": True,
            "inputmode": "numeric",
            "autocomplete": "one-time-code",
            "placeholder": "000000",
            "class": "block w-full rounded-lg border border-gray-300 px-4 py-3 text-center text-2xl tracking-widest focus:border-indigo-500 focus:ring-indigo-500",
        }),
    )

    def clean_code(self):
        code = self.cleaned_data["code"].strip()
        if not code.isdigit():
            raise forms.ValidationError("The code must contain only digits.")
        return code


class ProfileSetupForm(forms.Form):
    first_name = forms.CharField(
        label="First name",
        max_length=150,
        widget=forms.TextInput(attrs={
            "autofocus": True,
            "placeholder": "Jane",
            "autocomplete": "given-name",
            "class": "block w-full rounded-lg border border-gray-300 px-4 py-3 text-sm focus:border-indigo-500 focus:ring-indigo-500",
        }),
    )
    last_name = forms.CharField(
        label="Last name",
        max_length=150,
        widget=forms.TextInput(attrs={
            "placeholder": "Smith",
            "autocomplete": "family-name",
            "class": "block w-full rounded-lg border border-gray-300 px-4 py-3 text-sm focus:border-indigo-500 focus:ring-indigo-500",
        }),
    )
    position = forms.CharField(
        label="Job title",
        max_length=255,
        widget=forms.TextInput(attrs={
            "placeholder": "e.g. Product Manager",
            "class": "block w-full rounded-lg border border-gray-300 px-4 py-3 text-sm focus:border-indigo-500 focus:ring-indigo-500",
        }),
    )
    reference_code = forms.CharField(
        label="Company reference code",
        min_length=5,
        max_length=5,
        widget=forms.TextInput(attrs={
            "placeholder": "XXXXX",
            "class": "block w-full rounded-lg border border-gray-300 px-4 py-3 text-sm uppercase tracking-widest focus:border-indigo-500 focus:ring-indigo-500",
        }),
    )

    def clean_reference_code(self):
        code = self.cleaned_data["reference_code"].strip().upper()
        if not code.isalnum():
            raise forms.ValidationError("The reference code must be alphanumeric.")
        return code
