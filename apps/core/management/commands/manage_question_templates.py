from django.core.management.base import BaseCommand

from apps.core.workflows.question_template import run_manage_question_templates


class Command(BaseCommand):
    help = "Interactively manage the question template library"

    def handle(self, *args, **options):
        try:
            run_manage_question_templates()
        except KeyboardInterrupt:
            self.stdout.write("\nAborted.")
