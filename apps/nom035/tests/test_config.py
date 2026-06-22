from apps.nom035 import _nom035_scoring as cfg
from apps.nom035 import constants as c


def _required_codes(prefix, count):
    return {f"{prefix}-{i}" for i in range(1, count + 1)}


def _assert_monotonic_bands(bands):
    uppers = [u for u, _ in bands]
    assert uppers == sorted(uppers)
    assert bands[-1][0] == float("inf")
    assert {level for _, level in bands} <= set(c.NDR_ORDER)


def test_guia1_codes():
    assert cfg.GUIA1_TRIGGER_CODE == "g1-1"
    assert set(cfg.GUIA1_FOLLOWUP_CODES) == _required_codes("g1", 15) - {"g1-1"}


def test_taxonomy_covers_every_likert_item():
    small = cfg.taxonomy_for_variant("small")
    large = cfg.taxonomy_for_variant("large")
    assert _required_codes("g2", 46) <= set(small)
    assert _required_codes("g3", 72) <= set(large)
    for mapping in (small, large):
        for value in mapping.values():
            categoria, dominio = value
            assert categoria and dominio


def test_thresholds_present_and_monotonic_for_every_group():
    for variant in ("small", "large"):
        taxonomy = cfg.taxonomy_for_variant(variant)
        categorias = {cat for cat, _ in taxonomy.values()}
        dominios = {dom for _, dom in taxonomy.values()}
        _assert_monotonic_bands(cfg.thresholds_for("final", "final", variant))
        for cat in categorias:
            _assert_monotonic_bands(cfg.thresholds_for(c.LEVEL_CATEGORIA, cat, variant))
        for dom in dominios:
            _assert_monotonic_bands(cfg.thresholds_for(c.LEVEL_DOMINIO, dom, variant))


def test_known_final_band_large():
    # From the documented Guía III final table (Ejemplo Reporte Resultados).
    assert cfg.thresholds_for("final", "final", "large") == [
        (50, c.NDR_NULO),
        (75, c.NDR_BAJO),
        (99, c.NDR_MEDIO),
        (140, c.NDR_ALTO),
        (float("inf"), c.NDR_MUY_ALTO),
    ]


def test_inverted_items_are_known_codes():
    large = cfg.taxonomy_for_variant("large")
    small = cfg.taxonomy_for_variant("small")
    known = set(large) | set(small)
    assert cfg.INVERTED_ITEMS  # non-empty
    assert cfg.INVERTED_ITEMS <= known


def test_action_text_exists_for_every_level():
    for level in c.NDR_ORDER:
        assert cfg.action_text(level)
