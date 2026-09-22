"""Chart geometry: pure functions from plain data to positions.

Knows nothing about NOM-035 or about Tailwind. Items carry a `color` *key*;
`templatetags/charts.py` turns keys into classes. Every position is a percent
of the chart's width (or height, for columns), so an SVG scales to any width.
"""

from dataclasses import dataclass

COLUMN_HEADROOM = 88.0  # tallest column's height, leaving room for its count
LABEL_GAP = 9.0  # minimum % between two marker labels sharing a lane
EDGE = 6.0  # % from either end where a label anchors to the edge


def format_number(value: float) -> str:
    rounded = round(value, 1)
    return str(int(rounded)) if rounded == int(rounded) else f"{rounded:.1f}"


def _count(value: int, unit: tuple[str, str]) -> str:
    return f"{value} {unit[0] if value == 1 else unit[1]}"


def largest_remainder(values: list[int]) -> list[int]:
    """Whole percents that always add up to 100 (or all 0 when nothing counted)."""
    total = sum(values)
    if not total:
        return [0] * len(values)
    raw = [v * 100 / total for v in values]
    floors = [int(r) for r in raw]
    short = 100 - sum(floors)
    order = sorted(range(len(values)), key=lambda i: (-(raw[i] - floors[i]), i))
    for i in order[:short]:
        floors[i] += 1
    return floors


@dataclass(frozen=True)
class Segment:
    key: str
    label: str
    value: int
    percent: int
    x: float
    width: float
    color: str
    tooltip: str


def stacked_segments(items, unit) -> list[Segment]:
    items = list(items)
    total = sum(item.value for item in items)
    if not total:
        return []
    percents = largest_remainder([item.value for item in items])
    segments, x = [], 0.0
    for item, percent in zip(items, percents):
        width = item.value * 100 / total
        if item.value:
            segments.append(
                Segment(
                    key=item.key,
                    label=item.label,
                    value=item.value,
                    percent=percent,
                    x=round(x, 3),
                    width=round(width, 3),
                    color=item.color,
                    tooltip=f"{item.label} · {_count(item.value, unit)} · {percent} %",
                )
            )
        x += width
    return segments


@dataclass(frozen=True)
class Column:
    key: str
    label: str
    value: int
    x: float
    width: float
    center: float
    y: float
    height: float
    color: str
    tooltip: str


def columns(items, unit) -> list[Column]:
    items = list(items)
    peak = max((item.value for item in items), default=0)
    slot = 100 / len(items) if items else 0
    out = []
    for i, item in enumerate(items):
        height = round(item.value * COLUMN_HEADROOM / peak, 3) if peak else 0.0
        out.append(
            Column(
                key=item.key,
                label=item.label,
                value=item.value,
                x=round(i * slot + slot * 0.15, 3),
                width=round(slot * 0.7, 3),
                center=round(i * slot + slot / 2, 3),
                y=round(100 - height, 3),
                height=height,
                color=item.color,
                tooltip=f"{item.label} · {_count(item.value, unit)}",
            )
        )
    return out


@dataclass(frozen=True)
class StripBand:
    color: str
    label: str
    x: float
    width: float


@dataclass(frozen=True)
class Marker:
    key: str
    label: str
    value: float
    display: str
    x: float
    lane: str  # "above" | "below"
    anchor: str  # SVG text-anchor: "start" | "middle" | "end"
    band_label: str
    tooltip: str


@dataclass(frozen=True)
class Strip:
    bands: tuple[StripBand, ...]
    markers: tuple[Marker, ...]
    scale_max: int


def _band_label(bands, value) -> str:
    for upper, _color, label in bands:
        if value < upper:
            return label
    return bands[-1][2]


def range_strip(bands, scale_max, points) -> Strip | None:
    """Bands as (upper_exclusive, color, label), ascending; points as (key, label, value)."""
    if scale_max <= 0:
        return None
    drawn, lower = [], 0.0
    for upper, color, label in bands:
        upper = min(upper, scale_max)
        if upper > lower:
            drawn.append(
                StripBand(
                    color=color,
                    label=label,
                    x=round(lower * 100 / scale_max, 3),
                    width=round((upper - lower) * 100 / scale_max, 3),
                )
            )
            lower = upper

    last = {"above": None, "below": None}
    markers = []
    for key, label, value in sorted(points, key=lambda p: p[2]):
        x = round(min(max(value, 0), scale_max) * 100 / scale_max, 3)
        if last["above"] is None or x - last["above"] >= LABEL_GAP:
            lane = "above"
        elif last["below"] is None or x - last["below"] >= LABEL_GAP:
            lane = "below"
        else:
            lane = "above" if x - last["above"] >= x - last["below"] else "below"
        last[lane] = x
        display = format_number(value)
        band_label = _band_label(bands, value)
        markers.append(
            Marker(
                key=key,
                label=label,
                value=value,
                display=display,
                x=x,
                lane=lane,
                anchor="start" if x < EDGE else "end" if x > 100 - EDGE else "middle",
                band_label=band_label,
                tooltip=f"{label}: {display} · {band_label}",
            )
        )
    return Strip(bands=tuple(drawn), markers=tuple(markers), scale_max=scale_max)
