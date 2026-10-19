import pytest
from django.template.loader import render_to_string

from apps.nom035 import _nom035_scoring as cfg
from apps.nom035 import constants as c
from apps.reports.content import RECOMMENDATIONS
from apps.reports.models import Report
from apps.reports.sections import context_for, render_sections

pytestmark = pytest.mark.django_db
SMALL_GROUP_NOTICE = "Grupo demasiado pequeño"


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


def test_the_report_prints_no_statistics(scored_assignment):
    html = _html(Report(assignment=scored_assignment))
    for absent in (
        "report-stats",
        "Mediana",
        "Prom.",
        "Máx. posible",
        "Calificación</p>",
    ):
        assert absent not in html, absent


def test_the_report_has_no_dimension_section(scored_assignment):
    html = _html(Report(assignment=scored_assignment))
    assert 'id="sec-resultadosdimension"' not in html
    assert "Resultados por dimensión" not in html
    assert "Sin umbral oficial" not in html


def _slice(html, key):
    return html.split(f'id="sec-{key}"')[1].split("</section>")[0]


def test_area_sections_show_every_group(scored_assignment):
    html = _html(Report(assignment=scored_assignment))
    area = _slice(html, "resultadosarea")
    assert "Operaciones" in area and "Ventas" in area and "Sin área" in area
    assert SMALL_GROUP_NOTICE not in html
    for label in ("Operaciones", "Ventas", "Sin área"):
        assert f'<h4 class="report-h4">{label}</h4>' in area


def test_per_area_sections_close_with_the_ndr_legend(scored_assignment):
    html = _html(Report(assignment=scored_assignment))
    for key in ("resultadosparticipacion", "resultadosarea"):
        assert 'class="report-legend"' in _slice(html, key)


def test_empty_assignment_shows_empty_states(company, nom035_survey):
    from apps.nom035.tests.factories import make_assignment

    html = _html(Report(assignment=make_assignment(company, nom035_survey)))
    assert "Aún no hay cuestionarios valorados" in html
    assert "<svg" not in html


def _blocks(section, css_class):
    return section.split(f'class="{css_class}')[1:]


def test_a_categoria_block_names_its_categoria_once(scored_assignment):
    html = _html(Report(assignment=scored_assignment))
    section = _slice(html, "resultadoscategoria")
    blocks = _blocks(section, "report-group report-page-group")
    assert blocks
    for block in blocks:
        label = block.split('<h4 class="report-h4">')[1].split("</h4>")[0]
        assert block.count(label) == 1, label
        assert "Distribución por nivel" in block


def test_a_dominio_block_opens_with_its_recommendations(scored_assignment):
    html = _html(Report(assignment=scored_assignment))
    section = _slice(html, "resultadosdominio")
    blocks = _blocks(section, "report-group report-group--nested")
    by_label = {
        b.split('<p class="report-group-label">')[1].split("</p>")[0]: b for b in blocks
    }
    condiciones = by_label["Condiciones en el ambiente de trabajo"]
    assert condiciones.index("Recomendaciones") < condiciones.index(
        "Distribución por nivel"
    )
    assert RECOMMENDATIONS[cfg.DOM_CONDICIONES][c.NDR_ALTO] in condiciones
    assert "report-badge--dom-alto" in condiciones
    assert " en Alto" not in condiciones  # the chart below prints the share
    for label, block in by_label.items():
        if "report-badge--dom-" not in block:
            assert "Recomendaciones" not in block, label


def test_a_dominio_block_names_its_dominio_once(scored_assignment):
    html = _html(Report(assignment=scored_assignment))
    section = _slice(html, "resultadosdominio")
    blocks = _blocks(section, "report-group report-group--nested")
    assert blocks
    for block in blocks:
        label = block.split('<p class="report-group-label">')[1].split("</p>")[0]
        assert block.count(label) == 1, label


def test_the_final_score_is_named_once(scored_assignment):
    html = _html(Report(assignment=scored_assignment))
    section = _slice(html, "resultadosfinal")
    assert section.count("Calificación final") == 1
