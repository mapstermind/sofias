import pytest
from django.urls import reverse

from apps.accounts.roles import ROLES
from apps.reports import pdf, publishing
from apps.reports.models import Report

pytestmark = pytest.mark.django_db
READY = dict(
    issued_in="CDMX",
    activities_summary="A",
    evaluator_name="S",
    evaluator_license="1",
    conclusions="C",
)


def test_render_report_pdf_produces_pages(scored_assignment):
    data = pdf.render_report_pdf(Report(assignment=scored_assignment))
    assert data.startswith(b"%PDF")
    assert len(data) > 10_000


def test_static_fetcher_refuses_non_static_urls():
    with pytest.raises(ValueError):
        pdf.static_fetcher("https://example.com/x.css")
    with pytest.raises(ValueError):
        pdf.static_fetcher(f"{pdf.BASE_URL}cuentas/")


def test_static_fetcher_refuses_missing_static_files():
    with pytest.raises(ValueError):
        pdf.static_fetcher(f"{pdf.BASE_URL}static/css/nope.css")


def test_static_fetcher_serves_static_files():
    result = pdf.static_fetcher(f"{pdf.BASE_URL}static/css/report.css")
    assert result["mime_type"] == "text/css"
    assert b"report-sheet" in result["string"]


def test_url_fetcher_serves_static_files_and_refuses_the_rest():
    fetcher = pdf.ReportURLFetcher()
    response = fetcher.fetch(f"{pdf.BASE_URL}static/fonts/SourceSerif4-Variable.ttf")
    assert response.content_type == "font/ttf"
    assert len(response.read()) > 100_000
    with pytest.raises(ValueError):
        fetcher.fetch("https://example.com/x.css")


def test_filename(scored_assignment):
    report = Report(assignment=scored_assignment)
    name = pdf.filename(report)
    assert name.startswith(
        f"reporte-nom035-{scored_assignment.company.reference_code}-"
    )
    assert name.endswith(".pdf")


def test_pdf_html_puts_the_contents_after_the_cover(scored_assignment):
    html = pdf.report_html(Report(assignment=scored_assignment))
    assert (
        html.index("report-cover")
        < html.index("report-toc")
        < html.index('id="sec-objetivo"')
    )
    assert "BORRADOR" in html


def test_admin_pdf_draft_has_watermark_html(
    client, make_user, bootstrap_groups, scored_assignment, monkeypatch
):
    captured = {}
    monkeypatch.setattr(
        pdf,
        "_write_pdf",
        lambda html: captured.setdefault("html", html) and b"%PDF-1.7",
    )
    user = make_user(email="op@x.mx")
    user.groups.add(bootstrap_groups[ROLES[0].name])
    client.force_login(user)
    url = reverse(
        "reports:admin_pdf",
        args=[scored_assignment.company.reference_code, scored_assignment.pk],
    )
    resp = client.get(url)
    assert resp["Content-Type"] == "application/pdf"
    assert "attachment;" in resp["Content-Disposition"]
    assert "BORRADOR" in captured["html"]


def test_published_pdf_has_no_watermark(make_user, scored_assignment):
    report = Report.objects.create(assignment=scored_assignment, **READY)
    publishing.publish(report, make_user(email="op@x.mx"))
    assert "BORRADOR" not in pdf.report_html(report)


def test_exec_pdf_only_when_published(
    client,
    make_user_with_profile,
    make_user,
    bootstrap_groups,
    scored_assignment,
    monkeypatch,
):
    monkeypatch.setattr(pdf, "_write_pdf", lambda html: b"%PDF-1.7")
    user = make_user_with_profile(email="e@x.mx", company=scored_assignment.company)
    user.groups.add(bootstrap_groups[ROLES[1].name])
    client.force_login(user)
    url = reverse("reports:exec_pdf", args=[scored_assignment.pk])
    report = Report.objects.create(assignment=scored_assignment, **READY)
    assert client.get(url).status_code == 404
    publishing.publish(report, make_user(email="op@x.mx"))
    assert client.get(url).status_code == 200


def test_detail_page_links_the_pdf(
    client, make_user, bootstrap_groups, scored_assignment
):
    user = make_user(email="op@x.mx")
    user.groups.add(bootstrap_groups[ROLES[0].name])
    client.force_login(user)
    code = scored_assignment.company.reference_code
    resp = client.get(
        reverse("reports:admin_detail", args=[code, scored_assignment.pk])
    )
    assert reverse("reports:admin_pdf", args=[code, scored_assignment.pk]) in (
        resp.content.decode()
    )
    assert "Descargar PDF" in resp.content.decode()


def test_static_fetcher_refuses_path_traversal():
    with pytest.raises(ValueError):
        pdf.static_fetcher(f"{pdf.BASE_URL}static/../config/settings.py")
    with pytest.raises(ValueError):
        pdf.static_fetcher(f"{pdf.BASE_URL}static/css/../../config/settings.py")


def test_report_html_paints_the_default_palette(scored_assignment):
    html = pdf.report_html(Report(assignment=scored_assignment))
    assert '<html lang="es" data-palette="petrol">' in html


def test_report_html_paints_a_chosen_palette(scored_assignment):
    html = pdf.report_html(Report(assignment=scored_assignment), palette="slate")
    assert 'data-palette="slate"' in html


def test_report_html_ignores_an_unknown_palette(scored_assignment):
    html = pdf.report_html(Report(assignment=scored_assignment), palette="durazno")
    assert 'data-palette="petrol"' in html


def test_the_report_sets_data_in_figtree_and_prose_in_source_serif():
    css = "".join(
        pdf.static_fetcher(f"{pdf.BASE_URL}static/css/{name}")["string"].decode()
        for name in ("report.css", "report-wide.css", "report-print.css")
    )
    assert "Source Sans" not in css
    assert '"Figtree"' in css and '"Source Serif 4"' in css


def test_no_chart_label_names_a_font_the_report_does_not_bundle():
    """WeasyPrint draws chart <text> from its font-family attribute, not the stylesheet."""
    from pathlib import Path

    charts = Path(__file__).resolve().parents[3] / "templates/components/charts"
    for template in charts.glob("*.html"):
        assert "Source Sans" not in template.read_text(), template.name
