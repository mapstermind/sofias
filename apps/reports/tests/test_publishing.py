import pytest

from apps.nom035.models import SubmissionScore
from apps.reports import publishing
from apps.reports.models import Report
from apps.surveys.models import SurveyAssignment

pytestmark = pytest.mark.django_db

READY = dict(
    issued_in="CDMX",
    activities_summary="Compras",
    evaluator_name="Sofía",
    evaluator_license="123",
    conclusions="Ok",
)


def test_blockers_list_every_unmet_condition(scored_assignment):
    scored_assignment.status = SurveyAssignment.Status.ACTIVE
    scored_assignment.save()
    report = Report.objects.create(assignment=scored_assignment)
    messages = publishing.blockers(report)
    assert (
        "La encuesta sigue activa; ciérrala antes de publicar el reporte." in messages
    )
    assert any("Lugar de emisión" in m for m in messages)
    assert any("Conclusiones" in m for m in messages)


def test_no_scores_blocks(company, nom035_survey):
    from apps.nom035.tests.factories import make_assignment

    a = make_assignment(company, nom035_survey)
    a.status = SurveyAssignment.Status.CLOSED
    a.save()
    report = Report.objects.create(assignment=a, **READY)
    assert publishing.blockers(report) == [
        "La encuesta no tiene cuestionarios valorados."
    ]


def test_publish_stores_snapshot(scored_assignment, make_user):
    report = Report.objects.create(assignment=scored_assignment, **READY)
    assert publishing.publish(report, make_user(email="a@x.mx")) == []
    report.refresh_from_db()
    assert report.status == Report.Status.PUBLISHED
    assert report.snapshot["responded"] == 12
    assert report.published_by.email == "a@x.mx"


def test_published_report_ignores_later_scores(scored_assignment, make_user):
    from apps.reports.snapshot import data_for

    report = Report.objects.create(assignment=scored_assignment, **READY)
    publishing.publish(report, make_user(email="a@x.mx"))
    before = data_for(report)
    SubmissionScore.objects.update(final_ndr="muy_alto")
    report.refresh_from_db()
    assert data_for(report) == before


def test_publish_and_unpublish_are_idempotent(scored_assignment, make_user):
    report = Report.objects.create(assignment=scored_assignment, **READY)
    user = make_user(email="a@x.mx")
    publishing.publish(report, user)
    first = report.published_at
    assert publishing.publish(report, user) == ["El reporte ya está publicado."]
    report.refresh_from_db()
    assert report.published_at == first
    publishing.unpublish(report)
    publishing.unpublish(report)
    report.refresh_from_db()
    assert report.status == Report.Status.DRAFT and report.snapshot is None
