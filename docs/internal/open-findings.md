# Open Findings

Issues surfaced during development that are **out of scope for the change that
found them**. Each entry records what it is, where it lives, and why it was left
alone — so the decision to defer is deliberate and revisitable, not forgotten.

This is a working list, not a spec. Delete an entry when it is fixed or when the
team decides it is not worth fixing (say which, and why).

---

## 1. Survey assignments are not scoped to the caller's company 🔴

**Where:** `apps/surveys/views.py` — `survey_detail(request, assignment_id)` does
`get_object_or_404(SurveyAssignment, id=assignment_id)` with no company filter.

**What:** Any authenticated user can open — and submit against — any company's
assignment by guessing or enumerating its integer id. There is no check that the
assignment's company matches the caller's `UserProfile.company`.

**Why it matters:** This is a tenant-isolation break, not a cosmetic one. A
submission created this way lands in another company's `SurveyAssignment`, so it
flows into that company's NOM-035 roll-up and dashboards.

**Found by:** code review of the área/localidad feature (Aug 2026). The
aggregation code was defensively hardened in that change — `_area_of()` in
`apps/nom035/aggregates.py` refuses to label a submission with an área belonging
to a different company, so a cross-company submission buckets as "Sin área"
instead of printing another client's catalog name. **That is mitigation of one
symptom, not a fix.** The underlying authorization gap is untouched.

**Suggested fix:** Scope the lookup to the caller's company (admins excepted),
mirroring the `reference_code` convention already used in `apps/core/views.py`.
Add a test asserting a user of company A gets 404 on company B's assignment.

---

## 2. Django admin mixes English and Spanish 🟡 — promoted to a feature doc

**Where:** `config/settings.py` (`LANGUAGE_CODE = "en-us"`) and model metadata
across all four apps.

**Status:** Scoped and written up as
[`docs/platform/localization.md`](../platform/localization.md). Scheduled for its
own session; three open questions there need answers before implementation.

Kept here only as a pointer — see that document for the analysis.

---

## 3. Tailwind compiles utilities out of Markdown prose 🟢

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

## 4. Accent-sensitive catalog uniqueness is undocumented 🟢

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

---

## 5. Retiring a localidad mid-activation silently substitutes another 🟢

**Where:** `apps/accounts/views.py` `setup_profile` +
`apps/accounts/forms.py` `ProfileActivationForm.implicit_location`.

**What:** If a company has two localidades, a user loads the activation form and
picks "Norte", and an admin deactivates "Norte" before the user submits, the
localidad field is dropped on the POST and `implicit_location` assigns the one
remaining localidad ("Matriz"). Activation succeeds with a localidad the user did
not choose.

**Why it's low priority:** requires an admin edit inside a user's form session.
The other TOCTOU directions already behave well (a deactivated área fails as
`invalid_choice`; a newly added second localidad makes the field required).

**If fixed:** detect that the submitted set differs from the offered set and
re-render with a "las opciones cambiaron, confirma tu selección" notice.
