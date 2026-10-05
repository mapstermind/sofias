from apps.nom035 import _nom035_scoring as cfg
from apps.nom035 import constants as c
from apps.reports import content


def test_matrix_covers_every_dominio_of_both_variants():
    for variant in ("small", "large"):
        dominios = {d for _c, d, _dim in cfg.taxonomy_for_variant(variant).values()}
        for dominio in dominios:
            assert set(content.RECOMMENDATIONS[dominio]) == {
                c.NDR_MEDIO,
                c.NDR_ALTO,
                c.NDR_MUY_ALTO,
            }, dominio
            assert all(content.RECOMMENDATIONS[dominio].values())


def test_fixed_text_is_present():
    assert "{company}" in content.CONFIDENTIALITY_NOTICE
    assert "NOMBRE NEGOCIO" not in content.CONFIDENTIALITY_NOTICE
    assert content.CONFIDENTIALITY_NOTICE.format(company="Acme").count("Acme") >= 1
    assert content.OBJECTIVE_PLACEHOLDER
    terms = [term for term, _ in content.GLOSSARY]
    assert "Violencia laboral" in terms
    assert [h for h, _ in content.LFT_ARTICLES] == [
        "Artículo 43",
        "Artículo 473",
        "Artículo 474",
        "Artículo 475",
    ]
