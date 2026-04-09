from apps.surveys.models import Survey

from .introspect import prompt_for_model
from .prompts import confirm
from .version_helpers import get_or_create_latest_version


def run_create_survey() -> None:
    print("\n=== Create Survey ===")
    data = prompt_for_model(Survey, exclude=["status"])
    survey = Survey.objects.create(**data, status=Survey.Status.DRAFT)
    version = get_or_create_latest_version(survey)
    print(f"\nCreated: {survey} (version {version.version_number})")

    if confirm("Add questions now?"):
        from .question import run_create_question
        run_create_question(survey=survey)
