import pytest

from apps.core.charts import largest_remainder
from apps.nom035 import _nom035_scoring as cfg
from apps.nom035 import constants as c
from apps.nom035.results import DistributionRow
from apps.reports import text
from apps.reports.snapshot import build_report_data

NB = " "


def row(key, counts, children=()):
    full = {lvl: 0 for lvl in c.NDR_ORDER} | counts
    return DistributionRow(
        key=key,
        label=cfg.group_label(key),
        n=sum(full.values()),
        counts=tuple((lvl, full[lvl]) for lvl in c.NDR_ORDER),
        children=tuple(children),
    )


def test_percent_uses_a_non_breaking_space():
    assert text.percent(1, 4) == f"25{NB}%"
    assert text.percent(0, 0) == f"0{NB}%"


def test_final_sentence():
    r = row(
        "final",
        {
            c.NDR_NULO: 120,
            c.NDR_BAJO: 70,
            c.NDR_MEDIO: 35,
            c.NDR_ALTO: 20,
            c.NDR_MUY_ALTO: 5,
        },
    )
    assert text.final_sentence(r) == (
        f"De los 250 colaboradores evaluados, el 76{NB}% presentó niveles de riesgo "
        f"Nulo o Bajo; el 24{NB}% restante, Medio, Alto o Muy alto."
    )


def test_final_sentence_one_person():
    r = row("final", {c.NDR_BAJO: 1})
    assert text.final_sentence(r).startswith("De 1 colaborador evaluado, el 100")


def test_categoria_sentence_single_leader():
    rows = [
        row(cfg.CAT_AMBIENTE, {c.NDR_NULO: 9, c.NDR_ALTO: 1}),
        row(cfg.CAT_LIDERAZGO, {c.NDR_NULO: 6, c.NDR_ALTO: 2, c.NDR_MUY_ALTO: 2}),
    ]
    assert text.categoria_sentence(rows) == (
        "La categoría «Liderazgo y relaciones en el trabajo» concentra la mayor "
        f"proporción de trabajadores en niveles Alto o Muy alto: 40{NB}%."
    )


def test_categoria_sentence_tie_names_both():
    rows = [
        row(cfg.CAT_AMBIENTE, {c.NDR_NULO: 3, c.NDR_ALTO: 1}),
        row(cfg.CAT_TIEMPO, {c.NDR_NULO: 6, c.NDR_MUY_ALTO: 2}),
    ]
    sentence = text.categoria_sentence(rows)
    assert sentence.startswith("Las categorías «")
    assert f"25{NB}% cada una" in sentence


def test_categoria_sentence_none():
    rows = [row(cfg.CAT_AMBIENTE, {c.NDR_NULO: 3, c.NDR_MEDIO: 2})]
    assert text.categoria_sentence(rows) == (
        "Ninguna categoría tiene trabajadores en niveles Alto o Muy alto."
    )


def test_dominio_sentence_top_three_skipping_zero():
    rows = [
        row(cfg.DOM_CARGA, {c.NDR_NULO: 6, c.NDR_ALTO: 4}),
        row(cfg.DOM_LIDERAZGO, {c.NDR_NULO: 5, c.NDR_MUY_ALTO: 5}),
        row(cfg.DOM_JORNADA, {c.NDR_NULO: 9, c.NDR_ALTO: 1}),
        row(cfg.DOM_VIOLENCIA, {c.NDR_NULO: 8, c.NDR_ALTO: 2}),
        row(cfg.DOM_CONTROL, {c.NDR_NULO: 10}),
    ]
    assert text.dominio_sentence(rows) == (
        "Los dominios con mayor proporción de trabajadores en niveles Alto o Muy "
        f"alto son «Liderazgo» (50{NB}%), «Carga de trabajo» (40{NB}%) y "
        f"«Violencia» (20{NB}%)."
    )


