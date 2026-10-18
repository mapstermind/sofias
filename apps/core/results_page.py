"""What the results page draws, shaped from `apps.nom035.results.Results`.

Pairs each distribution with its statistics, picks what *Ver* selects, and
shapes the small cards. Pure Python on the results tree, so a template never
looks a row up by key. The small-group rule is already applied in `Results`: a
suppressed group has no rows here either.
"""

from dataclasses import dataclass, replace
from math import ceil

from apps.core.charts import StemChart, largest_remainder, stem_chart
from apps.nom035.results import AT_RISK, PALETTE_DOMINIO, DistributionRow, StatsRow

UNIT = ("colaborador", "colaboradores")
MAX_TICKS = 45  # participation marks across the card, however large the company


def _levels(slices) -> list[dict]:
    """One entry per level slice, in order: its name, count, share and whole percent."""
    percents = largest_remainder([s.value for s in slices])
    total = sum(s.value for s in slices)
    return [
        {
            "share": round(s.value * 100 / total, 2) if total else 0.0,
            "level": s.key,
            "label": s.label,
            "color": s.color,
            "count": s.value,
            "percent": p,
        }
        for s, p in zip(slices, percents)
    ]


@dataclass(frozen=True)
class Group:
    """The final score, a categoría or a dominio: distribution and statistics."""

    dist: DistributionRow
    stats: StatsRow
    children: tuple["Group", ...] = ()
    view_url: str = ""  # the page with this group chosen in *Ver*

    @property
    def key(self) -> str:
        return self.dist.key

    @property
    def label(self) -> str:
        return self.dist.label

    @property
    def tier(self) -> str:
        """The ndr_bar tier: dominios draw in the deeper ramp."""
        return "dominio" if self.dist.palette == PALETTE_DOMINIO else ""

    @property
    def levels(self) -> list[dict]:
        return _levels(self.dist.slices)


@dataclass(frozen=True)
class Hero:
    group: Group
    chart: StemChart


@dataclass(frozen=True)
class AreaRow:
    row: object  # ParticipationRow
    slices: tuple  # the Ver's distribution for this área; () while suppressed
    at_risk_percent: int | None
    n: int

    @property
    def levels(self) -> list[dict]:
        return _levels(self.slices)


def _pair(dist: DistributionRow, stats: StatsRow) -> Group:
    return Group(
        dist=dist,
        stats=stats,
        children=tuple(_pair(d, s) for d, s in zip(dist.children, stats.children)),
    )


def groups(results) -> tuple[Group, tuple[Group, ...]]:
    """The final score and the categorías, each distribution paired with its statistics."""
    final = _pair(results.final_distribution, results.final_stats)
    categorias = tuple(
        _pair(d, s)
        for d, s in zip(results.categoria_distribution, results.categoria_stats)
    )
    return final, categorias


def hero_for(
    results, ver: str, view_url=lambda key: ""
) -> tuple[Hero, tuple[Group, ...]]:
    """The main box and the right-hand column's groups for the chosen *Ver*.

    With the final score chosen the column lists the categorías, each carrying
    `view_url(key)`, the link that chooses it in *Ver*; with a categoría chosen
    the main box shows it and the column lists its dominios.
    """
    final, categorias = groups(results)
    categorias = tuple(replace(g, view_url=view_url(g.key)) for g in categorias)
    chosen = next((g for g in categorias if g.key == ver), None) if ver else None
    group = chosen or final
    chart = stem_chart(group.dist.slices, UNIT)
    return Hero(group=group, chart=chart), (chosen.children if chosen else categorias)


def area_rows(results, ver: str) -> list[AreaRow]:
    rows = []
    for row in results.participation:
        slices = row.slices if not ver else row.categoria_slices(ver)
        total = sum(s.value for s in slices)
        at_risk = sum(s.value for s in slices if s.key in AT_RISK)
        rows.append(
            AreaRow(
                row=row,
                slices=slices,
                at_risk_percent=round(at_risk * 100 / total) if total else None,
                n=total,
            )
        )
    return rows


def participation_card(results) -> dict:
    registered = sum(r.registered or 0 for r in results.participation)
    responded = results.size
    per_tick = max(1, ceil(registered / MAX_TICKS))
    ticks = ceil(registered / per_tick) if registered else 0
    answered = min(ticks, round(responded / per_tick))
    return {
        "registered": registered,
        "responded": responded,
        "pending": max(0, registered - responded),
        "percent": round(responded * 100 / registered) if registered else None,
        "per_tick": per_tick,
        "ticks": [i < answered for i in range(ticks)],
    }


def sex_card(results) -> list[dict]:
    """Femenino and Masculino always; Sin dato only when someone has no sex on file."""
    shown = [s for s in results.sex if s.value or s.key != "none"]
    total = sum(s.value for s in shown)
    percents = largest_remainder([s.value for s in shown])
    return [
        {
            "label": s.label,
            "value": s.value,
            "percent": p,
            "share": round(s.value * 100 / total, 2) if total else 0.0,
            "color": s.color,
        }
        for s, p in zip(shown, percents)
    ]


def age_card(results, selected=(), url_for=lambda slug, on: "") -> list[dict]:
    """One column per age band; Sin dato only when someone has no date of birth.

    Heights are shares of the tallest column, scaled to 80 % of the plot so the
    count printed above it fits. A band with an age behind it is a link:
    `url_for(slug, selected)` is the page with that band added to the filters, or
    removed when it is already in `selected`.
    """
    shown = [s for s in results.age if s.value or s.key != "none"]
    peak = max((s.value for s in shown), default=0)
    return [
        {
            "label": s.label.split("–")[0].split(" ")[0] if s.key != "none" else "—",
            "name": s.label,
            "value": s.value,
            "height": round(s.value * 80 / peak, 2) if peak else 0.0,
            "selected": s.key in selected,
            "url": url_for(s.key, s.key in selected) if s.key != "none" else "",
        }
        for s in shown
    ]


def guia1_card(results) -> dict:
    g = results.guia1
    total = g.none + g.event + g.positive
    percents = largest_remainder([s.value for s in g.slices])
    return {
        "positive": g.positive,
        "total": total,
        "slices": [
            {
                "label": s.label,
                "value": s.value,
                "percent": p,
                "share": round(s.value * 100 / total, 2) if total else 0.0,
                "color": s.color,
            }
            for s, p in zip(g.slices, percents)
        ],
    }


def with_valid_ver(query, valid_keys):
    """`query` with a `ver` the assignment's variant does not measure dropped."""
    return query if query.ver in valid_keys or not query.ver else replace(query, ver="")
