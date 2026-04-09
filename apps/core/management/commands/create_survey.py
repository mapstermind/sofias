from django.core.management.base import BaseCommand

from apps.core.workflows.survey import run_create_survey


class Command(BaseCommand):
    help = "Interactively create a survey and its first version"

    def handle(self, *args, **options):
        try:
            run_create_survey()
        except KeyboardInterrupt:
            self.stdout.write("\nAborted.")
