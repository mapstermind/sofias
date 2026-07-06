import pytest
from django.core.management import call_command

from apps.nom035.models import SubmissionScore
from apps.responses.models import Answer, SurveySubmission
from apps.surveys.models import Question, Survey, SurveyAssignment

pytestmark = pytest.mark.django_db


def test_recompute_scores_all_completed(make_company):
    call_command("seed_nom035_survey")
    survey = Survey.objects.get(key="nom035")
    assignment = SurveyAssignment.objects.create(
        company=make_company(),
        survey=survey,
        variant=SurveyAssignment.Variant.LARGE,
        status=SurveyAssignment.Status.ACTIVE,
    )
    sub = SurveySubmission.objects.create(
        assignment=assignment, status=SurveySubmission.Status.COMPLETED
    )
    q = Question.objects.get(survey=survey, code="g3-1")
    Answer.objects.create(submission=sub, question=q, value=5)
    SubmissionScore.objects.all().delete()  # simulate stale/missing scores

    call_command("recompute_nom035_scores")

    assert SubmissionScore.objects.filter(submission=sub).exists()


def test_recompute_company_filter(make_company):
    call_command("seed_nom035_survey")
    survey = Survey.objects.get(key="nom035")
    q = Question.objects.get(survey=survey, code="g3-1")

    def _completed_submission(company):
        assignment = SurveyAssignment.objects.create(
            company=company,
            survey=survey,
            variant=SurveyAssignment.Variant.LARGE,
            status=SurveyAssignment.Status.ACTIVE,
        )
        sub = SurveySubmission.objects.create(
            assignment=assignment, status=SurveySubmission.Status.COMPLETED
        )
        Answer.objects.create(submission=sub, question=q, value=5)
        return sub

    target = _completed_submission(make_company(name="Target"))
    other = _completed_submission(make_company(name="Other"))
    SubmissionScore.objects.all().delete()  # clear scores created by the signal

    call_command(
        "recompute_nom035_scores",
        company=target.assignment.company.reference_code,
    )

    assert SubmissionScore.objects.filter(submission=target).exists()
    assert not SubmissionScore.objects.filter(submission=other).exists()
