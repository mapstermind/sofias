from apps.nom035 import constants as c
from apps.nom035.scoring import classify, guia1_severity, likert_item_score


def test_normal_item_maps_1_to_5_onto_0_to_4():
    assert likert_item_score(1, inverted=False) == 0  # Siempre
    assert likert_item_score(5, inverted=False) == 4  # Nunca


def test_inverted_item_reverses_the_scale():
    assert likert_item_score(1, inverted=True) == 4  # Siempre
    assert likert_item_score(5, inverted=True) == 0  # Nunca


def test_classify_returns_band_level():
    bands = [(50, c.NDR_NULO), (75, c.NDR_BAJO), (float("inf"), c.NDR_ALTO)]
    assert classify(bands, 49) == c.NDR_NULO
    assert classify(bands, 50) == c.NDR_BAJO
    assert classify(bands, 200) == c.NDR_ALTO


def test_guia1_severity_bands():
    assert guia1_severity(False, 9) == c.SEV_NONE  # no event → no flag
    assert guia1_severity(True, 1) == c.SEV_LOW
    assert guia1_severity(True, 3) == c.SEV_MED
    assert guia1_severity(True, 6) == c.SEV_HIGH
