"""The report as a letter-size PDF, rendered by WeasyPrint from the screen partials.

The document lives under a fictitious BASE_URL; its stylesheets, fonts and
images are relative links that ReportURLFetcher resolves through Django's
static finders. Nothing else is fetched: no network, no request to the app.
"""

import mimetypes

from django.conf import settings
from django.contrib.staticfiles import finders
from django.core.exceptions import SuspiciousFileOperation
from django.template.loader import render_to_string
from django.utils import timezone
from weasyprint import HTML
from weasyprint.text.fonts import FontConfiguration
from weasyprint.urls import URLFetcher, URLFetcherResponse

from apps.core.brand import palette_slugs
from apps.reports.sections import context_for, render_sections

BASE_URL = "https://reporte.sofias.invalid/"
_STATIC = f"{BASE_URL}static/"


def static_fetcher(url: str) -> dict:
    """Resolve the report's fonts, CSS and images from static files; nothing else."""
    if not url.startswith(_STATIC):
        raise ValueError(f"El PDF solo carga archivos estáticos: {url}")
    relative = url[len(_STATIC) :].split("?")[0].split("#")[0]
    try:
        path = finders.find(relative) if relative else None
    except SuspiciousFileOperation as exc:
        raise ValueError(f"Ruta de archivo estático no válida: {url}") from exc
    if path is None:
        raise ValueError(f"Archivo estático no encontrado: {url}")
    with open(path, "rb") as fh:
        data = fh.read()
    mime = mimetypes.guess_type(path)[0] or "application/octet-stream"
    return {"string": data, "mime_type": mime}


class ReportURLFetcher(URLFetcher):
    """WeasyPrint's fetcher, narrowed to `static_fetcher`."""

    def fetch(self, url, headers=None):
        found = static_fetcher(url)
        return URLFetcherResponse(
            url, found["string"], headers={"Content-Type": found["mime_type"]}
        )


def _write_pdf(html: str) -> bytes:
    fonts = FontConfiguration()
    document = HTML(string=html, base_url=BASE_URL, url_fetcher=ReportURLFetcher())
    return document.write_pdf(font_config=fonts)


def report_html(report, palette=None) -> str:
    """The report as one HTML document, painted in `palette` (the default when unknown).

    Rendered without a request, so the brand context processor does not run.
    """
    if palette not in palette_slugs():
        palette = settings.BRAND_PALETTE_DEFAULT
    ctx = context_for(report)
    return render_to_string(
        "reports/report_pdf.html",
        {
            "ctx": ctx,
            "sections": render_sections(ctx),
            "report": report,
            "palette": palette,
        },
    )


def render_report_pdf(report, palette=None) -> bytes:
    return _write_pdf(report_html(report, palette))


def filename(report) -> str:
    day = (
        timezone.localdate(report.published_at)
        if report.published_at
        else timezone.localdate()
    )
    code = report.assignment.company.reference_code
    return f"reporte-nom035-{code}-{day:%Y-%m}.pdf"
