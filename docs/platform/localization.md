# Localization (es-MX)

## Status

Draft — not implemented. Scheduled for its own session.

## Overview

SOFIA-S is a Spanish-language product operated by Spanish-speaking users, but its
code is written in English. This document defines how those two facts coexist:
which strings a user sees, who owns each of them, and the single rule that keeps
English identifiers from leaking onto Spanish screens.

The public app (`templates/`) is already Spanish — its copy is hand-written in
templates and forms. The gap is the **Django admin**, which is the primary
working surface for the platform administrator and currently renders a mix of
English and Spanish.

## Why we're building it

The platform is intended to be handed to a **non-technical administrator** who
manages companies, users, and survey assignments entirely through the Django
admin console. That surface must read as a coherent Spanish product, not as a
developer tool with some Spanish labels bolted on.

## The three layers of user-visible text

Understanding the split is what makes the work mechanical rather than
open-ended. Every string a user sees comes from exactly one of these:

| Layer | Examples | Owned by | How it becomes Spanish |
|---|---|---|---|
| **1. Django's own strings** | "Add another", "Delete?", "This field cannot be blank.", month names, date pickers | Django | `LANGUAGE_CODE` — Django ships Spanish catalogs; free |
| **2. Metadata we write** | `verbose_name`, `help_text`, admin column headers, inline section titles | Us | Write them in Spanish |
| **3. Python identifiers** | `is_activated`, `reference_code`, `legal_name` | Us | Never shown to users **— but only if layer 2 is filled in** |

**Layer 3 is the trap.** When a field has no explicit `verbose_name`, Django
derives the user-visible label from the Python attribute name:
`is_activated` → "Is activated", `must_change_password` → "Must change
password", `legal_name` → "Legal name". English identifiers become English UI
automatically.

So "English code, Spanish UI" is not a convention that holds on its own —
**`verbose_name` is the bridge that makes it true.** Every user-visible field
needs one.

### Current state, measured

| App | Model fields | With an explicit `verbose_name` |
|---|---|---|
| `apps/accounts` | 28 | 4 |
| `apps/surveys` | 33 | 0 |
| `apps/responses` | 8 | 0 |
| `apps/nom035` | 10 | 0 |

Effectively the whole admin displays auto-derived English labels today. The four
exceptions are on `CompanyArea` / `CompanyLocation` / `UserProfile.area` /
`UserProfile.location`, added with the área-localidad catalogs.

## Scope

**In scope:**

- Set `LANGUAGE_CODE = "es-mx"` so all of layer 1 becomes Spanish.
- Decide and set `TIME_ZONE` (see Open questions).
- Add Spanish `verbose_name` / `verbose_name_plural` / `help_text` to the models
  and fields an operator sees, and Spanish `description` to admin display
  callables and inline section headers.
- Fix `Company.Meta.verbose_name_plural`, currently the English `"companies"`
  (it exists only to stop Django rendering "companys").
- Record the resulting convention in `.claude/CLAUDE.md` so it is applied to
  every new model rather than re-litigated.

**Out of scope:**

- Any behavior change. This is presentation only — no schema changes beyond
  model `Meta`/field metadata, no view logic, no URL changes.
- Translating the public app templates: they are already Spanish.
- A second language, `gettext` catalogs, `LOCALE_PATHS`, `.po` files, or a
  language switcher. There is one target language.
- Translating Python identifiers, module names, or docstrings — code stays
  English (see `.claude/CLAUDE.md`).

## Public behavior

After this work, an administrator opening the Django admin sees:

