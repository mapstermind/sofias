"""Print page breaks: registry flags and repeated groups → report-print.css."""

import re
from pathlib import Path

import pytest
from django.template.loader import render_to_string

from apps.nom035.tests.factories import make_assignment, make_score
from apps.reports.models import Report
from apps.reports.sections import REGISTRY, context_for, render_sections

pytestmark = pytest.mark.django_db
PRINT_CSS = Path(__file__).resolve().parents[3] / "static/css/report-print.css"

BREAK_BEFORE = {
    "resultados",
    "resultados.dominio",
    "resultados.dimension",
    "resultados.area",
    "resultados.guia1",
    "criterios",
    "recomendaciones",
    "conclusiones",
    "responsables",
    "anexo",
}


def _flat(sections):
    for s in sections:
        yield s
        yield from _flat(s.children)


def _html(report):
    ctx = context_for(report)
    return render_to_string(
        "reports/_document.html", {"sections": render_sections(ctx), "ctx": ctx}
    )


def _open_tag(html, key):
    return re.search(rf'<section id="sec-{key.replace(".", "")}"[^>]*>', html).group(0)


def _section_body(html, key, next_key):
    start = html.index(f'id="sec-{key.replace(".", "")}"')
    end = html.index(f'id="sec-{next_key.replace(".", "")}"')
    return html[start:end]


def test_registry_flags_the_requested_breaks():
    assert {s.key for s in _flat(REGISTRY) if s.break_before} == BREAK_BEFORE


def test_flagged_sections_carry_the_break_class(scored_assignment):
    html = _html(Report(assignment=scored_assignment))
    for s in _flat(render_sections(context_for(Report(assignment=scored_assignment)))):
        tag = _open_tag(html, s.key)
        assert ("report-break-before" in tag) == (s.key in BREAK_BEFORE), s.key


def test_toc_ends_its_page(scored_assignment):
    html = _html(Report(assignment=scored_assignment))
    toc = re.search(r'<nav class="([^"]*)"[^>]*aria-label="Contenido"', html).group(1)
    assert "report-break-after" in toc.split()


def test_each_categoria_and_dominio_group_is_a_page_group(scored_assignment):
    html = _html(Report(assignment=scored_assignment))
    categorias = _section_body(html, "resultados.categoria", "resultados.dominio")
    dominios = _section_body(html, "resultados.dominio", "resultados.dimension")
    dimensiones = _section_body(html, "resultados.dimension", "resultados.area")
    data = context_for(Report(assignment=scored_assignment)).data
    assert categorias.count("report-page-group") == len(data.categoria_distribution)
    assert dominios.count("report-page-group") == len(data.categoria_distribution)
    assert dimensiones.count("report-page-group") == len(data.dimensions)


def test_small_variant_groups_render(company, nom035_survey):
    assignment = make_assignment(company, nom035_survey, variant="small")
    make_score(assignment)
    html = _html(Report(assignment=assignment))
    dimensiones = _section_body(html, "resultados.dimension", "resultados.area")
    assert dimensiones.count("report-page-group") == len(
        context_for(Report(assignment=assignment)).data.dimensions
    )


def test_print_css_turns_flags_into_page_breaks():
    css = PRINT_CSS.read_text()
    assert re.search(r"\.report-break-before\s*\{[^}]*break-before:\s*page", css)
    assert re.search(r"\.report-break-after\s*\{[^}]*break-after:\s*page", css)
    assert re.search(
        r"\.report-page-group\s*\+\s*\.report-page-group\s*\{[^}]*break-before:\s*page",
        css,
    )


def test_first_group_does_not_break():
    css = PRINT_CSS.read_text()
    # A bare `.report-page-group { break-before }` would break before the first too.
    standalone = r"(?:^|[},])\s*\.report-page-group\s*\{[^}]*break-before"
    assert not re.search(standalone, css, re.M)
