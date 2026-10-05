import pytest

from apps.nom035 import _nom035_scoring as cfg
from apps.nom035 import constants as c
from apps.nom035.results import NEUTRAL_BAND_LABEL, report_results
from apps.nom035.tests.factories import make_assignment, make_score

pytestmark = pytest.mark.django_db


def _cat(key, score, ndr):
    return (c.LEVEL_CATEGORIA, key, score, ndr)


@pytest.fixture
def two_areas(make_company, make_user_with_profile, make_area, nom035_survey):
    """Ops: 6 respondents (3 Alto in Ambiente, 1 Guía I positive); Dirección: 2."""
    company = make_company()
    ops = make_area(company, name="Operaciones")
    dir_ = make_area(company, name="Dirección")
    assignment = make_assignment(company, nom035_survey, variant="large")
    for i in range(6):
        user = make_user_with_profile(email=f"o{i}@x.mx", company=company, area=ops)
        ndr = c.NDR_ALTO if i < 3 else c.NDR_NULO
        make_score(
            assignment,
            user,
            final_ndr=ndr,
            guia1_event=i == 0,
            guia1_positive=i == 0,
            groups=[_cat(cfg.CAT_AMBIENTE, 12 if i < 3 else 2, ndr)],
        )
    for i in range(2):
        user = make_user_with_profile(email=f"d{i}@x.mx", company=company, area=dir_)
        make_score(assignment, user, groups=[_cat(cfg.CAT_AMBIENTE, 2, c.NDR_NULO)])
    return {"assignment": assignment, "ops": ops, "dir": dir_}


def test_report_results_is_the_whole_assignment_suppressed(two_areas):
    data = report_results(two_areas["assignment"])
    assert data.results.size == 8
    assert data.results.filtered is False
    assert data.registered == 8


def test_area_results_follow_participation_visibility(two_areas):
    data = report_results(two_areas["assignment"])
    by_label = {a.label: a for a in data.areas}
    # Dirección (2) is hidden; hiding it leaves 2 hidden, so Operaciones hides too.
    assert by_label["Dirección"].suppressed is True
    assert by_label["Operaciones"].suppressed is True
    assert by_label["Dirección"].final is None
    assert by_label["Dirección"].categorias == ()
    assert by_label["Dirección"].guia1 is None


def test_area_results_numbers_when_visible(
    make_company, make_user_with_profile, make_area, nom035_survey
):
    company = make_company()
    a = make_area(company, name="A")
    b = make_area(company, name="B")
    assignment = make_assignment(company, nom035_survey, variant="large")
    for area, prefix in ((a, "a"), (b, "b")):
        for i in range(5):
            user = make_user_with_profile(
                email=f"{prefix}{i}@x.mx", company=company, area=area
            )
            make_score(
                assignment,
                user,
                final_ndr=c.NDR_MEDIO if prefix == "a" else c.NDR_BAJO,
                guia1_event=prefix == "a" and i == 0,
                groups=[_cat(cfg.CAT_AMBIENTE, 9, c.NDR_MEDIO)],
            )
    data = report_results(assignment)
    row = next(x for x in data.areas if x.label == "A")
    assert row.suppressed is False
    assert row.n == 5
    assert dict(row.final.counts)[c.NDR_MEDIO] == 5
    assert [cat.key for cat in row.categorias][0] == cfg.CAT_AMBIENTE
    assert dict(row.categorias[0].counts)[c.NDR_MEDIO] == 5
    assert (row.guia1.none, row.guia1.event, row.guia1.positive) == (4, 1, 0)


def test_dimension_groups_follow_the_variant(two_areas):
    data = report_results(two_areas["assignment"])
    dominios = [g.key for g in data.dimensions]
    assert dominios[0] == cfg.DOM_CONDICIONES
    assert cfg.DOM_PERTENENCIA in dominios  # large variant has Entorno


def test_dimension_rows_use_one_neutral_band(make_company, nom035_survey):
    company = make_company()
    assignment = make_assignment(company, nom035_survey, variant="large")
    dim = cfg.dimensions_for_dominio(cfg.DOM_CONDICIONES, "large")[0]
    for value in (1, 3, 8):
        make_score(assignment, groups=[(c.LEVEL_DIMENSION, dim, value, "")])
    data = report_results(assignment)
    row = data.dimensions[0].rows[0]
    assert row.key == dim
    assert (row.n, row.minimum, row.median, row.maximum) == (3, 1, 3, 8)
    assert row.mean == 4.0
    assert row.strip_bands == ((row.scale_max, "none", NEUTRAL_BAND_LABEL),)
    items = sum(
        1 for _c, _d, d in cfg.taxonomy_for_variant("large").values() if d == dim
    )
    assert row.scale_max == items * 4


def test_small_variant_has_no_entorno_dimensions(make_company, nom035_survey):
    company = make_company()
    assignment = make_assignment(company, nom035_survey, variant="small")
    make_score(assignment)
    keys = [g.key for g in report_results(assignment).dimensions]
    assert cfg.DOM_RECONOCIMIENTO not in keys
    assert cfg.DOM_PERTENENCIA not in keys


def test_report_results_sin_area_and_deleted_user(
    make_company, make_user_with_profile, nom035_survey
):
    company = make_company()
    assignment = make_assignment(company, nom035_survey)
    for i in range(5):
        make_score(
            assignment, make_user_with_profile(email=f"n{i}@x.mx", company=company)
        )
    make_score(assignment, user=None)  # deleted account
    data = report_results(assignment)
    assert data.results.size == 6
    assert [a.label for a in data.areas] == ["Sin área"]
    assert data.areas[0].n == 6


def test_report_results_query_count_does_not_grow(
    two_areas, make_user_with_profile, django_assert_max_num_queries
):
    with django_assert_max_num_queries(20):
        report_results(two_areas["assignment"])
