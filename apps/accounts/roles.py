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
