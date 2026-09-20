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

## 4. Sexo and fecha de nacimiento are collected but nothing reads them 🟡

**Where:** `accounts.UserProfile.sex` / `date_of_birth` / `age`; the would-be
consumer is `apps/nom035/aggregates.py`, which today groups only by área.

**What:** Employees supply both at activation, and `age` derives completed years
on demand, but no dashboard, filter or chart segments on either. Collecting them
was the whole point: reading NOM-035 results by age range and sex, and by
combinations such as *mujeres de un área específica entre 18 y 35 años*.

**Why it was left alone:** the decisions that shape it — the age bands, the
minimum group size below which a segment must not be displayed (a real
re-identification risk in a small company), and where the segmentation UI lives —
need the domain expert and real data to look at. Deferred to a feature doc of its
own rather than guessed at. Until that doc exists this is branch C work: no code
before it is written and signed off.

---

## 5. The employee roster is a flat list, not grouped by localidad → área 🟡

**Where:** `apps/core/views.py` (the roster queryset) and
`templates/core/employee_list.html`.

**What:** The roster is one flat list ordered by apellido paterno, materno, then
nombre. Grouping it by localidad and then by área was discussed alongside the
demographics work and split out.

**Why it was left alone:** it is an undocumented feature in its own right, not an
extension of activation, so it needs `docs/platform/employee-roster.md` written
first. It depends on the paternal-surname ordering that now exists, so nothing
blocks it.
