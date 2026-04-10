from apps.surveys.models import SurveyVersion


def get_or_create_latest_version(survey) -> SurveyVersion:
    latest = survey.versions.order_by("-version_number").first()
    if latest is None:
        return SurveyVersion.objects.create(template=survey, version_number=1)
    return latest
