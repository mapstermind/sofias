"""How the employee detail page shows one answer: see docs/platform/design-system.md.

A frequency (likert) answer is its label plus the scale's options as squircles,
the chosen one filled. The stored value is the option's position, not a score
(NOM-035 reverses scoring on some items), so it is never printed.
"""

import re
from types import SimpleNamespace

from django.template import Context, Template

NOM035_LABELS = ["Siempre", "Casi siempre", "Algunas veces", "Casi nunca", "Nunca"]


def _qa(question_type, value, labels=NOM035_LABELS, score=None):
    question = SimpleNamespace(
        text="Mi trabajo me exige hacer mucho esfuerzo físico",
        question_type=question_type,
        config={"labels": labels},
    )
    return SimpleNamespace(
        question=question, answer=SimpleNamespace(value=value), score=score
    )


def _row(qa):
    return Template('{% include "core/_answer_row.html" %}').render(Context({"qa": qa}))


def test_a_frequency_answer_names_its_label_and_position_for_screen_readers():
    html = _row(_qa("likert", 2))
    assert 'role="img"' in html
    assert 'aria-label="Casi siempre, opción 2 de 5, de Siempre a Nunca"' in html


def test_a_frequency_answer_fills_only_the_chosen_option():
    html = _row(_qa("likert", 2))
    assert html.count('data-step="on"') == 1
    assert html.count('data-step="off"') == 4


def test_a_frequency_answer_never_prints_its_stored_position():
    html = _row(_qa("likert", 2))
    assert "(2)" not in html


def test_the_scale_follows_the_questions_own_labels():
    html = _row(_qa("likert", 1, labels=["Nunca", "A veces", "Siempre"]))
    assert 'aria-label="Nunca, opción 1 de 3, de Nunca a Siempre"' in html
    assert html.count("data-step=") == 3


def test_yes_and_no_share_the_choice_pill():
    yes, no = _row(_qa("boolean", True)), _row(_qa("boolean", False))
    assert "bg-primary-50" in yes and "bg-primary-50" in no


def test_the_module_key_reads_the_first_frequency_questions_scale():
    from apps.surveys.templatetags.survey_extras import first_of_type

    items = [_qa("boolean", True), _qa("likert", 3), _qa("likert", 4)]
    assert first_of_type(items, "likert") is items[1]
    assert first_of_type(items[:1], "likert") is None


def test_the_module_key_reads_rows_built_as_dicts():
    """The employee detail view builds each answer row as a dict, not an object."""
    from apps.surveys.templatetags.survey_extras import first_of_type

    boolean, likert = _qa("boolean", True), _qa("likert", 3)
    items = [vars(boolean), vars(likert)]
    assert first_of_type(items, "likert") is items[1]


def _steps(html):
    return re.findall(r'data-step="(on|off)"', html)


def test_a_scored_answer_sits_at_its_score_not_its_position():
    """Siempre on a reversed item scores 4: the last square, though it is the first label."""
    html = _row(_qa("likert", 1, score=4))
    assert _steps(html) == ["off", "off", "off", "off", "on"]
    assert 'aria-label="Siempre, puntaje 4 de 4"' in html


def test_the_same_answer_on_a_normal_item_sits_at_the_start():
    html = _row(_qa("likert", 1, score=0))
    assert _steps(html) == ["on", "off", "off", "off", "off"]
    assert 'aria-label="Siempre, puntaje 0 de 4"' in html


def test_an_unscored_answer_keeps_the_answer_order():
    """A frequency question with no scoring engine behind it."""
    html = _row(_qa("likert", 2))
    assert _steps(html) == ["off", "on", "off", "off", "off"]
