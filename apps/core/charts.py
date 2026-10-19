"""Chart geometry: pure functions from plain data to positions.

Knows nothing about NOM-035 or about Tailwind. Items carry a `color` *key*;
`templatetags/charts.py` turns keys into classes. Every position is a percent
of the chart's width (or height, for columns), so an SVG scales to any width.
"""

from dataclasses import dataclass

COLUMN_HEADROOM = 88.0  # tallest column's height, leaving room for its count
CHAR_WIDTH = 1.0  # estimated % of a strip's width per marker-label character
LABEL_PAD = 1.5  # % kept clear between two marker labels sharing a lane
EDGE = 6.0  # % from either end where a label anchors to the edge
LEVEL_MIN_HEIGHT = 4.0  # % of a level column's height kept by any non-empty level


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
    description: str


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
                    description=f"{item.label} · {_count(item.value, unit)} · {percent} %",
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
    description: str


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
                description=f"{item.label} · {_count(item.value, unit)}",
            )
        )
    return out


@dataclass(frozen=True)
class LevelColumn:
    key: str
    label: str
    value: int
    percent: int
    x: float
    width: float
    y: float
    height: float
    color: str
    description: str


def level_columns(items, unit) -> list[LevelColumn]:
    """One column per item, empty ones included, on a fixed 0–100 % scale.

    Heights are the item's exact share of the total, so rows drawn with this
    function compare with each other; a non-empty item is never drawn shorter
    than LEVEL_MIN_HEIGHT.
    """
    items = list(items)
    total = sum(item.value for item in items)
    percents = largest_remainder([item.value for item in items])
    slot = 100 / len(items) if items else 0
    out = []
    for i, (item, percent) in enumerate(zip(items, percents)):
        height = item.value * 100 / total if total else 0.0
        if item.value:
            height = max(height, LEVEL_MIN_HEIGHT)
        out.append(
            LevelColumn(
                key=item.key,
                label=item.label,
                value=item.value,
                percent=percent,
                x=round(i * slot + slot * 0.14, 3),
                width=round(slot * 0.72, 3),
                y=round(100 - height, 3),
                height=round(height, 3),
                color=item.color,
                description=(
                    f"{item.label} · {_count(item.value, unit)} · {percent} %"
                ),
            )
        )
    return out


@dataclass(frozen=True)
class StripBand:
    color: str
    label: str
    x: float
    width: float
    description: str


@dataclass(frozen=True)
class Tick:
    display: str
    x: float
    anchor: str  # "start" | "middle" | "end"


@dataclass(frozen=True)
class Marker:
    key: str
    label: str
    value: float
    display: str
    x: float
    label_x: float  # where the label is drawn; differs from x when crowded aside
    lane: str  # "above" | "below"
    anchor: str  # SVG text-anchor: "start" | "middle" | "end"
    band_label: str
    description: str


@dataclass(frozen=True)
class Strip:
    bands: tuple[StripBand, ...]
    markers: tuple[Marker, ...]
    ticks: tuple[Tick, ...]
    scale_max: int


def _band_label(bands, value) -> str:
    for upper, _color, label in bands:
        if value < upper:
            return label
    return bands[-1][2]


def _label_left(x, anchor, width) -> float:
    return x if anchor == "start" else x - width if anchor == "end" else x - width / 2


def _place_labels(points):
    """Points as (x, anchor, width), ascending by x; returns (lane, label_x) each.

    Each label takes the lane where it needs the smaller shift right to clear the
    lane's previous label; a lane that then runs past the end is pushed back left.
    """
    lanes = {"above": [], "below": []}
    placed = []
    for x, anchor, width in points:

        def shift(lane, x=x, anchor=anchor, width=width):
            if not lanes[lane]:
                return 0.0
            prev_x, prev_anchor, prev_width = lanes[lane][-1]
            prev_right = _label_left(prev_x, prev_anchor, prev_width) + prev_width
            return max(0.0, prev_right + LABEL_PAD - _label_left(x, anchor, width))

        lane = min(("above", "below"), key=shift)
        label_x = x + shift(lane)
        lanes[lane].append([label_x, anchor, width])
        placed.append((lane, lanes[lane][-1]))
    for labels in lanes.values():
        limit = 100.0
        for label in reversed(labels):
            label_x, anchor, width = label
            left = _label_left(label_x, anchor, width)
            overflow = left + width - limit
            if overflow > 0:
                label[0] = label_x - overflow
                left -= overflow
            limit = left - LABEL_PAD
    return [(lane, round(label[0], 3)) for lane, label in placed]


