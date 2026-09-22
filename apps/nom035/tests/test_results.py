from datetime import date, datetime, timedelta

import pytest
from django.utils import timezone

from apps.core.results_query import ResultsQuery
from apps.nom035 import _nom035_scoring as cfg
from apps.nom035 import constants as c
from apps.nom035.models import GroupScore, SubmissionScore
from apps.nom035.results import (
    assignment_label,
    assignment_options,
    results_for,
    select_assignment,
    shows,
)
from apps.responses.models import SurveySubmission
from apps.surveys.models import Survey, SurveyAssignment

pytestmark = pytest.mark.django_db


@pytest.fixture
def nom035_survey(db):
    return Survey.objects.create(
        key="nom035", title="NOM-035", status=Survey.Status.PUBLISHED
    )


def make_assignment(company, survey, variant="large"):
    return SurveyAssignment.objects.create(
        company=company,
        survey=survey,
        variant=variant,
        status=SurveyAssignment.Status.ACTIVE,
    )


def make_score(
    assignment,
    user=None,
    *,
    final_score=10,
    final_ndr=c.NDR_BAJO,
    groups=(),
    guia1_event=False,
    guia1_positive=False,
    completed_at=None,
):
    """A scored submission without running the engine.

    Created IN_PROGRESS so the completion signal does not overwrite the
    explicit score; `completed_at` is set directly for label tests.
    `groups` is an iterable of (level, key, score, ndr).
    """
    sub = SurveySubmission.objects.create(
        assignment=assignment,
        user=user,
        status=SurveySubmission.Status.IN_PROGRESS,
        completed_at=completed_at,
    )
    score = SubmissionScore.objects.create(
        submission=sub,
        final_score=final_score,
        final_ndr=final_ndr,
        guia1_event=guia1_event,
        guia1_positive=guia1_positive,
    )
    GroupScore.objects.bulk_create(
        GroupScore(submission_score=score, level=level, key=key, score=value, ndr=ndr)
        for level, key, value, ndr in groups
    )
    return score


def test_assignment_label_forms():
    created = date(2026, 1, 12)
    assert (
        assignment_label("Guía III", None, None, created)
        == "Guía III · creada 12 ene 2026 · sin respuestas"
    )
    assert (
        assignment_label("Guía III", date(2026, 1, 12), date(2026, 2, 28), created)
        == "Guía III · aplicada 12 ene – 28 feb 2026"
    )
    assert (
        assignment_label("Guía II", date(2025, 12, 1), date(2026, 1, 5), created)
        == "Guía II · aplicada 1 dic 2025 – 5 ene 2026"
    )
    assert (
        assignment_label("Guía II", date(2026, 3, 4), date(2026, 3, 4), created)
        == "Guía II · aplicada 4 mar 2026"
    )


def test_assignment_options_only_nom035_newest_first(
    make_company, survey, nom035_survey
):
    company = make_company()
    make_assignment(company, survey)  # another instrument — excluded
    older = make_assignment(company, nom035_survey)
    newer = make_assignment(company, nom035_survey, variant="small")
    tz = timezone.get_current_timezone()
    make_score(older, completed_at=datetime(2026, 1, 12, 18, tzinfo=tz))
    make_score(older, completed_at=datetime(2026, 2, 28, 9, tzinfo=tz))

    options = assignment_options(company)

    assert [o.assignment for o in options] == [newer, older]
    assert options[1].label == "Guía III · aplicada 12 ene – 28 feb 2026"
    assert options[1].scored_count == 2
    assert options[0].scored_count == 0
    assert options[0].label.endswith("sin respuestas")


def test_select_assignment_prefers_request_then_latest_scored(
    make_company, nom035_survey
):
    company = make_company()
    scored = make_assignment(company, nom035_survey)
    make_score(scored)
    make_assignment(company, nom035_survey)  # newest, unscored
    options = assignment_options(company)

    assert select_assignment(options, None).assignment == scored
    assert select_assignment(options, options[0].assignment.pk) == options[0]
    assert select_assignment([], None) is None


def test_shows_rule():
    assert shows(3, 20, suppress=False)
    assert not shows(4, 20, suppress=True)
    assert shows(5, 20, suppress=True)
    assert not shows(17, 20, suppress=True)  # complement of 3
    assert shows(15, 20, suppress=True)
    assert shows(20, 20, suppress=True)  # complement of 0


def _years_ago(years):
    today = timezone.localdate()
    try:
        day = today.replace(year=today.year - years)
    except ValueError:  # 29 February in a non-leap target year
        day = today.replace(year=today.year - years, day=28)
    return day - timedelta(days=1)


