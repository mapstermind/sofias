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
