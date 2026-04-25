import pytest

from apps.responses.models import SurveySubmission
from apps.surveys.models import SurveyAssignment

pytestmark = pytest.mark.django_db


def _survey_url(assignment_id):
    return f"/encuestas/asignados/{assignment_id}/"


def _submitted_url(assignment_id):
    return f"/encuestas/asignados/{assignment_id}/enviada/"


class TestSurveyDetailView:
    def test_get_returns_200(self, client, active_assignment):
        response = client.get(_survey_url(active_assignment.pk))
        assert response.status_code == 200

    def test_closed_assignment_returns_200_with_closed_flag(
        self, client, active_assignment
    ):
        active_assignment.status = SurveyAssignment.Status.CLOSED
        active_assignment.save()
        response = client.get(_survey_url(active_assignment.pk))
        assert response.status_code == 200
        assert response.context["is_closed"] is True

    def test_nonexistent_assignment_returns_404(self, client):
        response = client.get(_survey_url(99999))
        assert response.status_code == 404

    def test_post_all_question_types_creates_submission(
        self, client, active_assignment, survey_with_questions
    ):
        questions = survey_with_questions["questions"]
        post_data = {}
        for q in questions:
            key = f"question_{q.id}"
            if q.question_type == "boolean":
                post_data[key] = "true"
            elif q.question_type == "multiple_choice":
                post_data[key] = ["a"]
            elif q.question_type == "integer":
                post_data[key] = "5"
            elif q.question_type == "decimal":
                post_data[key] = "3.14"
            elif q.question_type == "date":
                post_data[key] = "2025-01-01"
            elif q.question_type == "rating":
                post_data[key] = "4"
            elif q.question_type == "likert":
                post_data[key] = "3"
            else:
                post_data[key] = "Some text answer"

        response = client.post(_survey_url(active_assignment.pk), post_data)
        assert response.status_code == 302

        submission = SurveySubmission.objects.filter(
            assignment=active_assignment
        ).first()
        assert submission is not None
        assert submission.answers.count() == len(questions)

    def test_post_all_question_types_redirects_to_submitted(
        self, client, active_assignment, survey_with_questions
    ):
        questions = survey_with_questions["questions"]
        post_data = {}
        # Fill all types minimally
        for q in questions:
            key = f"question_{q.id}"
            if q.question_type == "boolean":
                post_data[key] = "true"
            elif q.question_type == "multiple_choice":
                post_data[key] = ["a"]
            elif q.question_type == "integer":
                post_data[key] = "1"
            elif q.question_type == "decimal":
                post_data[key] = "1.0"
            elif q.question_type == "date":
                post_data[key] = "2025-06-01"
            elif q.question_type == "rating":
                post_data[key] = "3"
            elif q.question_type == "likert":
                post_data[key] = "2"
            else:
                post_data[key] = "text"

        response = client.post(_survey_url(active_assignment.pk), post_data)
        assert response["Location"].endswith(_submitted_url(active_assignment.pk))

    def test_post_invalid_integer_shows_error_for_that_question(
        self, client, active_assignment, survey_with_questions
    ):
        questions = survey_with_questions["questions"]
        int_q = next(q for q in questions if q.question_type == "integer")

        response = client.post(
            _survey_url(active_assignment.pk),
            {f"question_{int_q.id}": "not-a-number"},
        )
        assert response.status_code == 200
        assert int_q.id in response.context["errors"]

    def test_post_invalid_decimal_shows_error(
        self, client, active_assignment, survey_with_questions
    ):
        questions = survey_with_questions["questions"]
        dec_q = next(q for q in questions if q.question_type == "decimal")

        response = client.post(
            _survey_url(active_assignment.pk),
            {f"question_{dec_q.id}": "abc"},
        )
        assert response.status_code == 200
        assert dec_q.id in response.context["errors"]


class TestSurveySubmittedView:
    def test_get_returns_200(self, client, active_assignment):
        response = client.get(_submitted_url(active_assignment.pk))
        assert response.status_code == 200

    def test_closed_assignment_returns_200(self, client, active_assignment):
        active_assignment.status = SurveyAssignment.Status.CLOSED
        active_assignment.save()
        response = client.get(_submitted_url(active_assignment.pk))
        assert response.status_code == 200
