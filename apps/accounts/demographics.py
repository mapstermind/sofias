"""Age bands for demographic breakdowns.

Instrument-agnostic: it describes `UserProfile`, so any results page or roster
may group by it. Age is derived as of a given day (ADR-0005), never stored.
"""

from dataclasses import dataclass
from datetime import date, timedelta


@dataclass(frozen=True)
class AgeBand:
    slug: str
    label: str
    lower: int
    upper: int | None  # inclusive; None for the open-ended last band


AGE_BANDS: tuple[AgeBand, ...] = (
    *(
        AgeBand(f"{lo}-{lo + 4}", f"{lo}–{lo + 4}", lo, lo + 4)
        for lo in range(15, 60, 5)
    ),
    AgeBand("60-mas", "60 o más", 60, None),
)

_BY_SLUG = {band.slug: band for band in AGE_BANDS}


def band_by_slug(slug: str) -> AgeBand | None:
    return _BY_SLUG.get(slug)


def age_on(date_of_birth: date, today: date) -> int:
    """Completed years on `today`."""
    birthday_passed = (today.month, today.day) >= (
        date_of_birth.month,
        date_of_birth.day,
    )
    return today.year - date_of_birth.year - (0 if birthday_passed else 1)


def age_band(age: int | None) -> AgeBand | None:
    if age is None:
        return None
    for band in AGE_BANDS:
        if age >= band.lower and (band.upper is None or age <= band.upper):
            return band
    return None


def _years_before(day: date, years: int) -> date:
    try:
        return day.replace(year=day.year - years)
    except ValueError:  # 29 February in a non-leap target year
        return day.replace(year=day.year - years, day=28)


def birth_date_range(band: AgeBand, today: date) -> tuple[date | None, date]:
    """Inclusive (earliest, latest) date of birth whose age on `today` is in `band`.

    `earliest` is None for the open-ended band. Filtering by this range in the
    database gives the same answer as `age_band(age_on(dob, today))`.
    """
    latest = _years_before(today, band.lower)
    if band.upper is None:
        return None, latest
    earliest = _years_before(today, band.upper + 1) + timedelta(days=1)
    return earliest, latest