@pytest.fixture
def people(
    make_company, make_user_with_profile, make_area, make_location, nom035_survey
):
    """Six respondents in Operaciones plus two in Ventas, one with no sex/dob."""
    company = make_company()
    ops = make_area(company, name="Operaciones")
    ventas = make_area(company, name="Ventas")
    matriz = make_location(company, name="Matriz")
    assignment = make_assignment(company, nom035_survey)
    specs = [
        ("female", 22, ops),
        ("female", 27, ops),
        ("female", 27, ops),
        ("male", 33, ops),
        ("male", 45, ops),
        ("male", 61, ops),
        ("female", 27, ventas),
        ("", None, ventas),
    ]
    for i, (sex, age, area) in enumerate(specs):
        user = make_user_with_profile(
            email=f"p{i}@x.mx", company=company, area=area, location=matriz
        )
        user.profile.sex = sex
        user.profile.date_of_birth = _years_ago(age) if age else None
        user.profile.save()
        make_score(assignment, user)
    return {"company": company, "assignment": assignment, "ops": ops, "ventas": ventas}


def test_unfiltered_group_is_the_whole_assignment(people):
    results = results_for(
        people["assignment"], ResultsQuery(), suppress_small_groups=True
    )
    assert (results.size, results.whole_size) == (8, 8)
    assert not results.filtered and not results.suppressed


def test_sex_and_age_profile(people):
    results = results_for(
        people["assignment"], ResultsQuery(), suppress_small_groups=True
    )
    assert [(s.label, s.value, s.color) for s in results.sex] == [
        ("Femenino", 4, "sex-female"),
        ("Masculino", 3, "sex-male"),
        ("Sin dato", 1, "none"),
    ]
    ages = {s.key: s.value for s in results.age}
    assert ages["20-24"] == 1 and ages["25-29"] == 3 and ages["60-mas"] == 1
    assert ages["none"] == 1
    assert [s.key for s in results.age][-1] == "none"


def test_filters_narrow_the_group(people):
    query = ResultsQuery(
        sex="female",
        sex_slug="femenino",
        age_slugs=("25-29",),
        area_ids=(people["ops"].pk,),
    )
    results = results_for(people["assignment"], query, suppress_small_groups=False)
    assert results.size == 2
    assert results.filtered


def test_profile_ignores_its_own_dimension(people):
    query = ResultsQuery(sex="female", sex_slug="femenino")
    results = results_for(people["assignment"], query, suppress_small_groups=False)
    assert results.size == 4
    assert sum(s.value for s in results.sex) == 8  # sex chart ignores the sex filter


def test_small_filtered_group_is_suppressed_for_executives_only(people):
    query = ResultsQuery(area_ids=(people["ventas"].pk,))
    locked = results_for(people["assignment"], query, suppress_small_groups=True)
    free = results_for(people["assignment"], query, suppress_small_groups=False)
    assert locked.suppressed and not free.suppressed
    assert locked.final_distribution is None
    assert sum(s.value for s in locked.sex) == 2  # people counts stay visible


def test_suppressed_group_hides_every_participation_row(people):
    query = ResultsQuery(area_ids=(people["ventas"].pk,))
    results = results_for(people["assignment"], query, suppress_small_groups=True)
    assert results.suppressed
    assert all(row.counts == () for row in results.participation)


def test_complement_rule_suppresses_all_but_a_few(people):
    # Operaciones = 6 of 8: the 2 left out would be exposed by subtraction.
    query = ResultsQuery(area_ids=(people["ops"].pk,))
    assert results_for(
        people["assignment"], query, suppress_small_groups=True
    ).suppressed


def test_empty_group(people):
    query = ResultsQuery(age_slugs=("50-54",))
    results = results_for(people["assignment"], query, suppress_small_groups=True)
    assert results.empty and not results.suppressed


def test_deleted_respondent_counts_unfiltered_but_drops_when_filtered(people):
    make_score(people["assignment"], None)
    whole = results_for(
        people["assignment"], ResultsQuery(), suppress_small_groups=False
    )
    assert whole.size == 9
    assert {s.key: s.value for s in whole.sex}["none"] == 2
    filtered = results_for(
        people["assignment"],
        ResultsQuery(sex="male", sex_slug="masculino"),
        suppress_small_groups=False,
    )
    assert filtered.size == 3


@pytest.fixture
def scored_large(make_company, nom035_survey):
    company = make_company()
    assignment = make_assignment(company, nom035_survey, variant="large")
    amb = cfg.CAT_AMBIENTE
    cond = cfg.DOM_CONDICIONES
    rows = [
        (40, c.NDR_NULO, 3, c.NDR_NULO, False, False),
        (60, c.NDR_BAJO, 6, c.NDR_BAJO, True, False),
        (80, c.NDR_MEDIO, 10, c.NDR_MEDIO, True, True),
        (160, c.NDR_MUY_ALTO, 14, c.NDR_MUY_ALTO, False, False),
    ]
    for final, final_ndr, cat_score, cat_ndr, event, positive in rows:
        make_score(
            assignment,
            final_score=final,
            final_ndr=final_ndr,
            guia1_event=event,
            guia1_positive=positive,
            groups=[
                (c.LEVEL_CATEGORIA, amb, cat_score, cat_ndr),
                (c.LEVEL_DOMINIO, cond, cat_score, cat_ndr),
            ],
        )
    return assignment


