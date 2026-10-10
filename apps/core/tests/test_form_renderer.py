"""Every Django form draws its fields through templates/forms/: see docs/platform/design-system.md."""

import re

import pytest
from django import forms


class DemoForm(forms.Form):
    name = forms.CharField(
        label="Nombre(s)", help_text="Como aparece en tu identificación."
    )
    nickname = forms.CharField(label="Apellido materno", required=False)
    born = forms.DateField(
        label="Fecha de nacimiento",
        required=False,
        help_text="Día, mes y año.",
        widget=forms.SelectDateWidget(years=range(2000, 1990, -1)),
    )
    agree = forms.BooleanField(label="Acepto el aviso de privacidad", required=False)
    secret = forms.CharField(widget=forms.HiddenInput, required=False)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["born"].shown_as_required = True

    def clean_name(self):
        raise forms.ValidationError(["Primer error.", "Segundo error."])

    def clean(self):
        raise forms.ValidationError("No se pudo guardar.")


def group(form, name):
    return str(form[name].as_field_group())


def test_label_help_control_and_errors_render_in_that_order():
    html = group(DemoForm(data={"name": "Ana"}), "name")
    positions = [
        html.index("Nombre(s)"),
        html.index("Como aparece"),
        html.index("<input"),
        html.index("Primer error."),
    ]
    assert positions == sorted(positions)


def test_every_error_shows():
    html = group(DemoForm(data={"name": "Ana"}), "name")
    assert "Primer error." in html and "Segundo error." in html


def test_only_optional_fields_say_so():
    form = DemoForm()
    assert "(opcional)" in group(form, "nickname")
    assert "(opcional)" not in group(form, "name")


def test_a_field_validated_as_required_is_not_marked_optional():
    assert "(opcional)" not in group(DemoForm(), "born")


def test_an_invalid_field_points_at_its_help_and_errors():
    html = group(DemoForm(data={"name": "Ana"}), "name")
    control = re.search(r"<input[^>]*>", html).group(0)
    assert 'aria-invalid="true"' in control
    described = re.search(r'aria-describedby="([^"]+)"', control).group(1).split()
    assert described == ["id_name_helptext", "id_name_error"]
    for id_ in described:
        assert f'id="{id_}"' in html


def test_a_multi_widget_is_a_fieldset_with_a_legend():
    html = group(DemoForm(), "born")
    assert "<fieldset" in html and "<legend" in html
    assert 'aria-describedby="id_born_helptext"' in html


def test_a_checkbox_sits_before_its_label_text():
    html = group(DemoForm(), "agree")
    assert html.index('type="checkbox"') < html.index("Acepto el aviso")
    assert "(opcional)" not in html


def test_the_form_draws_hidden_fields_bare_and_non_field_errors_as_an_alert():
    html = str(DemoForm(data={"name": "Ana"}))
    assert 'type="hidden"' in html
    assert 'role="alert"' in html and "No se pudo guardar." in html
    assert html.index("No se pudo guardar.") < html.index("Nombre(s)")


def test_controls_carry_no_classes_of_their_own():
    """The `field` wrapper styles them; see main.css."""
    html = group(DemoForm(), "name")
    assert 'class="field' in html
    assert "class" not in re.search(r"<input[^>]*>", html).group(0)


@pytest.mark.django_db
def test_the_admin_keeps_its_own_markup(staff_client):
    response = staff_client.get("/admin/accounts/user/add/")
    assert response.status_code == 200
    assert '<div class="field">' not in response.content.decode()


class HiddenForm(forms.Form):
    email = forms.EmailField(widget=forms.HiddenInput)


def test_a_hidden_field_error_shows_at_the_top():
    """It has no field of its own to show under, so it joins the form's alert."""
    html = str(HiddenForm(data={"email": "no-es-correo"}))
    assert 'role="alert"' in html
    assert "(Campo oculto email)" in html
