"""Parsing and applying the roster's query string.

Parsing (`TestDefaults` through `TestOrder` below) needs no database. The
`TestNarrowProfiles` and `TestSortMembers` classes that follow apply a parsed
query to the database and to assembled rows, respectively.
"""

from urllib.parse import urlencode

import pytest
from django.http import QueryDict

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
        assert query.area_ids == ()
        assert query.location_ids == ()
        assert query.role_names == ()
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
        assert parse({"area": "3"}, area_ids=[3, 7]).area_ids == (3,)

    def test_ignores_a_pk_belonging_to_another_company(self):
        assert parse({"area": "9"}, area_ids=[3, 7]).area_ids == ()

    def test_ignores_a_non_numeric_pk(self):
        assert parse({"area": "produccion"}, area_ids=[3]).area_ids == ()

    def test_accepts_a_localidad_the_same_way(self):
        assert parse({"localidad": "7"}, location_ids=[7]).location_ids == (7,)


class TestRole:
    def test_maps_the_slug_to_the_group_name(self):
        query = parse({"rol": "ejecutivo-principal"})

        assert query.role_names == ("Principal Exec",)
        assert query.role_slugs == ("ejecutivo-principal",)

    def test_ignores_the_group_name_itself(self):
        assert parse({"rol": "Principal Exec"}).role_names == ()

    def test_ignores_an_unknown_role(self):
        assert parse({"rol": "gerente"}).role_names == ()


