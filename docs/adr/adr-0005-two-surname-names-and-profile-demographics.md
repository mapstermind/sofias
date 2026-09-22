# ADR-0005: Two-surname user names and profile-level demographics

Date: 2026-08-23
Status: Accepted

## Context

The Aug 3 2026 session with the domain expert
(`docs/internal/meetings/20260803.md`) lists what an employee must supply when
activating their account. Four of those facts have no home in the data model:

```
- El usuario, después de "activar" su cuenta con código de empresa, pedir que llene:
  - [ ] apellido Paterno,     - [ ] sexo (Masculino/Femenino),
  - [ ] apellido Materno,     - [ ] fecha de nacimiento,
```

The purpose is segmentation of NOM-035 results — reading risk by age range and
by sex, and by combinations of those with área, such as *mujeres de un área
específica entre 18 y 35 años*. Today `apps/nom035/aggregates.py` can only group
by `UserProfile.area`, because área is the only respondent attribute the platform
records.

Two placement questions follow, and they do not have the same answer.

**The surname question.** Django's `AbstractUser` models a name as
`first_name` + `last_name`. A Mexican record is `nombre(s)` + `apellido paterno`
+ `apellido materno`, and the two surnames are not interchangeable: the paternal
one is what a roster sorts by and what an official document leads with. Storing
both in one `last_name` field means the platform can render a name but cannot
sort or search one correctly.

**The demographics question.** `accounts.User` and `accounts.UserProfile` are a
one-to-one pair, so either could physically hold `sex` and `date_of_birth`. They
differ in who has one: **operators and admins deliberately have no
`UserProfile`** (`apps/accounts/CLAUDE.md`, and `RequireProfileActivationMiddleware`
gates on `can_take_assigned_surveys` precisely so no admin carve-out is needed).

## Decision

**`User.last_name` is removed and replaced by `paternal_last_name` and
`maternal_last_name`.** `AbstractUser` is abstract, so setting `last_name = None`
on the concrete model drops the column outright rather than shadowing it. Both
new fields carry `db_collation = SPANISH_COLLATION` for the same reason
`first_name` already does — the employee roster orders by them. `get_full_name()`
is overridden to join the three parts, skipping empties.

**`sex` and `date_of_birth` are added to `UserProfile`, not to `User`.** `sex` is
a `TextChoices` pair stored as `male`/`female` and labelled `Masculino`/`Femenino`;
`date_of_birth` is a `DateField`.

**Age is derived, not stored.** `UserProfile.age` is a property computed from
`date_of_birth` against today's date in `America/Mexico_City`. Nothing is written
to `responses.SurveySubmission` or `nom035.SubmissionScore`.

All four fields are nullable/blank at the model layer and required in
`ProfileActivationForm` — except `maternal_last_name`, which is optional
everywhere.

## Consequences

**Positive:**

- A roster can sort by apellido paterno, which is how a Mexican list of people
  reads, and a search can match either surname independently.
- Every dimension a demographic breakdown needs — área, localidad, sex, date of
  birth — hangs off one related object, so `apps/nom035/results.py` reaches every
  dimension through one
  `select_related("submission__user__profile__area", "submission__user__profile__location")`
  rather than straddling two models for one conceptual grouping.
- Operator accounts carry no demographic columns, because they carry no
  `UserProfile`. There is no class of rows for which these fields are permanently
  meaningless.
- Requiredness is enforced where every other self-reported fact is already
  enforced — `ProfileActivationForm` — so there is one rule rather than two.
- The name is still entirely on `User`, so `get_full_name()` remains a `User`
  method and Django's admin keeps a coherent "Información personal" fieldset.

**Negative:**

- `CustomUserAdmin` composes `list_display` and `fieldsets` from `UserAdmin`'s
  defaults, and those name `last_name` in `list_display`, `search_fields` and the
  personal-info fieldset. All three must now be declared explicitly, and the
  penalty for forgetting is a failed system check rather than a quiet
  misrender. A `call_command("check")` test guards it.
- Any third-party package that assumes `user.last_name` exists will break. None
  is installed today; one added later must be checked against this.
- Sex and date of birth are facts about a person rather than about an employment
  relationship, so a reader looking for them on `User` will not find them there.
  `UserProfile` being a never-recreated one-to-one means nothing is lost — a
  company change edits the same row — but the placement has to be learned.
- Every employee who had already activated must activate again. The migration
  sets `is_activated=False` on employee profiles and the existing middleware
  traps them on the activation page, which prefills what is on record. This is a
  deliberate re-collection rather than a backfill: nobody but the employee knows
  their own date of birth.
- Reports are not reproducible across time. An age band computed today differs
  from the same query run next year, because the underlying date of birth is
  fixed but the age is not.

## Alternatives considered

- **Keep `last_name` as a derived field**, auto-populated in `save()` from the
  two authored surnames. Rejected: a denormalized column that no code reads is a
  column that drifts. Its only benefit was leaving the admin and the roster
  untouched, which is a one-time cost paid once rather than a standing one.
- **Reinterpret `last_name` as the paternal surname** and add only
  `maternal_last_name` beside it. Smallest diff, and rejected for the reason the
  diff is small: the column would no longer say what it holds, and every future
  reader has to be told.
- **Put `sex` and `date_of_birth` on `User`.** The purist reading — they are
  facts about a person, and the person is the `User`. Rejected: admins and
  operators have no `UserProfile` by design, so on `User` these two columns would
  be permanently null for every operator account, and the demographic breakdown
  would have to join two models to assemble one grouping key.
- **Move `first_name` to `UserProfile` too**, putting the whole name beside the
  demographics. Rejected: it would leave `User` with no human name at all, break
  `get_full_name()` as a `User` method, and require a custom admin display for
  every account list — a large cost to buy consistency with a field set that only
  employees have.
- **Snapshot sex and age-at-answer onto the submission** when it completes, so a
  report reproduces forever. Rejected for now: `area` is already read live from
  the profile, so snapshotting only the demographics would give one dashboard a
  mix of frozen and live dimensions — worse than either choice applied
  consistently. If a historical, STPS-facing report later needs reproducibility,
  it needs every dimension frozen together, which is a decision of its own.
- **A free-text `sex` field.** Rejected for the reason ADR-0004 replaced
  free-text `department`: a field that feeds a grouping needs stable identity, and
  normalization-by-luck is what produced the buckets that ADR exists to prevent.

## Links

- Requirement: `docs/internal/meetings/20260803.md`
- Spec: `docs/platform/auth-and-onboarding.md`, `docs/platform/database.md`
- Related: [ADR-0004 — per-company área/localidad catalogs](adr-0004-per-company-area-and-locality-catalogs.md)
  — establishes `UserProfile` as the home of the attributes a breakdown groups by
- App docs: `apps/accounts/CLAUDE.md`
