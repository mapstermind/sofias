import re

from apps.surveys.models import Choice, Question, Survey

from .prompts import ask, ask_int, choose, confirm
from .version_helpers import get_or_create_latest_version

CHOICE_TYPES = {Question.QuestionType.SINGLE_CHOICE, Question.QuestionType.MULTIPLE_CHOICE}


def _slugify(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", text.lower()).strip("_")


def _resolve_question(question=None):
    if question is not None:
        return question

    surveys = list(Survey.objects.all())
    if not surveys:
        print("No surveys found.")
        return None

    survey_options = [(str(s), s) for s in surveys]
    survey = choose("Select survey", survey_options)
    version = get_or_create_latest_version(survey)

    qs = list(version.questions.filter(question_type__in=list(CHOICE_TYPES)))
    if not qs:
        print("No choice-type questions found for this survey version.")
        return None

    q_options = [(str(q), q) for q in qs]
    return choose("Select question", q_options)


def _print_choices(question) -> None:
    choices = list(question.choices.all())
    if not choices:
        print("  (no choices yet)")
    else:
        for c in choices:
            print(f"  [{c.order}] {c.label} → {c.value}")


def _add_choice(question) -> None:
    label = ask("Label")
    value = ask("Value", default=_slugify(label))
    default_order = question.choices.count()
    order = ask_int("Order", default=default_order, required=False)
    if order is None:
        order = default_order
    c = Choice.objects.create(question=question, label=label, value=value, order=order)
    print(f"  Added: {c}")


def _edit_choice(question) -> None:
    choices = list(question.choices.all())
    if not choices:
        print("  No choices to edit.")
        return
    options = [(f"{c.label} ({c.value})", c) for c in choices]
    choice = choose("Select choice to edit", options, allow_back=True)
    if choice is None:
        return
    choice.label = ask("Label", default=choice.label)
    choice.value = ask("Value", default=choice.value)
    choice.order = ask_int("Order", default=choice.order) or choice.order
    choice.save()
    print(f"  Updated: {choice}")


def _delete_choice(question) -> None:
    choices = list(question.choices.all())
    if not choices:
        print("  No choices to delete.")
        return
    options = [(f"{c.label} ({c.value})", c) for c in choices]
    choice = choose("Select choice to delete", options, allow_back=True)
    if choice is None:
        return
    if confirm(f"Delete '{choice.label}'?", default=False):
        choice.delete()
        print("  Deleted.")


def run_manage_choices(question=None) -> None:
    print("\n=== Manage Choices ===")
    question = _resolve_question(question)
    if question is None:
        return

    menu = [
        ("Add choice", "add"),
        ("Edit choice", "edit"),
        ("Delete choice", "delete"),
        ("Done", "done"),
    ]

    while True:
        print(f"\nChoices for: {question}")
        _print_choices(question)
        action = choose("Action", menu)
        if action == "add":
            _add_choice(question)
        elif action == "edit":
            _edit_choice(question)
        elif action == "delete":
            _delete_choice(question)
        elif action == "done":
            break
