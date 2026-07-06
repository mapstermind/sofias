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


# Official NOM-035 Guía I clinical-referral rule (binary). A worker is "positive"
# (requires clinical attention) when a severe traumatic event occurred AND any of
# the per-section thresholds is met. See Guias de Referencia.md, "Interpretación de
# resultados ... Guía de Referencia I".
def guia1_positive(
    *, event: bool, section_ii: int, section_iii: int, section_iv: int
) -> bool:
    if not event:
        return False
    return section_ii >= 1 or section_iii >= 3 or section_iv >= 2


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
    guia1_positive: bool


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

    def _section_yes(codes):
        return sum(1 for code in codes if answers.get(code) is True)

    event = answers.get(cfg.GUIA1_TRIGGER_CODE) is True
    positive = guia1_positive(
        event=event,
        section_ii=_section_yes(cfg.GUIA1_SECTION_II_CODES),
        section_iii=_section_yes(cfg.GUIA1_SECTION_III_CODES),
        section_iv=_section_yes(cfg.GUIA1_SECTION_IV_CODES),
    )

    return ScoreResult(
        final_score=final,
        final_ndr=final_ndr,
        groups=groups,
        guia1_positive=positive,
    )
