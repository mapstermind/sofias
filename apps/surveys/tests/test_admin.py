import pytest
from django.urls import reverse

from apps.surveys.models import Module, Question, Survey, SurveyAssignment

pytestmark = pytest.mark.django_db


@pytest.mark.parametrize(
    "model,field,value,expected",
    [
        (Survey, "status", Survey.Status.PUBLISHED, "Publicada"),
        (Module, "applies_to", Module.AppliesTo.SMALL, "Variante pequeña"),
        (Question, "question_type", Question.QuestionType.LIKERT, "Escala Likert"),
        (SurveyAssignment, "status", SurveyAssignment.Status.ACTIVE, "Activa"),
        (SurveyAssignment, "variant", SurveyAssignment.Variant.LARGE, "Guía III"),
    ],
)
def test_choice_labels_are_spanish(model, field, value, expected):
    """Choice labels reach the operator through changelists and filter sidebars."""
    assert dict(model._meta.get_field(field).choices)[value] == expected


def test_survey_change_form_labels_are_spanish(staff_client, survey):
    response = staff_client.get(
        reverse("admin:surveys_survey_change", args=[survey.pk])
    )

    body = response.content.decode()
    assert "Umbral de plantilla" in body
    assert "Headcount threshold" not in body


# ---------------------------------------------------------------------------
# Assignment variant: automatic from headcount unless the operator picks one
# ---------------------------------------------------------------------------

ADD_URL = "admin:surveys_surveyassignment_add"


def _staff_company(make_company, make_user_with_profile, members):
    company = make_company()
    for i in range(members):
        make_user_with_profile(email=f"member{i}@example.com", company=company)
    return company


def _post_assignment(staff_client, company, survey, variant=""):
    return staff_client.post(
        reverse(ADD_URL),
        {
            "company": company.pk,
            "survey": survey.pk,
            "variant": variant,
            "status": SurveyAssignment.Status.ACTIVE,
            "due_date": "",
        },
        follow=True,
    )


def test_add_form_offers_automatic_variant(staff_client):
    body = staff_client.get(reverse(ADD_URL)).content.decode()

    assert "Automática (según número de colaboradores)" in body


@pytest.mark.parametrize(
    "members,expected",
    [(2, SurveyAssignment.Variant.SMALL), (3, SurveyAssignment.Variant.LARGE)],
)
def test_automatic_variant_follows_headcount(
    staff_client, make_company, make_user_with_profile, members, expected
):
    company = _staff_company(make_company, make_user_with_profile, members)
    survey = Survey.objects.create(key="s", title="S", headcount_threshold=2)

    response = _post_assignment(staff_client, company, survey)

    assignment = SurveyAssignment.objects.get(company=company)
    assert assignment.variant == expected
    assert (
        f"Variante asignada automáticamente: {assignment.get_variant_display()}"
        in response.content.decode()
    )


def test_explicit_variant_overrides_headcount(
    staff_client, make_company, make_user_with_profile
):
    company = _staff_company(make_company, make_user_with_profile, 3)
    survey = Survey.objects.create(key="s", title="S", headcount_threshold=2)

    response = _post_assignment(
        staff_client, company, survey, variant=SurveyAssignment.Variant.SMALL
    )

    assert (
        SurveyAssignment.objects.get(company=company).variant
        == SurveyAssignment.Variant.SMALL
    )
    assert "Variante asignada automáticamente" not in response.content.decode()


def test_missing_company_reports_only_the_company(staff_client, survey):
    response = staff_client.post(
        reverse(ADD_URL),
        {"survey": survey.pk, "variant": "", "status": "active", "due_date": ""},
    )

    form = response.context["adminform"].form
    assert set(form.errors) == {"company"}
    assert not SurveyAssignment.objects.exists()


def test_change_form_keeps_stored_variant_required(staff_client, active_assignment):
    response = staff_client.get(
        reverse("admin:surveys_surveyassignment_change", args=[active_assignment.pk])
    )

    body = response.content.decode()
    assert "Automática" not in body
    assert response.context["adminform"].form.fields["variant"].required
