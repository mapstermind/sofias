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


def test_stacked_bar_renders_segments_with_fill_and_no_focusable_marks():
    html = _render(
        "{% stacked_bar items legend=True label='Distribución' %}",
        items=[
            Item("bajo", "Bajo", 1, "ndr-bajo"),
            Item("alto", "Alto", 3, "ndr-alto"),
        ],
    )
    assert 'aria-label="Distribución"' in html
    assert "fill-orange-500" in html
    assert "tabindex" not in html and "data-tooltip" not in html
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
    assert 'aria-label="15–19 · 2 personas; Sin dato · 0 personas"' in html
    assert "tabindex" not in html


def test_range_strip_renders_bands_and_labelled_markers():
    html = _render(
        "{% range_strip bands 200 points %}",
        bands=[(100, "ndr-nulo", "Nulo"), (float("inf"), "ndr-muy_alto", "Muy alto")],
        points=[("mean", "Prom.", 84.3)],
    )
    assert "Prom. 84.3" in html
    assert "fill-red-500" in html
    assert ">100<" in html and ">200<" in html  # boundary and end ticks
    assert 'aria-label="Prom.: 84.3 · Nulo; Nulo: 0 a 100; Muy alto: 100 a 200"' in html
    assert "tabindex" not in html


def test_level_columns_render_every_level_with_percent_and_count():
    html = _render(
        "{% level_columns items %}",
        items=[
            Item("bajo", "Bajo", 1, "ndr-bajo"),
            Item("medio", "Medio", 0, "ndr-medio"),
            Item("alto", "Alto", 3, "ndr-alto"),
        ],
    )
    assert "repeat(3, minmax(0, 1fr))" in html
    assert html.count('class="fill-gray-300"') == 3  # a baseline for every slot
    assert html.count('rx="2"') == 2  # no bar for the empty level
    assert 'height="75.0%"' in html and "fill-orange-500" in html
    assert ">Medio<" in html and "0 %" in html
    assert '<span class="sr-only"> cuestionario</span>' in html
    assert '<span class="sr-only"> cuestionarios</span>' in html
    assert "md:sr-only" not in html
    assert "h-10" in html
    assert "tabindex" not in html and "data-tooltip" not in html


def test_level_columns_names_on_phone_only_and_size():
    html = _render(
        "{% level_columns items names='phone' size='lg' %}",
        items=[Item("bajo", "Bajo", 1, "ndr-bajo")],
    )
    assert "md:sr-only" in html
    assert "h-24" in html


def test_unknown_color_key_falls_back_to_gray():
    html = _render("{% stacked_bar items %}", items=[Item("a", "A", 1, "mystery")])
    assert "fill-gray-300" in html
