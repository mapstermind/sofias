from apps.nom035 import constants as c
from apps.nom035.scoring import classify, guia1_positive, likert_item_score


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


def test_guia1_positive_requires_an_event():
    # No Section I event → never positive, regardless of symptom counts.
    assert (
        guia1_positive(event=False, section_ii=2, section_iii=7, section_iv=5) is False
    )


def test_guia1_positive_section_thresholds():
    # Section II: any single "Sí" qualifies.
    assert guia1_positive(event=True, section_ii=1, section_iii=0, section_iv=0) is True
    # Section III: needs 3 or more.
    assert (
        guia1_positive(event=True, section_ii=0, section_iii=2, section_iv=0) is False
    )
    assert guia1_positive(event=True, section_ii=0, section_iii=3, section_iv=0) is True
    # Section IV: needs 2 or more.
    assert (
        guia1_positive(event=True, section_ii=0, section_iii=0, section_iv=1) is False
    )
    assert guia1_positive(event=True, section_ii=0, section_iii=0, section_iv=2) is True
    # Event with sub-threshold symptoms across sections → not positive.
    assert (
        guia1_positive(event=True, section_ii=0, section_iii=2, section_iv=1) is False
    )
