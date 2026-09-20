# Employee Roster Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Give the colaborador roster a search box, four filters, three sorts and a decluttered card, and make each person's authorization role visible in Spanish in both the app and the Django admin.

**Architecture:** The four group names, their Spanish labels and their URL slugs move into `apps/accounts/roles.py`, which `bootstrap_groups`, the admin and the roster all import. Roster filtering is server-side: a new `apps/core/roster.py` parses the query string into a frozen `RosterQuery` and applies it to the profile queryset before the existing per-member progress loop runs, so the page's N+1-free prefetch pattern is untouched. The template is rewritten around one metadata line per card instead of four pills.

**Tech Stack:** Django 6.0, PostgreSQL 17, pytest + pytest-django, TailwindCSS v4 (`npm run build:css`). No JavaScript is added.

**Spec:** [`docs/platform/employee-roster.md`](../employee-roster.md)

## What changes

The roster page gains search, filtering and sorting; every person's authorization
role becomes visible in Spanish in the app and in the Django admin; the roster
card drops from five badges to one; and the app's Spanish copy settles on
*colaborador* for a person, reserving *empleado* for the `Employees` role, which
renames the roster URLs to `/colaboradores/`.

This is a new feature doc — `docs/platform/employee-roster.md`, which no previous
doc covered. It makes a statement wrong in six other documents; the last task
corrects all six. It touches no ADR decision, so no ADR is written and none is
superseded.

## Global Constraints

- **Spanish UI, English code.** Every string a user sees is Spanish; identifiers, comments and docstrings stay English. `CompanyEmployeeListView`, `can_manage_employees` and `employee_id` keep their names.
- **Vocabulary.** A person on the roster is a *colaborador*. *Empleado* names the `Employees` role and nothing else.
- **Role labels are presentation only.** `auth.Group.name` keeps `Admins`, `Principal Exec`, `Secondary Exec`, `Employees`. Nothing in this plan renames a group or touches the CSV importer's `group` column.
- **Parameter values a human reads are Spanish** (`sexo`, `rol`, `orden`); `area` and `localidad` are numeric pks.
- **An unrecognized parameter value is ignored**, never raised on.
- **No migration.** If `makemigrations --check` reports one, something went wrong.
- **Preserve the N+1 pattern.** The company-wide answer and module prefetches in `CompanyEmployeeListView` stay as they are; filtering narrows the profile queryset *before* the per-member loop.
- **Tailwind compiles only what it finds** in the sources listed in `static/css/main.css`. Any new class needs `npm run build:css` and the regenerated `static/css/output.css` committed.
- Run `ruff format .` and `ruff check .` before each commit. The suite is `pytest` (`--reuse-db -x`).

---

### Task 1: The canonical role definitions

**Files:**
- Create: `apps/accounts/roles.py`
- Test: `apps/accounts/tests/test_roles.py`

**Interfaces:**
- Consumes: nothing.
- Produces: `RoleDefinition` (frozen dataclass with `.name`, `.label`, `.slug`), `ROLES: tuple[RoleDefinition, ...]` in display order, `ROLE_NAMES: tuple[str, ...]`, `role_for_slug(slug) -> RoleDefinition | None`, `label_for_name(name) -> str | None`, `labels_for_names(names) -> list[str]` (declared order, unknown names dropped).

The module is named `roles.py` and its dataclass `RoleDefinition` deliberately: `accounts.models.Role` already exists as the unmanaged sentinel that hosts the custom permissions, and the two must not be confused. `Role` is where permissions live; `roles.py` is where the four groups that bundle them are named.

- [x] **Step 1: Write the failing test**

```python
# apps/accounts/tests/test_roles.py
"""The canonical four authorization groups and their Spanish labels."""

from apps.accounts import roles


class TestRoleDefinitions:
    def test_declares_the_four_groups_in_display_order(self):
        assert roles.ROLE_NAMES == (
            "Admins",
            "Principal Exec",
            "Secondary Exec",
            "Employees",
        )

    def test_labels_are_spanish_and_singular(self):
        assert [r.label for r in roles.ROLES] == [
            "Administrador",
            "Ejecutivo principal",
            "Ejecutivo secundario",
            "Empleado",
        ]

    def test_employees_is_empleado_not_colaborador(self):
        """`colaborador` is the word for a person on the roster, whatever their
        role, so it cannot also name one of the four roles."""
        assert roles.label_for_name("Employees") == "Empleado"

    def test_slugs_are_url_safe_spanish(self):
        assert [r.slug for r in roles.ROLES] == [
            "administrador",
            "ejecutivo-principal",
            "ejecutivo-secundario",
            "empleado",
        ]

    def test_role_for_slug_finds_a_role(self):
        assert roles.role_for_slug("ejecutivo-principal").name == "Principal Exec"

    def test_role_for_slug_returns_none_for_an_unknown_slug(self):
        assert roles.role_for_slug("gerente") is None
        assert roles.role_for_slug("") is None

    def test_label_for_name_returns_none_for_an_unknown_group(self):
        """A group created by hand in the admin has no label to show."""
        assert roles.label_for_name("Auditores") is None

    def test_labels_for_names_uses_declared_order_not_argument_order(self):
        labels = roles.labels_for_names(["Employees", "Admins"])
        assert labels == ["Administrador", "Empleado"]

    def test_labels_for_names_drops_unknown_groups(self):
        assert roles.labels_for_names(["Auditores", "Employees"]) == ["Empleado"]
```

- [x] **Step 2: Run the test to verify it fails**

Run: `pytest apps/accounts/tests/test_roles.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'apps.accounts.roles'`

- [x] **Step 3: Write the implementation**

```python
# apps/accounts/roles.py
"""The four authorization groups, named once.

`auth.Group.name` is the stored lookup key and stays English: it is matched by
string in several places and is an accepted value of the CSV importer's `group`
column, so renaming it is a behavior change rather than a presentation one (see
`docs/internal/open-findings.md` #1). What is Spanish is the label shown to a
user.

Not to be confused with `accounts.models.Role`, the unmanaged sentinel model
that hosts the project's custom permissions. That is where a permission is
declared; this is where the groups that bundle them are named.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class RoleDefinition:
    name: str
    """`auth.Group.name` — the stored value, matched by string."""

    label: str
    """What a user reads. Singular, because it names one person's role."""

    slug: str
    """The value this role takes in a URL's `rol` parameter."""


# Declaration order is display order: most authority first.
ROLES: tuple[RoleDefinition, ...] = (
    RoleDefinition("Admins", "Administrador", "administrador"),
    RoleDefinition("Principal Exec", "Ejecutivo principal", "ejecutivo-principal"),
    RoleDefinition("Secondary Exec", "Ejecutivo secundario", "ejecutivo-secundario"),
    RoleDefinition("Employees", "Empleado", "empleado"),
)

ROLE_NAMES: tuple[str, ...] = tuple(role.name for role in ROLES)

_BY_NAME = {role.name: role for role in ROLES}
_BY_SLUG = {role.slug: role for role in ROLES}


def role_for_slug(slug: str) -> RoleDefinition | None:
    """The role a URL's `rol` value names, or None if it names none."""
    return _BY_SLUG.get(slug)


def label_for_name(name: str) -> str | None:
    """The Spanish label for a group name, or None for a group we did not create."""
    role = _BY_NAME.get(name)
    return role.label if role else None


def labels_for_names(names) -> list[str]:
    """Labels for the given group names, in declared order, unknown ones dropped."""
    wanted = set(names)
    return [role.label for role in ROLES if role.name in wanted]
```

