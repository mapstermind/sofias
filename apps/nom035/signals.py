from django.db.models.signals import post_save
from django.dispatch import receiver

from apps.nom035._nom035_scoring import NOM035_SURVEY_KEY
from apps.nom035.services import materialize
from apps.responses.models import SurveySubmission


@receiver(post_save, sender=SurveySubmission)
def score_on_completion(sender, instance, **kwargs):
    """Materialize a score whenever a NOM-035 submission is completed."""
    if instance.status != SurveySubmission.Status.COMPLETED:
        return
    if instance.assignment.survey.key != NOM035_SURVEY_KEY:
        return  # the engine is NOM-035-specific (see ADR-0003)
    materialize(instance)
