"""Parsing the roster's query string. No database: parsing is pure."""

from apps.core import roster


def parse(params=None, area_ids=(), location_ids=()):
    return roster.parse_roster_query(
        params or {}, area_ids=set(area_ids), location_ids=set(location_ids)
    )


class TestDefaults:
    def test_an_empty_query_string_narrows_nothing(self):
        query = parse()

        assert query.terms == ()
        assert query.sex == ""
        assert query.area_id is None
        assert query.location_id is None
        assert query.role_name == ""
        assert query.order == roster.ORDER_NAME
        assert query.is_narrowed is False


class TestSearch:
    def test_splits_on_whitespace(self):
        """`ana ruiz` must find Ana Ruiz, whose two words live in two columns."""
        assert parse({"q": "ana ruiz"}).terms == ("ana", "ruiz")

    def test_folds_case_and_accents(self):
        assert parse({"q": "ÁLVAREZ"}).terms == ("alvarez",)

    def test_keeps_the_raw_text_for_redisplay(self):
        assert parse({"q": "  Ana  "}).raw_q == "Ana"

    def test_ignores_whitespace_only_search(self):
        query = parse({"q": "   "})

        assert query.terms == ()
        assert query.is_narrowed is False

    def test_caps_the_number_of_terms(self):
        query = parse({"q": "a b c d e f g h"})

        assert len(query.terms) == roster.MAX_SEARCH_TERMS


class TestSex:
    def test_maps_the_spanish_slug_to_the_stored_value(self):
        query = parse({"sexo": "femenino"})

        assert query.sex == "female"
        assert query.sex_slug == "femenino"
        assert query.is_narrowed is True

    def test_ignores_the_stored_value_itself(self):
        """The URL speaks Spanish; `?sexo=female` is not a valid address."""
        assert parse({"sexo": "female"}).sex == ""

    def test_ignores_an_unknown_value(self):
        assert parse({"sexo": "otro"}).sex == ""


class TestCatalogs:
    def test_accepts_a_pk_belonging_to_the_company(self):
        assert parse({"area": "3"}, area_ids=[3, 7]).area_id == 3

    def test_ignores_a_pk_belonging_to_another_company(self):
        assert parse({"area": "9"}, area_ids=[3, 7]).area_id is None

    def test_ignores_a_non_numeric_pk(self):
        assert parse({"area": "produccion"}, area_ids=[3]).area_id is None

    def test_accepts_a_localidad_the_same_way(self):
        assert parse({"localidad": "7"}, location_ids=[7]).location_id == 7


class TestRole:
    def test_maps_the_slug_to_the_group_name(self):
        query = parse({"rol": "ejecutivo-principal"})

        assert query.role_name == "Principal Exec"
        assert query.role_slug == "ejecutivo-principal"

    def test_ignores_the_group_name_itself(self):
        assert parse({"rol": "Principal Exec"}).role_name == ""

    def test_ignores_an_unknown_role(self):
        assert parse({"rol": "gerente"}).role_name == ""


class TestOrder:
    def test_accepts_the_three_orders(self):
        for value in (
            roster.ORDER_NAME,
            roster.ORDER_PROGRESS,
            roster.ORDER_ACTIVATION,
        ):
            assert parse({"orden": value}).order == value

    def test_falls_back_to_name_for_an_unknown_order(self):
        assert parse({"orden": "cargo"}).order == roster.ORDER_NAME

    def test_ordering_alone_does_not_count_as_narrowing(self):
        """`Limpiar filtros` is about what is hidden, not about sequence."""
        assert parse({"orden": roster.ORDER_PROGRESS}).is_narrowed is False
