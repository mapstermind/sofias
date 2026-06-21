"""
Survey-agnostic conditional-visibility evaluation.

A `visible_when` rule (on Module or Question) is a small JSON object. Supported
forms:

    {"question": "<code>", "equals": <value>}      # single-answer gate
    {"any_in_module": "<module key>", "equals": <value>}  # module aggregate

A null/empty rule means always visible. This module is the single source of
truth used by both the take/autosave/submit flow (server) and the rendered
template (client mirrors the same semantics).
"""

_TRUE_STRINGS = {"si", "sí", "true", "yes", "1"}
_FALSE_STRINGS = {"no", "false", "0"}


def _normalize(value):
    """Loosely normalize a comparison operand so booleans authored as strings
    ("si"/"no") match stored boolean answers, and numbers compare by value."""
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        lowered = value.strip().lower()
        if lowered in _TRUE_STRINGS:
            return True
        if lowered in _FALSE_STRINGS:
            return False
        return lowered
    return value


def _matches(actual, expected):
    return _normalize(actual) == _normalize(expected)


def is_visible(rule, answers_by_code, module_to_codes=None):
    """Evaluate a single `visible_when` rule. Null/empty => visible."""
    if not rule:
        return True

    if "question" in rule:
        return _matches(answers_by_code.get(rule["question"]), rule.get("equals"))

    if "any_in_module" in rule:
        codes = (module_to_codes or {}).get(rule["any_in_module"], [])
        return any(
            _matches(answers_by_code.get(code), rule.get("equals")) for code in codes
        )

    # Unknown rule shape: fail safe to visible.
    return True


def visible_questions(assignment, answers_by_code):
    """
    Ordered list of Questions visible for this assignment given the current
    answers (keyed by question code). Applies variant filtering, then module
    rules, then per-question rules.
    """
    modules = list(assignment.modules_for_variant().prefetch_related("questions"))
    module_to_codes = {m.key: [q.code for q in m.questions.all()] for m in modules}

    result = []
    for module in modules:
        if not is_visible(module.visible_when, answers_by_code, module_to_codes):
            continue
        for question in module.questions.all():
            if is_visible(question.visible_when, answers_by_code, module_to_codes):
                result.append(question)
    return result
