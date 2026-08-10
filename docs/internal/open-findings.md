# Open Findings

Issues surfaced during development that are **out of scope for the change that
found them**. Each entry records what it is, where it lives, and why it was left
alone — so the decision to defer is deliberate and revisitable, not forgotten.

This is a working list, not a spec. Delete an entry when it is fixed or when the
team decides it is not worth fixing (say which, and why).

---

## 1. Django admin mixes English and Spanish 🟡 — promoted to a feature doc

**Where:** `config/settings.py` (`LANGUAGE_CODE = "en-us"`) and model metadata
across all four apps.

**Status:** Scoped and written up as
[`docs/platform/localization.md`](../platform/localization.md). Scheduled for its
own session; three open questions there need answers before implementation.

Kept here only as a pointer — see that document for the analysis.
