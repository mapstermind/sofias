from django.db.models.signals import post_save
from django.dispatch import receiver

from apps.nom035.services import materialize
from apps.responses.models import SurveySubmission


@receiver(post_save, sender=SurveySubmission)
def score_on_completion(sender, instance, **kwargs):
    """Materialize a NOM-035 score whenever a submission is completed."""
    if instance.status == SurveySubmission.Status.COMPLETED:
        materialize(instance)
