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


@register.filter
def ndr_badge(ndr):
    """Tailwind classes for a colored NDR badge (pill)."""
    return _BADGE.get(ndr, _NEUTRAL_BADGE)


@register.filter
def ndr_bar(ndr):
    """Tailwind background class for an NDR distribution-bar segment."""
    return _BAR.get(ndr, _NEUTRAL_BAR)
