"""Sentences and lists the report generates from its data. Pure functions."""

from collections.abc import Sequence
from dataclasses import dataclass
from fractions import Fraction

from apps.core.charts import largest_remainder
from apps.nom035 import _nom035_scoring as cfg
from apps.nom035 import constants as c
from apps.nom035.results import DistributionRow
from apps.reports.content import RECOMMENDATIONS
from apps.reports.snapshot import ReportData

NBSP = " "
HIGH = (c.NDR_ALTO, c.NDR_MUY_ALTO)
LOW = (c.NDR_NULO, c.NDR_BAJO)
RECOMMENDED = (c.NDR_MEDIO, c.NDR_ALTO, c.NDR_MUY_ALTO)


def row_percents(row: DistributionRow) -> dict[str, int]:
    """Largest-remainder percents for a row, as the charts print them."""
    levels = [lvl for lvl, _n in row.counts]
    return dict(zip(levels, largest_remainder([n for _l, n in row.counts])))


def _high_share(row: DistributionRow) -> Fraction:
    counts = dict(row.counts)
    return Fraction(sum(counts[lvl] for lvl in HIGH), row.n) if row.n else Fraction(0)


def high_share_text(row: DistributionRow) -> str:
    """High-level share as the charts print it: summed largest-remainder percents."""
    pct = row_percents(row)
    return f"{sum(pct[lvl] for lvl in HIGH)}{NBSP}%"


@dataclass(frozen=True)
class Finding:
    """A section's generated finding: a lead line, then (share, name) rows."""

    lead: str
    rows: tuple[tuple[str, str], ...] = ()


def final_finding(row: DistributionRow) -> Finding:
    pct = row_percents(row)
    noun = "colaborador evaluado" if row.n == 1 else "colaboradores evaluados"
    lead = "de" if row.n == 1 else "de los"
    return Finding(
        lead=f"Nivel de riesgo {lead} {row.n} {noun}:",
        rows=tuple(
            (f"{sum(pct[lvl] for lvl in levels)}{NBSP}%", label)
            for levels, label in (
                (LOW, "Nulo o Bajo"),
                ((c.NDR_MEDIO,), "Medio"),
                (HIGH, "Alto o Muy alto"),
            )
        ),
    )


def _leaders(subject: tuple[str, str], rows: Sequence[DistributionRow]) -> Finding:
    """`subject` is (singular, plural): "La categoría", "Las categorías"."""
    singular, plural = subject
    who = singular if len(rows) == 1 else plural
    verb = "es" if len(rows) == 1 else "son"
    return Finding(
        lead=(
            f"{who} con mayor proporción de trabajadores en niveles Alto o Muy alto "
            f"{verb}:"
        ),
        rows=tuple((high_share_text(r), r.label) for r in rows),
    )


def categoria_finding(rows: Sequence[DistributionRow]) -> Finding:
    """Every categoría tied for the largest exact Alto + Muy alto share."""
    ranked = [r for r in rows if _high_share(r) > 0]
    if not ranked:
        return Finding(
            "Ninguna categoría tiene trabajadores en niveles Alto o Muy alto."
        )
    top = max(_high_share(r) for r in ranked)
    leaders = [r for r in ranked if _high_share(r) == top]
    return _leaders(("La categoría", "Las categorías"), leaders)


def dominio_finding(rows: Sequence[DistributionRow]) -> Finding:
    """Up to three dominios by Alto + Muy alto share, ties at the cut-off included."""
    ranked = sorted(
        (r for r in rows if _high_share(r) > 0), key=lambda r: -_high_share(r)
    )
    if not ranked:
        return Finding("Ningún dominio tiene trabajadores en niveles Alto o Muy alto.")
    cutoff = _high_share(ranked[min(2, len(ranked) - 1)])
    chosen = [r for r in ranked if _high_share(r) >= cutoff]
    return _leaders(("El dominio", "Los dominios"), chosen)


def _dominio_rows(data: ReportData) -> list[DistributionRow]:
    return [d for cat in data.categoria_distribution for d in cat.children]


def levels_present(data: ReportData) -> list[str]:
    rows = [
        *filter(None, [data.final_distribution]),
        *data.categoria_distribution,
        *_dominio_rows(data),
    ]
    reached = {lvl for r in rows for lvl, n in r.counts if n}
    return [lvl for lvl in c.NDR_ORDER if lvl in reached]


def action_criteria(data: ReportData) -> list[tuple[str, str, str]]:
    return [
        (lvl, c.NDR_LABELS[lvl], cfg.action_text(lvl)) for lvl in levels_present(data)
    ]


@dataclass(frozen=True)
class Recommendation:
    level: str
    level_label: str
    text: str


def recommendations(dominio: DistributionRow) -> list[Recommendation]:
    """The matrix text for each recommended level at least one worker reached."""
    return [
        Recommendation(
            level=lvl,
            level_label=c.NDR_LABELS[lvl],
            text=RECOMMENDATIONS[dominio.key][lvl],
        )
        for lvl, n in dominio.counts
        if lvl in RECOMMENDED and n
    ]
