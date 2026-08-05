import pytest

from apps.nom035 import _nom035_scoring as cfg
from apps.nom035 import constants as c
from apps.nom035.aggregates import company_valuation, employee_valuation
from apps.nom035.models import SubmissionScore
from apps.responses.models import SurveySubmission
from apps.surveys.models import SurveyAssignment

pytestmark = pytest.mark.django_db


@pytest.fixture
def scored(make_company, make_user, survey):
    company = make_company()
    user = make_user(email="e@x.mx")
    assignment = SurveyAssignment.objects.create(
        company=company,
        survey=survey,
        variant=SurveyAssignment.Variant.LARGE,
        status=SurveyAssignment.Status.ACTIVE,
    )
    # In-progress so the completion signal does not auto-create a score; this test
    # sets the SubmissionScore values explicitly.
    sub = SurveySubmission.objects.create(
        assignment=assignment, user=user, status=SurveySubmission.Status.IN_PROGRESS
    )
    SubmissionScore.objects.create(
        submission=sub,
        final_score=160,
        final_ndr=c.NDR_MUY_ALTO,
        guia1_positive=True,
    )
    return {"company": company, "user": user}


def test_company_valuation_counts(scored):
    data = company_valuation(scored["company"])
    assert data["scored_count"] == 1
    assert data["needing_action"] == 1
    assert data["guia1_positive_count"] == 1
    assert data["distribution"][c.NDR_MUY_ALTO] == 1


def _make_score(company, survey, user, ndr):
    from apps.nom035.models import SubmissionScore

    assignment = SurveyAssignment.objects.create(
        company=company,
        survey=survey,
        variant=SurveyAssignment.Variant.LARGE,
        status=SurveyAssignment.Status.ACTIVE,
    )
    sub = SurveySubmission.objects.create(
        assignment=assignment, user=user, status=SurveySubmission.Status.IN_PROGRESS
    )
    SubmissionScore.objects.create(submission=sub, final_score=1, final_ndr=ndr)


def test_company_valuation_area_breakdown(
    make_company, make_user_with_profile, make_area, survey
):
    from apps.nom035 import constants as c

    company = make_company()
    sistemas = make_area(company, name="Sistemas")

    _make_score(
        company,
        survey,
        make_user_with_profile(email="a@x.mx", company=company, area=sistemas),
        c.NDR_MUY_ALTO,
    )
    _make_score(
        company,
        survey,
        make_user_with_profile(email="b@x.mx", company=company, area=sistemas),
        c.NDR_BAJO,
    )
    # No área → its own bucket, so no scored employee is dropped.
    _make_score(
        company,
        survey,
        make_user_with_profile(email="c@x.mx", company=company),
        c.NDR_MEDIO,
    )

    data = company_valuation(company)
    areas = {a["label"]: a for a in data["areas"]}
    assert set(areas) == {"Sistemas", "Sin área"}
    bucket = areas["Sistemas"]
    assert bucket["scored_count"] == 2
    assert bucket["needing_action"] == 1
    assert bucket["action_ndr"] == c.NDR_MUY_ALTO  # most-severe present
    assert bucket["action"] == cfg.action_text(c.NDR_MUY_ALTO)
    assert areas["Sin área"]["action_ndr"] == c.NDR_MEDIO


def test_identically_named_areas_in_different_companies_do_not_merge(
    make_company, make_user_with_profile, make_area, survey
):
    """Grouping is by área pk, not by name — the point of the catalog models."""
    from apps.nom035 import constants as c

    company = make_company(name="Cliente A")
    other = make_company(name="Cliente B")
    mine = make_area(company, name="Operaciones")
    theirs = make_area(other, name="Operaciones")

    _make_score(
        company,
        survey,
        make_user_with_profile(email="mine@x.mx", company=company, area=mine),
        c.NDR_BAJO,
    )
    _make_score(
        other,
        survey,
        make_user_with_profile(email="theirs@x.mx", company=other, area=theirs),
        c.NDR_MUY_ALTO,
    )

    data = company_valuation(company)
    assert len(data["areas"]) == 1
    assert data["areas"][0]["scored_count"] == 1
    assert data["areas"][0]["area_id"] == mine.pk
    assert data["areas"][0]["action_ndr"] == c.NDR_BAJO


