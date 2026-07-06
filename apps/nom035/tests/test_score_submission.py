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


def _answer_guia1(sub, codes, *, event, yes_codes=()):
    if event:
        Answer.objects.create(submission=sub, question=codes["g1-1"], value=True)
    for code in yes_codes:
        Answer.objects.create(submission=sub, question=codes[code], value=True)


def test_guia1_positive_via_section_ii(nom035_assignment):
    sub = SurveySubmission.objects.create(
        assignment=nom035_assignment, status=SurveySubmission.Status.COMPLETED
    )
    codes = {
        q.code: q for q in Question.objects.filter(survey=nom035_assignment.survey)
    }
    # Event + one "Sí" in Section II (g1-2) → positive.
    _answer_guia1(sub, codes, event=True, yes_codes=["g1-2"])

    assert score_submission(sub).guia1_positive is True


def test_guia1_not_positive_below_section_thresholds(nom035_assignment):
    sub = SurveySubmission.objects.create(
        assignment=nom035_assignment, status=SurveySubmission.Status.COMPLETED
    )
    codes = {
        q.code: q for q in Question.objects.filter(survey=nom035_assignment.survey)
    }
    # Event, but only 2 "Sí" in Section III (needs 3) and 1 in Section IV (needs 2).
    _answer_guia1(sub, codes, event=True, yes_codes=["g1-4", "g1-5", "g1-11"])

    assert score_submission(sub).guia1_positive is False


def test_guia1_not_positive_without_event(nom035_assignment):
    sub = SurveySubmission.objects.create(
        assignment=nom035_assignment, status=SurveySubmission.Status.COMPLETED
    )
    codes = {
        q.code: q for q in Question.objects.filter(survey=nom035_assignment.survey)
    }
    # Symptoms present but Section I answered "No"/absent → not positive.
    _answer_guia1(sub, codes, event=False, yes_codes=["g1-2", "g1-3"])

    assert score_submission(sub).guia1_positive is False


def test_known_case_mixes_normal_and_inverted_items(nom035_assignment):
    """Hand-computed Guía III case locking inversion + threshold classification.

    g3-1 is a normal item; answering Nunca(5) → 4.
    g3-17, g3-18 are inverted items; answering Siempre(1) → 4 each.
    """
    sub = SurveySubmission.objects.create(
        assignment=nom035_assignment, status=SurveySubmission.Status.IN_PROGRESS
    )
    codes = {
        q.code: q for q in Question.objects.filter(survey=nom035_assignment.survey)
    }
    Answer.objects.create(submission=sub, question=codes["g3-1"], value=5)  # normal→4
    Answer.objects.create(submission=sub, question=codes["g3-17"], value=1)  # inv→4
    Answer.objects.create(submission=sub, question=codes["g3-18"], value=1)  # inv→4

    result = score_submission(sub)
    groups = {(g.level, g.key): g for g in result.groups}

    assert result.final_score == 12
    assert result.final_ndr == c.NDR_NULO
    # Jornada dominio = items 17+18 = 8 → Muy alto (bands 1/2/4/6).
    jornada = groups[(c.LEVEL_DOMINIO, cfg.DOM_JORNADA)]
    assert jornada.score == 8
    assert jornada.ndr == c.NDR_MUY_ALTO
    # Condiciones dominio = item 1 = 4 → Nulo (bands 5/9/11/14).
    condiciones = groups[(c.LEVEL_DOMINIO, cfg.DOM_CONDICIONES)]
    assert condiciones.score == 4
    assert condiciones.ndr == c.NDR_NULO
    # Categoría organización del tiempo = 8 → Medio (bands 5/7/10/13).
    assert groups[(c.LEVEL_CATEGORIA, cfg.CAT_TIEMPO)].ndr == c.NDR_MEDIO


def test_skipped_conditional_block_sums_only_present_items(nom035_assignment):
    """Absent items (e.g. the clientes block g3-65..68) contribute nothing.

    Answering the 11 main 'Carga de trabajo' items (g3-6..g3-16, all inverted)
    at Siempre(1)→4 yields 44, while items 65..68 stay absent.
    """
    sub = SurveySubmission.objects.create(
        assignment=nom035_assignment, status=SurveySubmission.Status.IN_PROGRESS
    )
    codes = {
        q.code: q for q in Question.objects.filter(survey=nom035_assignment.survey)
    }
    for n in range(6, 17):
        Answer.objects.create(submission=sub, question=codes[f"g3-{n}"], value=1)

    result = score_submission(sub)
    groups = {(g.level, g.key): g for g in result.groups}

    carga = groups[(c.LEVEL_DOMINIO, cfg.DOM_CARGA)]
    assert carga.score == 44  # 11 present items × 4; 65..68 absent
    assert carga.ndr == c.NDR_MUY_ALTO
