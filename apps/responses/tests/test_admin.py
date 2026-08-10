import pytest

from apps.responses.models import SurveySubmission

pytestmark = pytest.mark.django_db


@pytest.mark.parametrize(
    "value,expected",
    [
        (SurveySubmission.Status.IN_PROGRESS, "En progreso"),
        (SurveySubmission.Status.COMPLETED, "Completado"),
    ],
)
def test_submission_status_labels_are_spanish(value, expected):
    field = SurveySubmission._meta.get_field("status")
    assert dict(field.choices)[value] == expected


def test_submission_str_is_spanish(active_assignment, make_user):
    submission = SurveySubmission.objects.create(
        assignment=active_assignment, user=make_user(email="envio@x.mx")
    )

    assert str(submission).startswith(f"Envío {submission.pk} — ")
