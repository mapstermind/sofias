import re

from apps.surveys.models import ChoiceTemplate, QuestionTemplate

from .prompts import ask, ask_int, choose, confirm

CHOICE_TYPES = {QuestionTemplate.QuestionType.SINGLE_CHOICE, QuestionTemplate.QuestionType.MULTIPLE_CHOICE}


def _slugify(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", text.lower()).strip("_")


# ---------------------------------------------------------------------------
# ChoiceTemplate helpers
# ---------------------------------------------------------------------------

def _print_choice_templates(qt: QuestionTemplate) -> None:
    choices = list(qt.choices.all())
    if not choices:
        print("  (no choices yet)")
    else:
        for c in choices:
            print(f"  [{c.order}] {c.label} → {c.value}")


def _add_choice_template(qt: QuestionTemplate) -> None:
    label = ask("Label")
    value = ask("Value", default=_slugify(label))
    default_order = qt.choices.count()
    order = ask_int("Order", default=default_order, required=False)
    if order is None:
        order = default_order
    ct = ChoiceTemplate.objects.create(question=qt, label=label, value=value, order=order)
    print(f"  Added: {ct}")


def _edit_choice_template(qt: QuestionTemplate) -> None:
    choices = list(qt.choices.all())
    if not choices:
        print("  No choices to edit.")
        return
    options = [(f"{c.label} ({c.value})", c) for c in choices]
    ct = choose("Select choice to edit", options, allow_back=True)
    if ct is None:
        return
    ct.label = ask("Label", default=ct.label)
    ct.value = ask("Value", default=ct.value)
    ct.order = ask_int("Order", default=ct.order) or ct.order
    ct.save()
    print(f"  Updated: {ct}")


def _delete_choice_template(qt: QuestionTemplate) -> None:
    choices = list(qt.choices.all())
    if not choices:
        print("  No choices to delete.")
        return
    options = [(f"{c.label} ({c.value})", c) for c in choices]
    ct = choose("Select choice to delete", options, allow_back=True)
    if ct is None:
        return
    if confirm(f"Delete '{ct.label}'?", default=False):
        ct.delete()
        print("  Deleted.")


def _manage_choice_templates(qt: QuestionTemplate) -> None:
    menu = [
        ("Add choice", "add"),
        ("Edit choice", "edit"),
        ("Delete choice", "delete"),
        ("Done", "done"),
    ]
    while True:
        print(f"\nChoices for template: {qt}")
        _print_choice_templates(qt)
        action = choose("Action", menu)
        if action == "add":
            _add_choice_template(qt)
        elif action == "edit":
            _edit_choice_template(qt)
        elif action == "delete":
            _delete_choice_template(qt)
        elif action == "done":
            break


# ---------------------------------------------------------------------------
# QuestionTemplate helpers
# ---------------------------------------------------------------------------

def _create_question_template() -> None:
    print("\n--- Create Question Template ---")
    qt_options = [(label, value) for value, label in QuestionTemplate.QuestionType.choices]
    question_type = choose("Question type", qt_options)
    text = ask("Question text")

    qt = QuestionTemplate.objects.create(
        question_type=question_type,
        text=text,
    )
    print(f"\n  Created: {qt}")

    if question_type in CHOICE_TYPES:
        if confirm("Add choices now?"):
            _manage_choice_templates(qt)


def _edit_question_template(qt: QuestionTemplate) -> None:
    print(f"\n--- Edit: {qt} ---")
    qt.text = ask("Question text", default=qt.text)
    qt.save()
    print(f"  Updated: {qt}")

    if qt.question_type in CHOICE_TYPES:
        if confirm("Manage choices?"):
            _manage_choice_templates(qt)


def _delete_question_template(qt: QuestionTemplate) -> None:
    if confirm(f"Delete template '{qt}'? This cannot be undone.", default=False):
        qt.delete()
        print("  Deleted.")


def _print_templates(templates: list[QuestionTemplate]) -> None:
    if not templates:
        print("  (no templates yet)")
        return
    for qt in templates:
        choice_count = qt.choices.count() if qt.question_type in CHOICE_TYPES else None
        suffix = f" [{choice_count} choices]" if choice_count is not None else ""
        print(f"  [{qt.pk}] ({qt.question_type}) {qt.text}{suffix}")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def run_manage_question_templates() -> None:
    print("\n=== Question Template Library ===")

    menu = [
        ("Create template", "create"),
        ("Edit template", "edit"),
        ("Delete template", "delete"),
        ("Done", "done"),
    ]

    while True:
        templates = list(QuestionTemplate.objects.all())
        print(f"\nLibrary ({len(templates)} template{'s' if len(templates) != 1 else ''}):")
        _print_templates(templates)

        action = choose("Action", menu)

        if action == "create":
            _create_question_template()

        elif action == "edit":
            if not templates:
                print("  No templates to edit.")
                continue
            options = [(str(qt), qt) for qt in templates]
            qt = choose("Select template", options, allow_back=True)
            if qt is not None:
                _edit_question_template(qt)

        elif action == "delete":
            if not templates:
                print("  No templates to delete.")
                continue
            options = [(str(qt), qt) for qt in templates]
            qt = choose("Select template", options, allow_back=True)
            if qt is not None:
                _delete_question_template(qt)

        elif action == "done":
            break
