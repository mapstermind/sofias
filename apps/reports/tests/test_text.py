import pytest

from apps.core.charts import largest_remainder
from apps.nom035 import _nom035_scoring as cfg
from apps.nom035 import constants as c
from apps.nom035.results import DistributionRow
from apps.reports import text
from apps.reports.content import RECOMMENDATIONS
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


def test_final_finding():
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
    assert text.final_finding(r) == text.Finding(
        lead="Nivel de riesgo de los 250 colaboradores evaluados:",
        rows=(
            (f"76{NB}%", "Nulo o Bajo"),
            (f"14{NB}%", "Medio"),
            (f"10{NB}%", "Alto o Muy alto"),
        ),
    )


def test_final_finding_one_person():
    finding = text.final_finding(row("final", {c.NDR_BAJO: 1}))
    assert finding.lead == "Nivel de riesgo de 1 colaborador evaluado:"
    assert finding.rows[0] == (f"100{NB}%", "Nulo o Bajo")


def test_categoria_finding_single_leader():
    rows = [
        row(cfg.CAT_AMBIENTE, {c.NDR_NULO: 9, c.NDR_ALTO: 1}),
        row(cfg.CAT_LIDERAZGO, {c.NDR_NULO: 6, c.NDR_ALTO: 2, c.NDR_MUY_ALTO: 2}),
    ]
    assert text.categoria_finding(rows) == text.Finding(
        lead=(
            "La categoría con mayor proporción de trabajadores en niveles Alto o "
            "Muy alto es:"
        ),
        rows=((f"40{NB}%", "Liderazgo y relaciones en el trabajo"),),
    )


def test_categoria_finding_tie_lists_each_leader():
    rows = [
        row(cfg.CAT_AMBIENTE, {c.NDR_NULO: 3, c.NDR_ALTO: 1}),
        row(cfg.CAT_TIEMPO, {c.NDR_NULO: 6, c.NDR_MUY_ALTO: 2}),
    ]
    finding = text.categoria_finding(rows)
    assert finding.lead.startswith("Las categorías con mayor proporción")
    assert finding.lead.endswith("son:")
    assert [share for share, _label in finding.rows] == [f"25{NB}%", f"25{NB}%"]


def test_categoria_finding_tie_with_different_displayed_shares():
    # Both are exactly 25 %. A (n=8: 3 Nulo, 3 Bajo, 1 Alto, 1 Muy alto) has raw
    # 37.5/37.5/12.5/12.5, floors 37/37/12/12, two spare points go to the first
    # two .5 remainders (Nulo, Bajo) -> Alto + Muy alto = 24. B (n=4: 3 Nulo,
    # 1 Alto) is 75/25 -> 25. Each row prints its own share, as its chart does.
    a = row(
        cfg.CAT_AMBIENTE,
        {c.NDR_NULO: 3, c.NDR_BAJO: 3, c.NDR_ALTO: 1, c.NDR_MUY_ALTO: 1},
    )
    b = row(cfg.CAT_TIEMPO, {c.NDR_NULO: 3, c.NDR_ALTO: 1})
    assert text.categoria_finding([a, b]).rows == (
        (f"24{NB}%", a.label),
        (f"25{NB}%", b.label),
    )


def test_categoria_finding_none():
    rows = [row(cfg.CAT_AMBIENTE, {c.NDR_NULO: 3, c.NDR_MEDIO: 2})]
    assert text.categoria_finding(rows) == text.Finding(
        lead="Ninguna categoría tiene trabajadores en niveles Alto o Muy alto."
    )


def test_dominio_finding_top_three_skipping_zero():
    rows = [
        row(cfg.DOM_CARGA, {c.NDR_NULO: 6, c.NDR_ALTO: 4}),
        row(cfg.DOM_LIDERAZGO, {c.NDR_NULO: 5, c.NDR_MUY_ALTO: 5}),
        row(cfg.DOM_JORNADA, {c.NDR_NULO: 9, c.NDR_ALTO: 1}),
        row(cfg.DOM_VIOLENCIA, {c.NDR_NULO: 8, c.NDR_ALTO: 2}),
        row(cfg.DOM_CONTROL, {c.NDR_NULO: 10}),
    ]
    assert text.dominio_finding(rows) == text.Finding(
        lead=(
            "Los dominios con mayor proporción de trabajadores en niveles Alto o "
            "Muy alto son:"
        ),
        rows=(
            (f"50{NB}%", "Liderazgo"),
            (f"40{NB}%", "Carga de trabajo"),
            (f"20{NB}%", "Violencia"),
        ),
    )


def test_dominio_finding_tie_at_cutoff_included():
    rows = [
        row(cfg.DOM_CARGA, {c.NDR_NULO: 1, c.NDR_ALTO: 1}),
        row(cfg.DOM_LIDERAZGO, {c.NDR_NULO: 1, c.NDR_ALTO: 1}),
        row(cfg.DOM_JORNADA, {c.NDR_NULO: 1, c.NDR_ALTO: 1}),
        row(cfg.DOM_VIOLENCIA, {c.NDR_NULO: 1, c.NDR_ALTO: 1}),
    ]
    assert len(text.dominio_finding(rows).rows) == 4


def test_dominio_finding_single_and_none():
    one = [
        row(cfg.DOM_CARGA, {c.NDR_NULO: 3, c.NDR_ALTO: 1}),
        row(cfg.DOM_JORNADA, {c.NDR_NULO: 4}),
    ]
    assert text.dominio_finding(one) == text.Finding(
        lead=(
            "El dominio con mayor proporción de trabajadores en niveles Alto o "
            "Muy alto es:"
        ),
        rows=((f"25{NB}%", "Carga de trabajo"),),
    )
    assert text.dominio_finding([row(cfg.DOM_JORNADA, {c.NDR_NULO: 4})]) == (
        text.Finding(
            lead="Ningún dominio tiene trabajadores en niveles Alto o Muy alto."
        )
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
    dominios = {
        dom.key: dom for cat in data.categoria_distribution for dom in cat.children
    }
    condiciones = text.recommendations(dominios[cfg.DOM_CONDICIONES])
    assert [r.level for r in condiciones] == [c.NDR_ALTO]  # 45 % Bajo, 55 % Alto
    assert condiciones[0].text == RECOMMENDATIONS[cfg.DOM_CONDICIONES][c.NDR_ALTO]
    assert [r.level for r in text.recommendations(dominios[cfg.DOM_LIDERAZGO])] == [
        c.NDR_MUY_ALTO
    ]


def test_dominio_finding_share_is_the_sum_of_largest_remainder_percents():
    # n=3, 1 Alto + 1 Muy alto + 1 Nulo: raw 33.33 each, floors 33/33/33, the one
    # spare point goes to Nulo (first index) -> Alto 33 + Muy alto 33 = 66, not 67.
    r = row(cfg.DOM_CARGA, {c.NDR_NULO: 1, c.NDR_ALTO: 1, c.NDR_MUY_ALTO: 1})
    pct = dict(zip(c.NDR_ORDER, largest_remainder([n for _l, n in r.counts])))
    assert pct[c.NDR_ALTO] + pct[c.NDR_MUY_ALTO] == 66
    assert text.dominio_finding([r]).rows == ((f"66{NB}%", r.label),)
