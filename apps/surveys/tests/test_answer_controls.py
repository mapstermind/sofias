"""Every answer option is a row the whole of which is tappable.

Rendered height comes from padding, line height and the preflight reset
together, so no test here computes 44px — that is checked by a finger at 360px.
What *is* checkable is the structural half of the contract: the input sits
inside a label, so the tap area is the row rather than the 16px control.
"""

from html.parser import HTMLParser

import pytest
from django.template.loader import render_to_string

pytestmark = pytest.mark.django_db

ANSWER_INPUT_TYPES = {"radio", "checkbox"}


class _UnlabelledInputFinder(HTMLParser):
    """Collects the name of every radio/checkbox not nested inside a <label>."""

    def __init__(self):
        super().__init__()
        self.label_depth = 0
        self.unlabelled = []

    def handle_starttag(self, tag, attrs):
        if tag == "label":
            self.label_depth += 1
            return
        if tag != "input":
            return
        attributes = dict(attrs)
        if attributes.get("type") in ANSWER_INPUT_TYPES and self.label_depth == 0:
            self.unlabelled.append(attributes.get("name", "?"))

    def handle_endtag(self, tag):
        if tag == "label" and self.label_depth:
            self.label_depth -= 1


def _render(question, existing_answers=None):
    return render_to_string(
        "surveys/_question.html",
        {
            "question": question,
            "existing_answers": existing_answers or {},
            "errors": {},
        },
    )


def _question_of_type(survey_with_questions, question_type):
    return next(
        q
        for q in survey_with_questions["questions"]
        if q.question_type == question_type
    )


@pytest.mark.parametrize(
    "question_type",
    ["boolean", "single_choice", "multiple_choice", "rating", "likert"],
)
def test_every_option_is_wrapped_in_its_own_label(question_type, survey_with_questions):
    """An input outside a label makes the 16px control the only hit target."""
    question = _question_of_type(survey_with_questions, question_type)

    finder = _UnlabelledInputFinder()
    finder.feed(_render(question))

    assert finder.unlabelled == [], (
        f"{question_type}: inputs rendered outside a <label>, so only the "
        f"control itself is tappable: {finder.unlabelled}"
    )


def test_likert_renders_one_row_per_label(survey_with_questions):
    """Five options, five rows, labels intact — the scale reads as a list."""
    question = _question_of_type(survey_with_questions, "likert")
    # Set in memory, not saved: the template renders the object it is handed,
    # and `likert_pairs` reads `question.config` straight off it.
    question.config = {
        "labels": ["Siempre", "Casi siempre", "Algunas veces", "Casi nunca", "Nunca"]
    }

    html = _render(question)

    for label in question.config["labels"]:
        assert label in html, f"likert lost its {label!r} option label"
    assert html.count('type="radio"') == 5


def test_likert_options_carry_no_unprefixed_minimum_width(survey_with_questions):
    """A minimum width defeats shrinking; five of them overflow a phone.

    The horizontal scale survives behind `lg:`, where there is room for it.
    """
    question = _question_of_type(survey_with_questions, "likert")

    html = _render(question)

    assert "min-w-[72px]" not in html.replace("lg:min-w-[72px]", "")
