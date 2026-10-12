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
