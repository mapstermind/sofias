"""Search, filtering and ordering for the colaborador roster.

Parsing is separated from the view and from the database so every rule below is
testable on its own: `parse_roster_query` is handed the pks that exist for the
company being viewed rather than looking them up.

The spec's rule is that a parameter which is absent, empty, unrecognized, or
names a catalog entry from another company is ignored and the roster renders as
though it had not been given. A URL is not a form: there is no field for the
person to correct, so there is nothing useful to raise at them.
"""

from dataclasses import dataclass

from django.db.models import Q

from apps.accounts.models import FoldCatalogName, catalog_name_key
from apps.accounts.roles import ROLES

# SEX_SLUGS / SEX_SLUGS_TO_LABELS are re-exported: templates and tests import
# them as `roster.SEX_SLUGS` / `roster.SEX_SLUGS_TO_LABELS`.
from apps.core.query_params import (
    SEX_SLUGS,  # noqa: F401
    SEX_SLUGS_TO_LABELS,  # noqa: F401
    first_sex,
    valid_pks,
    values,
)

ORDER_NAME = "nombre"
ORDER_PROGRESS = "progreso"
ORDER_ACTIVATION = "activacion"
ORDERS = (ORDER_NAME, ORDER_PROGRESS, ORDER_ACTIVATION)

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
    area_ids: tuple[int, ...] = ()
    location_ids: tuple[int, ...] = ()
    role_names: tuple[str, ...] = ()
    role_slugs: tuple[str, ...] = ()
    order: str = ORDER_NAME

    @property
    def is_narrowed(self) -> bool:
        """Whether anything is being hidden. Ordering is not narrowing."""
        return bool(
            self.terms
            or self.sex
            or self.area_ids
            or self.location_ids
            or self.role_names
        )


def parse_roster_query(params, *, area_ids: set[int], location_ids: set[int]):
    """Turn a request's GET parameters into a validated `RosterQuery`."""
    raw_q = (params.get("q") or "").strip()
    terms = tuple(catalog_name_key(term) for term in raw_q.split()[:MAX_SEARCH_TERMS])

    sex, sex_slug = first_sex(params)

    role_slugs = {slug for slug in values(params, "rol")}
    selected_roles = [role for role in ROLES if role.slug in role_slugs]

    order = (params.get("orden") or "").strip()
    if order not in ORDERS:
        order = ORDER_NAME

    return RosterQuery(
        raw_q=raw_q,
        terms=terms,
        sex=sex,
        sex_slug=sex_slug,
        area_ids=valid_pks(values(params, "area"), area_ids),
        location_ids=valid_pks(values(params, "localidad"), location_ids),
        role_names=tuple(role.name for role in selected_roles),
        role_slugs=tuple(role.slug for role in selected_roles),
        order=order,
    )


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
    if query.area_ids:
        queryset = queryset.filter(area_id__in=query.area_ids)
    if query.location_ids:
        queryset = queryset.filter(location_id__in=query.location_ids)
    if query.role_names:
        # `__in` across the groups M2M returns one row per matching group, so a
        # colaborador holding two of the selected roles would be listed twice.
        queryset = queryset.filter(user__groups__name__in=query.role_names).distinct()

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