- Spanish chrome and validation from Django itself ("Agregar otro", "¿Está
  seguro?", "Este campo no puede estar en blanco").
- Spanish model names in the app index and breadcrumbs ("Empresas", "Áreas",
  "Perfiles de usuario").
- Spanish column headers on every changelist and Spanish labels on every form
  field, with help text in Spanish where a field needs explanation.
- Dates formatted per es-MX conventions (`d/m/Y`).

Nothing about the public employee-facing app changes.

## Data model impact

No migrations that alter columns. Changing `Meta.verbose_name` does generate an
`AlterModelOptions` migration, which is a no-op at the database level.

**One wrinkle worth planning around:** `Meta.verbose_name` feeds the
auto-generated permission names in `auth_permission` ("Can add company" →
"Can add empresa"). Those rows are written when a model is first migrated and
are **not** rewritten when `verbose_name` changes later. While the platform is
pre-production and databases are recreated freely, this costs nothing —
recreating the database regenerates them in Spanish. It becomes a data-migration
chore once there is data worth keeping, so doing this work *before* production is
materially cheaper than after.

Verify after the change that `python manage.py bootstrap_groups` still runs
clean, since it assigns permissions by codename (codenames are unaffected).

## Key decisions

- **Decision:** Hardcode Spanish strings; do not introduce `gettext_lazy`.
  **Reason:** There is one target language. Without `LOCALE_PATHS`, `.po` files,
  and a `compilemessages` step, `_()` is ceremony that renders identically —
  and building translation infrastructure for a second language that does not
  exist is the same premature generality rejected in ADR-0002 and ADR-0003.

- **Decision:** `LANGUAGE_CODE` does the heavy lifting; we only write what Django
  cannot know.
  **Reason:** Layer 1 is the bulk of the visible strings and costs one line.
  Hand-writing Spanish for anything Django already ships would be wasted work
  that also drifts out of date with Django releases.

- **Decision:** Code, identifiers, and comments stay English.
  **Reason:** Already the project convention; `verbose_name` is the explicit
  bridge, so the two do not conflict.

## Open questions

These need an answer before implementation starts.

1. **How far does the sweep go?** Three candidate scopes:
   - *Operator-facing models only* (~50 fields) — `accounts` (User, Company,
     CompanyArea, CompanyLocation, UserProfile, SetupAccessCode) plus `surveys`
     (Survey, Module, SurveyAssignment). Leaves developer/debug admins in
     English: `Question`, `Choice` (seeded by `seed_nom035_survey`, not
     hand-edited), `SurveySubmission`, `Answer`, `SubmissionScore`.
     *Recommended* — these are the screens the administrator actually works in.
   - *Every registered admin model* (~79 fields) — fully consistent, no English
     anywhere, but includes screens only developers open.
   - *`apps/accounts` only* (~28 fields) — smallest useful slice.

   If the "operator-facing only" split is chosen, record **why** each excluded
   admin is a developer surface, so the boundary is not mistaken for an
   oversight later.

2. **Should `TIME_ZONE` change from `"UTC"` to `"America/Mexico_City"`?**
   `LANGUAGE_CODE` changes date *formatting* but not the timezone, so an
   operator would otherwise read a 3pm submission as 9pm. `USE_TZ` stays `True`,
   so storage remains UTC and only display shifts. This affects the public app
   too (due dates, submission timestamps, OTP expiry), which is why it is called
   out rather than assumed. *Recommendation: change it.*

3. **Does the admin index need reordering or renaming beyond model names?**
   Django groups the admin by app label (`accounts`, `surveys`, `responses`,
   `nom035`), which are English and not configurable via `verbose_name` alone —
   it needs `AppConfig.verbose_name`. Cheap to add; confirm whether the app
   groupings should read as "Cuentas", "Encuestas", etc.

## Acceptance criteria

- Opening any operator-facing admin changelist or change form shows no
  auto-derived English labels.
- Submitting an invalid admin form shows Spanish validation messages.
- `python manage.py check` and the full test suite pass unchanged — this work
  must not alter behavior.
- A freshly created database plus `bootstrap_groups` yields Spanish permission
  names in the group permission picker.
- `.claude/CLAUDE.md` states the convention so new models follow it by default.

## Test mapping

Presentation-only work, so existing tests should pass untouched — that is itself
the primary check. Worth adding:

| Behavior | Suggested location |
|---|---|
| An operator-facing admin form renders Spanish field labels | `apps/accounts/tests/test_admin.py` |
| Django's own validation renders in Spanish | `apps/accounts/tests/test_admin.py` |

Assert on a representative label rather than every field; the value is catching
a `LANGUAGE_CODE` regression, not pinning every string.

## Linked ADRs

None required — this sets a convention rather than choosing between competing
architectures. If the `gettext` decision is ever revisited, that reversal
warrants an ADR.
