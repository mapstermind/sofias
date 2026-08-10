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
