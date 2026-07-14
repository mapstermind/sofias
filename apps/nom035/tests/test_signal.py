import pytest
from django.core.management import call_command

from apps.nom035.models import SubmissionScore
from apps.responses.models import Answer, SurveySubmission
from apps.surveys.models import Question, Survey, SurveyAssignment

pytestmark = pytest.mark.django_db


@pytest.fixture
def assignment(make_company):
    call_command("seed_nom035_survey")
    return SurveyAssignment.objects.create(
        company=make_company(),
        survey=Survey.objects.get(key="nom035"),
        variant=SurveyAssignment.Variant.LARGE,
        status=SurveyAssignment.Status.ACTIVE,
    )


def test_completed_submission_is_scored_automatically(assignment):
    sub = SurveySubmission.objects.create(
        assignment=assignment, status=SurveySubmission.Status.IN_PROGRESS
    )
    q = Question.objects.filter(survey=assignment.survey, code="g3-1").first()
    Answer.objects.create(submission=sub, question=q, value=5)
    assert not SubmissionScore.objects.filter(submission=sub).exists()

    sub.status = SurveySubmission.Status.COMPLETED
    sub.save()

    assert SubmissionScore.objects.filter(submission=sub).exists()


def test_non_nom035_submission_is_not_scored(make_company, survey):
    # `survey` fixture has key "test-survey"; the engine is NOM-035-specific.
    assignment = SurveyAssignment.objects.create(
        company=make_company(),
        survey=survey,
        variant=SurveyAssignment.Variant.LARGE,
        status=SurveyAssignment.Status.ACTIVE,
    )
    sub = SurveySubmission.objects.create(
        assignment=assignment, status=SurveySubmission.Status.COMPLETED
    )
    assert not SubmissionScore.objects.filter(submission=sub).exists()


def test_submission_without_user_is_scored(assignment):
    # `user` goes null when an employee is deleted (SET_NULL); the submission they
    # left behind must still score, so it keeps counting in the company aggregates.
    sub = SurveySubmission.objects.create(
        assignment=assignment, user=None, status=SurveySubmission.Status.IN_PROGRESS
    )
    q = Question.objects.get(survey=assignment.survey, code="g3-1")
    Answer.objects.create(submission=sub, question=q, value=5)

    sub.status = SurveySubmission.Status.COMPLETED
    sub.save()

    assert SubmissionScore.objects.filter(submission=sub).exists()
