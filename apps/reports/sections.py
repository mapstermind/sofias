"""The report, declared as one ordered list of sections.

Screen, PDF and table of contents all iterate REGISTRY; reorder, drop or add a
section here (plus its partial). Numbers are derived from position: a section
with a title is numbered, the untitled portada is not.
"""

from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import date

from django.utils import timezone

from apps.nom035 import _nom035_scoring as cfg
from apps.nom035 import constants as c
from apps.reports import content, text
from apps.reports.models import Report, ReportSignatory
from apps.reports.snapshot import ReportData, data_for

_T = "reports/sections/"


@dataclass(frozen=True)
class ReportContext:
    report: Report  # may be unsaved (assignment set, fields empty)
    data: ReportData
    draft: bool
    issued_on: date  # published_at date, else today
    signatories: list[ReportSignatory]


def _no_context(ctx: ReportContext) -> dict:
    return {}


@dataclass(frozen=True)
class Section:
    key: str
    title: str  # "" → not numbered, not in the TOC (portada)
    template: str
    build: Callable[[ReportContext], dict] = _no_context
    children: tuple["Section", ...] = ()


@dataclass(frozen=True)
class RenderedSection:
    key: str
    number: str  # "1", "5.3"; "" for the portada
    title: str
    template: str
    context: dict = field(default_factory=dict)
    children: tuple["RenderedSection", ...] = ()


def context_for(report: Report) -> ReportContext:
    published = report.status == Report.Status.PUBLISHED and report.snapshot is not None
    return ReportContext(
        report=report,
        data=data_for(report),
        draft=not published,
        issued_on=timezone.localdate(report.published_at)
        if published and report.published_at
        else timezone.localdate(),
        signatories=list(report.signatories.all()) if report.pk else [],
    )


def _walk(registry, ctx: ReportContext | None, prefix: str = "") -> list:
    """Number `registry` from its position; build contexts when `ctx` is given."""
    out, n = [], 0
    for s in registry:
        number = ""
        if s.title:
            n += 1
            number = f"{prefix}{n}"
        out.append(
            RenderedSection(
                key=s.key,
                number=number,
                title=s.title,
                template=s.template,
                context={}
                if ctx is None
                else {"data": ctx.data, "ctx": ctx, **s.build(ctx)},
                children=tuple(_walk(s.children, ctx, f"{number}.")),
            )
        )
    return out


def number_sections(registry) -> list[RenderedSection]:
    """The registry numbered, without building any section's context."""
    return _walk(registry, None)


def render_sections(ctx: ReportContext, registry=None) -> list[RenderedSection]:
    return _walk(REGISTRY if registry is None else registry, ctx)


# ── Annex: the method, from the scoring constants ───────────────────────────


def method_tables(variant: str, taxonomy: dict) -> dict:
    """Rows for the annex: taxonomy, scoring direction, thresholds — this variant only."""
    by_dim = {}
    for code, (cat, dom, dim) in taxonomy.items():
        by_dim.setdefault((cat, dom, dim), []).append(int(code.split("-")[1]))
    taxonomy_rows = [
        {
            "categoria": cfg.group_label(cat),
            "dominio": cfg.group_label(dom),
            "dimension": cfg.group_label(dim),
            "items": ", ".join(str(n) for n in sorted(items)),
        }
        for (cat, dom, dim), items in sorted(
            by_dim.items(),
            key=lambda kv: (cfg.CATEGORIA_ORDER.index(kv[0][0]), min(kv[1])),
        )
    ]
    numbers = sorted(int(code.split("-")[1]) for code in taxonomy)
    prefix = next(iter(taxonomy)).split("-")[0]
    direct = [n for n in numbers if not cfg.is_inverted(f"{prefix}-{n}")]
    inverted = [n for n in numbers if cfg.is_inverted(f"{prefix}-{n}")]

    def bands(level, key):
        """(level, "75 a < 99", level label) per NDR level, lowest first."""
        table = cfg.thresholds_for(level, key, variant)
        cells, low = [], 0
        for upper, ndr in table:
            if upper == float("inf"):
                band = f"≥ {low:g}"
            elif low == 0:
                band = f"< {upper:g}"
            else:
                band = f"{low:g} a < {upper:g}"
            cells.append((ndr, band, c.NDR_LABELS[ndr]))
            low = upper
        return cells

    used = taxonomy.values()
    categorias = [k for k in cfg.CATEGORIA_ORDER if any(t[0] == k for t in used)]
    dominios = [
        d
        for k in categorias
        for d in cfg.dominios_for_categoria(k)
        if any(t[1] == d for t in used)
    ]
    return {
        "taxonomy": taxonomy_rows,
        "direct": ", ".join(map(str, direct)),
        "inverted": ", ".join(map(str, inverted)),
        "final": bands("final", "final"),
        "categorias": [
            (cfg.group_label(k), bands(c.LEVEL_CATEGORIA, k)) for k in categorias
        ],
        "dominios": [(cfg.group_label(d), bands(c.LEVEL_DOMINIO, d)) for d in dominios],
        "levels": [(lvl, c.NDR_LABELS[lvl]) for lvl in c.NDR_ORDER],
    }


