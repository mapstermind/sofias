> **ARCHIVED 2026-06-20.** The interactive authoring CLI (`apps/core/workflows/`
> and the `create_*`/`manage_*`/`seed_*template*` commands) was removed when the
> survey model was flattened — see `docs/adr/adr-0002-flatten-survey-authoring-model.md`.
> Surveys are now seeded declaratively via `python manage.py seed_nom035_survey`.
> Kept for historical reference only; the commands below no longer exist.

# SOFIA-S Interactive Workflow Guide

The workflow layer provides five management commands for building surveys interactively from the terminal, plus three seed commands for the project's canonical content. This document covers the mental model, command-by-command walkthroughs, input conventions, recommended sequences, and guidance for extending the system.

---

## Overview

```
python manage.py manage_question_templates  # Manage the reusable question/choice library
python manage.py create_survey              # Create a SurveyTemplate + SurveyVersion v1
python manage.py create_question            # Add questions to a survey version (stamp or manual)
python manage.py manage_choices             # Add/edit/delete choices on a question
python manage.py manage_sections            # Create sections, assign and move questions
```

Each command also has a `make` shortcut: `make question-templates`, `make survey`, `make question`, `make choices`, `make sections`.

Seed commands build the project's canonical content non-interactively:

```
python manage.py seed_likert_templates       # 72 NOM-035 Likert statements into the library
python manage.py seed_demographic_templates  # demographic question templates into the library
python manage.py seed_nom035_survey          # the full NOM-035 survey, linked to the library
```

Run the two library seeds before `seed_nom035_survey` — it links its questions to existing library templates by text.

The interactive commands chain into each other. `create_survey` offers to open `create_question` when it finishes. `create_question` offers to open `manage_choices` after manually creating a single-choice or multiple-choice question. You can also run any command standalone — each one resolves its own dependencies by letting you pick from existing records.

Press `Ctrl-C` at any prompt to exit cleanly. No partial writes are left behind — each object is only created after all its prompts are answered.

### The library and stamping

The central concept: `QuestionTemplate` (and its `ChoiceTemplate`s) form a reusable, company-agnostic **library**. A library template is never shown to respondents directly — it is *stamped* into a `SurveyVersion`, which copies it into an independent `Question` (and `Choice`s). After stamping, editing the library does not affect the copy. Build the library once with `manage_question_templates`, then stamp from it when adding questions.

---

## Prerequisites

Database must be running and migrations applied:

```bash
sudo systemctl start postgresql
make migrate
```

Run the commands from the project root with the virtualenv active.

---

## Input Conventions

All prompts follow a small set of consistent rules.

### Text and number fields

```
Title: My Survey
Description []: Press Enter to leave blank
Order [3]:      Press Enter to accept the default shown in brackets
```

- A value in `[brackets]` is the default — press Enter to accept it.
- Fields marked required will keep asking until you type something.
- Optional fields accept an empty Enter and store an empty string or `None`.

### Yes/no prompts

```
Add questions now? [y/N]:   capital letter is the default
```

Accepted values: `y`, `yes`, `1` for yes — `n`, `no`, `0` for no. Case-insensitive. Confirmation prompts default to **No** — you have to actively type `y`.

### Numbered menus

```
Question type
  1. Text
  2. Integer
  3. Decimal
  ...
Choice:
```

Always enter the number. There is no fuzzy matching.

### Menus with a Back option

Some menus print `0. Back` as the first item. Entering `0` cancels the current sub-action and returns to the parent menu without making any changes.

### "Create new" and "None" options

Menus that let you pick from existing records may include a **Create new** entry at the bottom (drops you into an inline creation flow, then continues with the new object selected) and, where applicable, a **No section**-style "none" entry.

---

## Commands

### `manage_question_templates`

```bash
python manage.py manage_question_templates
```

Manages the reusable library. Loops on a main menu — **Create template** / **Edit template** / **Delete template** / **Done** — printing the current library (with choice counts for choice-type templates) at the top of each iteration.

- **Create:** pick a question type from the full enum menu, enter the question text. For `single_choice`/`multiple_choice`, offers `Add choices now? [y/N]`, which opens the same Add/Edit/Delete choice loop used everywhere.
- **Edit:** change the question text; for choice types, optionally manage choices. The type cannot be changed.
- **Delete:** requires confirmation. Deleting a template does **not** affect questions already stamped from it (their `source` FK is simply set to null).

### `create_survey`

```bash
python manage.py create_survey
```

1. Prompts for `Title` (required) and `Description` (optional).
2. Creates the `SurveyTemplate` with `status = draft`. Status is not prompted — new surveys always start as drafts. Change status through the Django admin when ready to publish.
3. Bootstraps `SurveyVersion` number 1 automatically.
4. Asks `Add questions now? [y/N]` — answering yes flows directly into `create_question` with the new survey pre-selected.

### `create_question`

```bash
python manage.py create_question
```

