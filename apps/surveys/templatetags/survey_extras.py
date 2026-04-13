from django import template

register = template.Library()

LIKERT_DEFAULT_LABELS = ["Nunca", "Casi nunca", "A veces", "Casi siempre", "Siempre"]


@register.filter
def dict_get(d, key):
    if isinstance(d, dict):
        return d.get(key)
    return None


@register.filter
def likert_pairs(question):
    """Return [(value_int, label_str), ...] for a likert question.

    Uses question.config['labels'] if present, otherwise the default 5-point scale.
    Values are always 1-5 regardless of the label list length.
    """
    labels = None
    if isinstance(question.config, dict):
        labels = question.config.get("labels")
    if not labels:
        labels = LIKERT_DEFAULT_LABELS
    return list(enumerate(labels, start=1))
