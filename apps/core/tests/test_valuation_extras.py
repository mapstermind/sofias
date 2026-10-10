from apps.core.templatetags.valuation_extras import ndr_badge, ndr_bar
from apps.nom035 import constants as c


def test_ndr_badge_covers_every_level():
    for level in c.NDR_ORDER:
        assert ndr_badge(level)


def test_ndr_badge_muy_alto_is_red():
    assert "red" in ndr_badge(c.NDR_MUY_ALTO)


def test_ndr_bar_unknown_is_neutral():
    assert "gray" in ndr_bar("")


def test_ndr_fill_maps_every_level():
    from apps.core.templatetags.valuation_extras import ndr_fill
    from apps.nom035 import constants as c

    assert ndr_fill(c.NDR_BAJO) == "fill-green-500"
    assert ndr_fill(c.NDR_MUY_ALTO) == "fill-red-500"
    assert ndr_fill("nonsense") == "fill-gray-200"


DOMINIO_HEX = {
    "nulo": "#9CA3AF",
    "bajo": "#4A8039",
    "medio": "#CA9429",
    "alto": "#B5531F",
    "muy_alto": "#7A1010",
}


def test_dominio_tier_classes():
    from apps.core.templatetags.valuation_extras import ndr_badge, ndr_bar, ndr_fill

    for level, hex_ in DOMINIO_HEX.items():
        assert ndr_bar(level, "dominio") == f"bg-[{hex_}]"
        assert ndr_fill(level, "dominio") == f"fill-[{hex_}]"
        assert f"bg-[{hex_}]" in ndr_badge(level, "dominio")
    for level in ("bajo", "alto", "muy_alto"):
        assert "text-white" in ndr_badge(level, "dominio")
    for level in ("nulo", "medio"):
        assert "text-gray-900" in ndr_badge(level, "dominio")


def test_categoria_tier_is_the_default():
    from apps.core.templatetags.valuation_extras import ndr_badge, ndr_bar, ndr_fill

    assert ndr_badge("bajo") == ndr_badge("bajo", "")
    assert ndr_badge("bajo").startswith("bg-green-50 text-green-700 ring-green-600/20 ")
    assert ndr_bar("alto") == "bg-orange-500"
    assert ndr_fill("medio") == "fill-amber-500"


def test_every_badge_carries_a_squircle_marker():
    """`pill-marker` draws a 2px-radius square, the shape of the legend swatches."""
    for tier in ("", "dominio"):
        for level in (*c.NDR_ORDER, "nonsense"):
            assert "pill-marker" in ndr_badge(level, tier).split(), (level, tier)


def test_a_tinted_badge_marker_takes_the_level_bar_color():
    """So a badge and its chart legend show the same mark."""
    for level in c.NDR_ORDER:
        assert f"before:{ndr_bar(level)}" in ndr_badge(level)


def test_a_solid_badge_marker_takes_the_text_color():
    """On a solid dominio badge the bar color is the background, so the marker uses the ink."""
    for level in c.NDR_ORDER:
        assert "before:bg-" not in ndr_badge(level, "dominio")
