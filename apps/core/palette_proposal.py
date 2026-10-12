"""Sample data for the palette comparison at /propuestas/paletas/.

One specimen screen is drawn three times, each under its palette. The numbers are
invented. Two of the palettes are the ones in `settings.BRAND_PALETTES`; the third
(`navy`) lives only in static/css/proposal-navy.css and is shown so the client can
see it was evaluated. Nothing here reads the database.
"""

from django import forms

from apps.nom035 import constants as c

TOTAL = 142
REGISTERED = 168

# Cuestionarios por nivel, in c.NDR_ORDER.
COUNTS = (18, 34, 41, 32, 17)

CATEGORIES = (
    ("Ambiente de trabajo", "7.8", c.NDR_BAJO),
    ("Factores propios de la actividad", "34.2", c.NDR_MEDIO),
    ("Organización del tiempo de trabajo", "10.6", c.NDR_ALTO),
    ("Liderazgo y relaciones en el trabajo", "26.1", c.NDR_BAJO),
    ("Entorno organizacional", "15.3", c.NDR_MEDIO),
)

# The row drawn as chosen, to show the selected-row tint.
SELECTED_CATEGORY = "Factores propios de la actividad"

PALETTES = (
    {
        "slug": "petrol",
        "name": "Petróleo",
        "tagline": "Azul verdoso alejado del verde, con un tinte lila frío.",
        "selectable": True,
        "character": "Calma clínica con algo de calidez. Evoca salud y bienestar sin parecer un hospital, lo que va con un producto de riesgo psicosocial. El tono lila la suaviza.",
        "risk": "Se inclina al azul para no confundirse con el verde de «Bajo». Junto a la escala de gris a rojo se mantiene claramente fría. El aviso informativo usa el mismo tono primario, así que no se agrega otro azul.",
        "reading": "Es distintiva entre las herramientas de recursos humanos, sostiene bien las tablas densas y conserva su carácter en tamaños pequeños.",
    },
    {
        "slug": "slate",
        "name": "Pizarra",
        "tagline": "Pizarra sobre piedra cálida, con durazno en las superficies.",
        "selectable": True,
        "character": "La más editorial y sobria. Va mejor con el reporte formal y deja la escala de riesgo en primer plano.",
        "risk": "La pizarra es lo bastante neutra para no tocar la escala. El durazno cae en la misma banda que el ámbar de «Medio», así que se reserva para superficies grandes, nunca para insignias ni gráficas.",
        "reading": "Es la de menos energía: los botones se ven discretos y se renuncia a un acento propio.",
    },
    {
        "slug": "navy",
        "name": "Azul marino",
        "tagline": "Azul institucional con neutros fríos y un tinte índigo claro.",
        "selectable": False,
        "character": "Institucional y creíble, cercana a un banco o a una dependencia de gobierno. Es la opción más segura para quien compra desde la dirección y la menos cálida.",
        "risk": "No choca con la escala de riesgo. Su costo es que se parece a cualquier otro software de oficina.",
        "reading": "Evaluada y descartada. Cumple, pero el petróleo logra lo mismo con más personalidad y se distingue mejor de otros productos del mismo tipo.",
    },
)


class PublishDemoForm(forms.Form):
    """A form with one valid and one invalid field, to show both states."""

    responsible = forms.CharField(
        label="Responsable del programa",
        help_text="Aparece en la portada del reporte.",
    )
    contact_email = forms.EmailField(
        label="Correo de contacto",
        error_messages={
            "invalid": "Escribe un correo completo, por ejemplo nombre@empresa.com."
        },
    )


def _levels() -> list[dict]:
    return [
        {
            "level": level,
            "label": c.NDR_LABELS[level],
            "count": count,
            "share": round(count / TOTAL * 100, 2),
        }
        for level, count in zip(c.NDR_ORDER, COUNTS, strict=True)
    ]


def _publish_form(slug: str) -> PublishDemoForm:
    """The demo form, with ids unique to one palette's specimen."""
    form = PublishDemoForm(
        prefix=slug,
        data={
            f"{slug}-responsible": "Mariana Ruiz Olvera",
            f"{slug}-contact_email": "mariana.ruiz@",
        },
    )
    form.is_valid()
    return form


def context() -> dict:
    levels = _levels()
    return {
        "candidates": [{**p, "form": _publish_form(p["slug"])} for p in PALETTES],
        "levels": levels,
        "categories": [
            {
                "label": label,
                "mean": mean,
                "level": level,
                "level_label": c.NDR_LABELS[level],
                "selected": label == SELECTED_CATEGORY,
            }
            for label, mean, level in CATEGORIES
        ],
        "average_level": c.NDR_MEDIO,
        "total": TOTAL,
        "registered": REGISTERED,
        "participation": round(TOTAL / REGISTERED * 100, 1),
    }