def test_user_without_a_profile_falls_into_sin_area(make_company, make_user, survey):
    """select_related through the reverse O2O makes this path non-obvious."""
    from apps.nom035 import constants as c

    company = make_company()
    _make_score(company, survey, make_user(email="noprofile@x.mx"), c.NDR_BAJO)

    data = company_valuation(company)
    assert [a["label"] for a in data["areas"]] == ["Sin área"]
    assert data["areas"][0]["area_id"] is None


def test_foreign_company_area_is_not_labelled_on_this_dashboard(
    make_company, make_user_with_profile, make_area, survey
):
    """Assignments are looked up without company scoping in apps/surveys, so a
    submission can reach the wrong roll-up. It must not print the other client's
    catalog name here."""
    from apps.nom035 import constants as c

    company = make_company(name="Cliente A")
    other = make_company(name="Cliente B")
    foreign_area = make_area(other, name="AreaSecretaDeB")
    employee_of_b = make_user_with_profile(
        email="crossed@x.mx", company=other, area=foreign_area
    )

    # Submission belongs to Cliente A's assignment, respondent belongs to B.
    _make_score(company, survey, employee_of_b, c.NDR_BAJO)

    data = company_valuation(company)
    labels = [a["label"] for a in data["areas"]]
    assert "AreaSecretaDeB" not in labels
    assert labels == ["Sin área"]


def test_employee_valuation_returns_nested_scores(scored):
    from apps.nom035 import constants as c
    from apps.nom035.models import GroupScore, SubmissionScore

    score = SubmissionScore.objects.get(submission__user=scored["user"])
    GroupScore.objects.create(
        submission_score=score,
        level=c.LEVEL_CATEGORIA,
        key="ambiente_de_trabajo",
        score=13,
        ndr=c.NDR_ALTO,
    )
    GroupScore.objects.create(
        submission_score=score,
        level=c.LEVEL_DOMINIO,
        key="condiciones_en_el_ambiente_de_trabajo",
        score=13,
        ndr=c.NDR_ALTO,
    )
    GroupScore.objects.create(
        submission_score=score,
        level=c.LEVEL_DIMENSION,
        key="trabajos_peligrosos",
        score=4,
        ndr="",
    )

    data = employee_valuation(scored["user"], scored["company"])
    assert data["final_ndr"] == c.NDR_MUY_ALTO
    assert "final_action" not in data
    cat = data["categories"][0]
    assert cat["key"] == "ambiente_de_trabajo"
    assert cat["score"] == 13
    assert cat["ndr_label"] == "Alto"
    dom = cat["domains"][0]
    assert dom["score"] == 13
    dim = dom["dimensions"][0]
    assert dim["key"] == "trabajos_peligrosos"
    assert dim["score"] == 4
    assert "ndr" not in dim  # dimensión is score-only


def test_employee_valuation_none_when_unscored(make_company, make_user):
    assert employee_valuation(make_user(email="n@x.mx"), make_company()) is None


def test_employee_valuation_picks_most_recently_completed(make_company, make_user):
    """When a user has several scored submissions, pick the latest by completion
    time — not by materialization time (computed_at), which a recompute reorders."""
    import datetime

    from django.utils import timezone

    from apps.surveys.models import Survey

    company = make_company()
    user = make_user(email="multi@x.mx")
    earlier = timezone.make_aware(datetime.datetime(2026, 1, 1, 12, 0))
    later = timezone.make_aware(datetime.datetime(2026, 1, 2, 12, 0))

    def _scored(key, completed_at, final_score):
        survey = Survey.objects.create(
            key=key, title=key, status=Survey.Status.PUBLISHED
        )
        assignment = SurveyAssignment.objects.create(
            company=company,
            survey=survey,
            variant=SurveyAssignment.Variant.LARGE,
            status=SurveyAssignment.Status.ACTIVE,
        )
        sub = SurveySubmission.objects.create(
            assignment=assignment,
            user=user,
            status=SurveySubmission.Status.IN_PROGRESS,
            completed_at=completed_at,
        )
        return SubmissionScore.objects.create(
            submission=sub, final_score=final_score, final_ndr=c.NDR_BAJO
        )

    # The most-recently-completed submission's score is materialized FIRST,
    # so ordering by computed_at would (wrongly) prefer the older submission.
    _scored("recent", later, final_score=11)
    _scored("old", earlier, final_score=22)

    data = employee_valuation(user, company)
    assert data["final_score"] == 11
