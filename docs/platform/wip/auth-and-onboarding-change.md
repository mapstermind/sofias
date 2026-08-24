# Change brief — employee demographics at activation

Branch: `feat/employee-demographics`
Live doc this rewrites: [`docs/platform/auth-and-onboarding.md`](../auth-and-onboarding.md)

## What changes

The profile activation form gains sexo and fecha de nacimiento, and its single
`apellidos` field becomes the two-surname pair Mexican records use:

| Field | Model | Required at activation |
|---|---|---|
| `User.paternal_last_name` | `accounts.User` | yes |
| `User.maternal_last_name` | `accounts.User` | no |
| `UserProfile.sex` | `accounts.UserProfile` | yes |
| `UserProfile.date_of_birth` | `accounts.UserProfile` | yes |

`User.last_name` is removed. `first_name`, `position`, `area` and `location` are
unchanged.

## Why

`docs/internal/meetings/20260803.md` records the Aug 3 2026 session with the
domain expert. Its activation checklist names six fields the employee must fill
in; four of them do not exist yet:

```
- El usuario, después de "activar" su cuenta con código de empresa, pedir que llene:
  - [ ] apellido Paterno,     - [ ] sexo (Masculino/Femenino),
  - [ ] apellido Materno,     - [ ] fecha de nacimiento,
  - [x] nombre(s),            - [x] localidad, [x] área
```

The purpose behind them is segmentation: reading NOM-035 results by age range
and sex, and by combinations such as *mujeres de un área específica entre 18 y
35 años*. That analysis is **not** part of this change — see Scope below.

## Scope

**In scope:** the four fields, their model placement, activation-form capture and
validation, the admin and roster ripple caused by removing `last_name`, and the
docs.

**Out of scope:** every demographic breakdown, filter and chart. Age bands, the
minimum group size before a segment may be displayed, and where the segmentation
UI lives are all deferred to a feature doc of their own, written once real
demographic data exists to look at. `apps/nom035/aggregates.py` is untouched by
this branch.

## Design decisions

**Surnames live on `User`; sex and date of birth live on `UserProfile`.**
Recorded with its rejected alternatives in
[ADR-0005](../../adr/adr-0005-two-surname-names-and-profile-demographics.md).

**`last_name` is removed, not kept as a derived field.** `AbstractUser` is
abstract, so `last_name = None` on the concrete model drops the column outright.
Also ADR-0005.

**Model layer nullable, form layer required.** All four fields are `blank` (and
`date_of_birth` `null`) on the model, and required in `ProfileActivationForm`.
This is the shape `area` already has, and it is forced by the same fact:
`import_users_from_csv` creates the `User` and `UserProfile` rows before the
employee has answered anything.

**`maternal_last_name` is optional even in the form.** Not everyone has two
surnames; requiring it would block foreign-national employees at the activation
gate for no analytical gain.

**Age is computed, not stored.** `UserProfile.age` is a property over
`date_of_birth` and today's date in `America/Mexico_City`. The alternative —
snapshotting age and sex onto the submission when it completes — was rejected
because `area` is already read live from the profile
(`apps/nom035/aggregates.py:9`), and a dashboard mixing one frozen dimension with
one live dimension is worse than either choice made consistently.

**Sex labels are `Masculino` / `Femenino`**, the wording the requirement uses.
Stored values are `male` / `female`, English like every other identifier.

**Date of birth is entered as three dropdowns** (`forms.SelectDateWidget`), with
`years` spanning `today.year - 99` to `today.year - 15`. A native `<input
type="date">` opens on the current year, which is the wrong decade for a
birthdate on a phone. Month names come out Spanish from `LANGUAGE_CODE`.

**Existing activated employees are sent back through the form.** The migration
sets `is_activated=False` on employee profiles;
`RequireProfileActivationMiddleware` already traps them on the activation page,
which prefills everything on record. No compatibility shim, no
nullable-forever escape hatch.

## What this makes wrong in `auth-and-onboarding.md`

