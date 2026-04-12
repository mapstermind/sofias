import pytest
from django.db import IntegrityError

from apps.responses.models import Answer, SurveySubmission

pytestmark = pytest.mark.django_db


class TestAnswerUniqueConstraint:
    def test_duplicate_answer_raises_integrity_error(
        self, active_assignment, survey_with_questions
    ):
        questions = survey_with_questions["questions"]
        question = questions[0]

        submission = SurveySubmission.objects.create(
            assignment=active_assignment,
            status=SurveySubmission.Status.IN_PROGRESS,
        )
        Answer.objects.create(submission=submission, question=question, value="first")

        with pytest.raises(IntegrityError):
            Answer.objects.create(
                submission=submission, question=question, value="second"
            )

    def test_same_question_different_submissions_allowed(
        self, active_assignment, survey_with_questions
    ):
        questions = survey_with_questions["questions"]
        question = questions[0]

        sub1 = SurveySubmission.objects.create(
            assignment=active_assignment,
            status=SurveySubmission.Status.IN_PROGRESS,
        )
        sub2 = SurveySubmission.objects.create(
            assignment=active_assignment,
            status=SurveySubmission.Status.IN_PROGRESS,
        )
        Answer.objects.create(submission=sub1, question=question, value="answer1")
        Answer.objects.create(submission=sub2, question=question, value="answer2")
        # No exception — different submissions can answer the same question
        assert Answer.objects.filter(question=question).count() == 2
