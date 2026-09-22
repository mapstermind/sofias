"""The canonical four authorization groups and their Spanish labels."""

import pytest

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

    def test_label_for_name_returns_none_for_an_unknown_group(self):
        """A group created by hand in the admin has no label to show."""
        assert roles.label_for_name("Auditores") is None

    def test_labels_for_names_uses_declared_order_not_argument_order(self):
        labels = roles.labels_for_names(["Employees", "Admins"])
        assert labels == ["Administrador", "Empleado"]

    def test_labels_for_names_drops_unknown_groups(self):
        assert roles.labels_for_names(["Auditores", "Employees"]) == ["Empleado"]


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


class TestSmallGroupsPermission:
    def test_only_admins_may_view_small_groups(self):
        from apps.accounts.management.commands.bootstrap_groups import (
            GROUP_PERMISSIONS,
        )

        holders = {
            name
            for name, codenames in GROUP_PERMISSIONS.items()
            if "can_view_small_groups" in codenames
        }
        assert holders == {"Admins"}

    @pytest.mark.django_db
    def test_small_groups_permission_exists(self):
        from django.contrib.auth.models import Permission

        perm = Permission.objects.get(codename="can_view_small_groups")
        assert perm.content_type.app_label == "accounts"
