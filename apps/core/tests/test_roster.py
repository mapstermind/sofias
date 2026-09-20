"""Parsing and applying the roster's query string.

Parsing (`TestDefaults` through `TestOrder` below) needs no database. The
`TestNarrowProfiles` and `TestSortMembers` classes that follow apply a parsed
query to the database and to assembled rows, respectively.
"""

import pytest

from apps.accounts.models import UserProfile
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


@pytest.mark.django_db
class TestNarrowProfiles:
    @pytest.fixture
    def roster_company(
        self,
        make_company,
        make_area,
        make_location,
        make_user_with_profile,
        bootstrap_groups,
    ):
        company = make_company()
        produccion = make_area(company, name="Producción")
        sistemas = make_area(company, name="Sistemas")
        matriz = make_location(company, name="Matriz")
        norte = make_location(company, name="Norte")

        ana = make_user_with_profile(
            email="ana@example.com",
            company=company,
            area=produccion,
            location=matriz,
            first_name="Ana",
            paternal_last_name="Álvarez",
        )
        ana.profile.sex = UserProfile.Sex.FEMALE
        ana.profile.save()
        ana.groups.add(bootstrap_groups["Employees"])

        beto = make_user_with_profile(
            email="beto@example.com",
            company=company,
            area=sistemas,
            location=norte,
            first_name="Beto",
            paternal_last_name="Ruiz",
            is_activated=False,
        )
        beto.profile.sex = UserProfile.Sex.MALE
        beto.profile.save()
        beto.groups.add(bootstrap_groups["Principal Exec"])

        return {
            "company": company,
            "ana": ana,
            "beto": beto,
            "produccion": produccion,
            "matriz": matriz,
        }

    def _emails(self, roster_company, **params):
        query = roster.parse_roster_query(
            params,
            area_ids={roster_company["produccion"].id},
            location_ids={roster_company["matriz"].id},
        )
        qs = roster.narrow_profiles(
            UserProfile.objects.filter(company=roster_company["company"]), query
        )
        return sorted(p.user.email for p in qs)

    def test_no_query_returns_everyone(self, roster_company):
        assert self._emails(roster_company) == ["ana@example.com", "beto@example.com"]

    def test_search_matches_a_first_name(self, roster_company):
        assert self._emails(roster_company, q="ana") == ["ana@example.com"]

    def test_search_ignores_accents(self, roster_company):
        """An operator types `alvarez`; the record says `Álvarez`."""
        assert self._emails(roster_company, q="alvarez") == ["ana@example.com"]

    def test_search_matches_an_email(self, roster_company):
        assert self._emails(roster_company, q="beto@") == ["beto@example.com"]

    def test_every_term_must_match_something(self, roster_company):
        assert self._emails(roster_company, q="ana alvarez") == ["ana@example.com"]
        assert self._emails(roster_company, q="ana ruiz") == []

    def test_filters_by_sex(self, roster_company):
        assert self._emails(roster_company, sexo="femenino") == ["ana@example.com"]

    def test_filters_by_area(self, roster_company):
        area_id = str(roster_company["produccion"].id)
        assert self._emails(roster_company, area=area_id) == ["ana@example.com"]

    def test_filters_by_location(self, roster_company):
        location_id = str(roster_company["matriz"].id)
        assert self._emails(roster_company, localidad=location_id) == [
            "ana@example.com"
        ]

    def test_filters_by_role(self, roster_company):
        assert self._emails(roster_company, rol="ejecutivo-principal") == [
            "beto@example.com"
        ]

    def test_filters_combine_with_and(self, roster_company):
        assert self._emails(roster_company, q="ana", rol="ejecutivo-principal") == []

    def test_a_person_in_two_groups_is_not_duplicated(
        self, roster_company, bootstrap_groups
    ):
        roster_company["ana"].groups.add(bootstrap_groups["Admins"])

        assert self._emails(roster_company, rol="empleado") == ["ana@example.com"]


class TestSortMembers:
    def _members(self):
        return [
            {"email": "a", "is_self": False, "survey_progress": [{"percent": 80}]},
            {"email": "b", "is_self": False, "survey_progress": [{"percent": 10}]},
            {"email": "c", "is_self": True, "survey_progress": [{"percent": 50}]},
            {"email": "d", "is_self": False, "survey_progress": []},
        ]

    def test_progress_order_puts_the_least_advanced_first(self):
        ordered = roster.sort_members(self._members(), roster.ORDER_PROGRESS)

        assert [m["email"] for m in ordered] == ["c", "b", "a", "d"]

    def test_a_person_with_no_assignment_sorts_last(self):
        ordered = roster.sort_members(self._members(), roster.ORDER_PROGRESS)

        assert ordered[-1]["email"] == "d"

    def test_the_viewer_stays_first_under_every_order(self):
        for order in roster.ORDERS:
            ordered = roster.sort_members(self._members(), order)

            assert ordered[0]["email"] == "c"

    def test_name_order_leaves_the_queryset_order_alone(self):
        ordered = roster.sort_members(self._members(), roster.ORDER_NAME)

        assert [m["email"] for m in ordered] == ["c", "a", "b", "d"]
