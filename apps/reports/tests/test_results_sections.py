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


def _slice(html, key):
    return html.split(f'id="sec-{key}"')[1].split("</section>")[0]


def test_area_sections_hide_small_groups(scored_assignment):
    html = _html(Report(assignment=scored_assignment))
    area = _slice(html, "resultadosarea")
    assert "Operaciones" in area and "Ventas" in area and "Sin área" in area
    # Ventas is hidden too: "Sin área" (1 respondent) alone would be deducible.
    assert area.count(SUPPRESSED) == 2
    assert SUPPRESSED in _slice(html, "resultadosguia1")
    # Only a visible área gets its categoría distributions.
    assert '<h4 class="report-h4">Operaciones</h4>' in area
    assert '<h4 class="report-h4">Ventas</h4>' not in area
    assert '<h4 class="report-h4">Sin área</h4>' not in area


def test_per_area_sections_close_with_the_ndr_legend(scored_assignment):
    html = _html(Report(assignment=scored_assignment))
    for key in ("resultadosparticipacion", "resultadosarea"):
        assert 'class="report-legend"' in _slice(html, key)


def test_stats_rows_print_the_highest_possible_score(scored_assignment):
    html = _html(Report(assignment=scored_assignment))
    dims = _slice(html, "resultadosdimension")
    # Condiciones peligrosas e inseguras: items 1 and 3, so 2 × 4 = 8.
    assert "<dt>Máx. posible</dt><dd>8</dd>" in dims
    assert "Máx. posible" in _slice(html, "resultadosfinal")


def test_empty_assignment_shows_empty_states(company, nom035_survey):
    from apps.nom035.tests.factories import make_assignment

    html = _html(Report(assignment=make_assignment(company, nom035_survey)))
    assert "Aún no hay cuestionarios valorados" in html
    assert "<svg" not in html
