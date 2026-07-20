from apps.core.templatetags.valuation_extras import ndr_badge, ndr_bar
from apps.nom035 import constants as c


def test_ndr_badge_covers_every_level():
    for level in c.NDR_ORDER:
        assert ndr_badge(level)


def test_ndr_badge_muy_alto_is_red():
    assert "red" in ndr_badge(c.NDR_MUY_ALTO)


def test_ndr_bar_unknown_is_neutral():
    assert "gray" in ndr_bar("")
