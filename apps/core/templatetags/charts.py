"""Inclusion tags for the chart components in templates/components/charts/.

This module is the chart palette: a color key from the data layer becomes a
pair of Tailwind classes here (an SVG fill, and a background for legend
swatches). NDR entries come from valuation_extras so the risk ramp has one
source. Classes are spelled out in full so Tailwind's scan of templatetags/
compiles them.
"""

from dataclasses import asdict

from django import template

from apps.core import charts
from apps.core.templatetags.valuation_extras import ndr_bar, ndr_fill
from apps.nom035 import constants as c

register = template.Library()

_COLORS = {
    **{f"ndr-{level}": (ndr_fill(level), ndr_bar(level)) for level in c.NDR_ORDER},
    "sex-female": ("fill-violet-600", "bg-violet-600"),
    "sex-male": ("fill-sky-600", "bg-sky-600"),
    "age": ("fill-indigo-500", "bg-indigo-500"),
    "none": ("fill-gray-300", "bg-gray-300"),
    "guia1-none": ("fill-gray-300", "bg-gray-300"),
    "guia1-event": ("fill-amber-500", "bg-amber-500"),
    "guia1-positive": ("fill-red-500", "bg-red-500"),
}
_FALLBACK = ("fill-gray-300", "bg-gray-300")

UNITS = {
    "cuestionario": ("cuestionario", "cuestionarios"),
    "persona": ("persona", "personas"),
}


def _paint(mark) -> dict:
    fill, swatch = _COLORS.get(mark.color, _FALLBACK)
    return {**asdict(mark), "fill": fill, "swatch": swatch}


@register.inclusion_tag("components/charts/stacked_bar.html")
def stacked_bar(items, unit="cuestionario", legend=False, label=""):
    segments = [_paint(s) for s in charts.stacked_segments(items, UNITS[unit])]
    return {
        "segments": segments,
        "legend": legend,
        "aria_label": label or "; ".join(s["tooltip"] for s in segments),
    }


@register.inclusion_tag("components/charts/column_chart.html")
def column_chart(items, unit="persona", label=""):
    cols = [_paint(col) for col in charts.columns(items, UNITS[unit])]
    return {
        "cols": cols,
        "aria_label": label or "; ".join(col["tooltip"] for col in cols),
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
            "scale_max": strip.scale_max,
        },
        "aria_label": label or "; ".join(m.tooltip for m in strip.markers),
    }
