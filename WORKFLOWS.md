# SOFIA-S Interactive Workflow Guide

The workflow layer provides four management commands for building surveys interactively from the terminal. This document covers everything you need to use them effectively: mental models, command-by-command walkthroughs, input conventions, recommended sequences, and guidance for extending the system.

---

## Table of Contents

1. [Overview](#overview)
2. [Prerequisites](#prerequisites)
3. [Input Conventions](#input-conventions)
4. [Commands](#commands)
   - [create_survey](#create_survey)
   - [create_question](#create_question)
   - [manage_choices](#manage_choices)
   - [manage_sections](#manage_sections)
5. [Data Model Refresher](#data-model-refresher)
6. [Recommended Sequences](#recommended-sequences)
   - [Build a survey end to end](#build-a-survey-end-to-end)
   - [Add questions to an existing survey](#add-questions-to-an-existing-survey)
   - [Retrofit sections onto a flat survey](#retrofit-sections-onto-a-flat-survey)
   - [Fix a choice after the fact](#fix-a-choice-after-the-fact)
7. [How the Workflow Layer Works](#how-the-workflow-layer-works)
   - [Automatic field detection](#automatic-field-detection)
   - [Fields that are always skipped](#fields-that-are-always-skipped)
   - [Version bootstrapping](#version-bootstrapping)
8. [Extending the Workflows](#extending-the-workflows)
9. [Troubleshooting](#troubleshooting)

---

## Overview

```
python manage.py create_survey      # Create a Survey + SurveyVersion v1
python manage.py create_question    # Add questions to any survey version
python manage.py manage_choices     # Add/edit/delete choices on a question
python manage.py manage_sections    # Create sections, assign and move questions
```

The commands chain into each other naturally. `create_survey` offers to open `create_question` when it finishes. `create_question` offers to open `manage_choices` when it creates a single-choice or multiple-choice question. You can also run any command standalone at any time — each one resolves its own dependencies by letting you pick from existing records.

Press `Ctrl-C` at any prompt to exit cleanly. No partial writes are left behind — each object is only created after all its prompts are answered.

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

All prompts follow a small set of consistent rules. Understanding them once means you can navigate every command without re-reading.

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
Add questions now? [Y/n]:   capital letter is the default
Create another? [y/N]:      press Enter for No here
```

Accepted values: `y`, `yes`, `1` for yes — `n`, `no`, `0` for no. Case-insensitive.

### Numbered menus

```
Question type
  1. Short Text
  2. Long Text
  3. Integer
  ...
Choice:
```

Always enter the number. There is no fuzzy matching.

### Menus with a Back option

Some menus print `0. Back` as the first item. Entering `0` cancels the current sub-action and returns to the parent menu without making any changes.

### The "Create new" option

Menus that let you pick from existing records always include a **Create new** entry at the bottom. Selecting it drops you into an inline creation flow and then returns you to where you were with the newly created object already selected.

---

## Commands

### `create_survey`

```bash
python manage.py create_survey
```

**What it does:**

1. Prompts for `title` (required) and `description` (optional).
2. Creates the `Survey` with `status = DRAFT`. Status is not prompted — new surveys always start as drafts. Change status through the Django admin or a future command when you are ready to publish.
3. Bootstraps `SurveyVersion` number 1 automatically. You do not need to think about versions during initial creation.
4. Asks `Add questions now? [Y/n]` — answering yes flows directly into `create_question` with the new survey pre-selected.

**Example session:**

```
=== Create Survey ===
Title: Customer Satisfaction Q3
Description []: Post-purchase feedback survey

Created: Customer Satisfaction Q3 (version 1)
Add questions now? [Y/n]: y

=== Create Question ===
...
```

**After running:** one `Survey` row and one `SurveyVersion` row (version_number=1) exist in the database.

---

### `create_question`

```bash
python manage.py create_question
```

**What it does:**

1. If no surveys exist, exits with a message. Create a survey first.
2. Prompts you to select a survey (skipped if called from `create_survey`).
3. Resolves or creates `SurveyVersion` v1 for that survey.
4. Asks which section to assign the question to, with three options:
   - An existing section by number
   - **No section** — question floats unassigned
   - **Create new section** — inline section creation, then the question is assigned to it
5. Asks for **question type** from the full `QuestionType` enum menu.
6. Prompts for `text` (required) and `required` (bool, defaults to `True`).
7. Prompts for `order`, defaulting to the current count of questions on that version (i.e., appends to the end).
8. For `single_choice` or `multiple_choice` types: asks `Manage choices now?` — answering yes flows into `manage_choices` for the new question.
9. Asks `Create another? [y/N]`. If yes, loops back to step 4 for the same survey.

**Question types:**

| Value | Label | Gets choices? |
|---|---|---|
| `short_text` | Short Text | No |
| `long_text` | Long Text | No |
| `integer` | Integer | No |
| `decimal` | Decimal | No |
| `date` | Date | No |
| `single_choice` | Single Choice | Yes |
| `multiple_choice` | Multiple Choice | Yes |
| `boolean` | Boolean | No |
| `rating` | Rating | No |

**The `order` field:** Controls display sequence within a version. The default is the next available integer (0-indexed count of existing questions). You can override it to insert a question at a specific position, but the database does not enforce uniqueness on `order` — gaps and duplicates are allowed. Renumbering is a future concern.

---

### `manage_choices`

```bash
python manage.py manage_choices
```

**What it does:**

Operates in a loop on a single question. The current choices are printed at the top of each loop iteration so you can see the current state before choosing an action.

**Navigation:**
1. Select survey → select question (only `single_choice` and `multiple_choice` questions are shown).
2. Main menu: **Add** / **Edit** / **Delete** / **Done**.

**Add:**
- Prompts `Label` (required) — the human-readable text shown to respondents, e.g. `Strongly Agree`.
- Prompts `Value` (defaults to a slugified version of the label) — the stored value in responses, e.g. `strongly_agree`. Override this if your analytics code expects a specific value format.
- Prompts `Order` (defaults to next available integer).

**Edit:**
- Shows `0. Back` to cancel without changes.
- All fields pre-filled with current values — press Enter to keep them unchanged.

**Delete:**
- Shows `0. Back` to cancel.
- Requires explicit confirmation `Delete 'Label'? [y/N]` before removing. Default is No — you have to actively type `y`.

**Displayed choice format:**

```
Choices for: How satisfied are you?
  [0] Strongly Agree → strongly_agree
  [1] Agree → agree
  [2] Neutral → neutral
  [3] Disagree → disagree
  [4] Strongly Disagree → strongly_disagree
```

The number in brackets is the `order` value, not the menu item number.

**Value slugification:** When you type a label, the value field defaults to a lowercase, underscore-separated slug: `"Not Sure"` → `not_sure`. Spaces, hyphens, and other punctuation are all collapsed to underscores. Confirm or override at the `Value:` prompt.

---

### `manage_sections`

```bash
python manage.py manage_sections
```

**What it does:**

Sections group questions within a version for display purposes. They are optional — questions without a section are valid and will always appear.

**Navigation:**
1. Select survey.
2. Resolves the latest version.
3. Main menu loops until **Done**. The current section list is printed at the top of each iteration.

**Menu options:**

**Create section:**
- Prompts `Title` (required) and `Description` (optional).
- Prompts `Order` (defaults to count of existing sections — i.e., appended).

**Add question to section:**
- Only shows questions that are currently **unsectioned** (section is null). Questions already in a section do not appear here — use **Move question** to reassign them.
- Pick a section, then pick a question. The question's `section` FK is updated.

**Move question:**
- Pick the source section → pick the question → pick the destination.
- Destination options include all other sections plus **No section** (sets section to null, effectively removing it from any section).

**List questions in section:**
- Pick a section. Prints all questions in that section ordered by `order`.
- Read-only — no changes made.

**Section ordering:** Like questions, sections have an `order` field that controls display sequence. The database does not enforce uniqueness.

---

## Data Model Refresher

Understanding the object hierarchy prevents confusion when navigating menus.

```
Survey
└── SurveyVersion  (one per version number; v1 created automatically)
    ├── Section    (optional grouping; has order)
    │   └── Question (FK to section, nullable)
    └── Question   (may have no section)
        └── Choice (only meaningful on single_choice / multiple_choice)
```

**Key constraints:**
- `SurveyVersion` has a unique constraint on `(survey, version_number)`. You cannot have two v1s for the same survey.
- `Choice` belongs to a `Question`, not a version. If you delete a question, all its choices are deleted via cascade.
- `Section` belongs to a `SurveyVersion`. Sections from v1 are not shared with v2.
- Questions belong to a `SurveyVersion`, not directly to a `Survey`. All workflow commands currently operate on the **latest version** as returned by `get_or_create_latest_version`.

**Status lifecycle:** `Survey.status` has three values: `draft`, `published`, `closed`. The workflows always create surveys as `draft`. Transitioning to `published` or `closed` is not handled by the CLI — use the Django admin (`/admin/`) or the shell.

---

## Recommended Sequences

### Build a survey end to end

This is the fastest path. One command does everything:

```bash
python manage.py create_survey
```

At `Add questions now?` answer `y`. For each question, answer `y` to `Manage choices now?` if it is a choice type. Answer `y` to `Create another?` to keep going. Answer `n` when done.

---

### Add questions to an existing survey

```bash
python manage.py create_question
```

Select the survey from the menu. The rest is identical to the question loop above.

---

### Retrofit sections onto a flat survey

You already have questions with no sections. Now you want to organise them.

```bash
python manage.py manage_sections
```

1. Select your survey.
2. **Create section** → create all sections you need first, in order.
3. **Add question to section** → assign each unsectioned question to a section.
4. If you need to reassign a question: **Move question** → pick source section → pick question → pick destination.
5. **List questions in section** to verify the result before exiting.

---

### Fix a choice after the fact

```bash
python manage.py manage_choices
```

Select the survey, then the question. Use **Edit** to correct a label or value, or **Delete** + **Add** to replace a choice entirely. Deleting a choice does not affect responses that have already been collected — response data stores the raw value string, so archived response data remains intact.

---

## How the Workflow Layer Works

### Automatic field detection

The prompts for `create_survey` and `create_question` are not hardcoded. They are generated at runtime by `apps/core/workflows/introspect.py`, which walks `Model._meta.get_fields()` and builds a `FieldSpec` for each promptable field.

This means: **if you add a new field to `Survey`, `Question`, or `Section`, the workflow will prompt for it automatically** — no changes needed in the workflow code, as long as the field type is one the system understands (text, int, bool, or a field with `.choices`).

Field prompting rules:

| Django field type | Prompt style |
|---|---|
| `CharField`, `TextField` | Free text input |
| `PositiveIntegerField`, `IntegerField` | Integer-validated input |
| `BooleanField` | `[Y/n]` yes/no |
| Any field with `.choices` | Numbered menu |
| `JSONField` | Always skipped (use model default) |
| Relation fields (FK, M2M) | Always skipped (handled explicitly per workflow) |

Required vs optional is determined by whether the field has `blank=True`, `null=True`, or a `default`. If none of those are true, the prompt will refuse to accept an empty value.

### Fields that are always skipped

The following field names are excluded regardless of field type:

```
id, created_at, updated_at, published_at, started_at, completed_at
```

Fields with `auto_now=True` or `auto_now_add=True` are also skipped automatically.

Individual workflow functions further exclude fields they handle themselves (e.g. `create_question` excludes `version`, `section`, `question_type`, `order`, and `config` from the generic prompt loop and handles each one explicitly).

### Version bootstrapping

Every workflow that operates on questions or sections calls `get_or_create_latest_version(survey)` from `apps/core/workflows/version_helpers.py`. This function:

1. Queries `survey.versions.order_by("-version_number").first()`.
2. If no version exists, creates `SurveyVersion(survey=survey, version_number=1)`.
3. Returns whatever it found or created.

The implication: you can safely call `create_question` on a survey that somehow has no version — v1 will be created on the spot. In practice, `create_survey` always bootstraps v1 immediately, so this is a safety net rather than a normal path.

There is currently no command to create a new version (v2, v3, etc.). To do that manually:

```python
# Django shell
from apps.surveys.models import Survey, SurveyVersion
survey = Survey.objects.get(title="My Survey")
latest = survey.versions.order_by("-version_number").first()
SurveyVersion.objects.create(survey=survey, version_number=latest.version_number + 1)
```

Once v2 exists, all subsequent workflow commands will operate on it (since they always resolve the highest version number).

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
- In `prompt_for_model()`: add an `elif spec.field_type == "mytype":` branch calling the appropriate `prompts.py` function.

If the field needs a custom prompt primitive, add it to `prompts.py`. All terminal I/O must go through `prompts.py` — no other module should call `input()` directly.

### Using prompt functions in your own code

All primitive functions are importable:

```python
from apps.core.workflows.prompts import ask, ask_int, ask_bool, choose, choose_or_create, confirm
```

| Function | Use for |
|---|---|
| `ask(prompt, default, required)` | Any text field |
| `ask_int(prompt, default, required)` | Integer fields |
| `ask_bool(prompt, default)` | Boolean fields, feature flags |
| `choose(prompt, options, allow_back)` | Selecting from a fixed list |
| `choose_or_create(prompt, options, ...)` | Selecting from DB records with inline creation |
| `confirm(prompt, default)` | Destructive or irreversible actions — default is `False` |

---

## Troubleshooting

**`No surveys found. Create one first.`**
Run `create_survey` before running `create_question`, `manage_choices`, or `manage_sections`.

**`No choice-type questions found for this survey version.`**
`manage_choices` only shows questions with type `single_choice` or `multiple_choice`. Run `create_question` and select one of those types first.

**`No unsectioned questions available.`** (in manage_sections → Add question to section)
All questions are already assigned to a section. Use **Move question** to reassign.

**`django.db.utils.OperationalError: could not connect to server`**
PostgreSQL is not running. `sudo systemctl start postgresql`.

**`django.db.utils.ProgrammingError: relation does not exist`**
Migrations haven't been applied. `python manage.py migrate`.

**A field I added to the model is not being prompted.**
Check that the field is not a relation, does not appear in `SKIP_FIELDS`, does not have `auto_now` or `auto_now_add`, and is not a `JSONField`. Also check that your workflow's `exclude` list does not include it. If the field type is new, add handling in `introspect.py` as described above.

**I entered the wrong value for a field I can't re-prompt.**
Use the Django admin at `/admin/` to edit the record directly. Ensure `INSTALLED_APPS` includes `django.contrib.admin` (it does by default) and a superuser exists (`python manage.py createsuperuser`).
