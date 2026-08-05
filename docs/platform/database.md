# Database Structure

## Overview

The schema is organized around three distinct concerns:

1. **Who** — identity and company membership (`accounts` app)
2. **What** — the fixed survey instrument: `surveys` app `Survey → Module → Question → Choice`. There is no reusable question library and no numbered versions; operators seed fixed instruments (NOM-035) and a material change means a new `Survey`. See `docs/adr/adr-0002-flatten-survey-authoring-model.md`.
3. **Context & results** — who must answer, in which variant, and what they said (`surveys` app: `SurveyAssignment`; `responses` app: `SurveySubmission`, `Answer`)
4. **Derived valuation** — NOM-035 scores/NDR computed from the answers (`nom035` app: `SubmissionScore`, `GroupScore`)

A `Survey` is modular: each `Module` is tagged `applies_to` (`all`/`small`/`large`) and the company's headcount selects a variant (frozen on the assignment). Conditional branching is a data-driven `visible_when` rule.

---

## Apps & Models

### `accounts`

#### `Company`
Represents an organization that participates in surveys.

| Field | Type | Notes |
|---|---|---|
| `id` | BigAutoField | PK |
| `name` | CharField(255) | Display name |
| `legal_name` | CharField(255) | Official registered name |
| `rfc` | CharField(13) | Optional RFC |
| `address` | CharField(500) | Optional address |
| `reference_code` | CharField(5) | Unique alphanumeric identifier; auto-generated on save if blank |
| `created_at` | DateTimeField | Auto-set on creation |
| `updated_at` | DateTimeField | Auto-updated on save |

#### `CompanyArea` / `CompanyLocation`
Per-company catalogs of áreas and localidades, curated by an admin as inlines on the Company change page and offered to employees as pickers during account activation. Both derive from the abstract `CompanyCatalogEntry` and have identical fields. See [ADR-0004](../adr/adr-0004-per-company-area-and-locality-catalogs.md).

| Field | Type | Notes |
|---|---|---|
| `id` | BigAutoField | PK |
| `company` | ForeignKey → `Company` | CASCADE on company delete; `related_name` `areas` / `locations` |
| `name` | CharField(120) | Shown to the employee in the picker |
| `is_active` | BooleanField | Default `True`; unset to retire an entry without deleting it |

Constraint: `UniqueConstraint(company, Lower(name))` — names are unique per company **case-insensitively**, so "Ventas"/"ventas" cannot coexist, while two different companies may each have an "Operaciones". Default ordering is alphabetical by `name`. Neither model is registered as a standalone admin, so the Company inline is the only write surface.

#### `User`
Extends Django's `AbstractUser`. Inherits all standard auth fields (`username`, `email`, `password`, `is_staff`, etc.).

| Field | Type | Notes |
|---|---|---|
| `email` | EmailField | Unique; used by OTP, setup-code, and password fallback login |
| `must_change_password` | BooleanField | Forces setup-code/password-fallback users through the password-change flow |

#### `UserProfile`
Extends `User` with business context. Created separately from the auth user.

| Field | Type | Notes |
|---|---|---|
| `id` | BigAutoField | PK |
| `user` | OneToOneField → `User` | Cascades on user delete |
| `position` | CharField(255) | Job title, optional |
| `is_activated` | BooleanField | First-login activation flag, default `False` |
| `company` | ForeignKey → `Company` | SET NULL on company delete; nullable |
| `area` | ForeignKey → `CompanyArea` | SET NULL; nullable. Chosen by the employee at activation; groups the per-área NOM-035 breakdown |
| `location` | ForeignKey → `CompanyLocation` | SET NULL; nullable. Chosen at activation only when the company has >1; auto-assigned when it has exactly 1 |

`clean()` rejects an `area`/`location` belonging to a different company than `company`.

#### `Role`
Sentinel model used only to define project permissions. It is `managed = False`, so Django does not create a database table for it.

Permissions:

- `can_manage_surveys`
- `can_view_dashboard`
- `can_view_insights`
- `can_take_assigned_surveys`
- `can_manage_employees`
- `can_view_submissions`

#### `EmailOTP`
One-time passcode record for passwordless login. The email is stored as a plain `EmailField`, not a foreign key, because OTP request and verification are email-driven.

