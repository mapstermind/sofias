"""Query-string parsing for the NOM-035 results page.

Same rule as the roster: an absent, empty, unrecognized or foreign-company
value is ignored, never an error. Spanish slugs in, English values out.
"""

from dataclasses import dataclass
from urllib.parse import urlencode

from apps.accounts.demographics import AGE_BANDS, band_by_slug
from apps.core.query_params import SEX_SLUGS_TO_LABELS, first_sex, valid_pks, values


@dataclass(frozen=True)
class ResultsQuery:
    assignment_id: int | None = None
    sex: str = ""
    sex_slug: str = ""
    age_slugs: tuple[str, ...] = ()
    area_ids: tuple[int, ...] = ()
    location_ids: tuple[int, ...] = ()

    @property
    def is_filtered(self) -> bool:
        """Whether the group is narrower than the whole assignment."""
        return bool(self.sex or self.age_slugs or self.area_ids or self.location_ids)

    def params(self) -> list[tuple[str, str]]:
        pairs = []
        if self.assignment_id is not None:
            pairs.append(("encuesta", str(self.assignment_id)))
        if self.sex_slug:
            pairs.append(("sexo", self.sex_slug))
        pairs += [("edad", slug) for slug in self.age_slugs]
        pairs += [("area", str(pk)) for pk in self.area_ids]
        pairs += [("localidad", str(pk)) for pk in self.location_ids]
        return pairs


def parse_results_query(
    params, *, assignment_ids, area_ids, location_ids
) -> ResultsQuery:
    assignment = valid_pks(values(params, "encuesta")[:1], assignment_ids)
    sex, sex_slug = first_sex(params)
    wanted = {raw.strip() for raw in values(params, "edad")}
    return ResultsQuery(
        assignment_id=assignment[0] if assignment else None,
        sex=sex,
        sex_slug=sex_slug,
        age_slugs=tuple(band.slug for band in AGE_BANDS if band.slug in wanted),
        area_ids=valid_pks(values(params, "area"), area_ids),
        location_ids=valid_pks(values(params, "localidad"), location_ids),
    )


def results_url(base, query, *, drop=None, add=None) -> str:
    pairs = [pair for pair in query.params() if pair != drop]
    if add is not None and add not in pairs:
        pairs.append(add)
    return f"{base}?{urlencode(pairs)}" if pairs else base


@dataclass(frozen=True)
class Pill:
    label: str
    remove_url: str


def filter_pills(query, base, *, area_names, location_names) -> list[Pill]:
    entries = []
    if query.sex_slug:
        entries.append((SEX_SLUGS_TO_LABELS[query.sex_slug], ("sexo", query.sex_slug)))
    entries += [(band_by_slug(s).label, ("edad", s)) for s in query.age_slugs]
    entries += [(area_names[pk], ("area", str(pk))) for pk in query.area_ids]
    entries += [
        (location_names[pk], ("localidad", str(pk))) for pk in query.location_ids
    ]
    return [Pill(label, results_url(base, query, drop=pair)) for label, pair in entries]
