import pytest
from django.urls import reverse

from apps.nom035 import constants as c
from apps.nom035.models import SubmissionScore
from apps.responses.models import SurveySubmission
from apps.surveys.models import SurveyAssignment

pytestmark = pytest.mark.django_db


def test_panel_shows_ndr_for_insights_user(
    client, bootstrap_groups, make_user_with_profile, make_company, survey
):
    company = make_company()
    admin = make_user_with_profile(email="admin@x.mx", company=company)
    admin.groups.add(bootstrap_groups["Admins"])
    employee = make_user_with_profile(email="emp@x.mx", company=company)
    assignment = SurveyAssignment.objects.create(
        company=company,
        survey=survey,
        variant=SurveyAssignment.Variant.LARGE,
        status=SurveyAssignment.Status.ACTIVE,
    )
    # In-progress so the completion signal does not overwrite our explicit score.
    sub = SurveySubmission.objects.create(
        assignment=assignment, user=employee, status=SurveySubmission.Status.IN_PROGRESS
    )
    SubmissionScore.objects.create(
        submission=sub, final_score=160, final_ndr=c.NDR_MUY_ALTO
    )

    client.force_login(admin)
    resp = client.get(reverse("core:company_employee_detail", args=[employee.id]))
    assert resp.status_code == 200
    assert "Valoración de resultados".encode() in resp.content
    assert "Muy alto".encode() in resp.content


def test_panel_shows_scores_and_hierarchy(
    client, bootstrap_groups, make_user_with_profile, make_company, survey
):
    from apps.nom035.models import GroupScore

    company = make_company()
    admin = make_user_with_profile(email="admin2@x.mx", company=company)
    admin.groups.add(bootstrap_groups["Admins"])
    employee = make_user_with_profile(email="emp2@x.mx", company=company)
    assignment = SurveyAssignment.objects.create(
        company=company,
        survey=survey,
        variant=SurveyAssignment.Variant.LARGE,
        status=SurveyAssignment.Status.ACTIVE,
    )
    sub = SurveySubmission.objects.create(
        assignment=assignment, user=employee, status=SurveySubmission.Status.IN_PROGRESS
    )
    score = SubmissionScore.objects.create(
        submission=sub, final_score=160, final_ndr=c.NDR_MUY_ALTO
    )
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

    client.force_login(admin)
    resp = client.get(reverse("core:company_employee_detail", args=[employee.id]))
    body = resp.content.decode()
    assert "Ambiente de trabajo" in body
    assert "Trabajos peligrosos" in body  # dimensión label rendered
    assert "Se requiere" not in body  # no action sentence on the card