| Field | Type | Notes |
|---|---|---|
| `id` | BigAutoField | PK |
| `email` | EmailField | Indexed |
| `code` | CharField(6) | Six-digit code |
| `created_at` | DateTimeField | Auto-set on creation |
| `expires_at` | DateTimeField | Auto-set from `settings.OTP_EXPIRY_MINUTES` when omitted |
| `is_used` | BooleanField | Marks consumed OTPs |

#### `SetupAccessCode`
One-time first-login code for users whose client blocks external OTP email.

| Field | Type / Notes |
|---|---|
| `user` | ForeignKey to `accounts.User`; related name `setup_access_codes` |
| `code` | Nullable 9-digit code; populated while unused and cleared after use |
| `created_at` | DateTimeField |
| `used_at` | DateTimeField, nullable |

Unused setup access code values are globally unique. A user may have at most one unused setup access code.

---

### `surveys` — Survey instrument

#### `Survey`
A fixed survey instrument (e.g. NOM-035). Owns its modules directly. No library, no versions.

| Field | Type | Notes |
|---|---|---|
| `id` | BigAutoField | PK |
| `key` | SlugField | Unique stable identifier, e.g. `nom035` |
| `title` | CharField(255) | |
| `description` | TextField | Optional |
| `status` | CharField | `draft` / `published` / `archived` |
| `headcount_threshold` | PositiveIntegerField | Default 50; `headcount > threshold → large` variant |
| `created_at` / `updated_at` | DateTimeField | Auto |

#### `Module`
An ordered group of questions within a survey. Carries applicability and an optional branching rule.

| Field | Type | Notes |
|---|---|---|
| `id` | BigAutoField | PK |
| `survey` | ForeignKey → `Survey` | Cascades |
| `key` | SlugField | Stable; unique per survey. Referenced by `any_in_module` rules |
| `title` / `description` | Char/Text | |
| `order` | PositiveIntegerField | Default 0 |
| `applies_to` | CharField | `all` / `small` / `large` |
| `visible_when` | JSONField | Nullable conditional-visibility rule (null = always visible) |

Constraint: `UNIQUE (survey, key)`

#### `Question`
A question owned by a `Module`. Carries a stable `code` — the integration key the valuation engine (`apps/nom035`) consumes. No scoring data lives here.

| Field | Type | Notes |
|---|---|---|
| `id` | BigAutoField | PK |
| `module` | ForeignKey → `Module` | Cascades |
| `survey` | ForeignKey → `Survey` | Denormalized from `module.survey` (set in `save()`); enables per-survey `code` uniqueness |
| `code` | SlugField | Stable; unique per survey, e.g. `g3-29` |
| `question_type` | CharField | `text`, `integer`, `decimal`, `date`, `single_choice`, `multiple_choice`, `boolean`, `rating`, `likert` |
| `text` | TextField | Prompt |
| `order` | PositiveIntegerField | Default 0 |
| `config` | JSONField | Flexible per-type metadata (e.g. likert `labels`) |
| `visible_when` | JSONField | Nullable conditional-visibility rule |

Constraint: `UNIQUE (survey, code)`

#### `Choice`
A selectable option for `single_choice` / `multiple_choice` questions.

| Field | Type | Notes |
|---|---|---|
| `id` | BigAutoField | PK |
| `question` | ForeignKey → `Question` | Cascades |
| `label` | CharField(255) | Display text |
| `value` | CharField(255) | Stored value |
| `order` | PositiveIntegerField | Default 0 |

#### `SurveyAssignment`
Scopes a `Survey` to a `Company` with a frozen variant. The company-level campaign.

| Field | Type | Notes |
|---|---|---|
| `id` | BigAutoField | PK |
| `company` | ForeignKey → `Company` | Cascades |
| `survey` | ForeignKey → `Survey` | Cascades |
| `variant` | CharField | `small` / `large`; resolved from headcount, operator-overridable, frozen at creation |
| `status` | CharField | `active` / `closed` |
| `due_date` | DateField | Optional deadline |
| `created_at` | DateTimeField | Auto-set |

Helpers: `SurveyAssignment.resolve_default_variant(company, survey)` (pure) and
`assignment.modules_for_variant()` (modules where `applies_to` is `all` or the variant).