- [x] **Step 4: Run the test to verify it passes**

Run: `pytest apps/accounts/tests/test_roles.py -v`
Expected: PASS, 9 tests.

- [x] **Step 5: Commit**

```bash
ruff format . && ruff check .
git add apps/accounts/roles.py apps/accounts/tests/test_roles.py
git commit -m "feat(accounts): name the four authorization groups in one place"
```

---

### Task 2: Wire the canonical names into bootstrap_groups and the test fixture

**Files:**
- Modify: `apps/accounts/management/commands/bootstrap_groups.py`
- Modify: `conftest.py:8-50` (the `bootstrap_groups` fixture)
- Test: `apps/accounts/tests/test_roles.py` (extend)

**Interfaces:**
- Consumes: `ROLE_NAMES` from Task 1.
- Produces: `GROUP_PERMISSIONS` keyed by `ROLE_NAMES`, importable by `conftest.py`.

The fixture currently retypes the whole permission map. Importing it removes the third place a permission has to be added, which is the point of Task 1 — the canonical list exists once.

- [x] **Step 1: Write the failing test**

Append to `apps/accounts/tests/test_roles.py`:

```python
class TestCanonicalNamesAreUsedEverywhere:
    def test_bootstrap_groups_is_keyed_by_the_canonical_names(self):
        """The command must not retype the names it creates."""
        from apps.accounts.management.commands.bootstrap_groups import (
            GROUP_PERMISSIONS,
        )

        assert tuple(GROUP_PERMISSIONS) == roles.ROLE_NAMES

    def test_the_test_fixture_creates_exactly_those_groups(self, bootstrap_groups):
        """A fixture that drifts from the command tests a system nobody runs."""
        assert set(bootstrap_groups) == set(roles.ROLE_NAMES)
```

- [x] **Step 2: Run the test to verify it fails**

Run: `pytest apps/accounts/tests/test_roles.py::TestCanonicalNamesAreUsedEverywhere -v`
Expected: FAIL — `GROUP_PERMISSIONS` is a plain dict literal whose key order is not asserted against `ROLE_NAMES`; the first test fails only if the order or set differs, so confirm it fails by temporarily reordering. If it passes as written, still complete Steps 3–4: the value is that the two can no longer drift.

- [x] **Step 3: Write the implementation**

In `bootstrap_groups.py`, replace the dict literal's bare string keys with the canonical constants:

```python
from django.contrib.auth.models import Group, Permission
from django.core.management.base import BaseCommand

from apps.accounts.roles import ROLES

# Maps each group name to the permission codenames it should hold. The names
# come from `apps.accounts.roles` so this command and the app agree on them.
GROUP_PERMISSIONS: dict[str, list[str]] = {
    ROLES[0].name: [  # Administrador
        "can_manage_surveys",
        "can_view_dashboard",
        "can_view_insights",
        "can_manage_employees",
        "can_view_submissions",
    ],
    ROLES[1].name: [  # Ejecutivo principal
        "can_view_dashboard",
        "can_view_insights",
        "can_manage_employees",
        "can_take_assigned_surveys",
    ],
    ROLES[2].name: [  # Ejecutivo secundario
        "can_view_dashboard",
        "can_manage_employees",
        "can_take_assigned_surveys",
    ],
    ROLES[3].name: [  # Empleado
        "can_take_assigned_surveys",
    ],
}
```

The rest of the command is unchanged.

In `conftest.py`, replace the fixture's duplicated map with an import:

```python
@pytest.fixture
def bootstrap_groups(db):
    """
    Create the four authorization groups with their permissions.
    Required by verify_otp, which calls Group.objects.get(name="Employees").
    Declare this fixture explicitly on any test that exercises that flow.

    The permission map is imported rather than retyped, so a new permission is
    declared in two places (`Role.Meta.permissions` and `GROUP_PERMISSIONS`)
    and the fixture follows automatically.
    """
    from apps.accounts.management.commands.bootstrap_groups import GROUP_PERMISSIONS

    codenames = [c for names in GROUP_PERMISSIONS.values() for c in names]
    perms = {p.codename: p for p in Permission.objects.filter(codename__in=codenames)}

    groups = {}
    for name, cnames in GROUP_PERMISSIONS.items():
        g, _ = Group.objects.get_or_create(name=name)
        g.permissions.set([perms[c] for c in cnames if c in perms])
        groups[name] = g
    return groups
```

- [x] **Step 4: Run the whole suite**

Run: `pytest`
Expected: PASS. The fixture feeds many tests, so a regression here surfaces immediately.

- [x] **Step 5: Commit**

```bash
ruff format . && ruff check .
git add apps/accounts/management/commands/bootstrap_groups.py conftest.py apps/accounts/tests/test_roles.py
git commit -m "refactor(accounts): source group names and permissions from one map"
```

---

### Task 3: Rol in the Django admin

**Files:**
- Modify: `apps/accounts/admin.py:28-77` (`CustomUserAdmin`)
- Test: `apps/accounts/tests/test_admin.py`

**Interfaces:**
- Consumes: `labels_for_names` from Task 1.
- Produces: `CustomUserAdmin.role_labels(obj) -> str`.

- [x] **Step 1: Write the failing test**

Create or extend `apps/accounts/tests/test_admin.py`:

