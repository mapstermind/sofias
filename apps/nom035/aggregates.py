from apps.nom035 import _nom035_scoring as cfg
from apps.nom035 import constants as c
from apps.nom035.models import NDR, SubmissionScore


def _scores_for_company(company):
    return SubmissionScore.objects.filter(submission__assignment__company=company)


def company_valuation(company) -> dict:
    """Aggregate scored submissions for a company (computed on demand)."""
    scores = list(_scores_for_company(company))
    distribution = {level: 0 for level in c.NDR_ORDER}
    needing_action = 0
    guia1_positive_count = 0
    for s in scores:
        distribution[s.final_ndr] += 1
        if s.final_ndr in (c.NDR_ALTO, c.NDR_MUY_ALTO):
            needing_action += 1
        if s.guia1_positive:
            guia1_positive_count += 1
    distribution_rows = [
        {"ndr": level, "label": c.NDR_LABELS[level], "count": distribution[level]}
        for level in c.NDR_ORDER
    ]
    return {
        "scored_count": len(scores),
        "distribution": distribution,
        "distribution_rows": distribution_rows,
        "needing_action": needing_action,
        "guia1_positive_count": guia1_positive_count,
    }


def employee_valuation(user, company) -> dict | None:
    """The latest scored submission for a user, as a nested categoría→dominio→
    dimensión tree with scores. Dimensión is score-only (no NDR)."""
    score = (
        _scores_for_company(company)
        .filter(submission__user=user)
        .select_related("submission__assignment")
        .prefetch_related("groups")
        .order_by("-submission__completed_at", "-computed_at")
        .first()
    )
    if score is None:
        return None
    variant = score.submission.assignment.variant
    rows = {(g.level, g.key): g for g in score.groups.all()}

    categories = []
    for cat_key in cfg.CATEGORIA_ORDER:
        cat_row = rows.get((c.LEVEL_CATEGORIA, cat_key))
        if cat_row is None:
            continue
        domains = []
        for dom_key in cfg.dominios_for_categoria(cat_key):
            dom_row = rows.get((c.LEVEL_DOMINIO, dom_key))
            if dom_row is None:
                continue
            dimensions = [
                {
                    "key": dim_key,
                    "label": cfg.group_label(dim_key),
                    "score": rows[(c.LEVEL_DIMENSION, dim_key)].score,
                }
                for dim_key in cfg.dimensions_for_dominio(dom_key, variant)
                if (c.LEVEL_DIMENSION, dim_key) in rows
            ]
            domains.append({
                "key": dom_key,
                "label": cfg.group_label(dom_key),
                "score": dom_row.score,
                "ndr": dom_row.ndr,
                "ndr_label": NDR(dom_row.ndr).label,
                "dimensions": dimensions,
            })
        categories.append({
            "key": cat_key,
            "label": cfg.group_label(cat_key),
            "score": cat_row.score,
            "ndr": cat_row.ndr,
            "ndr_label": NDR(cat_row.ndr).label,
            "domains": domains,
        })

    return {
        "final_ndr": score.final_ndr,
        "final_ndr_label": NDR(score.final_ndr).label,
        "final_score": score.final_score,
        "categories": categories,
        "guia1_positive": score.guia1_positive,
    }
