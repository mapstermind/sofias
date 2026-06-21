import pytest
from django.core.management import call_command

from apps.surveys.models import Question, Survey

pytestmark = pytest.mark.django_db


class TestSeedNom035:
    def test_seed_builds_survey_structure(self):
        call_command("seed_nom035_survey")

        survey = Survey.objects.get(key="nom035")
        applies = set(survey.modules.values_list("applies_to", flat=True))
        assert applies == {"all", "small", "large"}

    def test_likert_counts_per_variant(self):
        call_command("seed_nom035_survey")
        survey = Survey.objects.get(key="nom035")

        likert = Question.objects.filter(survey=survey, question_type="likert")
        small = likert.filter(module__applies_to__in=["all", "small"]).count()
        large = likert.filter(module__applies_to__in=["all", "large"]).count()
        # Guía II = 46 likert items, Guía III = 72 (Guía I is boolean, not likert).
        assert small == 46
        assert large == 72

    def test_codes_unique_and_idempotent(self):
        call_command("seed_nom035_survey")
        call_command("seed_nom035_survey")  # re-run

        assert Survey.objects.filter(key="nom035").count() == 1
        survey = Survey.objects.get(key="nom035")
        total = Question.objects.filter(survey=survey).count()
        distinct = (
            Question.objects.filter(survey=survey).values("code").distinct().count()
        )
        assert total == distinct

    def test_branching_gates_seeded(self):
        call_command("seed_nom035_survey")
        survey = Survey.objects.get(key="nom035")

        followup = survey.modules.get(key="g1-followup")
        assert followup.visible_when == {"any_in_module": "g1-trigger", "equals": True}

        gated = Question.objects.get(survey=survey, code="g2-41")
        assert gated.visible_when == {"question": "g2-clientes", "equals": True}
