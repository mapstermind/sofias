# Localization (es-MX)

## Status

Implemented.

## Overview

SOFIA-S is a Spanish-language product operated by Spanish-speaking users, but its
code is written in English. This document defines how those two facts coexist:
which strings a user sees, who owns each of them, and the single rule that keeps
English identifiers from leaking onto Spanish screens.

The public app (`templates/`) is Spanish — its copy is hand-written in templates
and forms. The **Django admin** is the primary working surface for the platform
administrator, and it reads as Spanish for the same reason: not by accident, but
because every piece of metadata behind it is written that way.

## Why we built it

The platform is intended to be handed to a **non-technical administrator** who
manages companies, users, and survey assignments entirely through the Django
admin console. That surface must read as a coherent Spanish product, not as a
developer tool with some Spanish labels bolted on.

## The three layers of user-visible text

Understanding the split is what makes the work mechanical rather than
open-ended. Every string a user sees comes from exactly one of these:

| Layer | Examples | Owned by | How it becomes Spanish |
|---|---|---|---|
| **1. Django's own strings** | "Agregar otro", "¿Está seguro?", "Este campo es obligatorio.", month names, date pickers | Django | `LANGUAGE_CODE` — Django ships Spanish catalogs; free |
| **2. Metadata we write** | `verbose_name`, `help_text`, `TextChoices` labels, `__str__`, admin fieldset titles | Us | Written in Spanish |
| **3. Python identifiers** | `is_activated`, `reference_code`, `legal_name` | Us | Never shown to users **— because layer 2 is filled in** |

**Layer 3 is the trap.** When a field has no explicit `verbose_name`, Django
derives the user-visible label from the Python attribute name:
`is_activated` → "Is activated", `must_change_password` → "Must change
password", `legal_name` → "Legal name". English identifiers become English UI
automatically.

So "English code, Spanish UI" is not a convention that holds on its own —
**`verbose_name` is the bridge that makes it true.** Every user-visible field
has one.

### The rule, enforced

Every model in `apps/accounts`, `apps/surveys`, `apps/responses` and
`apps/nom035` carries:

- an explicit lowercase Spanish `verbose_name` on **every** field,
- a Spanish `Meta.verbose_name` / `verbose_name_plural`,
- Spanish labels on every `TextChoices`,
- a Spanish `__str__` where one is defined.

Labels are lowercase (`verbose_name = "empresa"`); Django applies `capfirst` at
render time, so the changelist header reads *Empresa* and the app index reads
*Empresas*.

Fields inherited from `AbstractUser` (`username`, `password`, `is_staff`,
`date_joined`, `groups`, …) are left alone: Django ships their Spanish
translations and `LANGUAGE_CODE` picks them up.

The `assert_explicit_labels` fixture in the root `conftest.py` walks an app and
fails listing every field whose label Django derived from its English
identifier. Each app's `tests/test_admin.py` calls it, so a new model that
forgets a `verbose_name` fails the build rather than shipping an English label.

## Scope

**Covered:**

- `LANGUAGE_CODE = "es-mx"`, so all of layer 1 is Spanish.
- `TIME_ZONE = "America/Mexico_City"`.
- Spanish metadata on **every model in the four apps** — including those with no
  registered `ModelAdmin` (`EmailOTP`, `Role`, `CompanyArea`, `CompanyLocation`),
  whose auto-generated permissions appear in the Groups permission picker.
