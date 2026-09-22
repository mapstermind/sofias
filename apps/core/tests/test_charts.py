from dataclasses import dataclass

from apps.core.charts import (
    columns,
    format_number,
    largest_remainder,
    range_strip,
    stacked_segments,
)

UNIT = ("cuestionario", "cuestionarios")


@dataclass
class Item:
    key: str
    label: str
    value: int
    color: str = "c"


def test_largest_remainder_sums_to_100():
    assert largest_remainder([1, 1, 1]) == [34, 33, 33]
    assert sum(largest_remainder([7, 13, 29, 2, 0])) == 100
    assert largest_remainder([0, 0]) == [0, 0]
    assert largest_remainder([0, 5]) == [0, 100]


def test_stacked_segments_positions_and_omits_empty():
    segs = stacked_segments(
        [Item("a", "Bajo", 1), Item("b", "Medio", 0), Item("c", "Alto", 3)], UNIT
    )
    assert [s.key for s in segs] == ["a", "c"]
    assert (segs[0].x, segs[0].width) == (0.0, 25.0)
    assert (segs[1].x, segs[1].width) == (25.0, 75.0)
    assert segs[0].tooltip == "Bajo · 1 cuestionario · 25 %"
    assert segs[1].tooltip == "Alto · 3 cuestionarios · 75 %"


def test_stacked_segments_empty_when_total_zero():
    assert stacked_segments([Item("a", "A", 0)], UNIT) == []


def test_columns_scale_to_the_tallest_with_headroom():
    cols = columns(
        [Item("a", "15–19", 2), Item("b", "20–24", 4), Item("c", "Sin dato", 0)], UNIT
    )
    assert [c.height for c in cols] == [44.0, 88.0, 0.0]
    assert cols[1].y == 12.0
    assert cols[0].x < cols[0].center < cols[1].x
    assert cols[2].tooltip == "Sin dato · 0 cuestionarios"


BANDS = [
    (50, "ndr-nulo", "Nulo"),
    (75, "ndr-bajo", "Bajo"),
    (99, "ndr-medio", "Medio"),
    (140, "ndr-alto", "Alto"),
    (float("inf"), "ndr-muy_alto", "Muy alto"),
]


def test_range_strip_bands_clip_to_scale():
    strip = range_strip(BANDS, 200, [])
    assert [b.label for b in strip.bands] == [
        "Nulo",
        "Bajo",
        "Medio",
        "Alto",
        "Muy alto",
    ]
    assert strip.bands[0].x == 0.0 and strip.bands[0].width == 25.0
    assert strip.bands[-1].x == 70.0 and strip.bands[-1].width == 30.0


def test_range_strip_markers_band_and_lanes():
    points = [
        ("min", "Mín", 20),
        ("median", "Mediana", 80),
        ("mean", "Prom.", 84.3),
        ("max", "Máx", 180),
    ]
    strip = range_strip(BANDS, 200, points)
    by_key = {m.key: m for m in strip.markers}
    assert by_key["min"].band_label == "Nulo"
    assert by_key["mean"].band_label == "Medio"
    assert by_key["mean"].display == "84.3"
    assert by_key["median"].display == "80"
    # Median (40%) and mean (42.15%) are too close to share a lane.
    assert by_key["median"].lane != by_key["mean"].lane
    assert by_key["min"].lane == "above"
    assert by_key["mean"].tooltip == "Prom.: 84.3 · Medio"


def test_range_strip_anchors_labels_at_the_edges():
    strip = range_strip(BANDS, 200, [("min", "Mín", 0), ("max", "Máx", 200)])
    anchors = {m.key: m.anchor for m in strip.markers}
    assert anchors == {"min": "start", "max": "end"}


def test_range_strip_none_for_empty_scale():
    assert range_strip(BANDS, 0, []) is None


def test_format_number():
    assert format_number(81.0) == "81"
    assert format_number(81.5) == "81.5"
    assert format_number(84.25) == "84.2"