---

### `responses`

#### `SurveySubmission`
A single attempt by a user to answer a survey, scoped to a specific assignment (and therefore implicitly to a company).

| Field | Type | Notes |
|---|---|---|
| `id` | BigAutoField | PK |
| `assignment` | ForeignKey → `SurveyAssignment` | Cascades |
| `user` | ForeignKey → `User` | SET NULL; nullable (supports unauthenticated responses) |
| `status` | CharField | `in_progress` / `completed` |
| `started_at` | DateTimeField | Auto-set on creation |
| `completed_at` | DateTimeField | Nullable; set on completion |

Constraint: `UNIQUE (user, assignment)` when `user` is not null — one authenticated submission per user per assignment.

#### `Answer`
The recorded value for one question within a submission.

| Field | Type | Notes |
|---|---|---|
| `id` | BigAutoField | PK |
| `submission` | ForeignKey → `SurveySubmission` | Cascades |
| `question` | ForeignKey → `Question` | Cascades |
| `value` | JSONField | Interpretation depends on `question.question_type` |

Constraint: `UNIQUE (submission, question)` — one answer per question per submission.

### `nom035`

Materialized NOM-035 valuation results, derived from `responses.Answer` rows by the
`apps/nom035` engine (see `docs/platform/nom-035-analytics.md`). Written by a
`post_save` signal when a submission is completed and re-buildable via
`python manage.py recompute_nom035_scores`.

#### `SubmissionScore`
One row per scored submission: the final score, its Nivel de Riesgo (NDR), and the binary Guía I clinical-referral flag.

| Field | Type | Notes |
|---|---|---|
| `id` | BigAutoField | PK |
| `submission` | OneToOneField → `SurveySubmission` | Cascades; `related_name="nom035_score"` (scored submission, incl. one whose `user` went null on employee deletion) |
| `final_score` | IntegerField | `Cfinal` (sum of scored items) |
| `final_ndr` | CharField | `nulo` / `bajo` / `medio` / `alto` / `muy_alto` |
| `guia1_positive` | BooleanField | Official Guía I clinical-referral outcome (binary) |
| `computed_at` | DateTimeField | `auto_now`; last materialization |

#### `GroupScore`
Per-grouping breakdown for a submission — one row per categoría and per dominio (dimensión is not scored).

| Field | Type | Notes |
|---|---|---|
| `id` | BigAutoField | PK |
| `submission_score` | ForeignKey → `SubmissionScore` | Cascades; `related_name="groups"` |
| `level` | CharField | `categoria` / `dominio` |
| `key` | CharField | Stable group identifier from the scoring taxonomy |
| `score` | IntegerField | Summed score for the group |
| `ndr` | CharField | Group NDR (same choices as `final_ndr`) |

Constraint: `UNIQUE (submission_score, level, key)`. Indexes on `(submission_score, level)` and `(level, ndr)`.

---

## Relation Diagram

```
accounts_company ───────────────────────────────────┐
      │                                              │ (survey_assignments)
      │ (members)                                    ▼
      ▼                                     surveys_surveyassignment
accounts_userprofile                              │   │ (survey)
      │ (user)                                     │   ▼
      ▼                                            │  surveys_survey
 accounts_user                                     │       │ (modules)
      │ (submissions)                              │       ▼
      ▼                                            │  surveys_module
responses_surveysubmission ◄───────────────────────┘       │ (questions)
      │ (answers)                                           ▼
      ▼                                              surveys_question
 responses_answer ───────────────────────────────►  surveys_choice
                          (question)
```

The per-company catalogs hang off `Company` and are pointed at by `UserProfile`:

```
      accounts_company
        │           │ (locations)
        │ (areas)   ▼
        ▼      accounts_companylocation
accounts_companyarea      │
        │                 │ (members)
        │ (members)       │
        ▼                 ▼
      accounts_userprofile
```

Derived results (`apps/nom035`), materialized from a submission's answers:

```
responses_surveysubmission
      │ (nom035_score, 1:1)
      ▼
 nom035_submissionscore
      │ (groups)
      ▼
 nom035_groupscore
```

---

## Instance Creation Workflow

### 1. Set up a Company and its users

