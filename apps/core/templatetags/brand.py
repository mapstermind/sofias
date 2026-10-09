"""`{% brand_logo "h-8 w-auto" %}`: the logo file inlined, so it takes the surrounding text color.

The file named by `settings.BRAND["logo"]` is a bare `<svg>` whose shapes use
`fill="currentColor"`; replacing the logo means replacing that file.
"""

from functools import lru_cache

from django import template
from django.conf import settings
from django.contrib.staticfiles import finders
from django.utils.html import format_html
from django.utils.safestring import mark_safe

register = template.Library()


@lru_cache(maxsize=4)
def _svg(path: str) -> str:
    with open(finders.find(path), encoding="utf-8") as fh:
        return fh.read().strip()


@register.simple_tag
def brand_logo(css_class=""):
    attrs = format_html(
        ' class="{}" role="img" aria-label="{}"',
        css_class,
        f"Logo {settings.BRAND['name']}",
    )
    return mark_safe(_svg(settings.BRAND["logo"]).replace("<svg", "<svg" + attrs, 1))