# ── Section builders ─────────────────────────────────────────────────────────


def _portada(ctx):
    return {"provider": ctx.data.company.name}


def _objetivo(ctx):
    return {"objective": content.OBJECTIVE_PLACEHOLDER}


def _actividades(ctx):
    r = ctx.report
    return {
        "headcounts": [
            (label, value)
            for label, value in (
                ("Presencial", r.headcount_in_person),
                ("Home office", r.headcount_home_office),
                ("Híbrido", r.headcount_hybrid),
            )
            if value is not None
        ],
        "headcount_total": r.headcount_total,
    }


def _poblacion(ctx):
    return {"guides": f"Guía I y la {ctx.data.variant_label}"}


def _criterios(ctx):
    return {"criteria": text.action_criteria(ctx.data)}


def _recomendaciones(ctx):
    return {"recommendations": text.recommendations(ctx.data)}


def _responsables(ctx):
    name = ctx.data.company.name
    return {
        "provider": name,
        "notice": content.CONFIDENTIALITY_NOTICE.format(company=name),
    }


def _anexo(ctx):
    variant = ctx.data.variant
    method = method_tables(variant, cfg.taxonomy_for_variant(variant))
    return {
        "glossary": content.GLOSSARY,
        "lft": content.LFT_ARTICLES,
        "method": method,
        "final_rows": [("Calificación final", method["final"])],
    }


# ── Results builders ─────────────────────────────────────────────────────────

LEGEND = tuple((lvl, c.NDR_LABELS[lvl]) for lvl in c.NDR_ORDER)


def _finding(fn, rows) -> dict:
    """The section's generated sentence; "" while nothing is scored."""
    return {"finding": fn(rows) if rows else ""}


def _final(ctx):
    return {
        **_finding(text.final_sentence, ctx.data.final_distribution),
        "legend": LEGEND,
    }


def _paired(dists, stats) -> list[dict]:
    """Each distribution row with the statistics row of the same key."""
    by_key = {s.key: s for s in stats}
    return [{"dist": d, "stats": by_key.get(d.key)} for d in dists]


def _categoria(ctx):
    data = ctx.data
    return {
        **_finding(text.categoria_sentence, data.categoria_distribution),
        "rows": _paired(data.categoria_distribution, data.categoria_stats),
        "legend": LEGEND,
    }


def _dominio(ctx):
    data = ctx.data
    stats = [s for cat in data.categoria_stats for s in cat.children]
    groups = [
        {"label": cat.label, "rows": _paired(cat.children, stats)}
        for cat in data.categoria_distribution
    ]
    rows = [d for cat in data.categoria_distribution for d in cat.children]
    return {
        **_finding(text.dominio_sentence, rows),
        "groups": groups,
        "legend": LEGEND,
    }


# ── The registry ─────────────────────────────────────────────────────────────

_R = _T + "results/"

RESULTS_CHILDREN = (
    Section("resultados.perfil", "Perfil de quienes respondieron", _R + "_perfil.html"),
    Section(
        "resultados.participacion", "Participación por área", _R + "_participacion.html"
    ),
    Section("resultados.final", "Calificación final", _R + "_final.html", _final),
    Section(
        "resultados.categoria",
        "Resultados por categoría",
        _R + "_categoria.html",
        _categoria,
    ),
    Section(
        "resultados.dominio", "Resultados por dominio", _R + "_dominio.html", _dominio
    ),
    Section("resultados.dimension", "Resultados por dimensión", _R + "_dimension.html"),
    Section("resultados.area", "Resultados por área", _R + "_area.html"),
    Section("resultados.guia1", "Guía I", _R + "_guia1.html"),
)

REGISTRY = (
    Section("portada", "", _T + "_portada.html", _portada),
    Section("datos", "Datos del centro de trabajo", _T + "_datos.html"),
    Section("objetivo", "Objetivo", _T + "_objetivo.html", _objetivo),
    Section(
        "actividades", "Principales actividades", _T + "_actividades.html", _actividades
    ),
    Section(
        "poblacion", "Selección de la población", _T + "_poblacion.html", _poblacion
    ),
    Section(
        "resultados", "Resultados", _T + "_resultados.html", children=RESULTS_CHILDREN
    ),
    Section("criterios", "Criterios de acción", _T + "_criterios.html", _criterios),
    Section(
        "recomendaciones",
        "Recomendaciones según riesgo identificado",
        _T + "_recomendaciones.html",
        _recomendaciones,
    ),
    Section("conclusiones", "Conclusiones", _T + "_conclusiones.html"),
    Section("responsables", "Responsables", _T + "_responsables.html", _responsables),
    Section("anexo", "Anexo", _T + "_anexo.html", _anexo),
)
