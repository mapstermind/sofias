import json

from django import template
from django.utils.html import escape
from django.utils.safestring import mark_safe

register = template.Library()

LIKERT_DEFAULT_LABELS = ["Nunca", "Casi nunca", "A veces", "Casi siempre", "Siempre"]


@register.filter
def dict_get(d, key):
    if isinstance(d, dict):
        return d.get(key)
    return None


@register.filter
def as_json(value):
    """Compact, HTML-attribute-safe JSON for a value (e.g. a visible_when rule).

    Returns an empty string for null so `data-visible-when=""` means "no rule".
    """
    if value is None:
        return ""
    return mark_safe(escape(json.dumps(value, separators=(",", ":"))))


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