def test_final_distribution_counts_every_level(scored_large):
    results = results_for(scored_large, ResultsQuery(), suppress_small_groups=True)
    row = results.final_distribution
    assert row.n == 4
    assert dict(row.counts) == {
        c.NDR_NULO: 1,
        c.NDR_BAJO: 1,
        c.NDR_MEDIO: 1,
        c.NDR_ALTO: 0,
        c.NDR_MUY_ALTO: 1,
    }
    assert [s.color for s in row.slices] == [f"ndr-{lvl}" for lvl in c.NDR_ORDER]


def test_categoria_rows_follow_the_variant(scored_large):
    results = results_for(scored_large, ResultsQuery(), suppress_small_groups=True)
    keys = [row.key for row in results.categoria_distribution]
    assert keys == [k for k in cfg.CATEGORIA_ORDER]  # Guía III has all five
    ambiente = results.categoria_distribution[0]
    assert ambiente.n == 4
    assert [d.key for d in ambiente.children][0] == cfg.DOM_CONDICIONES
    tiempo = results.categoria_distribution[2]
    assert tiempo.n == 0  # no rows stored for it in this fixture


def test_small_variant_has_no_entorno(make_company, nom035_survey):
    assignment = make_assignment(make_company(), nom035_survey, variant="small")
    make_score(assignment)
    results = results_for(assignment, ResultsQuery(), suppress_small_groups=False)
    assert cfg.CAT_ENTORNO not in [row.key for row in results.categoria_distribution]
    assert len(results.categoria_distribution) == 4


def test_statistics_final_and_categoria(scored_large):
    results = results_for(scored_large, ResultsQuery(), suppress_small_groups=True)
    final = results.final_stats
    assert (final.n, final.mean, final.median, final.minimum, final.maximum) == (
        4,
        85.0,
        70,
        40,
        160,
    )
    assert final.scale_max == len(cfg.taxonomy_for_variant("large")) * 4
    assert final.strip_bands[0] == (50, "ndr-nulo", "Nulo")
    assert [p[0] for p in final.strip_points] == ["min", "median", "mean", "max"]
    ambiente = results.categoria_stats[0]
    assert (ambiente.mean, ambiente.median) == (8.2, 8.0)
    tiempo = results.categoria_stats[2]
    assert tiempo.n == 0 and tiempo.mean is None and tiempo.strip_points == []


def test_guia1_outcomes(scored_large):
    results = results_for(scored_large, ResultsQuery(), suppress_small_groups=True)
    assert (results.guia1.none, results.guia1.event, results.guia1.positive) == (
        2,
        1,
        1,
    )
    assert [s.color for s in results.guia1.slices] == [
        "guia1-none",
        "guia1-event",
        "guia1-positive",
    ]


def test_group_rows_query_count_does_not_grow(
    scored_large, django_assert_max_num_queries
):
    assignment = SurveyAssignment.objects.select_related("company").get(
        pk=scored_large.pk
    )
    with django_assert_max_num_queries(5):
        results_for(assignment, ResultsQuery(), suppress_small_groups=True)


def test_participation_rows(people, make_user_with_profile):
    # One more Ventas member who never answered.
    make_user_with_profile(
        email="quiet@x.mx", company=people["company"], area=people["ventas"]
    )
    results = results_for(
        people["assignment"], ResultsQuery(), suppress_small_groups=False
    )
    rows = {r.label: r for r in results.participation}
    assert [r.label for r in results.participation] == ["Operaciones", "Ventas"]
    assert (
        rows["Ventas"].registered,
        rows["Ventas"].responded,
        rows["Ventas"].participation,
    ) == (3, 2, 67)
    assert rows["Operaciones"].registered == 6


def test_participation_area_rows_follow_the_small_group_rule(people):
    locked = results_for(
        people["assignment"], ResultsQuery(), suppress_small_groups=True
    )
    rows = {r.label: r for r in locked.participation}
    assert rows["Ventas"].suppressed  # 2 respondents
    assert rows["Operaciones"].suppressed  # complement of 2 within 8
    assert rows["Ventas"].counts == ()


def test_participation_sin_area_row_for_orphaned_respondents(people):
    make_score(people["assignment"], None)  # deleted account
    results = results_for(
        people["assignment"], ResultsQuery(), suppress_small_groups=False
    )
    last = results.participation[-1]
    assert (last.label, last.registered, last.responded, last.participation) == (
        "Sin área",
        None,
        1,
        None,
    )


