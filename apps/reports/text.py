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


def percent(count: int, n: int) -> str:
    return f"{round(count * 100 / n) if n else 0}{NBSP}%"


def _join(items: list[str]) -> str:
    return items[0] if len(items) == 1 else f"{', '.join(items[:-1])} y {items[-1]}"


def _row_percents(row: DistributionRow) -> dict[str, int]:
    """Largest-remainder percents for a row, as the charts print them."""
    levels = [lvl for lvl, _n in row.counts]
    return dict(zip(levels, largest_remainder([n for _l, n in row.counts])))


def _high_share(row: DistributionRow) -> Fraction:
    counts = dict(row.counts)
    return Fraction(sum(counts[lvl] for lvl in HIGH), row.n) if row.n else Fraction(0)


def _share_text(row: DistributionRow) -> str:
    return f"{round(_high_share(row) * 100)}{NBSP}%"


def final_sentence(row: DistributionRow) -> str:
    pct = _row_percents(row)
    low = sum(pct[lvl] for lvl in LOW)
    noun = "colaborador evaluado" if row.n == 1 else "colaboradores evaluados"
    lead = "De" if row.n == 1 else "De los"
    return (
        f"{lead} {row.n} {noun}, el {low}{NBSP}% presentó niveles de riesgo Nulo o "
        f"Bajo; el {100 - low}{NBSP}% restante, Medio, Alto o Muy alto."
    )


def categoria_sentence(rows: Sequence[DistributionRow]) -> str:
    ranked = [r for r in rows if _high_share(r) > 0]
    if not ranked:
        return "Ninguna categoría tiene trabajadores en niveles Alto o Muy alto."
    top = max(_high_share(r) for r in ranked)
    leaders = [r for r in ranked if _high_share(r) == top]
    names = _join([f"«{r.label}»" for r in leaders])
    share = _share_text(leaders[0])
    if len(leaders) == 1:
        return (
            f"La categoría {names} concentra la mayor proporción de trabajadores en "
            f"niveles Alto o Muy alto: {share}."
        )
    return (
        f"Las categorías {names} concentran la mayor proporción de trabajadores en "
        f"niveles Alto o Muy alto: {share} cada una."
    )


def dominio_sentence(rows: Sequence[DistributionRow]) -> str:
    ranked = sorted(
        (r for r in rows if _high_share(r) > 0), key=lambda r: -_high_share(r)
    )
    if not ranked:
        return "Ningún dominio tiene trabajadores en niveles Alto o Muy alto."
    cutoff = _high_share(ranked[min(2, len(ranked) - 1)])
    chosen = [r for r in ranked if _high_share(r) >= cutoff]
    names = _join([f"«{r.label}» ({_share_text(r)})" for r in chosen])
    if len(chosen) == 1:
        return (
            "El dominio con mayor proporción de trabajadores en niveles Alto o Muy "
            f"alto es {names}."
        )
    return (
        "Los dominios con mayor proporción de trabajadores en niveles Alto o Muy "
        f"alto son {names}."
    )


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
    categoria_label: str
    dominio_key: str
    dominio_label: str
    level: str
    level_label: str
    share: str
    text: str


def recommendations(data: ReportData) -> list[Recommendation]:
    out = []
    for cat in data.categoria_distribution:
        for dom in cat.children:
            pct = _row_percents(dom)
            for lvl, n in dom.counts:
                if lvl in RECOMMENDED and n:
                    out.append(
                        Recommendation(
                            categoria_label=cat.label,
                            dominio_key=dom.key,
                            dominio_label=dom.label,
                            level=lvl,
                            level_label=c.NDR_LABELS[lvl],
                            share=f"{pct[lvl]}{NBSP}%",
                            text=RECOMMENDATIONS[dom.key][lvl],
                        )
                    )
    return out