```python
"""The Usuarios changelist shows each account's authorization role in Spanish."""

import pytest

from apps.accounts.admin import CustomUserAdmin


@pytest.mark.django_db
class TestUserAdminRoleColumn:
    def test_column_is_declared(self):
        assert "role_labels" in CustomUserAdmin.list_display

    def test_filter_by_group_is_declared(self):
        assert "groups" in CustomUserAdmin.list_filter

    def test_shows_the_spanish_label(self, make_user, bootstrap_groups):
        user = make_user(email="exec@example.com")
        user.groups.add(bootstrap_groups["Principal Exec"])

        assert CustomUserAdmin.role_labels(None, user) == "Ejecutivo principal"

    def test_joins_several_roles_in_declared_order(self, make_user, bootstrap_groups):
        user = make_user(email="both@example.com")
        user.groups.add(bootstrap_groups["Employees"], bootstrap_groups["Admins"])

        assert CustomUserAdmin.role_labels(None, user) == "Administrador, Empleado"

    def test_shows_a_dash_when_the_account_has_no_role(self, make_user):
        user = make_user(email="orphan@example.com")

        assert CustomUserAdmin.role_labels(None, user) == "—"

    def test_changelist_renders_the_label(self, staff_client, make_user, bootstrap_groups):
        user = make_user(email="exec2@example.com")
        user.groups.add(bootstrap_groups["Principal Exec"])

        response = staff_client.get("/admin/accounts/user/")

        assert response.status_code == 200
        assert "Ejecutivo principal".encode() in response.content
```

- [x] **Step 2: Run the test to verify it fails**

Run: `pytest apps/accounts/tests/test_admin.py -v`
Expected: FAIL — `role_labels` is not an attribute of `CustomUserAdmin`.

- [x] **Step 3: Write the implementation**

In `apps/accounts/admin.py`, add the import and the column. `list_display` is declared in full already — add `role_labels` to it, and add a `list_filter`:

```python
from .roles import labels_for_names
```

```python
    list_display = (
        "username",
        "email",
        "first_name",
        "paternal_last_name",
        "maternal_last_name",
        "role_labels",
        "is_staff",
        "must_change_password",
    )
    # Declared in full, like list_display above: an explicit tuple REPLACES
    # UserAdmin's default, so every filter the admin had must be named here.
    list_filter = ("groups", "is_staff", "is_superuser", "is_active")

    def get_queryset(self, request):
        # The Rol column reads every account's groups; without this the
        # changelist runs one query per row.
        return super().get_queryset(request).prefetch_related("groups")

    @admin.display(description="rol")
    def role_labels(self, obj):
        """The Spanish labels of the groups this account belongs to."""
        labels = labels_for_names(g.name for g in obj.groups.all())
        return ", ".join(labels) if labels else "—"
```

`@admin.display(description="rol")` is what keeps the column header Spanish; without it Django derives *Role labels* from the method name.

- [x] **Step 4: Run the tests to verify they pass**

Run: `pytest apps/accounts/tests/test_admin.py -v && python manage.py check`
Expected: PASS, and `check` reports no issues.

- [x] **Step 5: Commit**

```bash
ruff format . && ruff check .
git add apps/accounts/admin.py apps/accounts/tests/test_admin.py
git commit -m "feat(accounts): show each account's rol on the Usuarios changelist"
```

---

### Task 4: Parse the roster's query string

**Files:**
- Create: `apps/core/roster.py`
- Test: `apps/core/tests/test_roster.py`

**Interfaces:**
- Consumes: `role_for_slug` from Task 1.
- Produces: `RosterQuery` (frozen dataclass: `terms: tuple[str, ...]`, `raw_q: str`, `sex: str`, `sex_slug: str`, `area_id: int | None`, `location_id: int | None`, `role_name: str`, `role_slug: str`, `order: str`, property `is_narrowed: bool`), `parse_roster_query(params, *, area_ids, location_ids) -> RosterQuery`, and the constants `ORDER_NAME = "nombre"`, `ORDER_PROGRESS = "progreso"`, `ORDER_ACTIVATION = "activacion"`, `SEX_SLUGS`, `MAX_SEARCH_TERMS = 5`.

`parse_roster_query` touches no database: it is handed the sets of valid área and localidad pks. That is what lets every parsing rule be tested without fixtures, and it is what enforces the spec's rule that a catalog entry from another company is ignored.

- [x] **Step 1: Write the failing test**

```python
# apps/core/tests/test_roster.py
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
        for value in (roster.ORDER_NAME, roster.ORDER_PROGRESS, roster.ORDER_ACTIVATION):
            assert parse({"orden": value}).order == value

    def test_falls_back_to_name_for_an_unknown_order(self):
        assert parse({"orden": "cargo"}).order == roster.ORDER_NAME

    def test_ordering_alone_does_not_count_as_narrowing(self):
        """`Limpiar filtros` is about what is hidden, not about sequence."""
        assert parse({"orden": roster.ORDER_PROGRESS}).is_narrowed is False
```

- [x] **Step 2: Run the test to verify it fails**

Run: `pytest apps/core/tests/test_roster.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'apps.core.roster'`

- [x] **Step 3: Write the implementation**

```python
# apps/core/roster.py
"""Search, filtering and ordering for the colaborador roster.

Parsing is separated from the view and from the database so every rule below is
testable on its own: `parse_roster_query` is handed the pks that exist for the
company being viewed rather than looking them up.

The spec's rule is that a parameter which is absent, empty, unrecognized, or
names a catalog entry from another company is ignored and the roster renders as
though it had not been given. A URL is not a form: there is no field for the
person to correct, so there is nothing useful to raise at them.
"""

from dataclasses import dataclass, field

from apps.accounts.models import catalog_name_key
from apps.accounts.roles import role_for_slug

ORDER_NAME = "nombre"
ORDER_PROGRESS = "progreso"
ORDER_ACTIVATION = "activacion"
ORDERS = (ORDER_NAME, ORDER_PROGRESS, ORDER_ACTIVATION)

# The URL speaks Spanish; these map onto `UserProfile.Sex` values.
SEX_SLUGS = {"masculino": "male", "femenino": "female"}

# A search is a convenience, not a query language. More terms than this is a
# paste accident, and each one costs four LIKEs.
MAX_SEARCH_TERMS = 5


@dataclass(frozen=True)
class RosterQuery:
    """What the query string asked for, already validated."""

    raw_q: str = ""
    terms: tuple[str, ...] = ()
    sex: str = ""
    sex_slug: str = ""
    area_id: int | None = None
    location_id: int | None = None
    role_name: str = ""
    role_slug: str = ""
    order: str = ORDER_NAME

    @property
    def is_narrowed(self) -> bool:
        """Whether anything is being hidden. Ordering is not narrowing."""
        return bool(
            self.terms
            or self.sex
            or self.area_id is not None
            or self.location_id is not None
            or self.role_name
        )


def _valid_pk(raw: str, valid_ids: set[int]) -> int | None:
    try:
        pk = int(raw)
    except (TypeError, ValueError):
        return None
    return pk if pk in valid_ids else None


def parse_roster_query(params, *, area_ids: set[int], location_ids: set[int]):
    """Turn a request's GET parameters into a validated `RosterQuery`."""
    raw_q = (params.get("q") or "").strip()
    terms = tuple(
        catalog_name_key(term) for term in raw_q.split()[:MAX_SEARCH_TERMS]
    )

    sex_slug = (params.get("sexo") or "").strip()
    sex = SEX_SLUGS.get(sex_slug, "")
    if not sex:
        sex_slug = ""

    role = role_for_slug((params.get("rol") or "").strip())

    order = (params.get("orden") or "").strip()
    if order not in ORDERS:
        order = ORDER_NAME

    return RosterQuery(
        raw_q=raw_q,
        terms=terms,
        sex=sex,
        sex_slug=sex_slug,
        area_id=_valid_pk(params.get("area"), area_ids),
        location_id=_valid_pk(params.get("localidad"), location_ids),
        role_name=role.name if role else "",
        role_slug=role.slug if role else "",
        order=order,
    )
```