```
Company.create(name, legal_name)              ← reference_code auto-generated
  ├─ CompanyArea.create(company, name)        ← at least one, or activation is blocked
  ├─ CompanyLocation.create(company, name)    ← optional
  └─ User.create(username, email, password, ...)
       └─ UserProfile.create(user, position, company, is_activated=False)
```

A `Company` is created first, **together with its áreas and localidades** — these are curated as inlines on the Company change page in the admin. Loading at least one área matters: an employee whose company has no active área cannot complete activation (the activation screen tells them to contact their administrator). The Company changelist shows área/localidad counts so the gap is visible before anyone hits it.

Users are then created via Django's auth system, manual admin entry, or CSV import. A `UserProfile` links non-admin users to their company; company headcount is `company.members.count()`. The employee's `area`/`location` are normally set by themselves at activation; the CSV importer can pre-set `area` by name (lookup-only — it never creates catalog entries).

### 2. Seed the survey instrument

```
python manage.py seed_nom035_survey
```

The instrument is defined declaratively in `apps/core/management/commands/_nom035_data.py` and built by the seed command: one `Survey` (`key="nom035"`) with modules for Guía I (`all`), Guía II (`small`) and Guía III (`large`), each question carrying a stable `code`. The seed is idempotent (upsert by `key`, modules replaced). There is no interactive authoring CLI.

### 3. Assign the survey to a Company

```
variant = SurveyAssignment.resolve_default_variant(company, survey)  # headcount-based
SurveyAssignment.create(company, survey, variant, status=ACTIVE, due_date)
```

The variant defaults from headcount vs `survey.headcount_threshold`, is operator-overridable, and is frozen on the assignment. At take-time the respondent sees `assignment.modules_for_variant()` (modules tagged `all` plus the variant's), with `visible_when` rules hiding gated questions.

### 4. Collect responses

```
SurveySubmission.create(assignment, user, status=IN_PROGRESS)
  └─ Answer.create(submission, question, value)   ← one per visible question
       ...
  └─ submission.status = COMPLETED   ← when all *visible* required questions answered
     submission.completed_at = now()
```

Completion counts only questions visible under the current answers (see `apps/surveys/visibility.py`). Company isolation is automatic: `Answer → submission → assignment → company` always stays within one company's data.

---

## Key Design Decisions

**Fixed instruments, no library or versions.** Operators seed a few fixed surveys; a material change is a new `Survey`, not a new version. This removed the `QuestionTemplate`/`ChoiceTemplate` library, `SurveyTemplate`/`SurveyVersion` split, copy-on-stamp, and numbered versioning. See `docs/adr/adr-0002-flatten-survey-authoring-model.md`.

**Modular by `applies_to`.** A single `Survey` expresses the NOM-035 modular structure; the company's headcount selects which `small`/`large` modules join the shared `all` modules. Each item is defined once.

**Variant frozen on the assignment.** `SurveyAssignment.variant` is stored at creation, so later headcount changes do not alter a company's in-flight or historical assignment.

**`visible_when` is data-driven and survey-agnostic.** Branching (Guía I skip, "atiendo clientes"/"soy jefe" gates) is a JSON rule evaluated by one component used server- and client-side. The future second survey reuses it.

**`Question.code` is the scoring boundary.** Codes are stable and unique per survey; the valuation engine (`apps/nom035`) references them. No scoring (inverted flags, dimensión/dominio/categoría, thresholds) lives in `apps/surveys` — it belongs to the instrument's engine app.

**Company isolation through the assignment.** All response data traces back to a `SurveyAssignment` belonging to exactly one `Company`.

**Users are decoupled from companies at the auth level.** `User` is a standard Django auth model; company membership lives in `UserProfile`.

**Company-scoped catalogs, case-insensitively unique.** Áreas and localidades are per-company child tables rather than free text or a shared enum, because the employee picks from them at activation and the per-área NOM-035 breakdown groups by their pk. `UniqueConstraint(company, Lower(name))` makes duplicate spellings impossible within a company while leaving names free across companies. Entries are retired with `is_active=False`, not deleted — the FKs are `SET_NULL` (so deleting a `Company` stays possible) and the admin inline blocks deleting an entry that still has members. See `docs/adr/adr-0004-per-company-area-and-locality-catalogs.md`.
