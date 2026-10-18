from apps.core.results_query import (
    ResultsQuery,
    filter_pills,
    parse_results_query,
    results_url,
)


def _parse(params, **ids):
    return parse_results_query(
        params,
        assignment_ids=ids.get("assignment_ids", {7}),
        area_ids=ids.get("area_ids", {1, 2}),
        location_ids=ids.get("location_ids", {5}),
    )


def test_empty_query_is_unfiltered():
    query = _parse({})
    assert query == ResultsQuery()
    assert not query.is_filtered


def test_parses_every_dimension():
    query = _parse(
        {
            "encuesta": "7",
            "sexo": "femenino",
            "edad": ["25-29", "20-24"],
            "area": ["2", "1"],
            "localidad": "5",
        }
    )
    assert query.assignment_id == 7
    assert (query.sex, query.sex_slug) == ("female", "femenino")
    assert query.age_slugs == ("20-24", "25-29")  # band order, not URL order
    assert query.area_ids == (2, 1)
    assert query.location_ids == (5,)
    assert query.is_filtered


def test_ignores_foreign_and_malformed_values():
    query = _parse(
        {
            "encuesta": "99",
            "sexo": "otro",
            "edad": ["abc", "25-29", "25-29"],
            "area": ["3", "x", "1"],
            "localidad": "6",
        }
    )
    assert query.assignment_id is None
    assert query.sex == ""
    assert query.age_slugs == ("25-29",)
    assert query.area_ids == (1,)
    assert query.location_ids == ()


def test_assignment_alone_is_not_a_filter():
    assert not _parse({"encuesta": "7"}).is_filtered


def test_results_url_round_trips_and_edits():
    query = _parse({"encuesta": "7", "sexo": "femenino", "area": ["1", "2"]})
    base = "/tablero-empresa/resultados/"
    assert results_url(base, query) == base + "?encuesta=7&sexo=femenino&area=1&area=2"
    assert (
        results_url(base, query, drop=("area", "1"))
        == base + "?encuesta=7&sexo=femenino&area=2"
    )
    assert results_url(base, query, add=("localidad", "5")).endswith("&localidad=5")
    assert results_url(base, query, add=("area", "1")).count("area=1") == 1
    assert results_url(base, ResultsQuery()) == base


def test_filter_pills_label_and_remove_one_value():
    query = _parse(
        {
            "encuesta": "7",
            "sexo": "masculino",
            "edad": "30-34",
            "area": "1",
            "localidad": "5",
        }
    )
    pills = filter_pills(
        query, "/r/", area_names={1: "Operaciones"}, location_names={5: "Matriz"}
    )
    assert [p.label for p in pills] == ["Masculino", "30–34", "Operaciones", "Matriz"]
    assert pills[2].remove_url == "/r/?encuesta=7&sexo=masculino&edad=30-34&localidad=5"


def test_ver_names_a_categoria_and_is_not_a_filter():
    query = _parse({"ver": "ambiente_de_trabajo"})
    assert query.ver == "ambiente_de_trabajo"
    assert not query.is_filtered
    assert ("ver", "ambiente_de_trabajo") in query.params()


def test_ver_ignores_an_unknown_value_and_takes_the_first_known_one():
    assert _parse({"ver": "nonsense"}).ver == ""
    assert _parse(
        {"ver": ["nonsense", "liderazgo_y_relaciones_en_el_trabajo"]}
    ).ver == ("liderazgo_y_relaciones_en_el_trabajo")


def test_urls_keep_ver():
    query = ResultsQuery(assignment_id=7, ver="ambiente_de_trabajo")
    assert results_url("/r/", query, add=("area", "2")) == (
        "/r/?encuesta=7&ver=ambiente_de_trabajo&area=2"
    )


def test_pills_name_the_dimension_they_filter():
    query = _parse({"sexo": "femenino", "edad": "25-29", "area": "1", "localidad": "5"})
    pills = filter_pills(
        query, "/r/", area_names={1: "Ventas"}, location_names={5: "Matriz"}
    )
    assert [(p.dimension, p.label) for p in pills] == [
        ("Sexo", "Femenino"),
        ("Edad", "25–29"),
        ("Área", "Ventas"),
        ("Localidad", "Matriz"),
    ]
