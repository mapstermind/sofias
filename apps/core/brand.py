"""The palette's values, for renderers that cannot read a CSS variable.

See docs/platform/design-system.md.
"""

import re
from functools import lru_cache

from django.contrib.staticfiles import finders


@lru_cache(maxsize=1)
def palette_hex() -> dict[str, str]:
    """The palette's `--brand-*` values from static/css/main.css, keyed by token ("primary-600").

    The stylesheet is the only place the palette is defined. Python reads it for the
    renderers that cannot resolve a CSS variable: WeasyPrint paints an inline SVG
    mark from its `fill` attribute, never from the page's stylesheets.
    """
    with open(finders.find("css/main.css"), encoding="utf-8") as fh:
        css = fh.read()
    return dict(re.findall(r"--brand-([a-z]+-\d+):\s*(#[0-9A-Fa-f]{6})", css))
