from django.core.management.base import BaseCommand

from apps.core.workflows.question import run_create_question


class Command(BaseCommand):
    help = "Interactively create a question within a survey version"

    def handle(self, *args, **options):
        try:
            run_create_question()
        except KeyboardInterrupt:
            self.stdout.write("\nAborted.")
