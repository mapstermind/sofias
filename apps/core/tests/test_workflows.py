"""
Tests for the interactive workflow layer (apps/core/workflows/).

Strategy:
  - Import tests: verify all modules load without ImportError. These catch the
    class of bug where a model is renamed and the workflow still references the
    old name. They run at collection time, before any DB access.
  - Functional tests: patch the prompt functions so the workflows run
    non-interactively, then assert the correct DB records were created/modified.
    All I/O goes through apps.core.workflows.prompts, so patching at the
    workflow-module level (e.g. apps.core.workflows.survey.confirm) is enough.
"""

import pytest
from unittest.mock import patch

pytestmark = pytest.mark.django_db


# ── Import smoke tests ────────────────────────────────────────────────────────
# These fail instantly with ImportError if a workflow references a model that
# no longer exists. No DB access needed; the marker is harmless here.


class TestWorkflowImports:
    def test_survey_workflow_imports(self):
        from apps.core.workflows import survey  # noqa: F401

    def test_question_workflow_imports(self):
        from apps.core.workflows import question  # noqa: F401

    def test_choices_workflow_imports(self):
        from apps.core.workflows import choices  # noqa: F401

    def test_sections_workflow_imports(self):
        from apps.core.workflows import sections  # noqa: F401

    def test_introspect_imports(self):
        from apps.core.workflows import introspect  # noqa: F401

    def test_version_helpers_imports(self):
        from apps.core.workflows import version_helpers  # noqa: F401


# ── run_create_survey ─────────────────────────────────────────────────────────


class TestRunCreateSurvey:
    def test_creates_survey_template_and_version(self):
        from apps.core.workflows.survey import run_create_survey
        from apps.surveys.models import SurveyTemplate, SurveyVersion

        with patch("apps.core.workflows.survey.prompt_for_model", return_value={"title": "Q3 Survey", "description": ""}), \
             patch("apps.core.workflows.survey.confirm", return_value=False):
            run_create_survey()

        assert SurveyTemplate.objects.filter(title="Q3 Survey").exists()
        assert SurveyVersion.objects.filter(template__title="Q3 Survey", version_number=1).exists()

    def test_new_survey_status_is_always_draft(self):
        from apps.core.workflows.survey import run_create_survey
        from apps.surveys.models import SurveyTemplate

        with patch("apps.core.workflows.survey.prompt_for_model", return_value={"title": "Draft Check", "description": ""}), \
             patch("apps.core.workflows.survey.confirm", return_value=False):
            run_create_survey()

        survey = SurveyTemplate.objects.get(title="Draft Check")
        assert survey.status == SurveyTemplate.Status.DRAFT

    def test_answering_yes_chains_into_create_question(self):
        """confirm=True triggers run_create_question; we patch that to avoid
        running the full question flow and just verify it was called."""
        from apps.core.workflows.survey import run_create_survey

        with patch("apps.core.workflows.survey.prompt_for_model", return_value={"title": "Chained", "description": ""}), \
             patch("apps.core.workflows.survey.confirm", return_value=True), \
             patch("apps.core.workflows.question.run_create_question") as mock_create_q:
            run_create_survey()

        mock_create_q.assert_called_once()


# ── run_create_question ───────────────────────────────────────────────────────


class TestRunCreateQuestion:
    def test_creates_non_choice_question(self, survey_version):
        from apps.core.workflows.question import run_create_question
        from apps.surveys.models import Question

        survey = survey_version.template

        with patch("apps.core.workflows.question.choose_or_create", return_value=None), \
             patch("apps.core.workflows.question.choose", return_value="short_text"), \
             patch("apps.core.workflows.question.prompt_for_model", return_value={"text": "How are you?", "required": True}), \
             patch("apps.core.workflows.question.ask_int", return_value=0), \
             patch("apps.core.workflows.question.confirm", return_value=False):
            run_create_question(survey=survey)

        q = Question.objects.get(text="How are you?", version=survey_version)
        assert q.question_type == "short_text"
        assert q.section is None

    def test_creates_choice_question_and_offers_manage_choices(self, survey_version):
        from apps.core.workflows.question import run_create_question
        from apps.surveys.models import Question

        survey = survey_version.template

        # confirm is called twice: "Manage choices now?" then "Create another?"
        with patch("apps.core.workflows.question.choose_or_create", return_value=None), \
             patch("apps.core.workflows.question.choose", return_value="single_choice"), \
             patch("apps.core.workflows.question.prompt_for_model", return_value={"text": "Pick one", "required": True}), \
             patch("apps.core.workflows.question.ask_int", return_value=0), \
             patch("apps.core.workflows.question.confirm", side_effect=[False, False]), \
             patch("apps.core.workflows.choices.run_manage_choices") as mock_choices:
            run_create_question(survey=survey)

        assert Question.objects.filter(text="Pick one", question_type="single_choice").exists()
        # manage_choices was NOT called because confirm("Manage choices now?") returned False
        mock_choices.assert_not_called()

    def test_question_is_assigned_to_section(self, survey_version):
        from apps.core.workflows.question import run_create_question
        from apps.surveys.models import Question, Section

        survey = survey_version.template
        section = Section.objects.create(version=survey_version, title="Intro", order=0)

        with patch("apps.core.workflows.question.choose_or_create", return_value=section), \
             patch("apps.core.workflows.question.choose", return_value="short_text"), \
             patch("apps.core.workflows.question.prompt_for_model", return_value={"text": "Sectioned Q", "required": True}), \
             patch("apps.core.workflows.question.ask_int", return_value=0), \
             patch("apps.core.workflows.question.confirm", return_value=False):
            run_create_question(survey=survey)

        q = Question.objects.get(text="Sectioned Q")
        assert q.section == section


