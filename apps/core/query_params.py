"""Shared GET-parameter readers for the roster and results-page queries.

Both `roster.parse_roster_query` and `results_query.parse_results_query` apply
the same rule: an absent, empty, unrecognized, or foreign-company value is
ignored, never an error. A URL is not a form: there is no field for the person
to correct, so there is nothing useful to raise at them.
"""

from apps.accounts.models import UserProfile

# The URL speaks Spanish; these map onto `UserProfile.Sex` values.
SEX_SLUGS = {"masculino": UserProfile.Sex.MALE, "femenino": UserProfile.Sex.FEMALE}

# Labels come from the model so relabelling the choice cannot leave the
# filter pill reading a word the rest of the app has stopped using.
SEX_SLUGS_TO_LABELS = {
    slug: UserProfile.Sex(value).label for slug, value in SEX_SLUGS.items()
}


def values(params, key) -> list[str]:
    """Every value given for `key`, whether params is a QueryDict or a dict.

    The view hands us `request.GET`, which may repeat a parameter; unit tests
    hand us a plain dict. `getlist` exists only on the former.
    """
    getlist = getattr(params, "getlist", None)
    if getlist is not None:
        return getlist(key)
    value = params.get(key)
    if value is None:
        return []
    return list(value) if isinstance(value, (list, tuple)) else [value]


def _valid_pk(raw: str, valid_ids: set[int]) -> int | None:
    try:
        pk = int(raw)
    except (TypeError, ValueError):
        return None
    return pk if pk in valid_ids else None


def valid_pks(raw_values, valid_ids: set[int]) -> tuple[int, ...]:
    """Every value that names an entry the company owns, deduplicated.

    A bad value is dropped on its own rather than discarding its neighbours:
    a stale bookmark listing four áreas, one of them since deleted, should
    still filter by the other three.
    """
    seen = []
    for raw in raw_values:
        pk = _valid_pk(raw, valid_ids)
        if pk is not None and pk not in seen:
            seen.append(pk)
    return tuple(seen)


def first_sex(params) -> tuple[str, str]:
    """The first `sexo` value that names a sex we know, as (stored, slug).

    `QueryDict.get()` returns the LAST value, which would let an unrecognized
    value shadow a valid one before it.
    """
    for candidate in values(params, "sexo"):
        stored = SEX_SLUGS.get(candidate.strip())
        if stored:
            return stored, candidate.strip()
    return "", ""
