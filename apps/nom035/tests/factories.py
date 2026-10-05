"""Builders for NOM-035 result tests: scored submissions without running the engine."""

from apps.nom035 import constants as c
from apps.nom035.models import GroupScore, SubmissionScore
from apps.responses.models import SurveySubmission
from apps.surveys.models import SurveyAssignment


def make_assignment(company, survey, variant="large"):
    return SurveyAssignment.objects.create(
        company=company,
        survey=survey,
        variant=variant,
        status=SurveyAssignment.Status.ACTIVE,
    )


def make_score(
    assignment,
    user=None,
    *,
    final_score=10,
    final_ndr=c.NDR_BAJO,
    groups=(),
    guia1_event=False,
    guia1_positive=False,
    completed_at=None,
):
    """A scored submission without running the engine.

    Created IN_PROGRESS so the completion signal does not overwrite the
    explicit score; `completed_at` is set directly for label tests.
    `groups` is an iterable of (level, key, score, ndr).
    """
    sub = SurveySubmission.objects.create(
        assignment=assignment,
        user=user,
        status=SurveySubmission.Status.IN_PROGRESS,
        completed_at=completed_at,
    )
    score = SubmissionScore.objects.create(
        submission=sub,
        final_score=final_score,
        final_ndr=final_ndr,
        guia1_event=guia1_event,
        guia1_positive=guia1_positive,
    )
    GroupScore.objects.bulk_create(
        GroupScore(submission_score=score, level=level, key=key, score=value, ndr=ndr)
        for level, key, value, ndr in groups
    )
    return score
