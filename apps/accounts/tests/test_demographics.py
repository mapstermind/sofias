from datetime import date, timedelta

import pytest

from apps.accounts.demographics import (
    AGE_BANDS,
    age_band,
    age_on,
    band_by_slug,
    birth_date_range,
)


def test_bands_are_contiguous_five_year_steps_then_sixty_plus():
    assert [b.slug for b in AGE_BANDS] == [
        "15-19",
        "20-24",
        "25-29",
        "30-34",
        "35-39",
        "40-44",
        "45-49",
        "50-54",
        "55-59",
        "60-mas",
    ]
    assert AGE_BANDS[0].label == "15–19"
    assert AGE_BANDS[-1].label == "60 o más"
    assert AGE_BANDS[-1].upper is None


@pytest.mark.parametrize(
    ("age", "slug"),
    [
        (15, "15-19"),
        (19, "15-19"),
        (20, "20-24"),
        (59, "55-59"),
        (60, "60-mas"),
        (99, "60-mas"),
    ],
)
def test_age_band_edges(age, slug):
    assert age_band(age).slug == slug


def test_age_band_outside_or_missing():
    assert age_band(14) is None
    assert age_band(None) is None


def test_band_by_slug():
    assert band_by_slug("25-29").lower == 25
    assert band_by_slug("nonsense") is None


def test_age_on_counts_completed_years():
    assert age_on(date(2000, 9, 21), date(2026, 9, 21)) == 26
    assert age_on(date(2000, 9, 22), date(2026, 9, 21)) == 25


@pytest.mark.parametrize(
    "today", [date(2026, 9, 21), date(2028, 2, 29), date(2027, 2, 28)]
)
def test_birth_date_range_agrees_with_age_band(today):
    """Every date of birth inside a band's range has an age in that band, and
    every date just outside does not — including around 29 February."""
    for band in AGE_BANDS:
        earliest, latest = birth_date_range(band, today)
        assert age_band(age_on(latest, today)) == band
        assert age_band(age_on(latest + timedelta(days=1), today)) != band
        if earliest is not None:
            assert age_band(age_on(earliest, today)) == band
            assert age_band(age_on(earliest - timedelta(days=1), today)) != band
