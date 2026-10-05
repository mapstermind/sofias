import pytest
from django.template.loader import render_to_string

from apps.reports.models import Report, ReportSignatory
from apps.reports.sections import REGISTRY, context_for, render_sections

pytestmark = pytest.mark.django_db


def _render(report):
    ctx = context_for(report)
    return render_to_string(
        "reports/_document.html", {"sections": render_sections(ctx), "ctx": ctx}
    )


@pytest.fixture
def report(scored_assignment):
    report = Report.objects.create(
        assignment=scored_assignment,
        issued_in="Ciudad de México",
        activities_summary="Compras\nAlmacén",
        evaluator_name="Sofía Santana Arciniega",
        evaluator_license="1234567",
        conclusions="Primera.\n\nSegunda.",
    )
    ReportSignatory.objects.create(
        report=report, title="Dirección de RH", name="Lic. Ana", order=1
    )
    return report


def _flatten(sections):
    for s in sections:
        yield s
        yield from _flatten(s.children)


def test_numbering_skips_the_portada_and_nests_results():
    from apps.reports.sections import number_sections

    numbers = [(s.key, s.number) for s in _flatten(number_sections(REGISTRY))]
    assert numbers[0] == ("portada", "")
    assert ("datos", "1") in numbers
    assert ("resultados.final", "5.3") in numbers


def test_document_renders_every_section(report):
    html = _render(report)
    for heading in (
        "Datos del centro de trabajo",
        "Objetivo",
        "Principales actividades",
        "Selección de la población",
        "Resultados",
        "Criterios de acción",
        "Recomendaciones según riesgo identificado",
        "Conclusiones",
        "Responsables",
        "Anexo",
    ):
        assert heading in html, heading
    assert "Planta Norte" in html and "Manufactura" in html
    assert "Lic. Ana" in html and "1234567" in html


def test_admin_text_is_escaped_and_keeps_paragraphs(report):
    report.conclusions = "<script>x</script>\n\nSegundo párrafo."
    report.save()
    html = _render(report)
    assert "<script>x</script>" not in html
    assert "&lt;script&gt;" in html
    assert html.count("<p") >= 2


def test_optional_blocks_are_left_out(report):
    report.signatories.all().delete()
    html = _render(report)
    assert "Responsables de la empresa" not in html
    assert "Número de trabajadores" not in html  # no headcounts entered
    assert "Recomendaciones adicionales" not in html


def test_optional_blocks_render_when_filled(report):
    report.headcount_in_person = 10
    report.headcount_hybrid = 4
    report.additional_recommendations = "Revisar turnos."
    report.save()
    html = _render(report)
    assert "Número de trabajadores" in html
    assert "Responsables de la empresa" in html
    assert "Recomendaciones adicionales" in html and "Revisar turnos." in html
    assert ">14<" in html  # the headcount sum


def test_poblacion_prints_the_bare_application_span(report):
    html = _render(report)
    poblacion = html.split('id="sec-poblacion"')[1].split("</section>")[0]
    assert "en el periodo 3 feb – 10 mar 2026." in poblacion
    assert "Guía I y la Guía III" in poblacion
    assert "Guía III ·" not in poblacion
    assert "sin respuestas" not in poblacion


def test_poblacion_omits_the_period_without_answer_dates(company, nom035_survey):
    from apps.nom035.tests.factories import make_assignment, make_score

    assignment = make_assignment(company, nom035_survey, variant="small")
    make_score(assignment)
    html = _render(Report(assignment=assignment))
    poblacion = html.split('id="sec-poblacion"')[1].split("</section>")[0]
    assert "periodo" not in poblacion


def test_unsaved_report_previews(scored_assignment):
    html = _render(Report(assignment=scored_assignment))
    assert "Datos del centro de trabajo" in html


def test_small_variant_report_renders(company, nom035_survey):
    from apps.nom035.tests.factories import make_assignment, make_score

    assignment = make_assignment(company, nom035_survey, variant="small")
    make_score(assignment)
    html = _render(Report(assignment=assignment))
    assert "Guía II" in html
    assert "Entorno organizacional" not in html.split("Anexo")[0]


def test_reordering_the_registry_renumbers():
    from apps.reports.sections import number_sections

    swapped = (REGISTRY[0], REGISTRY[2], REGISTRY[1], *REGISTRY[3:])
    numbers = {s.key: s.number for s in number_sections(swapped)}
    assert numbers["objetivo"] == "1"
    assert numbers["datos"] == "2"


def test_render_sections_numbers_like_number_sections(report):
    from apps.reports.sections import number_sections

    rendered = [
        (s.key, s.number) for s in _flatten(render_sections(context_for(report)))
    ]
    plain = [(s.key, s.number) for s in _flatten(number_sections(REGISTRY))]
    assert rendered == plain


def test_method_tables_match_the_engine():
    from apps.nom035 import _nom035_scoring as cfg
    from apps.reports.sections import method_tables

    large = method_tables("large", cfg.taxonomy_for_variant("large"))
    assert large["final"][0][1] == "< 50"
    assert large["final"][-1][1] == "≥ 140"
    assert large["final"][2][1] == "75 a < 99"
    small = method_tables("small", cfg.taxonomy_for_variant("small"))
    assert len(small["categorias"]) == 4
    assert "1" in small["inverted"].split(", ")  # Guía II item 1 scores 4→0
