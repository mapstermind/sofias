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
attribute.
"""

from dataclasses import asdict

from django import template

from apps.core import charts
from apps.core.templatetags.valuation_extras import ndr_bar, ndr_fill
from apps.nom035 import constants as c

register = template.Library()

_COLORS = {
    **{f"ndr-{level}": (ndr_fill(level), ndr_bar(level)) for level in c.NDR_ORDER},
    **{
        f"dom-{level}": (ndr_fill(level, "dominio"), ndr_bar(level, "dominio"))
        for level in c.NDR_ORDER
    },
    "sex-female": ("fill-violet-600", "bg-violet-600"),
    "sex-male": ("fill-sky-600", "bg-sky-600"),
    "age": ("fill-indigo-500", "bg-indigo-500"),
    "none": ("fill-gray-300", "bg-gray-300"),
    "guia1-none": ("fill-gray-300", "bg-gray-300"),
    "guia1-event": ("fill-amber-500", "bg-amber-500"),
    "guia1-positive": ("fill-red-500", "bg-red-500"),
}
_FALLBACK = ("fill-gray-300", "bg-gray-300")

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
    "sex-female": "#7C3AED",
    "sex-male": "#0284C7",
    "age": "#6366F1",
    "none": "#D1D5DB",
    "guia1-none": "#D1D5DB",
    "guia1-event": "#F59E0B",
    "guia1-positive": "#EF4444",
}
_FALLBACK_HEX = "#D1D5DB"

UNITS = {
    "cuestionario": ("cuestionario", "cuestionarios"),
    "persona": ("persona", "personas"),
}


def _paint(mark) -> dict:
    fill, swatch = _COLORS.get(mark.color, _FALLBACK)
    hex_ = _HEX.get(mark.color, _FALLBACK_HEX)
    return {**asdict(mark), "fill": fill, "swatch": swatch, "hex": hex_}


@register.inclusion_tag("components/charts/stacked_bar.html")
def stacked_bar(items, unit="cuestionario", legend=False, label=""):
    segments = [_paint(s) for s in charts.stacked_segments(items, UNITS[unit])]
    return {
        "segments": segments,
        "legend": legend,
        "aria_label": label or "; ".join(s["description"] for s in segments),
    }


@register.inclusion_tag("components/charts/column_chart.html")
def column_chart(items, unit="persona", label=""):
    cols = [_paint(col) for col in charts.columns(items, UNITS[unit])]
    return {
        "cols": cols,
        "aria_label": label or "; ".join(col["description"] for col in cols),
    }


@register.inclusion_tag("components/charts/range_strip.html")
def range_strip(bands, scale_max, points, label=""):
    strip = charts.range_strip(bands, scale_max, points)
    if strip is None:
        return {"strip": None}
    return {
        "strip": {
            "bands": [_paint(b) for b in strip.bands],
            "markers": [asdict(m) for m in strip.markers],
            "ticks": [asdict(t) for t in strip.ticks],
        },
        "aria_label": label
        or "; ".join(
            [m.description for m in strip.markers]
            + [b.description for b in strip.bands]
        ),
    }


@register.inclusion_tag("components/charts/level_columns.html")
def level_columns(items, unit="cuestionario", names="always", size="md", label=""):
    """One column per item on a fixed 0–100 % scale, each with its percent and count.

    `names="phone"` keeps the item names for screen readers but shows them only
    below `md`, for rows that sit under a shared column header. `size` is the
    plot height: "sm", "md" or "lg".
    """
    singular, plural = UNITS[unit]
    cols = [
        {**_paint(col), "unit": singular if col.value == 1 else plural}
        for col in charts.level_columns(items, UNITS[unit])
    ]
    return {
        "cols": cols,
        "names_on_phone_only": names == "phone",
        "size": size,
        "aria_label": label or "; ".join(col["description"] for col in cols),
    }
