from dataclasses import dataclass

from apps.core.charts import (
    CHAR_WIDTH,
    columns,
    format_number,
    largest_remainder,
    level_columns,
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
    assert segs[0].description == "Bajo · 1 cuestionario · 25 %"
    assert segs[1].description == "Alto · 3 cuestionarios · 75 %"


def test_level_columns_keep_every_slot_on_a_fixed_scale():
    cols = level_columns(
        [Item("a", "Bajo", 1), Item("b", "Medio", 0), Item("c", "Alto", 3)], UNIT
    )
    assert [(c.key, c.value, c.percent) for c in cols] == [
        ("a", 1, 25),
        ("b", 0, 0),
        ("c", 3, 75),
    ]
    # Heights are shares of 100, not of the tallest column.
    assert [c.height for c in cols] == [25.0, 0.0, 75.0]
    assert cols[2].y == 25.0
    assert cols[0].x < cols[1].x < cols[2].x
    # Each column fills 72 % of its slot, centred.
    slot = 100 / 3
    assert cols[0].width == round(slot * 0.72, 3)
    assert cols[1].x == round(slot + slot * 0.14, 3)
    assert cols[1].description == "Medio · 0 cuestionarios · 0 %"


def test_level_columns_keep_a_tiny_share_visible():
    cols = level_columns([Item("a", "A", 1), Item("b", "B", 199)], UNIT)
    assert cols[0].height == 4.0
    assert cols[0].percent == 1


def test_level_columns_empty_total():
    cols = level_columns([Item("a", "A", 0), Item("b", "B", 0)], UNIT)
    assert [(c.height, c.percent) for c in cols] == [(0.0, 0), (0.0, 0)]


def test_stacked_segments_empty_when_total_zero():
    assert stacked_segments([Item("a", "A", 0)], UNIT) == []


def test_columns_scale_to_the_tallest_with_headroom():
    cols = columns(
        [Item("a", "15–19", 2), Item("b", "20–24", 4), Item("c", "Sin dato", 0)], UNIT
    )
    assert [c.height for c in cols] == [44.0, 88.0, 0.0]
    assert cols[1].y == 12.0
    assert cols[0].x < cols[0].center < cols[1].x
    assert cols[2].description == "Sin dato · 0 cuestionarios"


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


def test_range_strip_ticks_mark_each_band_boundary():
    strip = range_strip(BANDS, 200, [])
    assert [(t.display, t.x, t.anchor) for t in strip.ticks] == [
        ("0", 0.0, "start"),
        ("50", 25.0, "middle"),
        ("75", 37.5, "middle"),
        ("99", 49.5, "middle"),
        ("140", 70.0, "middle"),
        ("200", 100.0, "end"),
    ]
    assert strip.bands[1].description == "Bajo: 50 a 75"
    assert strip.bands[-1].description == "Muy alto: 140 a 200"


def test_range_strip_ticks_skip_boundaries_past_the_scale():
    strip = range_strip(BANDS, 60, [])
    assert [t.display for t in strip.ticks] == ["0", "50", "60"]


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
    assert by_key["mean"].description == "Prom.: 84.3 · Medio"


def _label_span(marker):
    width = len(f"{marker.label} {marker.display}") * CHAR_WIDTH
    if marker.anchor == "start":
        return marker.label_x, marker.label_x + width
    if marker.anchor == "end":
        return marker.label_x - width, marker.label_x
    return marker.label_x - width / 2, marker.label_x + width / 2


def _assert_no_lane_overlaps(strip):
    for lane in ("above", "below"):
        spans = sorted(_label_span(m) for m in strip.markers if m.lane == lane)
        for (_, right), (left, _) in zip(spans, spans[1:]):
            assert left >= right, (lane, spans)


def test_range_strip_three_close_values_keep_their_labels_apart():
    points = [
        ("min", "Mín.", 10),
        ("mean", "Prom.", 83.3),
        ("median", "Mediana", 90),
        ("max", "Máx.", 90),
    ]
    strip = range_strip(BANDS, 288, points)
    _assert_no_lane_overlaps(strip)
    by_key = {m.key: m for m in strip.markers}
    assert by_key["max"].x == by_key["median"].x  # the dots stay on their values


def test_range_strip_a_cluster_at_the_end_stays_inside_the_strip():
    points = [("a", "Prom.", 190), ("b", "Mediana", 195), ("c", "Máx.", 200)]
    strip = range_strip(BANDS, 200, points)
    _assert_no_lane_overlaps(strip)
    assert all(_label_span(m)[1] <= 100 for m in strip.markers)


def test_range_strip_an_uncrowded_label_sits_over_its_dot():
    strip = range_strip(BANDS, 200, [("mean", "Prom.", 84.3)])
    assert strip.markers[0].label_x == strip.markers[0].x


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


def test_stem_chart_scales_to_the_next_decena_above_the_largest_share():
    from apps.core.charts import stem_chart

    chart = stem_chart(
        [Item("a", "Nulo", 12), Item("b", "Bajo", 29), Item("c", "Medio", 5)], UNIT
    )
    # 12/46 = 26 %, 29/46 = 63 %, 5/46 = 11 % → the ceiling is 70.
    assert [s.percent for s in chart.stems] == [26, 63, 11]
    assert chart.ceiling == 70
    assert [g.label for g in chart.gridlines] == [f"{v} %" for v in range(10, 80, 10)]
    assert chart.gridlines[-1].bottom == 100.0
    assert chart.stems[1].height == round(29 / 46 * 100 * 100 / 70, 2)
    assert chart.peak == 1
    assert chart.stems[0].description == "Nulo · 12 cuestionarios · 26 %"


def test_stem_chart_with_nothing_counted_keeps_a_ten_percent_axis():
    from apps.core.charts import stem_chart

    chart = stem_chart([Item("a", "Nulo", 0), Item("b", "Bajo", 0)], UNIT)
    assert chart.ceiling == 10
    assert [s.height for s in chart.stems] == [0.0, 0.0]
    assert [g.label for g in chart.gridlines] == ["10 %"]


def test_stem_chart_ceiling_on_an_exact_decena_gets_no_headroom_decena():
    from apps.core.charts import stem_chart

    chart = stem_chart([Item("a", "A", 1), Item("b", "B", 1)], UNIT)
    assert chart.ceiling == 50
