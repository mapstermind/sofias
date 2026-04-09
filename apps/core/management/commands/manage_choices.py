from django.core.management.base import BaseCommand

from apps.core.workflows.choices import run_manage_choices


class Command(BaseCommand):
    help = "Interactively manage choices for a choice-type question"

    def handle(self, *args, **options):
        try:
            run_manage_choices()
        except KeyboardInterrupt:
            self.stdout.write("\nAborted.")