Delete the unused `field` import if ruff flags it.

- [x] **Step 4: Run the tests to verify they pass**

Run: `pytest apps/core/tests/test_roster.py -v`
Expected: PASS, 19 tests.

- [x] **Step 5: Commit**

```bash
ruff format . && ruff check .
git add apps/core/roster.py apps/core/tests/test_roster.py
git commit -m "feat(core): parse the roster's search, filter and sort parameters"
```

---

### Task 5: Apply the query to the roster queryset

**Files:**
- Modify: `apps/core/roster.py`
- Test: `apps/core/tests/test_roster.py` (extend)

**Interfaces:**
- Consumes: `RosterQuery` from Task 4.
- Produces: `narrow_profiles(queryset, query) -> QuerySet` and `sort_members(members, order) -> list`.

Accent-insensitive search reuses `FoldCatalogName` from `apps/accounts/models.py` — the expression the área and localidad catalogs already use for uniqueness. Postgres' own `unaccent()` is only STABLE and would add an extension for a rule this project has already written once.

- [x] **Step 1: Write the failing test**

Append to `apps/core/tests/test_roster.py`:

```python
import pytest

from apps.accounts.models import UserProfile


@pytest.mark.django_db
class TestNarrowProfiles:
    @pytest.fixture
    def roster_company(self, make_company, make_area, make_location, make_user_with_profile, bootstrap_groups):
        company = make_company()
        produccion = make_area(company, name="Producción")
        sistemas = make_area(company, name="Sistemas")
        matriz = make_location(company, name="Matriz")
        norte = make_location(company, name="Norte")

        ana = make_user_with_profile(
            email="ana@example.com", company=company, area=produccion, location=matriz,
            first_name="Ana", paternal_last_name="Álvarez",
        )
        ana.profile.sex = UserProfile.Sex.FEMALE
        ana.profile.save()
        ana.groups.add(bootstrap_groups["Employees"])

        beto = make_user_with_profile(
            email="beto@example.com", company=company, area=sistemas, location=norte,
            first_name="Beto", paternal_last_name="Ruiz", is_activated=False,
        )
        beto.profile.sex = UserProfile.Sex.MALE
        beto.profile.save()
        beto.groups.add(bootstrap_groups["Principal Exec"])

        return {"company": company, "ana": ana, "beto": beto,
                "produccion": produccion, "matriz": matriz}

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
        assert self._emails(roster_company, localidad=location_id) == ["ana@example.com"]

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
```

- [x] **Step 2: Run the test to verify it fails**

Run: `pytest apps/core/tests/test_roster.py -v`
Expected: FAIL — `AttributeError: module 'apps.core.roster' has no attribute 'narrow_profiles'`

- [x] **Step 3: Write the implementation**

Add to `apps/core/roster.py`:

```python
from django.db.models import Q

from apps.accounts.models import FoldCatalogName
```

```python
# The columns a search term may match, folded the way the catalogs fold theirs.
_SEARCH_FIELDS = (
    "user__first_name",
    "user__paternal_last_name",
    "user__maternal_last_name",
    "user__email",
)


def narrow_profiles(queryset, query: RosterQuery):
    """Apply a `RosterQuery`'s search and filters to a profile queryset.

    Ordering by name and by activation happens here too; ordering by progress
    cannot, because the percentage is computed per member after the fact.
    """
    if query.terms:
        queryset = queryset.annotate(
            **{
                f"fold_{i}": FoldCatalogName(path)
                for i, path in enumerate(_SEARCH_FIELDS)
            }
        )
        for term in query.terms:
            matches = Q()
            for i in range(len(_SEARCH_FIELDS)):
                matches |= Q(**{f"fold_{i}__contains": term})
            queryset = queryset.filter(matches)

    if query.sex:
        queryset = queryset.filter(sex=query.sex)
    if query.area_id is not None:
        queryset = queryset.filter(area_id=query.area_id)
    if query.location_id is not None:
        queryset = queryset.filter(location_id=query.location_id)
    if query.role_name:
        # At most one group matches a given name, so this cannot duplicate a row.
        queryset = queryset.filter(user__groups__name=query.role_name)

    # Paternal surname first: that is how a Mexican roster reads, and it is the
    # tie-breaker under every other order.
    by_name = (
        "user__paternal_last_name",
        "user__maternal_last_name",
        "user__first_name",
    )
    if query.order == ORDER_ACTIVATION:
        # Postgres sorts false below true, so the unactivated come first.
        return queryset.order_by("is_activated", *by_name)
    return queryset.order_by(*by_name)


def _first_percent(member) -> tuple[int, int]:
    """Sort key: people with no assignment go last, otherwise least advanced first."""
    progress = member["survey_progress"]
    if not progress:
        return (1, 0)
    return (0, progress[0]["percent"])


def sort_members(members: list, order: str) -> list:
    """Order the assembled member rows, pinning the viewer to the top.

    The queryset already carries name and activation order; only progress needs
    the computed percentage, which exists only once the rows are built.
    """
    ordered = list(members)
    if order == ORDER_PROGRESS:
        ordered.sort(key=_first_percent)
    ordered.sort(key=lambda member: not member["is_self"])
    return ordered
```

Both `sort` calls are stable, so the second preserves the first's order among everyone who is not the viewer.

- [x] **Step 4: Run the tests to verify they pass**

Run: `pytest apps/core/tests/test_roster.py -v`
Expected: PASS.

- [x] **Step 5: Commit**

```bash
ruff format . && ruff check .
git add apps/core/roster.py apps/core/tests/test_roster.py
git commit -m "feat(core): narrow and order the roster from a parsed query"
```

---

### Task 6: Wire the roster into the view

**Files:**
- Modify: `apps/core/views.py:244-341` (`CompanyEmployeeListView`)
- Test: `apps/core/tests/test_views.py` (extend `TestCompanyEmployeeListView`)

