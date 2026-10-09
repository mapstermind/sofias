"""Inclusion tags for the chart components in templates/components/charts/.

This module is the chart palette: a color key from the data layer becomes a
pair of Tailwind classes here (an SVG fill, and a background for legend
swatches). NDR entries come from valuation_extras so the risk ramp has one
source, in two tiers: `ndr-<level>` for categorías and the final score, and the
deeper `dom-<level>` for dominios. Classes are spelled out in full so Tailwind's scan of templatetags/
compiles them.

Each color key also has a hex, emitted as the mark's SVG `fill` attribute. On
screen the class wins (CSS beats presentation attributes); WeasyPrint draws
inline SVG without the page's stylesheets, so the PDF report paints from the
attribute. Risk levels and Guía I are fixed colors with a fixed hex (`_HEX`).
Series that are not a level (sex, age) and the empty baseline follow the
palette: their classes name palette tokens, and their hex is that token's value
in the active palette (`_PALETTE_TOKENS`, read through `brand.palette_hex`), so
the tags take the template context to learn which palette is active.
"""

from dataclasses import asdict

from django import template
from django.conf import settings

from apps.core import charts
from apps.core.brand import palette_hex, palette_slugs
from apps.core.templatetags.valuation_extras import ndr_bar, ndr_fill
from apps.nom035 import constants as c

register = template.Library()

_COLORS = {
    **{f"ndr-{level}": (ndr_fill(level), ndr_bar(level)) for level in c.NDR_ORDER},
    **{
        f"dom-{level}": (ndr_fill(level, "dominio"), ndr_bar(level, "dominio"))
        for level in c.NDR_ORDER
    },
    "sex-female": ("fill-series-1", "bg-series-1"),
    "sex-male": ("fill-series-2", "bg-series-2"),
    "age": ("fill-series-1", "bg-series-1"),
    "none": ("fill-neutral-300", "bg-neutral-300"),
    "guia1-none": ("fill-neutral-300", "bg-neutral-300"),
    "guia1-event": ("fill-[#CA9429]", "bg-[#CA9429]"),
    "guia1-positive": ("fill-[#7A1010]", "bg-[#7A1010]"),
}
_FALLBACK = ("fill-neutral-300", "bg-neutral-300")
_FALLBACK_TOKEN = "neutral-300"

# Keys whose hex is a palette token's value in the active palette.
_PALETTE_TOKENS = {
    "sex-female": "series-1",
    "sex-male": "series-2",
    "age": "series-1",
    "none": "neutral-300",
    "guia1-none": "neutral-300",
}

_HEX = {
    "ndr-nulo": "#D1D5DB",
    "ndr-bajo": "#22C55E",
    "ndr-medio": "#F59E0B",
    "ndr-alto": "#F97316",
    "ndr-muy_alto": "#EF4444",
    "dom-nulo": "#9CA3AF",
    "dom-bajo": "#4A8039",
    "dom-medio": "#CA9429",
    "dom-alto": "#B5531F",
    "dom-muy_alto": "#7A1010",
    "guia1-event": "#CA9429",
    "guia1-positive": "#7A1010",
}

UNITS = {
    "cuestionario": ("cuestionario", "cuestionarios"),
    "persona": ("persona", "personas"),
}


def _tokens(context) -> dict[str, str]:
    """The active palette's token values; the default palette's for a missing or unknown slug."""
    slug = context.get("palette")
    return palette_hex(
        slug if slug in palette_slugs() else settings.BRAND_PALETTE_DEFAULT
    )


def _paint(mark, tokens) -> dict:
    fill, swatch = _COLORS.get(mark.color, _FALLBACK)
    hex_ = (
        _HEX.get(mark.color) or tokens[_PALETTE_TOKENS.get(mark.color, _FALLBACK_TOKEN)]
    )
    return {**asdict(mark), "fill": fill, "swatch": swatch, "hex": hex_}


@register.inclusion_tag("components/charts/stacked_bar.html", takes_context=True)
def stacked_bar(context, items, unit="cuestionario", legend=False, label=""):
    tokens = _tokens(context)
    segments = [_paint(s, tokens) for s in charts.stacked_segments(items, UNITS[unit])]
    return {
        "segments": segments,
        "legend": legend,
        "aria_label": label or "; ".join(s["description"] for s in segments),
    }


@register.inclusion_tag("components/charts/column_chart.html", takes_context=True)
def column_chart(context, items, unit="persona", label=""):
    tokens = _tokens(context)
    cols = [_paint(col, tokens) for col in charts.columns(items, UNITS[unit])]
    return {
        "cols": cols,
        "aria_label": label or "; ".join(col["description"] for col in cols),
    }


@register.inclusion_tag("components/charts/range_strip.html", takes_context=True)
def range_strip(context, bands, scale_max, points, label=""):
    strip = charts.range_strip(bands, scale_max, points)
    if strip is None:
        return {"strip": None}
    return {
        "strip": {
            "bands": [_paint(b, _tokens(context)) for b in strip.bands],
            "markers": [asdict(m) for m in strip.markers],
            "ticks": [asdict(t) for t in strip.ticks],
        },
        "aria_label": label
        or "; ".join(
            [m.description for m in strip.markers]
            + [b.description for b in strip.bands]
        ),
    }


@register.inclusion_tag("components/charts/level_columns.html", takes_context=True)
def level_columns(
    context, items, unit="cuestionario", names="always", size="md", label=""
):
    """One column per item on a fixed 0–100 % scale, each with its percent and count.

    `names="phone"` keeps the item names for screen readers but shows them only
    below `md`, for rows that sit under a shared column header. `size` is the
    plot height: "sm", "md" or "lg".
    """
    singular, plural = UNITS[unit]
    tokens = _tokens(context)
    cols = [
        {**_paint(col, tokens), "unit": singular if col.value == 1 else plural}
        for col in charts.level_columns(items, UNITS[unit])
    ]
    return {
        "cols": cols,
        "names_on_phone_only": names == "phone",
        "size": size,
        "aria_label": label or "; ".join(col["description"] for col in cols),
    }