- Spanish `AppConfig.verbose_name` on the four apps that own models.
- Branded admin chrome.
- Spanish `auth_permission` names (see [Permission names](#permission-names)).

**Not covered:**

- The public app templates: they are already Spanish.
- A second language, `gettext` catalogs, `LOCALE_PATHS`, `.po` files, or a
  language switcher. There is one target language.
- Python identifiers, module names, and docstrings — code stays English
  (see `.claude/CLAUDE.md`).
- **Authorization group names** (`Admins`, `Principal Exec`, `Secondary Exec`,
  `Employees`). They are `auth.Group.name` values looked up by string in four
  places and accepted as a CSV column value, so renaming them is a behavior
  change rather than presentation. Tracked in
  [`docs/internal/open-findings.md`](../internal/open-findings.md).

## Public behavior

An administrator opening the Django admin sees:

- Spanish chrome and validation from Django itself ("Agregar otro", "¿Está
  seguro?", "Este campo es obligatorio.").
- The admin branded `Administración SOFIA-S` rather than `Administración de
  Django`.
- App groups named *Cuentas*, *Encuestas*, *Respuestas* and *NOM-035*.
- Spanish model names in the index and breadcrumbs (*Empresas*, *Áreas*,
  *Perfiles de colaborador*, *Envíos de encuesta*, *Valoraciones*).
- Spanish column headers on every changelist and Spanish labels on every form
  field, with help text in Spanish where a field needs explanation.
- A Groups permission picker that reads *Cuentas | empresa | Puede agregar
  empresa* end to end.
- Timestamps in Mexico City time and dates in es-MX format.

Nothing about the public employee-facing app changes except displayed times,
which shift with `TIME_ZONE`.

## Timezone

`USE_TZ` stays `True`, so storage remains UTC and only display shifts.
`LANGUAGE_CODE` changes date *formatting* but not the timezone, so without this
an operator would read a 15:00 submission from a Mexican client as 21:00.
Mexico abolished DST in 2022, so `America/Mexico_City` is a flat UTC−6.

## Data model impact

No migrations alter columns. Changing `Meta.verbose_name` generates an
`AlterModelOptions` migration and changing a field's `verbose_name`, `help_text`
or choice labels generates an `AlterField` — both no-ops at the database level.
The four migrations are `accounts/0005`, `surveys/0002`, `responses/0002` and
`nom035/0002`.

## Permission names

`auth_permission.name` is what the Groups permission picker displays, and it does
not follow `Meta.verbose_name` on its own. Django builds the four built-in
permission names from a hardcoded, **untranslated** `"Can %s %s"` template
(`django/contrib/auth/management/__init__.py`), so a Spanish `verbose_name`
alone yields `"Can add empresa"` — English and Spanish in one string.

`apps/core/permissions.py` fixes this with a `post_migrate` receiver,
`rename_permissions_to_spanish`, connected in `CoreConfig.ready()`. It derives
each name from the model's own `verbose_name`, rewrites `Permission.name` for the
four project apps on every `migrate`, and leaves Django's own apps alone. It is
display-only: codenames are never touched, so `bootstrap_groups` and every
`has_perm` check are unaffected.

It is connected without a sender because each app's permissions only exist once
that app's own `post_migrate` has fired; `django.contrib.auth` sits earlier in
`INSTALLED_APPS`, so `create_permissions` always runs first.

### Why a receiver rather than declaring the names

Declaring them is possible. Setting `Meta.default_permissions = ()` and listing
all four actions in `Meta.permissions` with Spanish names produces identical
codenames and passes `manage.py check`. Without the empty `default_permissions`
it does not: the explicit codenames collide with the built-ins and every model
raises `auth.E005`.

The receiver is preferred for three reasons:

- **Failure mode.** `default_permissions = ()` means a model whose `permissions`
  block is missing or incomplete gets **no permissions at all** — nobody can be
  granted access to it, and the breakage surfaces later as a puzzling
  authorization bug. Forgetting the receiver's app-label list costs an English
  label instead.
- **Volume.** Four hardcoded strings on each of the seventeen models, versus one
  ~45-line module.
- **Drift.** Declared names are literals, so renaming a model's `verbose_name`
  silently leaves four stale permission strings behind. The receiver derives the
  name, so the two cannot disagree.

One further difference: `create_permissions` reads the **historical migration
state**, so a `verbose_name` edit does not reach `auth_permission` until its
`AlterModelOptions` migration exists. The receiver reads the live app registry
and is not subject to that lag.

## Key decisions

- **Decision:** Hardcode Spanish strings; do not use `gettext_lazy`.
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

- **Decision:** Cover every model in the four apps, not only the operator-facing
  ones.
  **Reason:** Consistency, and the boundary leaks anyway — an unregistered
  model's auto-generated permissions still surface in the Groups picker.

- **Decision:** Spanish permission names come from a `post_migrate` receiver, not
  from `default_permissions = ()` plus explicitly declared `Meta.permissions`.
  **Reason:** Both produce the same codenames and names. The receiver wins on
  failure mode — an incomplete declaration creates no permissions at all, while a
  gap in the receiver's coverage only leaves an English label. It is also ~45
  lines against four strings on each of seventeen models, and it derives names
  from `verbose_name` instead of duplicating them. See
  [Why a receiver rather than declaring the names](#why-a-receiver-rather-than-declaring-the-names).

- **Decision:** `User.first_name` / `last_name` are labelled `"nombre(s)"` and
  `"apellidos"` rather than reusing Django's catalog.
  **Reason:** Django's `es_MX` renders `last name` as the singular `"apellido"`,
  which is wrong for Mexican usage (paterno + materno). Hardcoding also keeps
  the no-`gettext` rule absolute.

- **Decision:** Accept Django's `es_MX` date formats; no `FORMAT_MODULE_PATH`.
  **Reason:** `SHORT_DATE_FORMAT` is already `d/m/Y`, and the long form
  (`9 de Agosto de 2026 a las 15:00`) is correct enough for admin columns. A
  settings-level `DATE_FORMAT` is ignored when a locale formats module exists,
  so overriding means carrying a custom module for a cosmetic gain. Note that
  Django's `es_MX` catalog capitalizes month names, which Spanish orthography
  does not; that is upstream, not ours.

## Test mapping

| Behavior | Location |
|---|---|
| Language, timezone, admin chrome, app index names, permission names | `apps/core/tests/test_localization.py` |
| No auto-derived label in an app; representative rendered labels | `apps/<app>/tests/test_admin.py` |
| The label guard itself | `assert_explicit_labels` in `conftest.py` |

The permission-name tests read rows written by `post_migrate` at
database-creation time. `addopts` carries `--reuse-db`, so run them with
`pytest --create-db` after any change to model `verbose_name` or
`Role.Meta.permissions` — a reused database keeps the names it was born with.

## Linked ADRs

None required — this sets a convention rather than choosing between competing
architectures. If the `gettext` decision is ever revisited, that reversal
warrants an ADR.
