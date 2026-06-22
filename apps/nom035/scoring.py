from dataclasses import dataclass

from apps.nom035 import _nom035_scoring as cfg
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


@dataclass(frozen=True)
class GroupResult:
    level: str
    key: str
    score: int
    ndr: str


@dataclass(frozen=True)
class ScoreResult:
    final_score: int
    final_ndr: str
    groups: list[GroupResult]
    guia1_event: bool
    guia1_followup_count: int
    guia1_severity: str


def score_submission(submission) -> ScoreResult:
    """Compute the NOM-035 valuation for a submission from its answers + config."""
    variant = submission.assignment.variant
    answers = {
        a.question.code: a.value for a in submission.answers.select_related("question")
    }

    taxonomy = cfg.taxonomy_for_variant(variant)
    cat_scores: dict[str, int] = {}
    dom_scores: dict[str, int] = {}
    final = 0
    for code, (cat_key, dom_key) in taxonomy.items():
        value = answers.get(code)
        if value is None:
            continue  # unanswered or hidden block — excluded (see supuestos §2.4)
        item = likert_item_score(int(value), inverted=cfg.is_inverted(code))
        final += item
        cat_scores[cat_key] = cat_scores.get(cat_key, 0) + item
        dom_scores[dom_key] = dom_scores.get(dom_key, 0) + item

    groups = []
    for level, sums in (
        (c.LEVEL_DOMINIO, dom_scores),
        (c.LEVEL_CATEGORIA, cat_scores),
    ):
        for key, score in sums.items():
            ndr = classify(cfg.thresholds_for(level, key, variant), score)
            groups.append(GroupResult(level=level, key=key, score=score, ndr=ndr))

    final_ndr = classify(cfg.thresholds_for("final", "final", variant), final)

    event = answers.get(cfg.GUIA1_TRIGGER_CODE) is True
    followups = sum(1 for code in cfg.GUIA1_FOLLOWUP_CODES if answers.get(code) is True)

    return ScoreResult(
        final_score=final,
        final_ndr=final_ndr,
        groups=groups,
        guia1_event=event,
        guia1_followup_count=followups,
        guia1_severity=guia1_severity(event, followups),
    )
