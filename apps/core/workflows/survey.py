from apps.surveys.models import SurveyTemplate

from .introspect import prompt_for_model
from .prompts import confirm
from .version_helpers import get_or_create_latest_version


def run_create_survey() -> None:
    print("\n=== Create Survey Template ===")
    data = prompt_for_model(SurveyTemplate, exclude=["status"])
    survey = SurveyTemplate.objects.create(**data, status=SurveyTemplate.Status.DRAFT)
    version = get_or_create_latest_version(survey)
    print(f"\nCreated: {survey} (version {version.version_number})")

    if confirm("Add questions now?"):
        from .question import run_create_question
        run_create_question(survey=survey)
