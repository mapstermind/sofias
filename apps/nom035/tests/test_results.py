from datetime import date, datetime, timedelta

import pytest
from django.utils import timezone

from apps.core.results_query import ResultsQuery
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
