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
    terms = tuple(catalog_name_key(term) for term in raw_q.split()[:MAX_SEARCH_TERMS])

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
