# Database Structure

## Overview

The schema is organized around four distinct concerns:

1. **Who** — identity and company membership (`accounts` app)
2. **Question library** — reusable, company-agnostic question definitions (`surveys` app: `QuestionTemplate`, `ChoiceTemplate`)
3. **What** — the reusable survey definition (`surveys` app: `SurveyTemplate`, `SurveyVersion`, `Section`, `Question`, `Choice`)
4. **Context & results** — who must answer, in which context, and what they said (`surveys` app: `SurveyAssignment`; `responses` app: `SurveySubmission`, `Answer`)

This separation means a single survey template can be assigned to many companies without mixing their data, and a single question definition can be stamped into many surveys without coupling them.

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
| `reference_code` | CharField(5) | Unique alphanumeric identifier; auto-generated on save if blank |
| `created_at` | DateTimeField | Auto-set on creation |
| `updated_at` | DateTimeField | Auto-updated on save |

#### `User`
Extends Django's `AbstractUser`. Inherits all standard auth fields (`username`, `email`, `password`, `is_staff`, etc.).

#### `UserProfile`
Extends `User` with business context. Created separately from the auth user.

| Field | Type | Notes |
|---|---|---|
| `id` | BigAutoField | PK |
| `user` | OneToOneField → `User` | Cascades on user delete |
| `position` | CharField(255) | Job title, optional |
| `company` | ForeignKey → `Company` | SET NULL on company delete; nullable |

---

### `surveys` — Question library

#### `QuestionTemplate`
A reusable question in the library. Completely company- and survey-agnostic. This is the single source of truth for question wording, type, and default config.

| Field | Type | Notes |
|---|---|---|
| `id` | BigAutoField | PK |
| `question_type` | CharField | `short_text`, `long_text`, `integer`, `decimal`, `date`, `single_choice`, `multiple_choice`, `boolean`, `rating` |
| `text` | TextField | The question prompt |
| `required` | BooleanField | Default `True` |
| `config` | JSONField | Flexible metadata (min/max, placeholders, validation rules, etc.) |
| `created_at` | DateTimeField | Auto-set |
| `updated_at` | DateTimeField | Auto-updated |

**Key method — `stamp_into(version, section=None, order=0)`**: copies this template and all its `ChoiceTemplate` rows into an independent `Question` (and `Choice`) instance owned by the given `SurveyVersion`. After stamping the copy is fully independent — changes to the library do not affect it.

#### `ChoiceTemplate`
A selectable option belonging to a `QuestionTemplate`. Stamped alongside its parent into `Choice` instances.

| Field | Type | Notes |
|---|---|---|
| `id` | BigAutoField | PK |
| `question` | ForeignKey → `QuestionTemplate` | Cascades |
| `label` | CharField(255) | Display text |
| `value` | CharField(255) | Stored value |
| `order` | PositiveIntegerField | Default 0 |

---

### `surveys` — Survey definition

#### `SurveyTemplate`
The reusable, company-agnostic survey definition. A template can be assigned to multiple companies.

| Field | Type | Notes |
|---|---|---|
| `id` | BigAutoField | PK |
| `title` | CharField(255) | |
| `description` | TextField | Optional |
| `status` | CharField | `draft` / `published` / `archived` |
| `created_at` | DateTimeField | Auto-set |
| `updated_at` | DateTimeField | Auto-updated |

#### `SurveyVersion`
A snapshot of a template's content at a point in time. Assignments are pinned to a specific version so the form cannot change under active respondents.

| Field | Type | Notes |
|---|---|---|
| `id` | BigAutoField | PK |
| `template` | ForeignKey → `SurveyTemplate` | Cascades |
| `version_number` | PositiveIntegerField | Unique per template |
| `published_at` | DateTimeField | Nullable |
| `created_at` | DateTimeField | Auto-set |

Constraint: `UNIQUE (template, version_number)`

#### `Section`
An optional grouping of questions within a version.

| Field | Type | Notes |
|---|---|---|
| `id` | BigAutoField | PK |
| `version` | ForeignKey → `SurveyVersion` | Cascades |
| `title` | CharField(255) | |
| `description` | TextField | Optional |
| `order` | PositiveIntegerField | Display order, default 0 |

#### `Question`
A single question owned by a `SurveyVersion`. May be created manually or stamped from a `QuestionTemplate`. Once created it is fully independent of the library.

| Field | Type | Notes |
|---|---|---|
| `id` | BigAutoField | PK |
| `version` | ForeignKey → `SurveyVersion` | Cascades |
| `section` | ForeignKey → `Section` | Nullable; cascades |
| `source` | ForeignKey → `QuestionTemplate` | SET NULL; nullable — provenance only, no live coupling |
| `question_type` | CharField | Same choices as `QuestionTemplate.question_type` |
| `text` | TextField | The question prompt |
| `required` | BooleanField | Default `True` |
| `order` | PositiveIntegerField | Default 0 |
| `config` | JSONField | Flexible metadata |

#### `Choice`
A selectable option for `single_choice` or `multiple_choice` questions. May be stamped from a `ChoiceTemplate` or created manually.

| Field | Type | Notes |
|---|---|---|
| `id` | BigAutoField | PK |
| `question` | ForeignKey → `Question` | Cascades |
| `source` | ForeignKey → `ChoiceTemplate` | SET NULL; nullable — provenance only |
| `label` | CharField(255) | Display text |
| `value` | CharField(255) | Stored value |
| `order` | PositiveIntegerField | Default 0 |

