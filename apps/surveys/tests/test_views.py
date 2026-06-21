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

    def test_closed_assignment_redirects_to_home(self, client, active_assignment):
        active_assignment.status = SurveyAssignment.Status.CLOSED
        active_assignment.save()
        response = client.get(_survey_url(active_assignment.pk))
        assert response.status_code == 302
        assert response["Location"] == "/"

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


@pytest.fixture
def variant_survey(db, survey, make_company):
    """Survey with an `all` trigger+followup, a small-only and large-only question."""
    from apps.surveys.models import Module, Question

    trigger = Module.objects.create(
        survey=survey, key="trigger", title="T", applies_to="all", order=0
    )
    Question.objects.create(
        module=trigger, code="t1", question_type="boolean", text="Trigger?"
    )
    followup = Module.objects.create(
        survey=survey,
        key="followup",
        title="F",
        applies_to="all",
        order=1,
        visible_when={"any_in_module": "trigger", "equals": True},
    )
    Question.objects.create(
        module=followup, code="f1", question_type="text", text="Why?"
    )
    small = Module.objects.create(
        survey=survey, key="small", title="S", applies_to="small", order=2
    )
    Question.objects.create(
        module=small, code="s1", question_type="text", text="Small only"
    )
    large = Module.objects.create(
        survey=survey, key="large", title="L", applies_to="large", order=3
    )
    Question.objects.create(
        module=large, code="l1", question_type="text", text="Large only"
    )
    return survey


class TestVariantPresentation:
    def _assignment(self, survey, make_company, variant):
        return SurveyAssignment.objects.create(
            company=make_company(), survey=survey, variant=variant
        )

    def test_small_shows_small_not_large(self, client, variant_survey, make_company):
        a = self._assignment(variant_survey, make_company, "small")
        body = client.get(_survey_url(a.pk)).content.decode()
        assert "Small only" in body
        assert "Large only" not in body

    def test_large_shows_large_not_small(self, client, variant_survey, make_company):
        a = self._assignment(variant_survey, make_company, "large")
        body = client.get(_survey_url(a.pk)).content.decode()
        assert "Large only" in body
        assert "Small only" not in body

    def test_skip_path_completes_without_hidden_followup(
        self, client, variant_survey, make_company, make_user
    ):
        a = self._assignment(variant_survey, make_company, "small")
        user = make_user(email="emp@x.com")
        client.force_login(user)
        # Trigger = No hides f1; answer the visible questions only.
        from apps.surveys.models import Question

        q = {x.code: x for x in Question.objects.filter(survey=variant_survey)}
        post = {
            f"question_{q['t1'].id}": "false",
            f"question_{q['s1'].id}": "answer",
        }
        response = client.post(_survey_url(a.pk), post)
        assert response["Location"].endswith(_submitted_url(a.pk))
        sub = SurveySubmission.objects.get(assignment=a, user=user)
        assert sub.status == SurveySubmission.Status.COMPLETED


class TestSurveySubmittedView:
    def test_get_returns_200(self, client, active_assignment):
        response = client.get(_submitted_url(active_assignment.pk))
        assert response.status_code == 200

    def test_closed_assignment_returns_200(self, client, active_assignment):
        active_assignment.status = SurveyAssignment.Status.CLOSED
        active_assignment.save()
        response = client.get(_submitted_url(active_assignment.pk))
        assert response.status_code == 200
