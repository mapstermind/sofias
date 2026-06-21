from django.core.management.base import BaseCommand
from django.db import transaction

from apps.surveys.models import Module, Question, Survey

from ._nom035_data import (
    HEADCOUNT_THRESHOLD,
    SURVEY_DESCRIPTION,
    SURVEY_KEY,
    SURVEY_TITLE,
    build_modules,
)


class Command(BaseCommand):
    help = "Seed (or replace) the NOM-035 survey: modules, questions and choices."

    @transaction.atomic
    def handle(self, *args, **options):
        survey, created = Survey.objects.update_or_create(
            key=SURVEY_KEY,
            defaults={
                "title": SURVEY_TITLE,
                "description": SURVEY_DESCRIPTION,
                "status": Survey.Status.PUBLISHED,
                "headcount_threshold": HEADCOUNT_THRESHOLD,
            },
        )
        self.stdout.write(f"{'Created' if created else 'Updated'} Survey: {SURVEY_KEY}")

        # Replace modules/questions to keep the seed deterministic on re-run.
        survey.modules.all().delete()

        modules = build_modules()
        for order, mod_data in enumerate(modules):
            gate_code, followup_codes = mod_data.get("_gate_followups", (None, []))
            followup_set = set(followup_codes)

            module = Module.objects.create(
                survey=survey,
                key=mod_data["key"],
                title=mod_data["title"],
                description=mod_data.get("description", ""),
                order=order,
                applies_to=mod_data["applies_to"],
                visible_when=mod_data.get("visible_when"),
            )

            for q_order, q_data in enumerate(mod_data["questions"]):
                visible_when = q_data.get("visible_when")
                if gate_code and q_data["code"] in followup_set:
                    visible_when = {"question": gate_code, "equals": True}

                Question.objects.create(
                    module=module,
                    code=q_data["code"],
                    question_type=q_data["question_type"],
                    text=q_data["text"],
                    order=q_order,
                    config=q_data.get("config", {}),
                    visible_when=visible_when,
                )

        total_questions = Question.objects.filter(survey=survey).count()
        self.stdout.write(
            self.style.SUCCESS(
                f"Done. {survey.modules.count()} modules, {total_questions} questions."
            )
        )
