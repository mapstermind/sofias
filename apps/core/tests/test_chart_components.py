from dataclasses import dataclass

from django.template import Context, Template
from django.test import override_settings


@dataclass
class Item:
    key: str
    label: str
    value: int
    color: str


def _render(source, **context):
    return Template("{% load charts %}" + source).render(Context(context))


def test_stacked_bar_renders_segments_with_tooltip_and_fill():
    html = _render(
        "{% stacked_bar items legend=True label='Distribución' %}",
        items=[
            Item("bajo", "Bajo", 1, "ndr-bajo"),
            Item("alto", "Alto", 3, "ndr-alto"),
        ],
    )
    assert 'data-tooltip="Alto · 3 cuestionarios · 75 %"' in html
    assert "fill-orange-500" in html
    assert 'x="25.0%"' in html
    assert "<title>" not in html
    assert "75 %" in html  # legend


@override_settings(USE_THOUSAND_SEPARATOR=True)
def test_svg_numbers_never_localized():
    html = _render(
        "{% stacked_bar items %}",
        items=[Item("a", "A", 1, "none"), Item("b", "B", 2, "none")],
    )
    assert 'width="33.333%"' in html


def test_column_chart_labels_every_column():
    html = _render(
        "{% column_chart items %}",
        items=[Item("15-19", "15–19", 2, "age"), Item("none", "Sin dato", 0, "none")],
    )
    assert "15–19" in html and "Sin dato" in html
    assert "fill-indigo-500" in html
    assert 'data-tooltip="15–19 · 2 personas"' in html


def test_range_strip_renders_bands_and_labelled_markers():
    html = _render(
        "{% range_strip bands 200 points %}",
        bands=[(100, "ndr-nulo", "Nulo"), (float("inf"), "ndr-muy_alto", "Muy alto")],
        points=[("mean", "Prom.", 84.3)],
    )
    assert "Prom. 84.3" in html
    assert 'data-tooltip="Prom.: 84.3 · Nulo"' in html
    assert "fill-red-500" in html
    assert ">200<" in html


def test_unknown_color_key_falls_back_to_gray():
    html = _render("{% stacked_bar items %}", items=[Item("a", "A", 1, "mystery")])
    assert "fill-gray-300" in html