| Location | Why it becomes wrong |
|---|---|
| `### Profile activation`, activation-behavior list | Names the form fields as "nombre(s), apellidos, cargo, área picker" and states "Nombre(s) and apellidos are required" |
| Same section, final bullet | "`User.first_name`/`User.last_name` and `UserProfile.position`/`area`/`location`/`is_activated` are saved in a single transaction" |
| `## Inputs` | "Nombre(s), apellidos, and optional cargo" |
| `## Outputs` | "Updated `User.password`, `User.must_change_password`, `User.first_name`, and `User.last_name`" and the `UserProfile` line |
| `## API / routes / commands`, `/cuentas/completar-perfil/` POST row | Lists `first_name`, `last_name`, optional `position`, `area`, optional `location` |
| `## Data model impact`, Fields | Does not list the four new fields |
| `## Data model impact`, Migrations | "No migration is part of this spec" — one now is |
| `## Invariants`, `## Acceptance criteria`, `## Test mapping` | Reference the old field set |

## Ripple outside the feature doc

**`apps/accounts`**

- `models.py` — the fields above, `get_full_name()` override, `Sex` choices,
  `age` property, `clean()` rejecting a future date of birth and anything outside
  15–99 completed years.
- One migration: drop `last_name`, add three columns, flip `is_activated`.
- `forms.py` — `ProfileActivationForm` gains the four fields with Spanish
  `error_messages`.
- `views.py:296-297, 322-324` — `setup_profile` prefill and the `update_fields`
  list inside the existing transaction.
- `admin.py:31-37` — **fails Django's system checks if missed.**
  `CustomUserAdmin` builds `list_display` and `fieldsets` as `UserAdmin.X + (...)`,
  and Django's defaults name `last_name` in `list_display`, `search_fields` and
  the "Personal info" fieldset. All three must be declared explicitly.
  `UserProfileAdmin` gains `sex` and `date_of_birth`.
- `importers.py` — **no change.** `REQUIRED_HEADERS` never carried names.

**`apps/core`**

- `views.py:304` — the roster's `.order_by("user__first_name", "user__last_name")`
  becomes paternal, maternal, first. Sorting a Mexican roster by given name is not
  how it reads.
- `templates/core/employee_list.html:38-39` and
  `templates/core/employee_detail.html:4,19-20,37-38,45-46` — the hand-assembled
  `{{ user.first_name }} {{ user.last_name }}` pairs collapse to
  `{{ user.get_full_name }}`; the initials take first + paternal.

**Frontend build** — `npm run build:css` as the final step; `SelectDateWidget`
renders three selects in a row and those grid classes are not compiled yet.

**Other live docs to rewrite in this diff:** `docs/platform/database.md` (:53,
:360), `docs/platform/csv-user-import.md` (:108),
`docs/platform/localization.md` (:253), `apps/accounts/CLAUDE.md`.

## Testing

Python tests assert the server-rendered contract only; there is no JS runner.

- `get_full_name()` with and without a maternal surname.
- `age` across a birthday boundary.
- `clean()` rejecting a future date of birth and an out-of-range age.
- The collation-ordering test at `apps/accounts/tests/test_models.py:130` moved
  onto `paternal_last_name`.
- Form: paternal, sex and date of birth required; maternal optional.
- View: the activation POST writing the `User` and `UserProfile` fields in one
  transaction; prefill.
- `apps/core`: the roster's new ordering.
- `Sex.MALE.label == "Masculino"` — `conftest.py`'s `assert_explicit_labels`
  walks `model._meta` and does **not** check `TextChoices` labels.
- `call_command("check")` — the cheapest guard against the `admin.E108` trap.

Browser check-list for the reviewer: the three date-of-birth dropdowns rendering
Spanish month names, the sex select, the roster's new order, and the initials on
the employee detail page.

## Open questions for the domain expert

- `docs/internal/meetings/20260803.md` carries an unresolved duda — *"¿Queremos
  mantener 'Cargo' como un campo que pueda llenar el empleado?"*. This branch
  leaves `position` exactly as it is.
- The minimum age is set at 15, Mexico's legal working age. If the client's
  workforce is 18+ by policy, the floor should rise.

## Follow-on work

The grouped employee roster (localidad → área → apellido paterno) is a separate,
currently undocumented feature and gets its own doc,
`docs/platform/employee-roster.md`. It sorts by `paternal_last_name`, so it
follows this branch rather than accompanying it.