**Interfaces:**
- Consumes: `parse_roster_query`, `narrow_profiles`, `sort_members` from Tasks 4–5; `labels_for_names` from Task 1.
- Produces: template context keys `roster_query`, `role_options`, `sex_options`, `area_options`, `location_options`, `show_location_filter`, `total_count`, `shown_count`, `roster_querystring`; and `role_labels` on each member row.

- [x] **Step 1: Write the failing test**

Append to `TestCompanyEmployeeListView` in `apps/core/tests/test_views.py`:

```python
    def test_context_carries_the_filter_options(
        self, client, make_user, make_company, make_area, bootstrap_groups
    ):
        company = make_company()
        make_area(company, name="Producción")
        viewer = self._make_viewer(make_user, company)
        client.force_login(viewer)

        response = client.get(self.URL)

        assert response.status_code == 200
        assert [label for _, label in response.context["role_options"]] == [
            "Administrador",
            "Ejecutivo principal",
            "Ejecutivo secundario",
            "Empleado",
        ]
        assert [a.name for a in response.context["area_options"]] == ["Producción"]

    def test_location_filter_is_hidden_when_the_company_has_one_localidad(
        self, client, make_user, make_company, make_location
    ):
        company = make_company()
        make_location(company, name="Matriz")
        viewer = self._make_viewer(make_user, company)
        client.force_login(viewer)

        response = client.get(self.URL)

        assert response.context["show_location_filter"] is False

    def test_location_filter_appears_with_two_localidades(
        self, client, make_user, make_company, make_location
    ):
        company = make_company()
        make_location(company, name="Matriz")
        make_location(company, name="Norte")
        viewer = self._make_viewer(make_user, company)
        client.force_login(viewer)

        response = client.get(self.URL)

        assert response.context["show_location_filter"] is True

    def test_search_narrows_the_roster(
        self, client, make_user, make_company, make_user_with_profile
    ):
        company = make_company()
        make_user_with_profile(
            email="ana@example.com", company=company,
            first_name="Ana", paternal_last_name="Álvarez",
        )
        make_user_with_profile(
            email="beto@example.com", company=company,
            first_name="Beto", paternal_last_name="Ruiz",
        )
        viewer = self._make_viewer(make_user, company)
        client.force_login(viewer)

        response = client.get(self.URL, {"q": "alvarez"})

        emails = [m["profile"].user.email for m in response.context["members"]]
        assert emails == ["ana@example.com"]
        assert response.context["shown_count"] == 1
        assert response.context["total_count"] == 3

    def test_an_unknown_parameter_value_is_ignored(
        self, client, make_user, make_company
    ):
        """A stale or hand-edited URL renders the roster, not an error."""
        company = make_company()
        viewer = self._make_viewer(make_user, company)
        client.force_login(viewer)

        response = client.get(
            self.URL, {"sexo": "otro", "area": "999", "rol": "gerente", "orden": "x"}
        )

        assert response.status_code == 200
        assert response.context["roster_query"].is_narrowed is False

    def test_a_retired_area_can_still_be_filtered_by(
        self, client, make_user, make_company, make_area, make_user_with_profile
    ):
        """A retired área keeps its colaboradores, so a URL naming one must work
        even though the dropdown no longer offers it."""
        company = make_company()
        retired = make_area(company, name="Almacén", is_active=False)
        make_user_with_profile(email="ana@example.com", company=company, area=retired)
        viewer = self._make_viewer(make_user, company)
        client.force_login(viewer)

        response = client.get(self.URL, {"area": str(retired.id)})

        assert response.context["roster_query"].area_id == retired.id
        assert response.context["shown_count"] == 1
        assert [a.name for a in response.context["area_options"]] == []

    def test_role_labels_are_on_each_member(
        self, client, make_user, make_company, make_user_with_profile, bootstrap_groups
    ):
        company = make_company()
        ana = make_user_with_profile(email="ana@example.com", company=company)
        ana.groups.add(bootstrap_groups["Employees"])
        viewer = self._make_viewer(make_user, company)
        client.force_login(viewer)

        response = client.get(self.URL, {"q": "ana@"})

        assert response.context["members"][0]["role_labels"] == ["Empleado"]

    def test_a_member_with_no_group_has_no_labels(
        self, client, make_user, make_company, make_user_with_profile
    ):
        company = make_company()
        make_user_with_profile(email="ana@example.com", company=company)
        viewer = self._make_viewer(make_user, company)
        client.force_login(viewer)

        response = client.get(self.URL, {"q": "ana@"})

        assert response.context["members"][0]["role_labels"] == []

    def test_querystring_is_available_for_the_back_link(
        self, client, make_user, make_company
    ):
        company = make_company()
        viewer = self._make_viewer(make_user, company)
        client.force_login(viewer)

        response = client.get(self.URL, {"q": "ana", "orden": "progreso"})

        assert "q=ana" in response.context["roster_querystring"]
        assert "orden=progreso" in response.context["roster_querystring"]
```

- [x] **Step 2: Run the tests to verify they fail**

Run: `pytest apps/core/tests/test_views.py::TestCompanyEmployeeListView -v`
Expected: FAIL — `KeyError: 'role_options'` and friends.

- [x] **Step 3: Write the implementation**

In `apps/core/views.py`, add the imports:

```python
from apps.accounts.roles import ROLES, labels_for_names
from apps.core import roster
```

Replace the profile query, member loop and `render` call at the end of `CompanyEmployeeListView.get` (currently lines 303–341) with:

```python
        # Options offer only what an operator may still assign; validation
        # accepts every entry the company owns. A retired área keeps the
        # colaboradores already assigned to it, so a URL naming one has to keep
        # working even though it is no longer offered.
        areas = list(company.areas.filter(is_active=True).order_by("name"))
        locations = list(company.locations.filter(is_active=True).order_by("name"))

        query = roster.parse_roster_query(
            request.GET,
            area_ids=set(company.areas.values_list("id", flat=True)),
            location_ids=set(company.locations.values_list("id", flat=True)),
        )

        all_profiles = company.members.select_related("user", "area", "location")
        profiles = roster.narrow_profiles(all_profiles, query).prefetch_related(
            "user__groups"
        )

        members_data = []
        for profile in profiles:
            user = profile.user
            survey_progress = [
                _progress_entry(
                    assignment,
                    modules_map[assignment.id],
                    total_questions_map[assignment.id],
                    answers_map.get((user.id, assignment.id), {}),
                    submission_status_map.get((user.id, assignment.id), "not_started"),
                )
                for assignment in assignments
            ]
            members_data.append(
                {
                    "profile": profile,
                    "is_self": profile.user_id == request.user.id,
                    "role_labels": labels_for_names(g.name for g in user.groups.all()),
                    "survey_progress": survey_progress,
                }
            )

        members_data = roster.sort_members(members_data, query.order)

        return render(
            request,
            "core/employee_list.html",
            {
                "company": company,
                "is_admin_view": reference_code is not None,
                "members": members_data,
                "roster_query": query,
                "roster_querystring": request.GET.urlencode(),
                "role_options": [(role.slug, role.label) for role in ROLES],
                "sex_options": list(roster.SEX_SLUGS_TO_LABELS.items()),
                "area_options": areas,
                "location_options": locations,
                "show_location_filter": len(locations) > 1,
                "shown_count": len(members_data),
                "total_count": company.members.count(),
            },
        )
```

