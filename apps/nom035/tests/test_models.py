import pytest

from apps.nom035 import constants as c
from apps.nom035.models import GroupScore, SubmissionScore
from apps.responses.models import SurveySubmission

pytestmark = pytest.mark.django_db


def _submission(active_assignment):
    return SurveySubmission.objects.create(
        assignment=active_assignment, status=SurveySubmission.Status.COMPLETED
    )


def test_submission_score_is_one_per_submission(active_assignment):
    sub = _submission(active_assignment)
    SubmissionScore.objects.create(
        submission=sub,
        final_score=120,
        final_ndr=c.NDR_ALTO,
        guia1_event=True,
        guia1_followup_count=4,
        guia1_severity=c.SEV_MED,
    )
    with pytest.raises(Exception):
        SubmissionScore.objects.create(
            submission=sub, final_score=1, final_ndr=c.NDR_NULO
        )


def test_group_score_unique_per_level_and_key(active_assignment):
    sub = _submission(active_assignment)
    score = SubmissionScore.objects.create(
        submission=sub, final_score=10, final_ndr=c.NDR_NULO
    )
    GroupScore.objects.create(
        submission_score=score,
        level=c.LEVEL_CATEGORIA,
        key="ambiente",
        score=5,
        ndr=c.NDR_NULO,
    )
    with pytest.raises(Exception):
        GroupScore.objects.create(
            submission_score=score,
            level=c.LEVEL_CATEGORIA,
            key="ambiente",
            score=9,
            ndr=c.NDR_BAJO,
        )
