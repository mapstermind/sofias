from django.core.management.base import BaseCommand

from apps.nom035._nom035_scoring import NOM035_SURVEY_KEY
from apps.nom035.services import materialize
from apps.responses.models import SurveySubmission


class Command(BaseCommand):
    help = "Recompute NOM-035 scores for completed submissions."

    def add_arguments(self, parser):
        parser.add_argument("--company", default=None, help="Company reference_code")

    def handle(self, *args, **options):
        qs = SurveySubmission.objects.filter(
            status=SurveySubmission.Status.COMPLETED,
            assignment__survey__key=NOM035_SURVEY_KEY,
        )
        if options["company"]:
            qs = qs.filter(assignment__company__reference_code=options["company"])
        count = 0
        for submission in qs.iterator():
            materialize(submission)
            count += 1
        self.stdout.write(self.style.SUCCESS(f"Recomputed {count} submission scores."))