def range_strip(bands, scale_max, points) -> Strip | None:
    """Bands as (upper_exclusive, color, label), ascending; points as (key, label, value)."""
    if scale_max <= 0:
        return None
    drawn, lower = [], 0.0
    ticks = [Tick(display="0", x=0.0, anchor="start")]
    for upper, color, label in bands:
        upper = min(upper, scale_max)
        if upper > lower:
            drawn.append(
                StripBand(
                    color=color,
                    label=label,
                    x=round(lower * 100 / scale_max, 3),
                    width=round((upper - lower) * 100 / scale_max, 3),
                    description=(
                        f"{label}: {format_number(lower)} a {format_number(upper)}"
                    ),
                )
            )
            if upper < scale_max:
                ticks.append(
                    Tick(
                        display=format_number(upper),
                        x=round(upper * 100 / scale_max, 3),
                        anchor="middle",
                    )
                )
            lower = upper
    ticks.append(Tick(display=format_number(scale_max), x=100.0, anchor="end"))

    rows = []
    for key, label, value in sorted(points, key=lambda p: p[2]):
        x = round(min(max(value, 0), scale_max) * 100 / scale_max, 3)
        display = format_number(value)
        anchor = "start" if x < EDGE else "end" if x > 100 - EDGE else "middle"
        width = len(f"{label} {display}") * CHAR_WIDTH
        rows.append((key, label, value, display, x, anchor, width))
    placements = _place_labels([(x, anchor, width) for *_, x, anchor, width in rows])
    markers = []
    for (key, label, value, display, x, anchor, _), (lane, label_x) in zip(
        rows, placements
    ):
        band_label = _band_label(bands, value)
        markers.append(
            Marker(
                key=key,
                label=label,
                value=value,
                display=display,
                x=x,
                label_x=label_x,
                lane=lane,
                anchor=anchor,
                band_label=band_label,
                description=f"{label}: {display} · {band_label}",
            )
        )
    return Strip(
        bands=tuple(drawn),
        markers=tuple(markers),
        ticks=tuple(ticks),
        scale_max=scale_max,
    )


@dataclass(frozen=True)
class Stem:
    key: str
    label: str
    value: int
    percent: int
    height: float  # % of the plot's height, on the chart's own 0–ceiling scale
    color: str
    description: str


@dataclass(frozen=True)
class Gridline:
    label: str
    bottom: float  # % of the plot's height


@dataclass(frozen=True)
class StemChart:
    ceiling: int
    gridlines: list[Gridline]
    stems: list[Stem]
    peak: int  # index of the stem with the most; where a reader starts


def stem_chart(items, unit) -> StemChart:
    """One stem per item on a 0–ceiling % scale that fits the largest share.

    The ceiling is the next multiple of 10 above the largest percent (at least
    10), so a distribution concentrated in one level is not squeezed under a
    0–100 % axis. Gridlines fall on every multiple of 10 up to it. Unlike
    `level_columns`, two charts built this way are compared by their printed
    values, not by height.
    """
    items = list(items)
    percents = largest_remainder([item.value for item in items])
    ceiling = max(10, -(-max(percents, default=0) // 10) * 10)
    stems = [
        Stem(
            key=item.key,
            label=item.label,
            value=item.value,
            percent=percent,
            height=round(
                item.value * 100 / sum(i.value for i in items) * 100 / ceiling, 2
            )
            if item.value
            else 0.0,
            color=item.color,
            description=f"{item.label} · {_count(item.value, unit)} · {percent} %",
        )
        for item, percent in zip(items, percents)
    ]
    peak = max(range(len(items)), key=lambda i: items[i].value, default=0)
    return StemChart(
        ceiling=ceiling,
        gridlines=[
            Gridline(f"{v} %", round(v * 100 / ceiling, 2))
            for v in range(10, ceiling + 1, 10)
        ],
        stems=stems,
        peak=peak,
    )
