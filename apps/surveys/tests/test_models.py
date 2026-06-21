import pytest
from django.db import IntegrityError

from apps.surveys.models import Module, Question, Survey, SurveyAssignment

pytestmark = pytest.mark.django_db


class TestCodeUniqueness:
    def test_code_unique_per_survey(self, survey, survey_module):
        Question.objects.create(
            module=survey_module, code="dup", question_type="text", text="A"
        )
        with pytest.raises(IntegrityError):
            Question.objects.create(
                module=survey_module, code="dup", question_type="text", text="B"
            )

    def test_same_code_allowed_in_different_surveys(self, survey, survey_module):
        other = Survey.objects.create(key="other", title="Other")
        other_module = Module.objects.create(
            survey=other, key="m1", title="M", applies_to=Module.AppliesTo.ALL
        )
        Question.objects.create(
            module=survey_module, code="shared", question_type="text", text="A"
        )
        # No IntegrityError: uniqueness is per-survey.
        Question.objects.create(
            module=other_module, code="shared", question_type="text", text="B"
        )

    def test_module_key_unique_per_survey(self, survey):
        Module.objects.create(survey=survey, key="dup", title="A")
        with pytest.raises(IntegrityError):
            Module.objects.create(survey=survey, key="dup", title="B")

    def test_save_denormalizes_survey_from_module(self, survey, survey_module):
        q = Question.objects.create(
            module=survey_module, code="x", question_type="text", text="A"
        )
        assert q.survey_id == survey.id


class TestVariantResolution:
    def test_above_threshold_is_large(self, make_company, make_user_with_profile):
        company = make_company()
        survey = Survey.objects.create(key="s", title="S", headcount_threshold=2)
        for i in range(3):
            make_user_with_profile(email=f"u{i}@x.com", company=company)
        assert (
            SurveyAssignment.resolve_default_variant(company, survey)
            == SurveyAssignment.Variant.LARGE
        )

    def test_at_threshold_is_small(self, make_company, make_user_with_profile):
        company = make_company()
        survey = Survey.objects.create(key="s", title="S", headcount_threshold=2)
        for i in range(2):
            make_user_with_profile(email=f"u{i}@x.com", company=company)
        assert (
            SurveyAssignment.resolve_default_variant(company, survey)
            == SurveyAssignment.Variant.SMALL
        )

    def test_empty_company_is_small(self, make_company):
        company = make_company()
        survey = Survey.objects.create(key="s", title="S", headcount_threshold=50)
        assert (
            SurveyAssignment.resolve_default_variant(company, survey)
            == SurveyAssignment.Variant.SMALL
        )


class TestModulesForVariant:
    def _build(self, survey):
        Module.objects.create(
            survey=survey, key="all", title="All", applies_to="all", order=0
        )
        Module.objects.create(
            survey=survey, key="small", title="Small", applies_to="small", order=1
        )
        Module.objects.create(
            survey=survey, key="large", title="Large", applies_to="large", order=2
        )

    def test_small_assignment_sees_all_and_small(self, survey, make_company):
        self._build(survey)
        a = SurveyAssignment.objects.create(
            company=make_company(), survey=survey, variant="small"
        )
        keys = list(a.modules_for_variant().values_list("key", flat=True))
        assert keys == ["all", "small"]

    def test_large_assignment_sees_all_and_large(self, survey, make_company):
        self._build(survey)
        a = SurveyAssignment.objects.create(
            company=make_company(), survey=survey, variant="large"
        )
        keys = list(a.modules_for_variant().values_list("key", flat=True))
        assert keys == ["all", "large"]