Add the label map to `apps/core/roster.py`, beside `SEX_SLUGS`:

```python
# What each sexo slug is called on screen. `UserProfile.Sex` holds the same two
# labels against the stored values; these are keyed by slug because that is what
# the toolbar's <option> values are.
SEX_SLUGS_TO_LABELS = {"masculino": "Masculino", "femenino": "Femenino"}
```

Confirm the related names `company.areas` and `company.locations` match `CompanyArea`/`CompanyLocation`'s `related_name`, and the `is_active` field exists on both; adjust the two list comprehensions if they differ.

- [x] **Step 4: Run the tests to verify they pass**

Run: `pytest apps/core/tests/test_views.py -v`
Expected: PASS, including the pre-existing ordering and permission tests.

- [x] **Step 5: Guard the query count**

Add to `TestCompanyEmployeeListView`:

```python
    def test_roster_does_not_run_a_query_per_member(
        self, client, make_user, make_company, make_user_with_profile,
        bootstrap_groups, django_assert_max_num_queries,
    ):
        """The prefetch pattern is what makes this page survive a real company."""
        company = make_company()
        for i in range(12):
            member = make_user_with_profile(
                email=f"m{i}@example.com", company=company,
                first_name=f"M{i}", paternal_last_name="Pérez",
            )
            member.groups.add(bootstrap_groups["Employees"])
        viewer = self._make_viewer(make_user, company)
        client.force_login(viewer)

        with django_assert_max_num_queries(15):
            response = client.get(self.URL)

        assert response.status_code == 200
```

Run: `pytest apps/core/tests/test_views.py::TestCompanyEmployeeListView::test_roster_does_not_run_a_query_per_member -v`
Expected: PASS. If it fails, a `prefetch_related` was dropped — fix that rather than raising the ceiling.

- [x] **Step 6: Commit**

```bash
ruff format . && ruff check .
git add apps/core/views.py apps/core/roster.py apps/core/tests/test_views.py
git commit -m "feat(core): search, filter and sort the colaborador roster"
```

---

### Task 7: Rename the roster URLs and settle the vocabulary

**Files:**
- Modify: `apps/core/urls.py:14-17`
- Modify: `templates/core/employee_list.html`, `templates/core/employee_detail.html`, `templates/core/company_dashboard.html`, `templates/core/company_list.html`, `templates/core/about.html`
- Modify: `apps/core/tests/test_views.py` (URL constants and copy assertions)

**Interfaces:**
- Consumes: nothing.
- Produces: the four roster/detail URLs under `/colaboradores/`. The URL *names* (`company_employee_list`, `company_employee_detail`, and their `_for` variants) do not change, so no `{% url %}` tag needs editing.

- [x] **Step 1: Write the failing test**

Add to `apps/core/tests/test_views.py`, above `TestCompanyEmployeeListView`:

```python
class TestRosterUrls:
    def test_the_roster_lives_under_colaboradores(self):
        from django.urls import reverse

        assert reverse("core:company_employee_list") == "/tablero-empresa/colaboradores/"
        assert (
            reverse("core:company_employee_list_for", args=["AB12X"])
            == "/empresas/AB12X/colaboradores/"
        )

    def test_the_detail_page_does_too(self):
        from django.urls import reverse

        assert (
            reverse("core:company_employee_detail", args=[7])
            == "/tablero-empresa/colaboradores/7/"
        )
        assert (
            reverse("core:company_employee_detail_for", args=["AB12X", 7])
            == "/empresas/AB12X/colaboradores/7/"
        )
```

- [x] **Step 2: Run the test to verify it fails**

Run: `pytest apps/core/tests/test_views.py::TestRosterUrls -v`
Expected: FAIL — the reversed paths still read `/empleados/`.

- [x] **Step 3: Rename the URLs**

In `apps/core/urls.py`, change `empleados` to `colaboradores` in all four paths. Leave the `name=` arguments alone.

- [x] **Step 4: Update the tests that hardcode the old paths**

In `apps/core/tests/test_views.py`: `TestCompanyEmployeeListView.URL` becomes `"/tablero-empresa/colaboradores/"`, and the two detail-URL helpers near line 572 become `f"/tablero-empresa/colaboradores/{employee_id}/"` and `f"/empresas/{reference_code}/colaboradores/{employee_id}/"`. Search the file for `empleados` and leave nothing behind.

- [x] **Step 5: Sweep the copy**

Replace the generic uses. *Colaborador* is the person; *empleado* survives only where the `Employees` role is meant, which is nowhere in these templates:

| File | Now | Becomes |
|---|---|---|
| `templates/core/company_list.html:22` | `Empleados` | `Colaboradores` |
| `templates/core/employee_detail.html:10,14` | `← Empleados` | `← Colaboradores` |
| `templates/core/employee_detail.html:272` | `Este empleado aún no ha iniciado esta encuesta.` | `Este colaborador aún no ha iniciado esta encuesta.` |
| `templates/core/company_dashboard.html:24,34` | `Empleados registrados` | `Colaboradores registrados` |
| `templates/core/company_dashboard.html:30` | `Ver empleados →` | `Ver colaboradores →` |
| `templates/core/company_dashboard.html:100` | `el total de empleados registrados` | `el total de colaboradores registrados` |
| `templates/core/about.html:21` | `datos cuantitativos de los empleados` | `datos cuantitativos de los colaboradores` |

`templates/core/employee_list.html` is rewritten wholesale in Task 8 — leave it for now.

Then update the two assertions in `apps/core/tests/test_views.py` near lines 217 and 227 that assert on `"Ver empleados"`, changing them to `"Ver colaboradores"`.

- [x] **Step 6: Run the whole suite**

Run: `pytest`
Expected: PASS. Then `grep -rn "empleado" templates/` should return only `employee_list.html`.

- [x] **Step 7: Commit**

```bash
ruff format . && ruff check .
git add apps/core/urls.py apps/core/tests/test_views.py templates/core/
git commit -m "refactor: call a person a colaborador and move the roster to /colaboradores/"
```

---

### Task 8: Rebuild the roster page

