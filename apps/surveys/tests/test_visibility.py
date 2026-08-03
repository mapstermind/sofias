import pytest

from apps.surveys.models import Module, Question, SurveyAssignment
from apps.surveys.visibility import (
    is_visible,
    progress_for_modules,
    visible_questions,
)

pytestmark = pytest.mark.django_db


class TestIsVisible:
    def test_empty_rule_is_visible(self):
        assert is_visible(None, {}) is True
        assert is_visible({}, {}) is True

    def test_single_answer_gate(self):
        rule = {"question": "g-clientes", "equals": True}
        assert is_visible(rule, {"g-clientes": True}) is True
        assert is_visible(rule, {"g-clientes": False}) is False
        assert is_visible(rule, {}) is False

    def test_string_boolean_coercion(self):
        rule = {"question": "g", "equals": "si"}
        assert is_visible(rule, {"g": True}) is True
        assert is_visible(rule, {"g": "Sí"}) is True
        assert is_visible(rule, {"g": False}) is False

    def test_any_in_module_aggregate(self):
        rule = {"any_in_module": "trigger", "equals": True}
        mtc = {"trigger": ["a", "b"]}
        assert is_visible(rule, {"a": False, "b": True}, mtc) is True
        assert is_visible(rule, {"a": False, "b": False}, mtc) is False
        assert is_visible(rule, {}, mtc) is False


@pytest.fixture
def branching_survey(survey, make_company):
    """Trigger module + follow-up gated by any_in_module; plus a single-gate q."""
    trigger = Module.objects.create(
        survey=survey, key="trigger", title="T", applies_to="all", order=0
    )
    Question.objects.create(
        module=trigger, code="t1", question_type="boolean", text="Trigger?"
    )
    followup = Module.objects.create(
        survey=survey,
        key="followup",
        title="F",
        applies_to="all",
        order=1,
        visible_when={"any_in_module": "trigger", "equals": True},
    )
    Question.objects.create(
        module=followup, code="f1", question_type="boolean", text="Follow?"
    )
    gatemod = Module.objects.create(
        survey=survey, key="gate", title="G", applies_to="all", order=2
    )
    Question.objects.create(
        module=gatemod, code="gate-q", question_type="boolean", text="Gate?"
    )
    Question.objects.create(
        module=gatemod,
        code="gated",
        question_type="text",
        text="Gated",
        visible_when={"question": "gate-q", "equals": True},
    )
    assignment = SurveyAssignment.objects.create(
        company=make_company(), survey=survey, variant="small"
    )
    return assignment


class TestVisibleQuestions:
    def test_followup_hidden_until_trigger_yes(self, branching_survey):
        a = branching_survey
        # Trigger No -> followup module hidden, gated text hidden.
        codes = {q.code for q in visible_questions(a, {"t1": False, "gate-q": False})}
        assert "t1" in codes
        assert "f1" not in codes
        assert "gate-q" in codes
        assert "gated" not in codes

    def test_followup_and_gate_shown_when_yes(self, branching_survey):
        a = branching_survey
        codes = {q.code for q in visible_questions(a, {"t1": True, "gate-q": True})}
        assert {"t1", "f1", "gate-q", "gated"} <= codes


class TestProgressForModules:
    def _modules(self, assignment):
        return list(assignment.modules_for_variant().prefetch_related("questions"))

    def _by_code(self, assignment):
        return {
            q.code: q.id for m in self._modules(assignment) for q in m.questions.all()
        }

    def test_no_modules(self):
        assert progress_for_modules([], {}) == (0, 0)

    def test_nothing_answered_counts_only_ungated_questions(self, branching_survey):
        # 4 questions authored; f1 and `gated` need a "yes" that has not happened.
        assert progress_for_modules(self._modules(branching_survey), {}) == (0, 2)

    def test_gated_out_survey_reaches_total(self, branching_survey):
        codes = self._by_code(branching_survey)
        answers = {codes["t1"]: False, codes["gate-q"]: False}
        answered, total = progress_for_modules(self._modules(branching_survey), answers)
        assert (answered, total) == (2, 2)

    def test_gated_in_survey_counts_the_revealed_questions(self, branching_survey):
        codes = self._by_code(branching_survey)
        answers = {
            codes["t1"]: True,
            codes["gate-q"]: True,
            codes["f1"]: True,
            codes["gated"]: "x",
        }
        assert progress_for_modules(self._modules(branching_survey), answers) == (4, 4)

    def test_stale_answers_behind_a_flipped_gate_are_ignored(self, branching_survey):
        # Answered the follow-ups, then flipped both gates back to No.
        codes = self._by_code(branching_survey)
        answers = {
            codes["t1"]: False,
            codes["gate-q"]: False,
            codes["f1"]: True,
            codes["gated"]: "x",
        }
        answered, total = progress_for_modules(self._modules(branching_survey), answers)
        assert (answered, total) == (2, 2)  # never exceeds total

    def test_blank_values_do_not_count_as_answered(self, branching_survey):
        codes = self._by_code(branching_survey)
        answers = {codes["t1"]: False, codes["gate-q"]: ""}
        assert progress_for_modules(self._modules(branching_survey), answers) == (1, 2)
