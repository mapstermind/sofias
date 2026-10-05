import pytest
from django.template.loader import render_to_string

from apps.reports.models import Report
from apps.reports.sections import context_for, render_sections

pytestmark = pytest.mark.django_db
SUPPRESSED = "Grupo demasiado pequeño"


def _html(report):
    ctx = context_for(report)
    return render_to_string(
        "reports/_document.html", {"sections": render_sections(ctx), "ctx": ctx}
    )


def test_results_use_the_dashboard_charts(scored_assignment):
    html = _html(Report(assignment=scored_assignment))
    assert html.count("<svg") >= 10
    assert "De los 12 colaboradores evaluados" in html
    assert "concentra la mayor proporción" in html
    assert "Los dominios con mayor proporción" in html or "El dominio con mayor" in html


def test_dominios_are_always_expanded(scored_assignment):
    html = _html(Report(assignment=scored_assignment))
    assert "<details" not in html
    assert "Condiciones en el ambiente de trabajo" in html


def test_dimension_strip_is_neutral(scored_assignment):
    html = _html(Report(assignment=scored_assignment))
    assert "Sin umbral oficial" in html


def test_area_sections_hide_small_groups(scored_assignment):
    html = _html(Report(assignment=scored_assignment))
    area = html.split('id="sec-resultadosarea"')[1].split("</section>")[0]
    assert "Operaciones" in area and "Ventas" in area
    assert SUPPRESSED in html  # "Sin área" (1 respondent) is hidden


def test_empty_assignment_shows_empty_states(company, nom035_survey):
    from apps.nom035.tests.factories import make_assignment

    html = _html(Report(assignment=make_assignment(company, nom035_survey)))
    assert "Aún no hay cuestionarios valorados" in html
    assert "<svg" not in html