**Files:**
- Modify: `templates/core/employee_list.html` (rewritten)
- Modify: `static/css/output.css` (regenerated)
- Test: `apps/core/tests/test_views.py` (extend)

**Interfaces:**
- Consumes: every context key from Task 6.
- Produces: the rendered page. Element ids the tests assert on: the toolbar `<form id="roster-filters">`.

Use the `frontend-design` skill for this task. The design constraints are fixed by the spec and are not the skill's to revisit:

- The toolbar is a `method="get"` form (no CSRF token on a GET form), sticky to the top of the viewport, holding the search box, the sexo/área/rol selects, the localidad select when `show_location_filter`, the *Ordenar por* select, an *Aplicar* submit and a *Limpiar filtros* link pointing at the bare page URL.
- `Mostrando {{ shown_count }} de {{ total_count }} colaboradores` sits under the toolbar.
- The card is an `<article>`, not an `<a>`. The person's name is the only link, and it carries the `{% url %}` plus `?{{ roster_querystring }}`. Reuse the initials avatar markup from `employee_detail.html:36-43`.
- One metadata line per card: role labels joined with `, `, then cargo, área and localidad, separated by `·`, each rendered only when present. A person in no group reads `Sin rol` in the role's place — the line never starts with a separator.
- Badges: `Tú` on the viewer's own card, `Sin activar` on an unactivated one. No others. An activated card gets no badge and no green tint.
- Each progress bar is a `<div role="progressbar" aria-valuenow="{{ prog.percent }}" aria-valuemin="0" aria-valuemax="100" aria-label="...">` naming its survey. The *Completada / En progreso / Sin iniciar* pills are gone; the bar's fill colour carries the state.
- The empty state distinguishes the two cases: no colaboradores at all versus none matching, the latter offering *Limpiar filtros*.

- [ ] **Step 1: Write the failing tests**

Append to `TestCompanyEmployeeListView`:

```python
    def test_toolbar_is_a_get_form(
        self, client, make_user, make_company
    ):
        company = make_company()
        viewer = self._make_viewer(make_user, company)
        client.force_login(viewer)

        response = client.get(self.URL)
        html = response.content.decode()

        assert 'id="roster-filters"' in html
        assert 'method="get"' in html
        # A GET form must not carry a CSRF token — it would end up in the URL.
        assert "csrfmiddlewaretoken" not in html.split('id="roster-filters"')[1][:2000]

    def test_card_shows_the_role_label(
        self, client, make_user, make_company, make_user_with_profile, bootstrap_groups
    ):
        company = make_company()
        ana = make_user_with_profile(
            email="ana@example.com", company=company, position="Analista",
        )
        ana.groups.add(bootstrap_groups["Principal Exec"])
        viewer = self._make_viewer(make_user, company)
        client.force_login(viewer)

        response = client.get(self.URL)

        assert "Ejecutivo principal".encode() in response.content

    def test_a_member_with_no_group_reads_sin_rol(
        self, client, make_user, make_company, make_user_with_profile
    ):
        company = make_company()
        make_user_with_profile(email="ana@example.com", company=company)
        viewer = self._make_viewer(make_user, company)
        client.force_login(viewer)

        response = client.get(self.URL, {"q": "ana@"})

        assert "Sin rol".encode() in response.content

    def test_activated_members_carry_no_badge(
        self, client, make_user, make_company, make_user_with_profile
    ):
        """Activation is the normal state; a badge on every card says nothing."""
        company = make_company()
        make_user_with_profile(email="ana@example.com", company=company)
        viewer = self._make_viewer(make_user, company)
        client.force_login(viewer)

        response = client.get(self.URL)

        assert "Activado".encode() not in response.content

    def test_unactivated_members_are_flagged(
        self, client, make_user, make_company, make_user_with_profile
    ):
        company = make_company()
        make_user_with_profile(
            email="beto@example.com", company=company, is_activated=False
        )
        viewer = self._make_viewer(make_user, company)
        client.force_login(viewer)

        response = client.get(self.URL)

        assert "Sin activar".encode() in response.content

    def test_progress_bar_reports_its_value(
        self, client, make_user, make_company, make_user_with_profile, active_assignment
    ):
        company = active_assignment.company
        make_user_with_profile(email="ana@example.com", company=company)
        viewer = self._make_viewer(make_user, company)
        client.force_login(viewer)

        response = client.get(self.URL)

        assert 'role="progressbar"'.encode() in response.content
        assert 'aria-valuenow="0"'.encode() in response.content

    def test_empty_result_offers_to_clear_the_filters(
        self, client, make_user, make_company, make_user_with_profile
    ):
        company = make_company()
        make_user_with_profile(email="ana@example.com", company=company)
        viewer = self._make_viewer(make_user, company)
        client.force_login(viewer)

        response = client.get(self.URL, {"q": "nadie"})

        assert "Limpiar filtros".encode() in response.content
        assert response.context["shown_count"] == 0
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `pytest apps/core/tests/test_views.py::TestCompanyEmployeeListView -v`
Expected: FAIL on the toolbar, badge and progressbar assertions.

- [ ] **Step 3: Rewrite the template**

Rewrite `templates/core/employee_list.html` to the constraints above. Keep the existing `{% block header_nav %}` structure, changing its label to `Colaboradores`.

- [ ] **Step 4: Run the tests to verify they pass**

Run: `pytest apps/core/tests/test_views.py -v`
Expected: PASS.

- [ ] **Step 5: Rebuild the CSS**

Run: `npm run build:css`

Every class in the new template must appear in `static/css/output.css` afterwards. The template is already a Tailwind `@source`, so nothing needs adding to `static/css/main.css` unless a width is passed from Python. Spot-check one new class: `grep -c "sticky" static/css/output.css` should be non-zero.

- [ ] **Step 6: Commit**

```bash
git add templates/core/employee_list.html static/css/output.css apps/core/tests/test_views.py
git commit -m "feat(core): rebuild the roster card and add the filter toolbar"
```

---

### Task 9: Carry the filters through the detail page

**Files:**
- Modify: `apps/core/views.py` (`EmployeeDetailView.get` context)
- Modify: `templates/core/employee_detail.html:5-16`
- Test: `apps/core/tests/test_views.py`

**Interfaces:**
- Consumes: `roster_querystring` naming convention from Task 6.
- Produces: `roster_querystring` in the detail view's context.

- [ ] **Step 1: Write the failing test**

```python
    def test_back_link_preserves_the_roster_filters(
        self, client, make_user, make_company, make_user_with_profile
    ):
        """Opening a person and going back should not discard the search."""
        company = make_company()
        ana = make_user_with_profile(email="ana@example.com", company=company)
        viewer = self._make_viewer(make_user, company)
        client.force_login(viewer)

        response = client.get(self._detail_url(ana.id), {"q": "ana", "orden": "progreso"})

        html = response.content.decode()
        assert "/tablero-empresa/colaboradores/?q=ana&amp;orden=progreso" in html