def test_participation_respects_filters(people):
    query = ResultsQuery(sex="female", sex_slug="femenino")
    results = results_for(people["assignment"], query, suppress_small_groups=False)
    rows = {r.label: r for r in results.participation}
    assert (rows["Operaciones"].registered, rows["Operaciones"].responded) == (3, 3)


def test_foreign_area_buckets_as_sin_area(
    people, make_company, make_area, make_user_with_profile
):
    other = make_company(name="Otra")
    stray = make_user_with_profile(
        email="stray@x.mx",
        company=people["company"],
        area=make_area(other, name="Ajena"),
    )
    make_score(people["assignment"], stray)
    results = results_for(
        people["assignment"], ResultsQuery(), suppress_small_groups=False
    )
    assert "Ajena" not in [r.label for r in results.participation]
    assert results.participation[-1].label == "Sin área"


@pytest.fixture
def make_area_respondents(
    make_company, make_user_with_profile, make_area, nom035_survey
):
    """make_area_respondents({"A": 6, ...}) → assignment with that many scored per área."""

    def factory(sizes):
        company = make_company()
        assignment = make_assignment(company, nom035_survey)
        for name, count in sizes.items():
            area = make_area(company, name=name)
            for i in range(count):
                user = make_user_with_profile(
                    email=f"{name.lower()}{i}@x.mx", company=company, area=area
                )
                make_score(assignment, user)
        return assignment

    return factory


def test_participation_hides_more_areas_until_the_hidden_total_is_safe(
    make_area_respondents,
):
    # Final minus A minus B would reveal Dirección's single NDR.
    assignment = make_area_respondents({"A": 6, "B": 6, "Dirección": 1})
    results = results_for(assignment, ResultsQuery(), suppress_small_groups=True)
    rows = {r.label: r for r in results.participation}
    assert rows["Dirección"].suppressed
    assert rows["A"].suppressed or rows["B"].suppressed
    hidden = [r for r in results.participation if r.suppressed]
    assert sum(r.responded for r in hidden) >= c.MIN_GROUP_SIZE
    assert all(r.counts == () for r in hidden)
    assert [(r.registered, r.responded) for r in results.participation] == [
        (6, 6),
        (6, 6),
        (1, 1),
    ]


def test_participation_secondary_rule_picks_the_smallest_then_the_label(
    make_area_respondents,
):
    assignment = make_area_respondents({"A": 6, "B": 6, "Dirección": 1})
    results = results_for(assignment, ResultsQuery(), suppress_small_groups=True)
    rows = {r.label: r for r in results.participation}
    assert rows["A"].suppressed and not rows["B"].suppressed


def test_participation_secondary_rule_spares_admins(make_area_respondents):
    assignment = make_area_respondents({"A": 6, "B": 6, "Dirección": 1})
    results = results_for(assignment, ResultsQuery(), suppress_small_groups=False)
    assert not any(r.suppressed for r in results.participation)
    assert all(r.counts for r in results.participation)


def test_participation_no_secondary_rule_when_enough_is_already_hidden(
    make_area_respondents,
):
    assignment = make_area_respondents({"X": 3, "Y": 3, "Z": 10})
    results = results_for(assignment, ResultsQuery(), suppress_small_groups=True)
    rows = {r.label: r for r in results.participation}
    assert rows["X"].suppressed and rows["Y"].suppressed
    assert not rows["Z"].suppressed and rows["Z"].counts


def test_participation_secondary_rule_breaks_ties_between_equally_sized_rows(
    make_company, make_area, make_user_with_profile, nom035_survey
):
    """A catalog área literally named "Sin área" can tie the orphaned bucket.

    Both are candidates for secondary suppression with the same size and the
    same label, so the tie-break must not fall through to comparing area_id
    (an int) against the orphaned bucket's None.
    """
    company = make_company()
    named_sin_area = make_area(company, name="Sin área")
    small = make_area(company, name="Intranet")
    assignment = make_assignment(company, nom035_survey)
    for i in range(5):
        user = make_user_with_profile(
            email=f"sa{i}@x.mx", company=company, area=named_sin_area
        )
        make_score(assignment, user)
    for i in range(3):
        user = make_user_with_profile(email=f"sm{i}@x.mx", company=company, area=small)
        make_score(assignment, user)
    for _ in range(5):
        make_score(assignment, None)  # orphaned respondents bucket as "Sin área" too

    results = results_for(assignment, ResultsQuery(), suppress_small_groups=True)

    hidden = sum(r.responded for r in results.participation if r.suppressed)
    assert hidden == 0 or hidden >= c.MIN_GROUP_SIZE
