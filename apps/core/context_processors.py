from django.conf import settings
from django.utils.functional import SimpleLazyObject

from apps.core.brand import active_palette, can_switch_palette


def brand(request):
    """`brand`, the active `palette`, and whether this visitor gets the palette switch."""
    return {
        "brand": settings.BRAND,
        "palette": active_palette(request),
        "palettes": settings.BRAND_PALETTES,
        # Lazy: only base.html asks, so a fragment response never pays the group query.
        "show_palette_switch": SimpleLazyObject(
            lambda: can_switch_palette(request.user)
        ),
    }