# ── run_manage_choices ────────────────────────────────────────────────────────


class TestRunManageChoices:
    @pytest.fixture
    def choice_question(self, survey_version):
        from apps.surveys.models import Question
        return Question.objects.create(
            version=survey_version,
            question_type="single_choice",
            text="Favourite colour?",
            required=True,
            order=0,
        )

    def test_add_choice(self, choice_question):
        from apps.core.workflows.choices import run_manage_choices
        from apps.surveys.models import Choice

        # choose: first call picks "add" from the action menu, second picks "done"
        with patch("apps.core.workflows.choices.choose", side_effect=["add", "done"]), \
             patch("apps.core.workflows.choices.ask", side_effect=["Red", "red"]), \
             patch("apps.core.workflows.choices.ask_int", return_value=0):
            run_manage_choices(question=choice_question)

        assert Choice.objects.filter(question=choice_question, label="Red", value="red").exists()

    def test_edit_choice(self, choice_question):
        from apps.core.workflows.choices import run_manage_choices
        from apps.surveys.models import Choice

        choice = Choice.objects.create(question=choice_question, label="Blue", value="blue", order=0)

        # choose: "edit" → pick the choice → "done"
        with patch("apps.core.workflows.choices.choose", side_effect=["edit", choice, "done"]), \
             patch("apps.core.workflows.choices.ask", side_effect=["Blue Updated", "blue_updated"]), \
             patch("apps.core.workflows.choices.ask_int", return_value=0):
            run_manage_choices(question=choice_question)

        choice.refresh_from_db()
        assert choice.label == "Blue Updated"
        assert choice.value == "blue_updated"

    def test_delete_choice(self, choice_question):
        from apps.core.workflows.choices import run_manage_choices
        from apps.surveys.models import Choice

        choice = Choice.objects.create(question=choice_question, label="Green", value="green", order=0)

        # choose: "delete" → pick the choice → "done"
        with patch("apps.core.workflows.choices.choose", side_effect=["delete", choice, "done"]), \
             patch("apps.core.workflows.choices.confirm", return_value=True):
            run_manage_choices(question=choice_question)

        assert not Choice.objects.filter(pk=choice.pk).exists()

    def test_resolves_survey_template_from_db(self, survey_version, choice_question):
        """Exercises the SurveyTemplate.objects.all() path in _resolve_question."""
        from apps.core.workflows.choices import run_manage_choices

        survey = survey_version.template

        # choose: survey → question → action "done"
        with patch("apps.core.workflows.choices.choose", side_effect=[survey, choice_question, "done"]):
            run_manage_choices()  # no pre-selected question


# ── run_manage_sections ───────────────────────────────────────────────────────


class TestRunManageSections:
    def test_create_section(self, survey_version):
        from apps.core.workflows.sections import run_manage_sections
        from apps.surveys.models import Section

        survey = survey_version.template

        # choose: "create" in main loop → "done"
        with patch("apps.core.workflows.sections.choose", side_effect=["create", "done"]), \
             patch("apps.core.workflows.sections.prompt_for_model", return_value={"title": "Demographics", "description": ""}), \
             patch("apps.core.workflows.sections.ask_int", return_value=0):
            run_manage_sections(survey=survey)

        assert Section.objects.filter(version=survey_version, title="Demographics").exists()

    def test_add_question_to_section(self, survey_version):
        from apps.core.workflows.sections import run_manage_sections
        from apps.surveys.models import Question, Section

        survey = survey_version.template
        section = Section.objects.create(version=survey_version, title="Part A", order=0)
        question = Question.objects.create(
            version=survey_version, question_type="short_text", text="Name?", required=True, order=0
        )

        # choose: "add_q" → pick section → pick question → "done"
        with patch("apps.core.workflows.sections.choose", side_effect=["add_q", section, question, "done"]):
            run_manage_sections(survey=survey)

        question.refresh_from_db()
        assert question.section == section

    def test_move_question_between_sections(self, survey_version):
        from apps.core.workflows.sections import run_manage_sections
        from apps.surveys.models import Question, Section

        survey = survey_version.template
        sec_a = Section.objects.create(version=survey_version, title="A", order=0)
        sec_b = Section.objects.create(version=survey_version, title="B", order=1)
        question = Question.objects.create(
            version=survey_version, section=sec_a,
            question_type="short_text", text="Move me", required=True, order=0,
        )

        # choose: "move" → source section (A) → question → destination (B) → "done"
        with patch("apps.core.workflows.sections.choose", side_effect=["move", sec_a, question, sec_b, "done"]):
            run_manage_sections(survey=survey)

        question.refresh_from_db()
        assert question.section == sec_b

    def test_resolves_survey_template_from_db(self, survey_version):
        """Exercises the SurveyTemplate.objects.all() path in _resolve_survey."""
        from apps.core.workflows.sections import run_manage_sections

        survey = survey_version.template

        # choose: survey selection → "done" in main loop
        with patch("apps.core.workflows.sections.choose", side_effect=[survey, "done"]):
            run_manage_sections()  # no pre-selected survey
