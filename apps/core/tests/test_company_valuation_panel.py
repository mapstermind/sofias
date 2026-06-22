import pytest
from django.urls import reverse

from apps.nom035 import constants as c
from apps.nom035.models import SubmissionScore
from apps.responses.models import SurveySubmission
from apps.surveys.models import SurveyAssignment

pytestmark = pytest.mark.django_db


def test_dashboard_shows_valuation(
    client, bootstrap_groups, make_user_with_profile, make_company, survey
):
    company = make_company()
    admin = make_user_with_profile(email="a@x.mx", company=company)
    admin.groups.add(bootstrap_groups["Admins"])
    assignment = SurveyAssignment.objects.create(
        company=company,
        survey=survey,
        variant=SurveyAssignment.Variant.LARGE,
        status=SurveyAssignment.Status.ACTIVE,
    )
    # In-progress so the completion signal does not overwrite our explicit score.
    sub = SurveySubmission.objects.create(
        assignment=assignment, status=SurveySubmission.Status.IN_PROGRESS
    )
    SubmissionScore.objects.create(
        submission=sub, final_score=160, final_ndr=c.NDR_MUY_ALTO
    )

    client.force_login(admin)
    resp = client.get(
        reverse("core:company_dashboard_for", args=[company.reference_code])
    )
    assert resp.status_code == 200
    assert "Valoración de resultados".encode() in resp.content