```

Place it in the detail view's test class and use that class's existing URL helper in place of `self._detail_url` if it is named differently.

- [ ] **Step 2: Run the test to verify it fails**

Run: `pytest apps/core/tests/test_views.py -k back_link -v`
Expected: FAIL — the back link has no query string.

- [ ] **Step 3: Write the implementation**

Add `"roster_querystring": request.GET.urlencode(),` to `EmployeeDetailView`'s render context, and in `templates/core/employee_detail.html` append the query string to both back links:

```django
    <a href="{% url 'core:company_employee_list_for' company.reference_code %}{% if roster_querystring %}?{{ roster_querystring }}{% endif %}" class="text-sm text-gray-400 hover:text-gray-600 transition-colors">
      &larr; Colaboradores
    </a>
```

and the same for the non-admin branch with `{% url 'core:company_employee_list' %}`.

- [ ] **Step 4: Run the tests to verify they pass**

Run: `pytest apps/core/tests/test_views.py -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
ruff format . && ruff check .
git add apps/core/views.py templates/core/employee_detail.html apps/core/tests/test_views.py
git commit -m "feat(core): keep the roster's filters when returning from a colaborador"
```

---

### Task 10: Verify the whole change

**Files:** none modified unless a check fails.

- [ ] **Step 1: Run the full suite**

Run: `pytest`
Expected: PASS, no skips introduced by this branch.

- [ ] **Step 2: Confirm no migration was provoked**

Run: `python manage.py makemigrations --check --dry-run`
Expected: "No changes detected".

- [ ] **Step 3: Confirm the admin is still valid**

Run: `python manage.py check`
Expected: "System check identified no issues".

- [ ] **Step 4: Confirm the vocabulary sweep is complete**

Run: `grep -rn "empleado" templates/ apps/core/urls.py`
Expected: no matches.

- [ ] **Step 5: Confirm the CSS is current**

Run: `npm run build:css && git diff --stat static/css/output.css`
Expected: no diff. A diff here means Step 5 of Task 8 was skipped or a later template edit was not rebuilt — commit the regenerated file.

- [ ] **Step 6: Hand the reviewer a browser checklist**

There is no JavaScript test runner in this project, and the Python suite asserts only the server-rendered contract — it cannot see an uncompiled Tailwind class or a sticky bar that overlaps the header. Ask the reviewer to open a company roster and confirm:

1. The toolbar renders as a single row on a desktop width and stacks on a phone, with no horizontal scroll.
2. The toolbar stays visible while scrolling a long roster, and does not cover the page header.
3. Each select shows the value from the URL after applying a filter and after a browser refresh.
4. *Limpiar filtros* returns the full roster.
5. A card with no cargo, área or localidad shows only the role, with no stray `·` separators.
6. An unactivated colaborador is visually distinct and carries the *Sin activar* badge; an activated one carries no badge.
7. Clicking a name opens the person; the browser's back button and the page's *← Colaboradores* link both return to the filtered roster.
8. The Django admin's Usuarios changelist shows the *Rol* column and filters by it.

---

### Task 11: Documentation

The spec's rule: the live docs describe the new behavior in present tense, with
no migration commentary. A reader must not be able to tell a previous
implementation existed.

**Files:**
- Modify: `docs/platform/employee-roster.md`
- Modify: `docs/platform/localization.md`
- Modify: `docs/platform/auth-and-onboarding.md`
- Modify: `docs/internal/open-findings.md`
- Modify: `apps/accounts/CLAUDE.md`
- Modify: `apps/core/CLAUDE.md`
- Modify: `.claude/CLAUDE.md`

- [ ] **Step 1: Trim the feature doc to its post-ship form**

In `docs/platform/employee-roster.md`: set `## Status` to `Current — implemented in `apps/core` and `apps/accounts``, and delete the `## Documentation impact` section, which describes this change rather than the feature. Everything else is already written in present tense.

- [ ] **Step 2: Correct `docs/platform/localization.md`**

Replace the `**Authorization group names**` bullet under **Not covered** with a **Covered** bullet: the four groups keep their English `auth.Group.name`, which is the lookup key and a CSV import value, and are shown through the Spanish labels declared in `apps/accounts/roles.py`. Add a glossary row: the `Employees` role is **empleado**, while a person on a roster is a **colaborador** whatever their role. Add the Rol column to the admin list under **Public behavior**.

- [ ] **Step 3: Correct `docs/platform/auth-and-onboarding.md`**

Line 247's parenthetical and line 252's bullet: the canonical group-name contract lives in `apps/accounts/roles.py`, which `bootstrap_groups` reads.

- [ ] **Step 4: Correct `docs/internal/open-findings.md`**

Finding #1 keeps only the rename: the names are now shown in Spanish everywhere a user reads them, and what remains open is `auth.Group.name` itself, still matched by string and still a CSV column value. Delete finding #5 with a line saying the roster is narrowed by search, filters and sorting rather than grouped, and pointing at `docs/platform/employee-roster.md`.

- [ ] **Step 5: Correct the three CLAUDE.md files**

- `apps/accounts/CLAUDE.md:51` — the four names live in `apps/accounts/roles.py` with their Spanish labels and URL slugs; a new permission is added to `Role.Meta.permissions` and `GROUP_PERMISSIONS`, and the `conftest.py` fixture follows from the latter.
- `apps/core/CLAUDE.md` — `CompanyEmployeeListView` takes `q`, `sexo`, `area`, `localidad`, `rol` and `orden`, parsed and applied by `apps/core/roster.py`; add to the N+1 gotcha that narrowing happens before the per-member loop and that `user__groups` is prefetched for the Rol line.
- `.claude/CLAUDE.md` — in the Authorization bullet, name `apps/accounts/roles.py` as where the four group names and their Spanish labels live.

- [ ] **Step 6: Verify the docs describe only the current state**

Run: `grep -rniE "formerly|previously|no longer|used to|replaces the old|deprecated" docs/platform/employee-roster.md docs/platform/localization.md docs/platform/auth-and-onboarding.md`
Expected: no matches.

- [ ] **Step 7: Commit**

```bash
git add docs/ apps/accounts/CLAUDE.md apps/core/CLAUDE.md .claude/CLAUDE.md
git commit -m "docs: describe the colaborador roster and its Spanish role labels"
```

- [ ] **Step 8: Clean up the scaffolding**

This file is deleted when the branch merges, leaving `docs/platform/wip/` holding nothing but its README.
