from django import template

from apps.nom035 import constants as c

register = template.Library()

_BADGE = {
    c.NDR_NULO: "bg-gray-100 text-gray-600 ring-gray-500/20",
    c.NDR_BAJO: "bg-green-50 text-green-700 ring-green-600/20",
    c.NDR_MEDIO: "bg-amber-50 text-amber-700 ring-amber-600/20",
    c.NDR_ALTO: "bg-orange-50 text-orange-700 ring-orange-600/20",
    c.NDR_MUY_ALTO: "bg-red-50 text-red-700 ring-red-600/20",
}
_NEUTRAL_BADGE = "bg-gray-100 text-gray-500 ring-gray-500/20"

_BAR = {
    c.NDR_NULO: "bg-gray-300",
    c.NDR_BAJO: "bg-green-500",
    c.NDR_MEDIO: "bg-amber-500",
    c.NDR_ALTO: "bg-orange-500",
    c.NDR_MUY_ALTO: "bg-red-500",
}
_NEUTRAL_BAR = "bg-gray-200"

_FILL = {
    c.NDR_NULO: "fill-gray-300",
    c.NDR_BAJO: "fill-green-500",
    c.NDR_MEDIO: "fill-amber-500",
    c.NDR_ALTO: "fill-orange-500",
    c.NDR_MUY_ALTO: "fill-red-500",
}
_NEUTRAL_FILL = "fill-gray-200"

# The dominio tier: a deeper variant of the same five levels, so a reader can
# tell a dominio's level from a categoría's. Badges are solid fills (white text
# where it holds contrast, gray-900 on the light Nulo and Medio).
DOMINIO = "dominio"
_DOMINIO_BADGE = {
    c.NDR_NULO: "bg-[#9CA3AF] text-gray-900 ring-[#9CA3AF]",
    c.NDR_BAJO: "bg-[#4A8039] text-white ring-[#4A8039]",
    c.NDR_MEDIO: "bg-[#CA9429] text-gray-900 ring-[#CA9429]",
    c.NDR_ALTO: "bg-[#B5531F] text-white ring-[#B5531F]",
    c.NDR_MUY_ALTO: "bg-[#7A1010] text-white ring-[#7A1010]",
}
_DOMINIO_BAR = {
    c.NDR_NULO: "bg-[#9CA3AF]",
    c.NDR_BAJO: "bg-[#4A8039]",
    c.NDR_MEDIO: "bg-[#CA9429]",
    c.NDR_ALTO: "bg-[#B5531F]",
    c.NDR_MUY_ALTO: "bg-[#7A1010]",
}
_DOMINIO_FILL = {
    c.NDR_NULO: "fill-[#9CA3AF]",
    c.NDR_BAJO: "fill-[#4A8039]",
    c.NDR_MEDIO: "fill-[#CA9429]",
    c.NDR_ALTO: "fill-[#B5531F]",
    c.NDR_MUY_ALTO: "fill-[#7A1010]",
}


# Every badge opens with a small squircle marker, the shape of the legend
# swatches. On a tinted badge it takes the level's bar color, so the badge and
# the chart legend show the same mark; on a solid dominio badge the bar color is
# the background, so it takes the ink. Spelled out for Tailwind's scan.
_MARKER = (
    "inline-flex items-center gap-1.5 before:size-2 before:shrink-0 before:rounded-xs"
)
_MARKER_COLOR = {
    c.NDR_NULO: "before:bg-gray-300",
    c.NDR_BAJO: "before:bg-green-500",
    c.NDR_MEDIO: "before:bg-amber-500",
    c.NDR_ALTO: "before:bg-orange-500",
    c.NDR_MUY_ALTO: "before:bg-red-500",
}


@register.filter
def ndr_badge(ndr, tier=""):
    """Tailwind classes for a colored NDR badge (pill); `tier="dominio"` for a dominio."""
    if tier == DOMINIO:
        return f"{_DOMINIO_BADGE.get(ndr, _NEUTRAL_BADGE)} {_MARKER} before:bg-current"
    marker = _MARKER_COLOR.get(ndr, "before:bg-current")
    return f"{_BADGE.get(ndr, _NEUTRAL_BADGE)} {_MARKER} {marker}"


@register.filter
def ndr_bar(ndr, tier=""):
    """Tailwind background class for an NDR bar or swatch; `tier="dominio"` for a dominio."""
    table = _DOMINIO_BAR if tier == DOMINIO else _BAR
    return table.get(ndr, _NEUTRAL_BAR)


@register.filter
def ndr_fill(ndr, tier=""):
    """Tailwind SVG fill class for an NDR chart mark; `tier="dominio"` for a dominio."""
    table = _DOMINIO_FILL if tier == DOMINIO else _FILL
    return table.get(ndr, _NEUTRAL_FILL)


@register.filter
def ndr_scale(ndr):
    """The five NDR levels in order, marked up to where `ndr` sits.

    NOM-035 risk is an ordinal scale, so a single badge says the level without
    saying where it falls. Feeds `core/_ndr_scale.html`: every step up to and
    including the reached one is colored, the rest stay muted.
    """
    reached_index = c.NDR_ORDER.index(ndr) if ndr in c.NDR_ORDER else -1
    return [
        {
            "key": level,
            "label": c.NDR_LABELS[level],
            "bar": _BAR[level] if index <= reached_index else _NEUTRAL_BAR,
            "reached": index <= reached_index,
            "active": index == reached_index,
        }
        for index, level in enumerate(c.NDR_ORDER)
    ]
