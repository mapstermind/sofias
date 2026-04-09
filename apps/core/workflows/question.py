from apps.surveys.models import Question, Section, Survey

from .introspect import prompt_for_model
from .prompts import ask_int, choose, choose_or_create, confirm
from .version_helpers import get_or_create_latest_version

CHOICE_TYPES = {Question.QuestionType.SINGLE_CHOICE, Question.QuestionType.MULTIPLE_CHOICE}


def _resolve_survey(survey=None):
    if survey is not None:
        return survey
    surveys = list(Survey.objects.all())
    if not surveys:
        print("No surveys found. Create one first.")
        return None
    options = [(str(s), s) for s in surveys]
    return choose("Select survey", options)


def _resolve_section(version):
    sections = list(version.sections.all())
    options = [(str(s), s) for s in sections]
    result = choose_or_create(
        "Assign to section",
        options,
        create_label="Create new section",
        allow_none=True,
        none_label="No section",
    )
    if result == "__create__":
        from .sections import _create_section
        return _create_section(version)
    return result


def run_create_question(survey=None) -> None:
    print("\n=== Create Question ===")
    survey = _resolve_survey(survey)
    if survey is None:
        return

    while True:
        version = get_or_create_latest_version(survey)
        section = _resolve_section(version)

        qt_options = [(label, value) for value, label in Question.QuestionType.choices]
        question_type = choose("Question type", qt_options)

        data = prompt_for_model(Question, exclude=["version", "section", "question_type", "config", "order"])
        default_order = version.questions.count()
        order = ask_int("Order", default=default_order, required=False)
        if order is None:
            order = default_order

        question = Question.objects.create(
            version=version,
            section=section,
            question_type=question_type,
            order=order,
            **data,
        )
        print(f"\nCreated question: {question}")

        if question_type in CHOICE_TYPES:
            if confirm("Manage choices now?"):
                from .choices import run_manage_choices
                run_manage_choices(question=question)

        if not confirm("Create another?", default=False):
            break
