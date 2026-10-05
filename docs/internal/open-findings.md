# Open Findings

Issues surfaced during development that are **out of scope for the change that
found them**. Each entry records what it is, where it lives, and why it was left
alone — so the decision to defer is deliberate and revisitable, not forgotten.

This is a working list, not a spec. Delete an entry when it is fixed or when the
team decides it is not worth fixing (say which, and why).

---

## 1. `auth.Group.name` is stored in English 🟡

**Where:** `apps/accounts/roles.py` (the canonical four names),
`apps/accounts/management/commands/bootstrap_groups.py` (`GROUP_PERMISSIONS`),
`apps/accounts/importers.py`, `apps/accounts/views.py`
(`_redirect_after_login`), `apps/core/views.py`, `conftest.py`
(`bootstrap_groups` fixture).

**What:** The four stored group names — `Admins`, `Principal Exec`,
`Secondary Exec`, `Employees` — are English. They are shown in Spanish
everywhere a user reads a role, through the labels in `apps/accounts/roles.py`;
what is still English is the stored value itself, which surfaces on the admin's
Grupos page and is the accepted value of the CSV importer's `group` column.

**Why it was left alone:** `auth.Group.name` is matched **by string** at several
call sites and the CSV import contract accepts it as a column value, so renaming
it is a behavior change with an input-format consequence rather than the
presentation-only work
[`docs/platform/localization.md`](../platform/localization.md) covers. Doing it
properly means picking Spanish names, updating `roles.py` and every string
match, migrating the existing rows, and deciding whether the importer keeps
accepting the English spellings.

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

---

## 3. The minimum activation age of 15 is a legal floor, not a client policy 🟡

**Where:** `apps/accounts/models.py` (`MIN_ACTIVATION_AGE`), enforced by
`UserProfile.clean()` and by `ProfileActivationForm.clean_date_of_birth()`, and
reflected in the Año dropdown's range.

**What:** Fecha de nacimiento must fall in a 15-to-99-year window. 15 is Mexico's
legal minimum working age, chosen because it is the only bound defensible without
asking anyone. If the client's workforce is 18+ by policy, the floor should rise —
a 16-year-old would currently pass validation.

**Why it was left alone:** it needs the domain expert, not a developer. Raising it
is a one-constant change plus its two boundary tests; the Año dropdown follows from
the same constant.

---

*Finding 4 — reading NOM-035 results by sex and age — is **resolved** by the
results page, with its minimum group size of 5 awaiting the
domain expert's confirmation. See
[`docs/platform/nom-035-results-dashboard.md`](../platform/nom-035-results-dashboard.md)
and [`docs/platform/nom-035-valoracion-supuestos.md`](../platform/nom-035-valoracion-supuestos.md).*

*Finding 5 — grouping the employee roster by localidad → área — is **resolved**,
by a different design than it sketched: the roster is narrowed with a search
box, four filters and a sort control rather than split into sections. See
[`docs/platform/employee-roster.md`](../platform/employee-roster.md).*
