"""The dominio tier of the risk palette in the report."""

import pytest
from django.template.loader import render_to_string

from apps.nom035.tests.factories import make_assignment, make_score
from apps.reports.models import Report
from apps.reports.sections import context_for, render_sections

pytestmark = pytest.mark.django_db
DOMINIO_HEXES = ("#9CA3AF", "#4A8039", "#CA9429", "#B5531F", "#7A1010")


def _html(report):
    ctx = context_for(report)
    return render_to_string(
        "reports/_document.html", {"sections": render_sections(ctx), "ctx": ctx}
    )


def _between(html, key, next_key):
    start = html.index(f'id="sec-{key}"')
    return html[start : html.index(f'id="sec-{next_key}"', start)]


def test_recommendations_use_the_dominio_tier(scored_assignment):
    recs = _between(
        _html(Report(assignment=scored_assignment)), "recomendaciones", "conclusiones"
    )
    assert "report-badge--dom-" in recs
    assert "report-criterion--dom-" in recs
    assert "report-badge--alto" not in recs


def test_criteria_stay_in_the_categoria_tier(scored_assignment):
    crit = _between(
        _html(Report(assignment=scored_assignment)), "criterios", "recomendaciones"
    )
    assert "report-badge--dom-" not in crit
    assert "report-criterion--dom-" not in crit


def test_dominio_section_draws_dominio_marks_and_legend(scored_assignment):
    dom = _between(
        _html(Report(assignment=scored_assignment)),
        "resultadosdominio",
        "resultadosdimension",
    )
    assert any(f'fill="{h}"' in dom for h in DOMINIO_HEXES)
    assert 'fill="#F97316"' not in dom  # no categoría Alto mark among dominios
    assert "report-legend--dom" in dom
    assert "report-swatch--dom-muy_alto" in dom


def test_categoria_section_keeps_the_categoria_legend(scored_assignment):
    cat = _between(
        _html(Report(assignment=scored_assignment)),
        "resultadoscategoria",
        "resultadosdominio",
    )
    assert "report-legend--dom" not in cat
    assert "report-swatch--muy_alto" in cat


def test_annex_dominio_thresholds_use_the_dominio_tier(scored_assignment):
    annex = _html(Report(assignment=scored_assignment)).split('id="sec-anexo"')[1]
    assert annex.count("report-level--dom-muy_alto") == 1
    assert annex.count('class="report-level--muy_alto"') == 2  # final + categoría


def test_small_variant_dominio_legend(company, nom035_survey):
    assignment = make_assignment(company, nom035_survey, variant="small")
    make_score(assignment)
    dom = _between(
        _html(Report(assignment=assignment)), "resultadosdominio", "resultadosdimension"
    )
    assert "report-legend--dom" in dom


def test_document_prints_no_template_comment_markup(scored_assignment):
    html = _html(Report(assignment=scored_assignment))
    assert "{#" not in html and "#}" not in html


def test_every_page_group_carries_its_legend(scored_assignment):
    html = _html(Report(assignment=scored_assignment))
    for key, next_key, legend in (
        ("resultadoscategoria", "resultadosdominio", "report-legend"),
        ("resultadosdominio", "resultadosdimension", "report-legend--dom"),
    ):
        groups = _between(html, key, next_key).split("report-page-group")[1:]
        assert groups
        assert all(legend in g for g in groups), key
