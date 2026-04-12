import pytest
from django.db import IntegrityError

from apps.surveys.models import (
    ChoiceTemplate,
    Question,
    QuestionTemplate,
    SurveyVersion,
)

pytestmark = pytest.mark.django_db


class TestQuestionTemplateStampInto:
    def test_creates_question_in_version(self, survey_version):
        template = QuestionTemplate.objects.create(
            question_type="short_text",
            text="What is your role?",
        )
        question = template.stamp_into(survey_version)

        assert isinstance(question, Question)
        assert question.version == survey_version
        assert question.text == "What is your role?"

    def test_stamps_choices_from_template(self, survey_version):
        template = QuestionTemplate.objects.create(
            question_type="single_choice",
            text="Pick a color.",
        )
        ChoiceTemplate.objects.create(
            question=template, label="Red", value="red", order=0
        )
        ChoiceTemplate.objects.create(
            question=template, label="Blue", value="blue", order=1
        )

        question = template.stamp_into(survey_version)

        assert question.choices.count() == 2
        labels = set(question.choices.values_list("label", flat=True))
        assert labels == {"Red", "Blue"}

    def test_stamped_question_independent_of_template_changes(self, survey_version):
        template = QuestionTemplate.objects.create(
            question_type="long_text",
            text="Original text.",
        )
        question = template.stamp_into(survey_version)

        template.text = "Changed text."
        template.save()
        question.refresh_from_db()

        assert question.text == "Original text."

    def test_survey_version_unique_constraint(self, survey_template):
        SurveyVersion.objects.create(template=survey_template, version_number=1)
        with pytest.raises(IntegrityError):
            SurveyVersion.objects.create(template=survey_template, version_number=1)
