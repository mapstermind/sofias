from apps.nom035 import _nom035_scoring as cfg
from apps.nom035 import constants as c
from apps.nom035.models import NDR, GroupLevel, SubmissionScore


def _scores_for_company(company):
    return SubmissionScore.objects.filter(submission__assignment__company=company)


def company_valuation(company) -> dict:
    """Aggregate scored submissions for a company (computed on demand)."""
    scores = list(_scores_for_company(company))
    distribution = {level: 0 for level in c.NDR_ORDER}
    needing_action = 0
    guia1_flags = 0
    for s in scores:
        distribution[s.final_ndr] += 1
        if s.final_ndr in (c.NDR_ALTO, c.NDR_MUY_ALTO):
            needing_action += 1
        if s.guia1_event:
            guia1_flags += 1
    return {
        "scored_count": len(scores),
        "distribution": distribution,
        "needing_action": needing_action,
        "guia1_flags": guia1_flags,
    }


def employee_valuation(user, company) -> dict | None:
    """The latest scored submission for a user in a company, as display text."""
    score = (
        _scores_for_company(company)
        .filter(submission__user=user)
        .prefetch_related("groups")
        .order_by("-computed_at")
        .first()
    )
    if score is None:
        return None
    categories = [
        {
            "key": g.key,
            "label": g.key.replace("_", " ").capitalize(),
            "ndr": g.ndr,
            "ndr_label": NDR(g.ndr).label,
            "action": cfg.action_text(g.ndr),
        }
        for g in score.groups.all()
        if g.level == GroupLevel.CATEGORIA
    ]
    return {
        "final_ndr": score.final_ndr,
        "final_ndr_label": NDR(score.final_ndr).label,
        "final_score": score.final_score,
        "final_action": cfg.action_text(score.final_ndr),
        "categories": categories,
        "guia1_event": score.guia1_event,
        "guia1_severity": score.guia1_severity,
    }
