from apps.nom035 import constants as c


def likert_item_score(value: int, *, inverted: bool) -> int:
    """Map a stored Likert answer (1=Siempre … 5=Nunca) to the NOM-035 0–4 scale."""
    return (5 - value) if inverted else (value - 1)


def classify(bands: list[tuple[float, str]], score: int) -> str:
    """Return the NDR level for `score`. `bands` is ascending by upper bound."""
    for upper, level in bands:
        if score < upper:
            return level
    return bands[-1][1]


# MVP assumption (see docs/platform/nom-035-valoracion-supuestos.md §2.5):
# event with 1–2 follow-ups = low, 3–5 = med, 6+ = high.
def guia1_severity(event: bool, followup_count: int) -> str:
    if not event:
        return c.SEV_NONE
    if followup_count >= 6:
        return c.SEV_HIGH
    if followup_count >= 3:
        return c.SEV_MED
    return c.SEV_LOW
