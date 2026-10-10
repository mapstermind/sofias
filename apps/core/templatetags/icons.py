"""`{% icon "check-circle" "size-5" %}`: a Heroicon inlined, so it takes the surrounding text color.

The files in templates/icons/ are Heroicons v2 outline (24px, MIT, see the
LICENSE beside them), copied in rather than installed, and only the ones in
use. Adding an icon means downloading its file there. An icon is decorative
(`aria-hidden`) unless it gets a `label`, which makes it an image with that
accessible name.
"""

import re
from functools import lru_cache
from pathlib import Path

from django import template
from django.conf import settings
from django.utils.html import format_html
from django.utils.safestring import mark_safe

register = template.Library()

ICON_DIR = Path(settings.BASE_DIR) / "templates" / "icons"
NAME = re.compile(r"^[a-z0-9-]+$")


@lru_cache(maxsize=64)
def _source(name: str) -> str | None:
    path = ICON_DIR / f"{name}.svg"
    if not NAME.match(name) or not path.is_file():
        return None
    return path.read_text(encoding="utf-8").strip()


@register.simple_tag
def icon(name, css_class="", label=""):
    source = _source(name)
    if source is None:
        # A typo fails loudly in development; production drops the icon rather
        # than the page. tests/test_icons.py checks every name a template uses.
        if settings.DEBUG:
            raise template.TemplateSyntaxError(f"Unknown icon {name!r}")
        return ""
    if label:
        attrs = format_html(' class="{}" role="img" aria-label="{}"', css_class, label)
    else:
        attrs = format_html(' class="{}" aria-hidden="true"', css_class)
    return mark_safe(source.replace("<svg", "<svg" + attrs, 1))
