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

---

## 2. Tailwind compiles utilities out of Markdown prose 🟢

**Where:** `static/css/main.css` / the Tailwind v4 build.

**What:** Tailwind v4's automatic source detection scans the repository in
addition to the explicit `@source` lines, so English words in Markdown that
happen to match utility names get compiled into shipped CSS. Observed: `.invert`
compiled from the word "invert" in an ADR sentence.

**Impact:** A few dead rules; harmless today but it accumulates silently.

**Suggested fix:** `@import "tailwindcss" source(none);` in
`static/css/main.css`, keeping the explicit `@source` lines so only `templates/`
and `static/` are scanned.

---

## 3. Accent-sensitive catalog uniqueness is undocumented 🟢

**Where:** `apps/accounts/models.py` — `UniqueConstraint(company, Lower("name"))`
on `CompanyCatalogEntry`.

**What:** `Lower()` case-folds but does **not** fold accents, so `Dirección` and
`Direccion` are two distinct áreas within the same company. Both appear in the
activation picker, and an employee choosing between them is picking between two
spellings of one área — which then aggregate as separate buckets.

**Why it may be fine:** arguably correct — they are different strings, and the
admin curates the list. But nobody has decided this on purpose.

**If it should change:** use `unaccent` (requires the Postgres extension) in the
constraint. Either way, record the decision and add a test pinning it.
