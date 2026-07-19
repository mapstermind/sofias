import pytest

from apps.nom035 import _nom035_scoring as cfg
from apps.nom035 import constants as c
from apps.nom035._nom035_scoring import (
    _LARGE_DIMENSION_ITEMS,
    _LARGE_DOMINIO_ITEMS,
    _SMALL_DIMENSION_ITEMS,
    _SMALL_DOMINIO_ITEMS,
)


def _required_codes(prefix, count):
    return {f"{prefix}-{i}" for i in range(1, count + 1)}


def _assert_monotonic_bands(bands):
    uppers = [u for u, _ in bands]
    assert uppers == sorted(uppers)
    assert bands[-1][0] == float("inf")
    assert {level for _, level in bands} <= set(c.NDR_ORDER)


def test_guia1_section_codes():
    assert cfg.GUIA1_TRIGGER_CODE == "g1-1"
    assert cfg.GUIA1_SECTION_II_CODES == ["g1-2", "g1-3"]
    assert cfg.GUIA1_SECTION_III_CODES == [f"g1-{i}" for i in range(4, 11)]
    assert cfg.GUIA1_SECTION_IV_CODES == [f"g1-{i}" for i in range(11, 16)]
    # Trigger + the three sections cover every Guía I item g1-1..g1-15 exactly once.
    covered = [
        cfg.GUIA1_TRIGGER_CODE,
        *cfg.GUIA1_SECTION_II_CODES,
        *cfg.GUIA1_SECTION_III_CODES,
        *cfg.GUIA1_SECTION_IV_CODES,
    ]
    assert sorted(covered) == sorted(_required_codes("g1", 15))
    assert len(covered) == 15  # no overlaps


def test_taxonomy_covers_every_likert_item():
    small = cfg.taxonomy_for_variant("small")
    large = cfg.taxonomy_for_variant("large")
    assert _required_codes("g2", 46) <= set(small)
    assert _required_codes("g3", 72) <= set(large)
    for mapping in (small, large):
        for value in mapping.values():
            categoria, dominio, dimension = value
            assert categoria and dominio and dimension


def test_thresholds_present_and_monotonic_for_every_group():
    for variant in ("small", "large"):
        taxonomy = cfg.taxonomy_for_variant(variant)
        categorias = {cat for cat, _, _ in taxonomy.values()}
        dominios = {dom for _, dom, _ in taxonomy.values()}
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


def _dominio_item_numbers(variant):
    """{dominio_key: {item numbers}} reconstructed from the taxonomy."""
    result = {}
    for code, (_cat, dom, _dim) in cfg.taxonomy_for_variant(variant).items():
        result.setdefault(dom, set()).add(int(code.split("-")[1]))
    return result


def test_small_taxonomy_matches_official_guia2():
    dom_items = _dominio_item_numbers("small")
    assert dom_items[cfg.DOM_CONDICIONES] == {1, 2, 3}
    assert dom_items[cfg.DOM_CARGA] == {4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 41, 42, 43}
    assert dom_items[cfg.DOM_CONTROL] == {18, 19, 20, 21, 22, 26, 27}
    assert dom_items[cfg.DOM_JORNADA] == {14, 15}
    assert dom_items[cfg.DOM_INTERFERENCIA] == {16, 17}
    assert dom_items[cfg.DOM_LIDERAZGO] == {23, 24, 25, 28, 29}
    assert dom_items[cfg.DOM_RELACIONES] == {30, 31, 32, 44, 45, 46}
    assert dom_items[cfg.DOM_VIOLENCIA] == {33, 34, 35, 36, 37, 38, 39, 40}
    # Guía II has no Entorno organizacional categoría (nor its dominios).
    assert cfg.DOM_RECONOCIMIENTO not in dom_items
    assert cfg.DOM_PERTENENCIA not in dom_items
    small = cfg.taxonomy_for_variant("small")
    assert cfg.CAT_ENTORNO not in {cat for cat, _, _ in small.values()}


def test_small_inverted_items_match_official_guia2():
    # Items 18–33 score Siempre→0 … Nunca→4 (not inverted); all others are inverted.
    non_inverted = {n for n in range(1, 47) if not cfg.is_inverted(f"g2-{n}")}
    assert non_inverted == set(range(18, 34))


def test_known_small_threshold_bands():
    inf = float("inf")
    assert cfg.thresholds_for("final", "final", "small") == [
        (20, c.NDR_NULO),
        (45, c.NDR_BAJO),
        (70, c.NDR_MEDIO),
        (90, c.NDR_ALTO),
        (inf, c.NDR_MUY_ALTO),
    ]
    # Liderazgo dominio: the SME-corrected Medio band closes the old 7–8 gap.
    assert cfg.thresholds_for(c.LEVEL_DOMINIO, cfg.DOM_LIDERAZGO, "small") == [
        (3, c.NDR_NULO),
        (5, c.NDR_BAJO),
        (8, c.NDR_MEDIO),
        (11, c.NDR_ALTO),
        (inf, c.NDR_MUY_ALTO),
    ]


def test_inverted_items_are_known_codes():
    large = cfg.taxonomy_for_variant("large")
    small = cfg.taxonomy_for_variant("small")
    known = set(large) | set(small)
    assert cfg.INVERTED_ITEMS  # non-empty
    assert cfg.INVERTED_ITEMS <= known


def test_action_text_is_org_framed_for_every_level():
    for level in c.NDR_ORDER:
        text = cfg.action_text(level)
        assert text
    # The Muy alto guidance must not carry individual-clinical phrasing.
    assert "clínica" not in cfg.action_text(c.NDR_MUY_ALTO).lower()
    assert "colaboradores que" not in cfg.action_text(c.NDR_MUY_ALTO).lower()
    # It speaks about the área / centro de trabajo.
    assert "área" in cfg.action_text(c.NDR_MUY_ALTO).lower()


def test_group_label_covers_every_categoria_and_dominio():
    for variant in ("small", "large"):
        for categoria, dominio, dimension in cfg.taxonomy_for_variant(variant).values():
            assert cfg.group_label(categoria)
            assert cfg.group_label(dominio)
            assert cfg.group_label(dimension)
    # Labels are the official accented Spanish names, not slug prettifications.
    assert cfg.group_label(cfg.CAT_TIEMPO) == "Organización del tiempo de trabajo"
    assert cfg.group_label(cfg.DOM_RECONOCIMIENTO) == "Reconocimiento del desempeño"


def _dimension_numbers(dim_map):
    """{dominio: set(all item numbers across its dimensiones)}."""
    return {
        dominio: {n for _key, _label, nums in dims for n in nums}
        for dominio, dims in dim_map.items()
    }


@pytest.mark.parametrize(
    "dominio_map, dimension_map",
    [
        (_LARGE_DOMINIO_ITEMS, _LARGE_DIMENSION_ITEMS),
        (_SMALL_DOMINIO_ITEMS, _SMALL_DIMENSION_ITEMS),
    ],
)
def test_dimension_items_reconcile_with_dominio_items(dominio_map, dimension_map):
    dim_numbers = _dimension_numbers(dimension_map)
    assert set(dim_numbers) == set(dominio_map)
    for dominio, numbers in dominio_map.items():
        assert dim_numbers[dominio] == set(numbers), dominio


def test_taxonomy_values_are_three_tuples():
    for variant in ("small", "large"):
        for value in cfg.taxonomy_for_variant(variant).values():
            assert len(value) == 3
