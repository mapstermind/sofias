import pytest
from django.core.management import call_command

from apps.nom035 import _nom035_scoring as cfg
from apps.nom035 import constants as c
from apps.nom035.scoring import score_submission
from apps.responses.models import Answer, SurveySubmission
from apps.surveys.models import Question, Survey, SurveyAssignment

pytestmark = pytest.mark.django_db


@pytest.fixture
def nom035_assignment(make_company):
    call_command("seed_nom035_survey")
    survey = Survey.objects.get(key="nom035")
    return SurveyAssignment.objects.create(
        company=make_company(),
        survey=survey,
        variant=SurveyAssignment.Variant.LARGE,
        status=SurveyAssignment.Status.ACTIVE,
    )


def test_all_nunca_yields_expected_final_and_two_levels(nom035_assignment):
    sub = SurveySubmission.objects.create(
        assignment=nom035_assignment, status=SurveySubmission.Status.COMPLETED
    )
    taxonomy = cfg.taxonomy_for_variant("large")
    codes = {
        q.code: q for q in Question.objects.filter(survey=nom035_assignment.survey)
    }
    for code in taxonomy:
        Answer.objects.create(submission=sub, question=codes[code], value=5)  # Nunca

    result = score_submission(sub)

    # Nunca → normal item 4, inverted item 0.
    expected_final = sum(0 if cfg.is_inverted(code) else 4 for code in taxonomy)
    assert result.final_score == expected_final
    # Dimensión is not scored — only categoría and dominio groups exist.
    assert {g.level for g in result.groups} == {c.LEVEL_CATEGORIA, c.LEVEL_DOMINIO}


def test_guia1_flag_and_severity(nom035_assignment):
    sub = SurveySubmission.objects.create(
        assignment=nom035_assignment, status=SurveySubmission.Status.COMPLETED
    )
    codes = {
        q.code: q for q in Question.objects.filter(survey=nom035_assignment.survey)
    }
    Answer.objects.create(submission=sub, question=codes["g1-1"], value=True)
    for code in cfg.GUIA1_FOLLOWUP_CODES[:3]:
        Answer.objects.create(submission=sub, question=codes[code], value=True)

    result = score_submission(sub)
    assert result.guia1_event is True
    assert result.guia1_followup_count == 3
    assert result.guia1_severity == c.SEV_MED
