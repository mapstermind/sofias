import pytest

from apps.core import results_page
from apps.core.results_query import ResultsQuery
from apps.nom035 import _nom035_scoring as cfg
from apps.nom035 import constants as c
from apps.nom035.results import results_for
from apps.nom035.tests.factories import make_assignment, make_score

pytestmark = pytest.mark.django_db

AMB = cfg.CAT_AMBIENTE
COND = cfg.DOM_CONDICIONES


@pytest.fixture
def results(make_company, make_user_with_profile, make_area, nom035_survey):
    company = make_company()
    ops = make_area(company, name="Operaciones")
    assignment = make_assignment(company, nom035_survey, variant="large")
    specs = [
        (40, c.NDR_NULO, c.NDR_NULO),
        (60, c.NDR_BAJO, c.NDR_BAJO),
        (80, c.NDR_MEDIO, c.NDR_ALTO),
        (160, c.NDR_MUY_ALTO, c.NDR_MUY_ALTO),
        (170, c.NDR_MUY_ALTO, c.NDR_MUY_ALTO),
        (30, c.NDR_NULO, c.NDR_NULO),
    ]
    for i, (final, final_ndr, cat_ndr) in enumerate(specs):
        user = make_user_with_profile(email=f"u{i}@x.mx", company=company, area=ops)
        make_score(
            assignment,
            user,
            final_score=final,
            final_ndr=final_ndr,
            groups=[
                (c.LEVEL_CATEGORIA, AMB, 5, cat_ndr),
                (c.LEVEL_DOMINIO, COND, 5, cat_ndr),
            ],
        )
    return results_for(assignment, ResultsQuery(), suppress_small_groups=False)


def test_final_hero_lists_the_categorias_on_the_right(results):
    hero, column = results_page.hero_for(results, "")
    assert hero.group.key == "final"
    assert hero.chart.ceiling == 40  # 2 nulo, 1 bajo, 1 medio, 2 muy alto of 6 → 33 %
    assert [g.key for g in column][0] == AMB


def test_a_categoria_hero_lists_its_dominios_on_the_right(results):
    hero, column = results_page.hero_for(results, AMB)
    assert hero.group.key == AMB
    assert hero.group.stats.n == 6
    assert [g.key for g in column] == [COND]
    assert column[0].stats.key == COND  # distribution and statistics stay paired


def test_unknown_ver_falls_back_to_the_final_score(results):
    hero, _column = results_page.hero_for(results, "nonsense")
    assert hero.group.key == "final"


def test_area_rows_follow_ver(results):
    final = results_page.area_rows(results, "")[0]
    assert (final.n, final.at_risk_percent) == (6, 33)
    cat = results_page.area_rows(results, AMB)[0]
    assert (cat.n, cat.at_risk_percent) == (6, 50)  # alto + 2 muy alto of 6


def test_participation_card_has_one_mark_per_few_accounts(results):
    card = results_page.participation_card(results)
    assert (card["registered"], card["responded"], card["pending"]) == (6, 6, 0)
    assert card["percent"] == 100
    assert card["per_tick"] == 1
    assert len(card["ticks"]) == 6 and all(card["ticks"])


def test_sex_card_percents_sum_to_100(results):
    card = results_page.sex_card(results)
    assert sum(item["percent"] for item in card) in (0, 100)


def test_guia1_card_percents_sum_to_100(results):
    card = results_page.guia1_card(results)
    assert card["total"] == 6
    assert sum(s["percent"] for s in card["slices"]) == 100


def test_with_valid_ver_drops_a_categoria_the_variant_lacks():
    query = ResultsQuery(ver=cfg.CAT_ENTORNO)
    assert results_page.with_valid_ver(query, {AMB}).ver == ""
    assert results_page.with_valid_ver(query, {cfg.CAT_ENTORNO}).ver == cfg.CAT_ENTORNO


def test_each_categoria_carries_the_link_that_chooses_it(results):
    _hero, column = results_page.hero_for(results, "", lambda key: f"/r/?ver={key}")
    assert column[0].view_url == f"/r/?ver={AMB}"


def test_area_levels_carry_a_percent_each(results):
    levels = results_page.area_rows(results, "")[0].levels
    assert [lv["level"] for lv in levels] == c.NDR_ORDER
    assert sum(lv["percent"] for lv in levels) == 100


def test_age_columns_link_to_the_page_filtered_by_that_band(results):
    card = results_page.age_card(
        results, ("25-29",), lambda slug, on: f"/r/?{'off' if on else 'on'}={slug}"
    )
    by_name = {a["name"]: a for a in card}
    assert by_name["25–29"]["selected"] and by_name["25–29"]["url"] == "/r/?off=25-29"
    assert by_name["30–34"]["url"] == "/r/?on=30-34"
    assert all(a["url"] == "" for a in card if a["name"] == "Sin dato")