1. Prompts you to select a survey template (skipped if called from `create_survey`). Exits with a message if none exist.
2. Resolves the **latest** `SurveyVersion` for that survey (creates v1 if none exists).
3. Asks which section to assign the question to: an existing section, **No section**, or **Create new section** (inline creation).
4. Prompts for `Order`, defaulting to the current count of questions on the version (i.e., appends to the end).
5. Asks **Add question from**:
   - **Stamp from library template** — pick a `QuestionTemplate` (with `0. Back`); its text, type, config, and choices are copied into a new independent `Question`. If the library is empty you are told to run `make question-templates` first.
   - **Create manually** — pick a question type from the enum menu, enter the question `Text`. For `single_choice`/`multiple_choice`: asks `Manage choices now? [y/N]`, flowing into `manage_choices` for the new question.
6. Asks `Add another? [y/N]`. If yes, loops back to step 3 for the same survey.

**Question types:**

| Value | Label | Gets choices? |
|---|---|---|
| `text` | Text | No |
| `integer` | Integer | No |
| `decimal` | Decimal | No |
| `date` | Date | No |
| `single_choice` | Single Choice | Yes |
| `multiple_choice` | Multiple Choice | Yes |
| `boolean` | Boolean | No |
| `rating` | Rating | No |
| `likert` | Likert Scale | No (uses `config` labels; values 1–5) |

**The `order` field:** controls display sequence within a version. The default is the next available integer (0-indexed count of existing questions). You can override it to insert a question at a specific position, but the database does not enforce uniqueness on `order` — gaps and duplicates are allowed.

### `manage_choices`

```bash
python manage.py manage_choices
```

Operates in a loop on a single question. The current choices are printed at the top of each loop iteration.

**Navigation:**
1. Select survey template → select question (only `single_choice` and `multiple_choice` questions on the latest version are shown).
2. Main menu: **Add** / **Edit** / **Delete** / **Done**.

**Add:**
- `Label` (required) — the human-readable text shown to respondents, e.g. `Strongly Agree`.
- `Value` (defaults to a slugified version of the label) — the stored value in responses, e.g. `strongly_agree`. Override it if your analysis expects a specific format.
- `Order` (defaults to next available integer).

**Edit:** shows `0. Back` to cancel; all fields pre-filled with current values — press Enter to keep them.

**Delete:** shows `0. Back` to cancel; requires explicit confirmation `Delete 'Label'? [y/N]`.

**Displayed choice format:**

```
Choices for: How satisfied are you?
  [0] Strongly Agree → strongly_agree
  [1] Agree → agree
```

The number in brackets is the `order` value, not the menu item number.

**Value slugification:** the value defaults to a lowercase, underscore-separated slug of the label: `"Not Sure"` → `not_sure`. Anything that isn't a lowercase letter or digit collapses to underscores.

### `manage_sections`

```bash
python manage.py manage_sections
```

Sections group questions within a version for display purposes. They are optional — questions without a section are valid and always appear.

**Navigation:** select survey template → the latest version is resolved → main menu loops until **Done**, printing the current section list each iteration.

**Menu options:**

- **Create section:** prompts `Title` (required), `Description` (optional), and `Order` (defaults to count of existing sections).
- **Add question to section:** only shows questions that are currently **unsectioned**. Pick a section, then a question.
- **Move question:** pick the source section → the question → the destination (other sections or **No section**).
- **List questions in section:** read-only listing ordered by `order`.

---

## Data Model Refresher

```
SurveyTemplate                        QuestionTemplate   (library)
└── SurveyVersion                     └── ChoiceTemplate (library)
    ├── Section    (optional; ordered)        │
    │   └── Question (section FK nullable) ◄──┘ stamp_into() copies; `source` FK
    └── Question   (may have no section)        records provenance (SET_NULL)
        └── Choice (only on single/multiple choice)
```

**Key constraints:**
- `SurveyVersion` has a unique constraint on `(template, version_number)`.
- `Choice` belongs to a `Question`, not a version. Deleting a question cascades to its choices.
- `Section` belongs to a `SurveyVersion`. Sections from v1 are not shared with v2.
- Questions belong to a `SurveyVersion`, not directly to a `SurveyTemplate`. All workflow commands operate on the **latest version** as returned by `get_or_create_latest_version`.

**Status lifecycle:** `SurveyTemplate.status` has three values: `draft`, `published`, `archived`. The workflows always create surveys as `draft`. Transitions are not handled by the CLI — use the Django admin (`/admin/`) or the shell.

---

## Recommended Sequences

### Build a survey end to end

```bash
make question-templates   # build the library once (skip if already seeded)
make survey               # title/description, then answer y to "Add questions now?"
```

For each question, stamp from the library where possible; create manually for one-offs. Answer `y` to `Add another?` to keep going.

### Add questions to an existing survey

```bash
python manage.py create_question
```

Select the survey from the menu; the rest is the same question loop.

### Retrofit sections onto a flat survey

```bash
python manage.py manage_sections
```

1. **Create section** → create all sections first, in order.
2. **Add question to section** → assign each unsectioned question.
3. **Move question** to reassign; **List questions in section** to verify.

### Fix a choice after the fact

```bash
python manage.py manage_choices
```

Use **Edit** to correct a label or value, or **Delete** + **Add** to replace a choice. Deleting a choice does not affect answers already collected — `responses.Answer` stores the raw value, so existing response data remains intact.