class TestMultiValueParsing:
    def test_repeated_area_collects_every_valid_pk(self):
        params = QueryDict("area=3&area=7")
        query = roster.parse_roster_query(params, area_ids={3, 7}, location_ids=set())
        assert query.area_ids == (3, 7)

    def test_invalid_values_are_dropped_individually(self):
        """One bad value must not discard its good neighbours."""
        params = QueryDict("area=3&area=nonsense&area=999")
        query = roster.parse_roster_query(params, area_ids={3, 7}, location_ids=set())
        assert query.area_ids == (3,)

    def test_duplicate_values_collapse(self):
        params = QueryDict("area=3&area=3")
        query = roster.parse_roster_query(params, area_ids={3}, location_ids=set())
        assert query.area_ids == (3,)

    def test_repeated_rol_collects_group_names(self):
        params = QueryDict("rol=empleado&rol=administrador")
        query = roster.parse_roster_query(params, area_ids=set(), location_ids=set())
        assert query.role_names == ("Admins", "Employees")
        assert query.role_slugs == ("administrador", "empleado")

    def test_role_order_is_declared_order_not_url_order(self):
        """The modal lists roles in declared order; echoing URL order would make
        the same selection read differently depending on click sequence."""
        params = QueryDict("rol=empleado&rol=administrador")
        query = roster.parse_roster_query(params, area_ids=set(), location_ids=set())
        assert query.role_names == ("Admins", "Employees")

    def test_sexo_stays_single_valued(self):
        """Two values means selecting both equals selecting neither, so sexo is
        single-choice; a repeated parameter keeps the first recognized value."""
        params = QueryDict("sexo=femenino&sexo=masculino")
        query = roster.parse_roster_query(params, area_ids=set(), location_ids=set())
        assert query.sex == "female"

    def test_an_unrecognized_sexo_does_not_shadow_a_valid_one(self):
        """?sexo=otro&sexo=femenino must filter by femenino, the same way a bad
        área pk is dropped without discarding the good ones beside it."""
        params = QueryDict("sexo=otro&sexo=femenino")
        query = roster.parse_roster_query(params, area_ids=set(), location_ids=set())
        assert query.sex == "female"

    def test_a_plain_dict_still_works(self):
        """The view passes a QueryDict; unit tests pass dicts. Both must parse."""
        query = roster.parse_roster_query(
            {"area": "3"}, area_ids={3}, location_ids=set()
        )
        assert query.area_ids == (3,)

    def test_no_filters_means_empty_tuples_not_none(self):
        query = roster.parse_roster_query({}, area_ids=set(), location_ids=set())
        assert query.area_ids == ()
        assert query.role_names == ()
        assert query.is_narrowed is False


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
            "sistemas": sistemas,
            "matriz": matriz,
            "norte": norte,
        }

    def _query_dict(self, params):
        """Turn a plain dict (whose values may be lists) into a `QueryDict`,
        the same shape the view hands `parse_roster_query`. A list value
        becomes a repeated parameter, matching several `<option>`s selected
        in one dimension."""
        return QueryDict(urlencode(params, doseq=True))

    def _emails(self, roster_company, **params):
        query = roster.parse_roster_query(
            self._query_dict(params),
            area_ids={roster_company["produccion"].id, roster_company["sistemas"].id},
            location_ids={roster_company["matriz"].id, roster_company["norte"].id},
        )
        qs = roster.narrow_profiles(
            UserProfile.objects.filter(company=roster_company["company"]), query
        )
        return sorted(p.user.email for p in qs)

    def _emails_in_order(self, roster_company, **params):
        """Like `_emails`, but preserves the queryset's own sequence.

        `_emails` sorts its result, which is right for the filtering tests but
        would hide an ordering bug entirely — this is for the tests that must
        observe what the database actually returned first.
        """
        query = roster.parse_roster_query(
            self._query_dict(params),
            area_ids={roster_company["produccion"].id, roster_company["sistemas"].id},
            location_ids={roster_company["matriz"].id, roster_company["norte"].id},
        )
        qs = roster.narrow_profiles(
            UserProfile.objects.filter(company=roster_company["company"]), query
        )
        return [p.user.email for p in qs]

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

    def test_two_areas_are_or_ed_within_the_dimension(self, roster_company):
        area_ids = [
            str(roster_company["produccion"].id),
            str(roster_company["sistemas"].id),
        ]
        assert self._emails(roster_company, area=area_ids) == [
            "ana@example.com",
            "beto@example.com",
        ]

    def test_dimensions_are_and_ed(self, roster_company):
        """área in (Producción, Sistemas) AND rol=empleado narrows to Ana."""
        area_ids = [
            str(roster_company["produccion"].id),
            str(roster_company["sistemas"].id),
        ]
        assert self._emails(roster_company, area=area_ids, rol="empleado") == [
            "ana@example.com"
        ]

    def test_a_person_in_two_groups_is_not_duplicated(
        self, roster_company, bootstrap_groups
    ):
        roster_company["ana"].groups.add(bootstrap_groups["Admins"])

        assert self._emails(roster_company, rol="empleado") == ["ana@example.com"]

    def test_a_person_in_two_selected_roles_appears_once(
        self, roster_company, bootstrap_groups
    ):
        """`__in` over an M2M duplicates rows without `.distinct()`; a
        colaborador must never appear twice on a roster."""
        roster_company["ana"].groups.add(bootstrap_groups["Admins"])
        emails = self._emails(roster_company, rol=["empleado", "administrador"])
        assert emails == ["ana@example.com"]
        assert len(emails) == len(set(emails))

    def test_orden_activacion_puts_the_unactivated_person_first(self, roster_company):
        """Ana (Álvarez) has activated; Beto (Ruiz) has not. Name order would
        put Ana first, so this only passes if activation, not name, decided
        the sequence — a flipped `is_activated` sort would return the reverse."""
        assert self._emails_in_order(roster_company, orden=roster.ORDER_ACTIVATION) == [
            "beto@example.com",
            "ana@example.com",
        ]

    def test_orden_nombre_orders_by_paternal_surname(self, roster_company):
        """The same two people, in apellido-paterno order: Álvarez before Ruiz —
        the reverse of the activation order above."""
        assert self._emails_in_order(roster_company, orden=roster.ORDER_NAME) == [
            "ana@example.com",
            "beto@example.com",
        ]


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

    def test_the_viewer_stays_first_even_after_the_progress_resort(self):
        """`sort_members` only branches on progreso; nombre and activación are
        both plain pass-throughs here (activación's own ordering happens in the
        database query, not in this function), so looping over all three
        `ORDERS` would assert the identical fact three times. Progreso is the
        one case where the pin has to win against a resort that already ran,
        and `test_name_order_leaves_the_queryset_order_alone` below already
        pins down the pass-through branch by asserting the full sequence."""
        ordered = roster.sort_members(self._members(), roster.ORDER_PROGRESS)

        assert ordered[0]["email"] == "c"

    def test_name_order_leaves_the_queryset_order_alone(self):
        ordered = roster.sort_members(self._members(), roster.ORDER_NAME)

        assert [m["email"] for m in ordered] == ["c", "a", "b", "d"]
