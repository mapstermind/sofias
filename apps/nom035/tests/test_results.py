from datetime import date, datetime

import pytest
from django.utils import timezone

from apps.nom035 import constants as c
from apps.nom035.models import GroupScore, SubmissionScore
from apps.nom035.results import (
    assignment_label,
    assignment_options,
    select_assignment,
)
from apps.responses.models import SurveySubmission
from apps.surveys.models import Survey, SurveyAssignment

pytestmark = pytest.mark.django_db


@pytest.fixture
def nom035_survey(db):
    return Survey.objects.create(
        key="nom035", title="NOM-035", status=Survey.Status.PUBLISHED
    )


def make_assignment(company, survey, variant="large"):
    return SurveyAssignment.objects.create(
        company=company,
        survey=survey,
        variant=variant,
        status=SurveyAssignment.Status.ACTIVE,
    )


def make_score(
    assignment,
    user=None,
    *,
    final_score=10,
    final_ndr=c.NDR_BAJO,
    groups=(),
    guia1_event=False,
    guia1_positive=False,
    completed_at=None,
):
    """A scored submission without running the engine.

    Created IN_PROGRESS so the completion signal does not overwrite the
    explicit score; `completed_at` is set directly for label tests.
    `groups` is an iterable of (level, key, score, ndr).
    """
    sub = SurveySubmission.objects.create(
        assignment=assignment,
        user=user,
        status=SurveySubmission.Status.IN_PROGRESS,
        completed_at=completed_at,
    )
    score = SubmissionScore.objects.create(
        submission=sub,
        final_score=final_score,
        final_ndr=final_ndr,
        guia1_event=guia1_event,
        guia1_positive=guia1_positive,
    )
    GroupScore.objects.bulk_create(
        GroupScore(submission_score=score, level=level, key=key, score=value, ndr=ndr)
        for level, key, value, ndr in groups
    )
    return score


def test_assignment_label_forms():
    created = date(2026, 1, 12)
    assert (
        assignment_label("Guía III", None, None, created)
        == "Guía III · creada 12 ene 2026 · sin respuestas"
    )
    assert (
        assignment_label("Guía III", date(2026, 1, 12), date(2026, 2, 28), created)
        == "Guía III · aplicada 12 ene – 28 feb 2026"
    )
    assert (
        assignment_label("Guía II", date(2025, 12, 1), date(2026, 1, 5), created)
        == "Guía II · aplicada 1 dic 2025 – 5 ene 2026"
    )
    assert (
        assignment_label("Guía II", date(2026, 3, 4), date(2026, 3, 4), created)
        == "Guía II · aplicada 4 mar 2026"
    )


def test_assignment_options_only_nom035_newest_first(
    make_company, survey, nom035_survey
):
    company = make_company()
    make_assignment(company, survey)  # another instrument — excluded
    older = make_assignment(company, nom035_survey)
    newer = make_assignment(company, nom035_survey, variant="small")
    tz = timezone.get_current_timezone()
    make_score(older, completed_at=datetime(2026, 1, 12, 18, tzinfo=tz))
    make_score(older, completed_at=datetime(2026, 2, 28, 9, tzinfo=tz))

    options = assignment_options(company)

    assert [o.assignment for o in options] == [newer, older]
    assert options[1].label == "Guía III · aplicada 12 ene – 28 feb 2026"
    assert options[1].scored_count == 2
    assert options[0].scored_count == 0
    assert options[0].label.endswith("sin respuestas")


def test_select_assignment_prefers_request_then_latest_scored(
    make_company, nom035_survey
):
    company = make_company()
    scored = make_assignment(company, nom035_survey)
    make_score(scored)
    make_assignment(company, nom035_survey)  # newest, unscored
    options = assignment_options(company)

    assert select_assignment(options, None).assignment == scored
    assert select_assignment(options, options[0].assignment.pk) == options[0]
    assert select_assignment([], None) is None