---

## How the Workflow Layer Works

### Automatic field detection

The prompts for `create_survey`, `create_question` (manual path), and section creation are not hardcoded. They are generated at runtime by `apps/core/workflows/introspect.py`, which walks `Model._meta.get_fields()` and builds a `FieldSpec` for each promptable field.

This means: **if you add a new promptable field to `SurveyTemplate`, `Question`, or `Section`, the workflow prompts for it automatically** — as long as the field type is one the system understands (text, int, bool, or a field with `.choices`).

Field prompting rules:

| Django field type | Prompt style |
|---|---|
| `CharField`, `TextField` | Free text input |
| `PositiveIntegerField`, `IntegerField` | Integer-validated input |
| `BooleanField` | `[Y/n]` yes/no |
| Any field with `.choices` | Numbered menu |
| `JSONField` | Always skipped (use model default) |
| Relation fields (FK, M2M) | Always skipped (handled explicitly per workflow) |

Required vs optional is determined by `blank=True`, `null=True`, or a `default`. If none apply, the prompt refuses an empty value.

### Fields that are always skipped

```
id, created_at, updated_at, published_at, started_at, completed_at
```

Fields with `auto_now=True` or `auto_now_add=True` are also skipped automatically.

Individual workflow functions further exclude fields they handle themselves (e.g. `create_question` excludes `version`, `section`, `question_type`, `config`, `order`, and `source` from the generic prompt loop).

### Version bootstrapping

Every workflow that operates on questions or sections calls `get_or_create_latest_version(survey)` from `apps/core/workflows/version_helpers.py`:

1. Queries `survey.versions.order_by("-version_number").first()`.
2. If no version exists, creates `SurveyVersion(template=survey, version_number=1)`.
3. Returns whatever it found or created.

In practice `create_survey` always bootstraps v1 immediately, so this is a safety net.

There is no command to create a new version (v2, v3, …). To do it manually:

```python
# Django shell
from apps.surveys.models import SurveyTemplate, SurveyVersion
survey = SurveyTemplate.objects.get(title="My Survey")
latest = survey.versions.order_by("-version_number").first()
SurveyVersion.objects.create(template=survey, version_number=latest.version_number + 1)
```

Once v2 exists, all workflow commands operate on it (they always resolve the highest version number).

---

## Extending the Workflows

### Adding a new command

1. Create `apps/core/workflows/my_workflow.py` with a `run_my_workflow()` function.
2. Create `apps/core/management/commands/my_command.py`:

```python
from django.core.management.base import BaseCommand
from apps.core.workflows.my_workflow import run_my_workflow

class Command(BaseCommand):
    help = "Description shown in manage.py help"

    def handle(self, *args, **options):
        try:
            run_my_workflow()
        except KeyboardInterrupt:
            self.stdout.write("\nAborted.")
```

3. No registration needed — Django discovers management commands automatically.

### Adding prompts for a new field type

If you add a field type not currently handled (e.g. `DateField`, `DecimalField`), add a branch in `introspect.py`:

- In `_field_type()`: map the Django field class to a new type string.
- In `prompt_for_model()`: add a branch for the new type calling the appropriate `prompts.py` function.

All terminal I/O must go through `prompts.py` — no other module should call `input()` directly.

### Using prompt functions in your own code

```python
from apps.core.workflows.prompts import ask, ask_int, ask_bool, choose, choose_or_create, confirm
```

| Function | Use for |
|---|---|
| `ask(prompt, default, required)` | Any text field |
| `ask_int(prompt, default, required)` | Integer fields |
| `ask_bool(prompt, default)` | Boolean fields (default Yes unless overridden) |
| `choose(prompt, options, allow_back)` | Selecting from a fixed list |
| `choose_or_create(prompt, options, ...)` | Selecting from DB records with inline creation |
| `confirm(prompt, default)` | Destructive or chained actions — default is `False` |

---

## Troubleshooting

**`No survey templates found. Create one first.`**
Run `create_survey` before `create_question`, `manage_choices`, or `manage_sections`.

**`No question templates found. Build the library first...`**
The stamping path needs library templates. Run `manage_question_templates` or the seed commands.

**`No choice-type questions found for this survey version.`**
`manage_choices` only shows `single_choice`/`multiple_choice` questions. Create one first.

**`No unsectioned questions available.`** (manage_sections → Add question to section)
All questions are already in a section. Use **Move question** to reassign.

**`django.db.utils.OperationalError: could not connect to server`**
PostgreSQL is not running: `sudo systemctl start postgresql`.

**`django.db.utils.ProgrammingError: relation does not exist`**
Migrations haven't been applied: `python manage.py migrate`.

**A field I added to the model is not being prompted.**
Check that the field is not a relation, not in `SKIP_FIELDS`, has no `auto_now`/`auto_now_add`, and is not a `JSONField`. Also check the workflow's `exclude` list. New field types need handling in `introspect.py`.

**I entered the wrong value for a field I can't re-prompt.**
Use the Django admin at `/admin/` to edit the record directly.
