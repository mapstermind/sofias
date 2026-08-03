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


def visible_questions_for_modules(modules, answers_by_code):
    """
    Ordered list of Questions visible across already-fetched `modules`, given
    the current answers (keyed by question code). Applies module rules, then
    per-question rules.

    Takes modules rather than an assignment so callers evaluating many
    respondents (dashboards, employee lists) can prefetch once instead of
    issuing a query per respondent.
    """
    module_to_codes = {m.key: [q.code for q in m.questions.all()] for m in modules}

    result = []
    for module in modules:
        if not is_visible(module.visible_when, answers_by_code, module_to_codes):
            continue
        for question in module.questions.all():
            if is_visible(question.visible_when, answers_by_code, module_to_codes):
                result.append(question)
    return result


def visible_questions(assignment, answers_by_code):
    """
    Ordered list of Questions visible for this assignment given the current
    answers (keyed by question code). Applies variant filtering, then delegates
    to `visible_questions_for_modules`.
    """
    modules = list(assignment.modules_for_variant().prefetch_related("questions"))
    return visible_questions_for_modules(modules, answers_by_code)


def progress_for_modules(modules, answers_by_qid):
    """
    `(answered, total)` over the questions that apply given the answers so far.

    `answers_by_qid` maps `Question.id` to its stored value. `total` counts only
    visible questions, so answers stranded behind a gate the respondent later
    flipped are ignored and `answered` can never exceed `total`.
    """
    answers_by_code = {
        q.code: answers_by_qid.get(q.id)
        for module in modules
        for q in module.questions.all()
    }
    visible = visible_questions_for_modules(modules, answers_by_code)
    answered = sum(1 for q in visible if answers_by_qid.get(q.id) not in (None, "", []))
    return answered, len(visible)
