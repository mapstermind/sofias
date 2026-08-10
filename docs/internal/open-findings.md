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

## 3. Accented names sort last under the database's C collation 🟢

**Where:** `CompanyCatalogEntry.Meta.ordering = ["name"]` (and every other
`ORDER BY` on user-visible Spanish text).

**What:** the database is created with `C.UTF-8` collation, i.e. byte order. A
name starting with an accented letter sorts after every ASCII name: `Álvaro
Obregón` lands below `Zacatecas` in the employee's localidad picker and in the
admin inline, and `Dirección` sorts after every `Direccion…`.

**Impact:** cosmetic but visible on any list an employee reads — the picker is
not in the alphabetical order a Spanish speaker expects. It also weakens the
admin's ability to spot a near-duplicate sitting next to its twin.

**If fixed:** create the database with an ICU/`es-MX` collation, or attach a
collation to the ordering (`Collate`) on the affected columns. The first is a
database-level decision; the second scatters per-query detail.
