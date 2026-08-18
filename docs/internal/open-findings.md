# Open Findings

Issues surfaced during development that are **out of scope for the change that
found them**. Each entry records what it is, where it lives, and why it was left
alone — so the decision to defer is deliberate and revisitable, not forgotten.

This is a working list, not a spec. Delete an entry when it is fixed or when the
team decides it is not worth fixing (say which, and why).

---

## 1. Authorization group names are in English 🟡

**Where:** `apps/accounts/management/commands/bootstrap_groups.py`
(`GROUP_PERMISSIONS`), `apps/accounts/importers.py`, `apps/accounts/views.py`
(`_redirect_after_login`), `conftest.py` (`bootstrap_groups` fixture).

**What:** The four groups — `Admins`, `Principal Exec`, `Secondary Exec`,
`Employees` — appear in English in the admin's Groups list and in the CSV
importer's `group` column, on an otherwise Spanish operator surface.

**Why it was left alone:** `auth.Group.name` is looked up **by string** in four
places, and the CSV import contract accepts it as a column value. Renaming is a
behavior change with an input-format consequence, not the presentation-only
sweep that [`docs/platform/localization.md`](../platform/localization.md)
covers. Doing it properly means picking Spanish names, updating all four call
sites, and deciding whether the importer keeps accepting the English spellings.

---

## 2. Survey answer validation messages are in English 🟠

**Where:** `apps/surveys/views.py:67,75,83` — the three error strings returned by
`_parse_value`.

**What:** `"Please enter a whole number."`, `"Please enter a number."` and
`"Please select a valid option."` are rendered to the **employee** taking a
survey. `survey_detail` collects them into `errors[q.id]`, and
`templates/surveys/_question.html:114` prints them above the question. They are
the only user-facing English strings left in the codebase — every other
message in `views.py`/`forms.py` across the four apps is already Spanish.

Suggested wording: `"Escribe un número entero."`, `"Escribe un número."`,
`"Selecciona una opción válida."`

**Why it was left alone:** out of scope for
[`docs/platform/localization.md`](../platform/localization.md), which covered the
Django admin. These sit in the public survey flow, not in model metadata, so no
part of that sweep touched them.

**Note:** the rule this violates is that **everything a user sees is Spanish** —
not just admin metadata. That covers view and form validation messages,
`messages.*` calls, and template copy, in the public app as much as the admin.
Fixing this is a small, self-contained change with a test in
`apps/surveys/tests/test_views.py`.
