from django.db import transaction

from apps.nom035.models import GroupScore, SubmissionScore
from apps.nom035.scoring import score_submission


@transaction.atomic
def materialize(submission) -> SubmissionScore:
    """Compute and persist the score for a submission (idempotent upsert)."""
    result = score_submission(submission)
    score, _ = SubmissionScore.objects.update_or_create(
        submission=submission,
        defaults={
            "final_score": result.final_score,
            "final_ndr": result.final_ndr,
            "guia1_positive": result.guia1_positive,
        },
    )
    score.groups.all().delete()
    GroupScore.objects.bulk_create(
        [
            GroupScore(
                submission_score=score,
                level=g.level,
                key=g.key,
                score=g.score,
                ndr=g.ndr,
            )
            for g in result.groups
        ]
    )
    return score
