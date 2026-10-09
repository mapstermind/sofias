"""Brand and palette lookups shared by the context processor, the palette switch and the PDF.

See docs/platform/design-system.md.
"""

import re
from functools import lru_cache

from django.conf import settings
from django.contrib.staticfiles import finders

COOKIE = "paleta"


def palette_slugs() -> set[str]:
    return {slug for slug, _ in settings.BRAND_PALETTES}


def active_palette(request) -> str:
    """The palette the request's cookie names, or the default when it names none we have."""
    chosen = request.COOKIES.get(COOKIE) if request is not None else None
    return chosen if chosen in palette_slugs() else settings.BRAND_PALETTE_DEFAULT


def can_switch_palette(user) -> bool:
    """Administrators compare the palettes; in development everyone may."""
    if settings.DEBUG:
        return True
    if not user.is_authenticated:
        return False
    return user.is_superuser or user.groups.filter(name="Admins").exists()


@lru_cache(maxsize=8)
def palette_hex(slug: str) -> dict[str, str]:
    """One palette's `--brand-*` values from static/css/main.css, keyed by token ("primary-600").

    The stylesheet is the only place a palette is defined. Python reads it for the
    renderers that cannot resolve a CSS variable: WeasyPrint paints an inline SVG
    mark from its `fill` attribute, never from the page's stylesheets.
    """
    with open(finders.find("css/main.css"), encoding="utf-8") as fh:
        css = fh.read()
    block = re.search(r'\[data-palette="%s"\][^{]*\{([^}]*)\}' % re.escape(slug), css)
    if block is None:
        return {}
    return dict(
        re.findall(r"--brand-([a-z]+-\d+):\s*(#[0-9A-Fa-f]{6})", block.group(1))
    )
