"""What the styleguide at /estilos/ shows: a demo form and the color swatches.

The page renders the real components, so it can only drift from the app if
these demo values do. See docs/platform/design-system.md (Components).
"""

import re

from django import forms
from django.contrib.staticfiles import finders

from apps.core.brand import palette_hex

# The publish blockers' own wording (apps/reports/publishing.py), for the list alert.
BLOCKER_EXAMPLES = (
    "La encuesta sigue activa; ciérrala antes de publicar el reporte.",
    "Falta completar: Responsables de la empresa.",
)

SCALES = ("primary", "accent", "neutral", "series")
STATUS_SCALES = ("success", "warning", "danger")


class DemoForm(forms.Form):
    first_name = forms.CharField(
        label="Nombre(s)",
        help_text="Como aparece en tu identificación oficial.",
        error_messages={"required": "Escribe tu nombre."},
    )
    maternal_last_name = forms.CharField(label="Apellido materno", required=False)
    sex = forms.ChoiceField(
        label="Sexo",
        choices=[
            ("", "Selecciona tu sexo"),
            ("female", "Femenino"),
            ("male", "Masculino"),
        ],
        error_messages={"required": "Selecciona tu sexo."},
    )
    date_of_birth = forms.DateField(
        label="Fecha de nacimiento",
        required=False,
        widget=forms.SelectDateWidget(
            years=range(2008, 1925, -1), empty_label=("Año", "Mes", "Día")
        ),
    )
    privacy = forms.BooleanField(
        label="Acepto el aviso de privacidad",
        error_messages={"required": "Acepta el aviso de privacidad para continuar."},
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["date_of_birth"].shown_as_required = True

    def clean_date_of_birth(self):
        if self.cleaned_data["date_of_birth"] is None:
            raise forms.ValidationError("Selecciona tu fecha de nacimiento.")
        return self.cleaned_data["date_of_birth"]


def palette_swatches(slug: str) -> list[tuple[str, list[tuple[str, str]]]]:
    """The palette's scales as (scale, [(token, hex)]), lightest first."""
    tokens = palette_hex(slug)
    return [
        (scale, [(t, h) for t, h in tokens.items() if t.startswith(f"{scale}-")])
        for scale in SCALES
    ]


def status_swatches() -> list[tuple[str, list[tuple[str, str]]]]:
    """The fixed status scales as (scale, [(token, hex)]), read from main.css."""
    with open(finders.find("css/main.css"), encoding="utf-8") as fh:
        css = fh.read()
    return [
        (
            scale,
            [
                (f"{scale}-{step}", hex_)
                for step, hex_ in re.findall(
                    r"--color-%s-(\d+):\s*(#[0-9A-Fa-f]{6});" % scale, css
                )
            ],
        )
        for scale in STATUS_SCALES
    ]