#### `SurveyAssignment`
Scopes a specific `SurveyVersion` to a `Company`. This is the company-level campaign — all submissions for that company flow through this record.

| Field | Type | Notes |
|---|---|---|
| `id` | BigAutoField | PK |
| `company` | ForeignKey → `Company` | Cascades |
| `version` | ForeignKey → `SurveyVersion` | Cascades |
| `status` | CharField | `active` / `closed` |
| `due_date` | DateField | Optional deadline |
| `created_at` | DateTimeField | Auto-set |

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

#### `Answer`
The recorded value for one question within a submission.

| Field | Type | Notes |
|---|---|---|
| `id` | BigAutoField | PK |
| `submission` | ForeignKey → `SurveySubmission` | Cascades |
| `question` | ForeignKey → `Question` | Cascades |
| `value` | JSONField | Interpretation depends on `question.question_type` |

Constraint: `UNIQUE (submission, question)` — one answer per question per submission.

---

## Relation Diagram

```
                    ┌─────────────────────────────────────────┐
                    │         QUESTION LIBRARY                │
                    │                                         │
                    │  QuestionTemplate                       │
                    │    └─ ChoiceTemplate                    │
                    │            │ (stamp_into)               │
                    └────────────┼────────────────────────────┘
                                 │ source (SET NULL)
                                 ▼
accounts_company ──────────────────────────────────────────┐
      │                         │                          │
      │ (members)               │                          │ (survey_assignments)
      ▼                         ▼                          ▼
accounts_userprofile       surveys_question        surveys_surveyassignment
      │                    surveys_choice           │         │
      │ (user)                  │                  │         │ (version)
      ▼                         │ (version)        │         ▼
 accounts_user ◄────────────────┼──────────────────┘  surveys_surveyversion
      │                         │                           │
      │ (submissions)           ▼                           │ (template)
      ▼                   surveys_section                   ▼
responses_surveysubmission                       surveys_surveytemplate
      │
      │ (answers)
      ▼
 responses_answer ──────► surveys_question
```

---

## Instance Creation Workflow

### 1. Set up a Company and its users

```
Company.create(name, legal_name)              ← reference_code auto-generated
  └─ User.create(username, email, password, ...)
       └─ UserProfile.create(user, position, company)
```

A `Company` is created first. Users are then created via Django's auth system and a `UserProfile` is attached to link them to their company.

### 2. Build the question library

```
QuestionTemplate.create(question_type, text, required, config)
  └─ ChoiceTemplate.create(question, label, value, order)   ← for choice questions only
```

The library is built once and maintained independently of any survey. These records are never directly shown to respondents — they are the source of truth used when stamping questions into surveys.

### 3. Build a SurveyTemplate and populate it from the library

```
SurveyTemplate.create(title, description, status=DRAFT)
  └─ SurveyVersion.create(template, version_number=1)
       ├─ Section.create(version, title, order)             ← optional
       └─ question_template.stamp_into(version, section, order)
            # Creates Question + Choice copies, source FK set for provenance
```

`stamp_into()` is the bridge between the library and a live survey. It copies all fields and choices from the template into new independent rows owned by the version. After stamping, the question is self-contained — editing the library does not affect it.

Questions can also be created manually (without a library source) for one-off additions.

### 4. Assign a SurveyVersion to a Company

```
SurveyAssignment.create(company, version, status=ACTIVE, due_date)
```

This is the act of "sending" the survey to a company. The assignment is pinned to a specific `SurveyVersion`, so the template can be revised without affecting in-flight assignments. Multiple companies can hold assignments against the same version independently.

### 5. Collect responses

```
SurveySubmission.create(assignment, user, status=IN_PROGRESS)
  └─ Answer.create(submission, question, value)   ← one per question
       ...
  └─ submission.status = COMPLETED
     submission.completed_at = now()
```

When a user opens the survey URL (identified by `assignment_id`), a `SurveySubmission` is created for that assignment. As they submit, an `Answer` is stored per question. Company isolation is automatic: querying `Answer` objects through `submission → assignment → company` always stays within a single company's data.

---

## Key Design Decisions

**The library never touches live surveys.** `QuestionTemplate` and `ChoiceTemplate` are authored independently. The `stamp_into()` method is the only crossing point — after it runs, the `Question` row is fully owned by its `SurveyVersion`. Editing a library entry does not silently alter any survey.

**`source` is provenance, not a dependency.** The FK from `Question → QuestionTemplate` (and `Choice → ChoiceTemplate`) is set to `SET_NULL`. If a library entry is deleted, existing survey questions are unaffected. The field exists to answer "where did this question come from?" and to enable future tooling (e.g. "re-sync from library" on draft versions).

**Templates are company-agnostic.** `SurveyTemplate` and its child models carry no reference to any company. A template can be reused across any number of companies without duplication.

**Assignments pin a version.** `SurveyAssignment.version` is a FK to `SurveyVersion`, not `SurveyTemplate`. This guarantees the exact questions a company was assigned are preserved even when the template evolves.

**Company isolation through the assignment.** All response data (`SurveySubmission`, `Answer`) traces back to a `SurveyAssignment`, which belongs to exactly one `Company`. There is no cross-company leakage by construction.

**Users are decoupled from companies at the auth level.** `User` is a standard Django auth model. Company membership lives in `UserProfile`, keeping the auth layer clean and the business layer flexible.
