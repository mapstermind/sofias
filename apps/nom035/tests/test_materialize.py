import pytest
from django.core.management import call_command

from apps.nom035.models import SubmissionScore
from apps.nom035.services import materialize
from apps.responses.models import Answer, SurveySubmission
from apps.surveys.models import Question, Survey, SurveyAssignment

pytestmark = pytest.mark.django_db


@pytest.fixture
def completed_submission(make_company):
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
    codes = {q.code: q for q in Question.objects.filter(survey=survey)}
    for code in [f"g3-{i}" for i in range(1, 10)]:
        Answer.objects.create(submission=sub, question=codes[code], value=5)
    return sub


def test_materialize_creates_rows(completed_submission):
    score = materialize(completed_submission)
    assert SubmissionScore.objects.count() == 1
    assert score.groups.count() > 0


def test_materialize_is_idempotent(completed_submission):
    first = materialize(completed_submission)
    before = first.groups.count()
    second = materialize(completed_submission)
    assert SubmissionScore.objects.count() == 1
    assert second.groups.count() == before
