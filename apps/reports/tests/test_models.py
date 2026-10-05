import pytest

from apps.reports.models import Report, ReportSignatory
from apps.surveys.models import SurveyAssignment

pytestmark = pytest.mark.django_db


@pytest.fixture
def assignment(company, nom035_survey):
    return SurveyAssignment.objects.create(
        company=company, survey=nom035_survey, variant="large"
    )


def test_reports_app_labels_are_spanish(assert_explicit_labels):
    assert_explicit_labels("reports")


def test_company_report_fields_have_labels(assert_explicit_labels):
    assert_explicit_labels("accounts")


def test_report_defaults_to_draft_without_snapshot(assignment):
    report = Report.objects.create(assignment=assignment)
    assert report.status == Report.Status.DRAFT
    assert report.snapshot is None
    assert report.published_at is None


def test_headcount_total(assignment):
    report = Report(assignment=assignment)
    assert report.headcount_total is None
    report.headcount_in_person = 10
    report.headcount_hybrid = 4
    assert report.headcount_total == 14


def test_signatories_are_ordered(assignment):
    report = Report.objects.create(assignment=assignment)
    ReportSignatory.objects.create(report=report, title="B", name="Y", order=2)
    ReportSignatory.objects.create(report=report, title="A", name="X", order=1)
    assert [s.title for s in report.signatories.all()] == ["A", "B"]


def test_app_verbose_name():
    from django.apps import apps

    assert apps.get_app_config("reports").verbose_name == "Reportes"
