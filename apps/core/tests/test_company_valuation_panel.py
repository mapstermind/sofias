import pytest
from django.urls import reverse

from apps.nom035 import constants as c
from apps.nom035.models import SubmissionScore
from apps.responses.models import SurveySubmission
from apps.surveys.models import Survey, SurveyAssignment

pytestmark = pytest.mark.django_db


def test_dashboard_links_to_results(
    client, bootstrap_groups, make_user_with_profile, make_company
):
    company = make_company()
    admin = make_user_with_profile(email="a@x.mx", company=company)
    admin.groups.add(bootstrap_groups["Admins"])
    survey = Survey.objects.create(
        key="nom035", title="NOM-035", status=Survey.Status.PUBLISHED
    )
    assignment = SurveyAssignment.objects.create(
        company=company,
        survey=survey,
        variant="large",
        status=SurveyAssignment.Status.ACTIVE,
    )
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
    body = resp.content.decode()
    assert "Valoración de resultados" in body
    assert reverse("core:company_results_for", args=[company.reference_code]) in body
    assert "Por área" not in body
    assert "company_valuation" not in resp.context


def test_dashboard_hides_results_card_without_permission(
    client, bootstrap_groups, make_user_with_profile, make_company
):
    from apps.accounts.roles import ROLES

    company = make_company()
    user = make_user_with_profile(email="s@x.mx", company=company)
    user.groups.add(bootstrap_groups[ROLES[2].name])  # Ejecutivo secundario
    client.force_login(user)
    body = client.get(reverse("core:company_dashboard")).content.decode()
    assert "Ver resultados" not in body
