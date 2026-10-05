"""Publishing freezes the report's data; unpublishing discards it."""

from django.db import transaction
from django.utils import timezone

from apps.nom035.models import SubmissionScore
from apps.reports.models import Report
from apps.reports.snapshot import build_report_data, dump
from apps.surveys.models import SurveyAssignment

REQUIRED = (
    ("issued_in", "Lugar de emisión"),
    ("activities_summary", "Principales actividades"),
    ("evaluator_name", "Responsable de la evaluación"),
    ("evaluator_license", "Cédula profesional"),
    ("conclusions", "Conclusiones"),
)


def blockers(report) -> list[str]:
    out = []
    assignment = report.assignment
    if assignment.status == SurveyAssignment.Status.ACTIVE:
        out.append("La encuesta sigue activa; ciérrala antes de publicar el reporte.")
    if not SubmissionScore.objects.filter(submission__assignment=assignment).exists():
        out.append("La encuesta no tiene cuestionarios valorados.")
    out += [
        f"Falta completar: {label}."
        for name, label in REQUIRED
        if not getattr(report, name).strip()
    ]
    return out


def publish(report, user) -> list[str]:
    if report.status == Report.Status.PUBLISHED:
        return ["El reporte ya está publicado."]
    problems = blockers(report)
    if problems:
        return problems
    with transaction.atomic():
        report.snapshot = dump(build_report_data(report.assignment))
        report.status = Report.Status.PUBLISHED
        report.published_at = timezone.now()
        report.published_by = user
        report.save()
    return []


def unpublish(report) -> None:
    if report.status == Report.Status.DRAFT:
        return
    report.snapshot = None
    report.status = Report.Status.DRAFT
    report.published_at = None
    report.published_by = None
    report.save()
