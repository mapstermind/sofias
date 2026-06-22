import pytest

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
        guia1_event=True,
        guia1_followup_count=6,
        guia1_severity=c.SEV_HIGH,
    )
    return {"company": company, "user": user}


def test_company_valuation_counts(scored):
    data = company_valuation(scored["company"])
    assert data["scored_count"] == 1
    assert data["needing_action"] == 1
    assert data["guia1_flags"] == 1
    assert data["distribution"][c.NDR_MUY_ALTO] == 1


def test_employee_valuation_returns_text(scored):
    data = employee_valuation(scored["user"], scored["company"])
    assert data["final_ndr"] == c.NDR_MUY_ALTO
    assert data["final_action"]


def test_employee_valuation_none_when_unscored(make_company, make_user):
    assert employee_valuation(make_user(email="n@x.mx"), make_company()) is None
