from apps.surveys.models import Section, SurveyTemplate

from .introspect import prompt_for_model
from .prompts import ask_int, choose
from .version_helpers import get_or_create_latest_version


def _resolve_survey(survey=None):
    if survey is not None:
        return survey
    surveys = list(SurveyTemplate.objects.all())
    if not surveys:
        print("No survey templates found. Create one first.")
        return None
    options = [(str(s), s) for s in surveys]
    return choose("Select survey template", options)


def _create_section(version) -> Section:
    print("\n--- Create Section ---")
    data = prompt_for_model(Section, exclude=["version", "order"])
    default_order = version.sections.count()
    order = ask_int("Order", default=default_order, required=False)
    if order is None:
        order = default_order
    section = Section.objects.create(version=version, order=order, **data)
    print(f"  Created section: {section}")
    return section


def _add_question_to_section(version) -> None:
    sections = list(version.sections.all())
    if not sections:
        print("  No sections yet. Create one first.")
        return
    unsectioned = list(version.questions.filter(section__isnull=True))
    if not unsectioned:
        print("  No unsectioned questions available.")
        return
    s_options = [(str(s), s) for s in sections]
    section = choose("Select section", s_options, allow_back=True)
    if section is None:
        return
    q_options = [(str(q), q) for q in unsectioned]
    question = choose("Select question to add", q_options, allow_back=True)
    if question is None:
        return
    question.section = section
    question.save()
    print(f"  Moved '{question}' → '{section}'")


def _move_question(version) -> None:
    sections = list(version.sections.all())
    if not sections:
        print("  No sections exist.")
        return
    questions_with_section = list(version.questions.filter(section__isnull=False))
    if not questions_with_section:
        print("  No sectioned questions to move.")
        return

    s_options = [(str(s), s) for s in sections]
    from_section = choose("Move from section", s_options, allow_back=True)
    if from_section is None:
        return

    qs = list(from_section.questions.all())
    if not qs:
        print("  No questions in that section.")
        return

    q_options = [(str(q), q) for q in qs]
    question = choose("Select question", q_options, allow_back=True)
    if question is None:
        return

    dest_options = [(str(s), s) for s in sections if s != from_section]
    dest_options.append(("No section", None))
    dest = choose("Move to", dest_options)
    question.section = dest
    question.save()
    dest_name = str(dest) if dest else "no section"
    print(f"  Moved '{question}' → {dest_name}")


def _list_questions(version) -> None:
    sections = list(version.sections.all())
    if not sections:
        print("  No sections.")
        return
    s_options = [(str(s), s) for s in sections]
    section = choose("Select section to list", s_options, allow_back=True)
    if section is None:
        return
    qs = list(section.questions.order_by("order"))
    if not qs:
        print("  (no questions in this section)")
    for q in qs:
        print(f"  [{q.order}] {q}")


def run_manage_sections(survey=None) -> None:
    print("\n=== Manage Sections ===")
    survey = _resolve_survey(survey)
    if survey is None:
        return

    version = get_or_create_latest_version(survey)

    menu = [
        ("Create section", "create"),
        ("Add question to section", "add_q"),
        ("Move question", "move"),
        ("List questions in section", "list"),
        ("Done", "done"),
    ]

    while True:
        print(f"\nSurvey: {survey} (version {version.version_number})")
        sections = list(version.sections.all())
        if sections:
            print("Sections: " + ", ".join(str(s) for s in sections))
        else:
            print("Sections: (none)")
        action = choose("Action", menu)
        if action == "create":
            _create_section(version)
        elif action == "add_q":
            _add_question_to_section(version)
        elif action == "move":
            _move_question(version)
        elif action == "list":
            _list_questions(version)
        elif action == "done":
            break