def test_dominio_sentence_tie_at_cutoff_included():
    rows = [
        row(cfg.DOM_CARGA, {c.NDR_NULO: 1, c.NDR_ALTO: 1}),
        row(cfg.DOM_LIDERAZGO, {c.NDR_NULO: 1, c.NDR_ALTO: 1}),
        row(cfg.DOM_JORNADA, {c.NDR_NULO: 1, c.NDR_ALTO: 1}),
        row(cfg.DOM_VIOLENCIA, {c.NDR_NULO: 1, c.NDR_ALTO: 1}),
    ]
    assert text.dominio_sentence(rows).count("«") == 4


def test_dominio_sentence_single_and_none():
    one = [
        row(cfg.DOM_CARGA, {c.NDR_NULO: 3, c.NDR_ALTO: 1}),
        row(cfg.DOM_JORNADA, {c.NDR_NULO: 4}),
    ]
    assert text.dominio_sentence(one) == (
        "El dominio con mayor proporción de trabajadores en niveles Alto o Muy alto "
        f"es «Carga de trabajo» (25{NB}%)."
    )
    assert text.dominio_sentence([row(cfg.DOM_JORNADA, {c.NDR_NULO: 4})]) == (
        "Ningún dominio tiene trabajadores en niveles Alto o Muy alto."
    )


@pytest.mark.django_db
def test_levels_present_and_criteria(scored_assignment):
    data = build_report_data(scored_assignment)
    assert text.levels_present(data) == [
        c.NDR_NULO,
        c.NDR_BAJO,
        c.NDR_ALTO,
        c.NDR_MUY_ALTO,
    ]
    levels = [lvl for lvl, _label, _text in text.action_criteria(data)]
    assert levels == text.levels_present(data)


@pytest.mark.django_db
def test_recommendations_one_per_dominio_level_reached(scored_assignment):
    data = build_report_data(scored_assignment)
    recs = [(r.dominio_key, r.level, r.share) for r in text.recommendations(data)]
    assert (cfg.DOM_CONDICIONES, c.NDR_ALTO, f"55{NB}%") in recs
    assert (cfg.DOM_LIDERAZGO, c.NDR_MUY_ALTO, f"100{NB}%") in recs
    assert all(level != c.NDR_BAJO for _d, level, _s in recs)


def test_dominio_sentence_share_is_the_sum_of_largest_remainder_percents():
    # n=3, 1 Alto + 1 Muy alto + 1 Nulo: raw 33.33 each, floors 33/33/33, the one
    # spare point goes to Nulo (first index) -> Alto 33 + Muy alto 33 = 66, not 67.
    r = row(cfg.DOM_CARGA, {c.NDR_NULO: 1, c.NDR_ALTO: 1, c.NDR_MUY_ALTO: 1})
    pct = dict(zip(c.NDR_ORDER, largest_remainder([n for _l, n in r.counts])))
    assert pct[c.NDR_ALTO] + pct[c.NDR_MUY_ALTO] == 66
    assert f"(66{NB}%)" in text.dominio_sentence([r])


def test_categoria_sentence_tie_with_different_displayed_shares():
    # Both are exactly 25 %. A (n=8: 3 Nulo, 3 Bajo, 1 Alto, 1 Muy alto) has raw
    # 37.5/37.5/12.5/12.5, floors 37/37/12/12, two spare points go to the first
    # two .5 remainders (Nulo, Bajo) -> Alto + Muy alto = 24. B (n=4: 3 Nulo,
    # 1 Alto) is 75/25 -> 25.
    a = row(
        cfg.CAT_AMBIENTE,
        {c.NDR_NULO: 3, c.NDR_BAJO: 3, c.NDR_ALTO: 1, c.NDR_MUY_ALTO: 1},
    )
    b = row(cfg.CAT_TIEMPO, {c.NDR_NULO: 3, c.NDR_ALTO: 1})
    assert text.categoria_sentence([a, b]) == (
        f"Las categorías «{a.label}» (24{NB}%) y «{b.label}» (25{NB}%) concentran "
        "la mayor proporción de trabajadores en niveles Alto o Muy alto."
    )
