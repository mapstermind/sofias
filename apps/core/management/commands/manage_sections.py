from django.core.management.base import BaseCommand

from apps.core.workflows.sections import run_manage_sections


class Command(BaseCommand):
    help = "Interactively manage sections within a survey version"

    def handle(self, *args, **options):
        try:
            run_manage_sections()
        except KeyboardInterrupt:
            self.stdout.write("\nAborted.")
