# Design system — the type scale

## What changes

**What.**
- The type scale becomes tokens in `static/css/main.css`. Tailwind's size classes keep their
  names and take the scale's values: 13 / 14 / 16 / 20 / 25 / 31 / 39px, each with its own line
  height.
- Every use of a size class moves to the class that matches its role.
- Sentence text leaves the smallest size.
- The survey's questions, answers and inputs reach the 16px floor.

**Why.**
- The app runs on Tailwind's defaults (12 / 14 / 16 / 18 / 20 / 24 / 30). 92 uses sit at 12px,
  many of them sentences.
- On the survey, the question, every answer option and the survey's own text inputs are 14px. That
  is below the 16px floor for reading text on a phone, and below the size at which iOS zooms in on
  a focused input.
- Survey respondents often find devices hard to use, and executives scan the dashboards and
  reports.

**Live doc sections this makes wrong** (`docs/platform/design-system.md`):
- *Scope → Type scale*: it lists Tailwind's default steps, and gains the scale, the line heights,
  the roles and the survey floor.
- *Scope → Components → The form control*: survey inputs become `control` too.
- *Key decisions* and *Enforcement*: gain the entries under **Decisions** and **Tests**.

**ADRs.** None touched.

## Design

### The scale

Declared in the `@theme` block of `main.css` as `--text-<name>` and `--text-<name>--line-height`.
Because the sizes are in `rem`, a reader who raises their browser's or phone's text size still
scales every step.

| Class | Size | Line height | Role |
|---|---|---|---|
| `text-xs` | 13px | 1.4 | A label on a graphic or a badge: a pill, a legend entry, a chart caption, a count beside an icon |
| `text-sm` | 14px | 1.5 | Secondary text: table cells, metadata, dates, help, errors, field labels |
| `text-base` | 16px | 1.5 | Body copy, form controls, the survey's questions and answers |
| `text-lg` | 20px | 1.4 | Section headings, modal titles |
| `text-xl` | 25px | 1.25 | Page titles (`h1`) |
| `text-2xl` | 31px | 1.2 | Stat numbers, the 6-digit login code |
| `text-3xl` | 39px | 1.15 | Reserved: nothing uses it after the move |

### Moving uses to their role

- **Page titles** (`text-2xl`, 24px, and the survey's `text-3xl` title, 30px): become `text-xl`
  (25).
- **Stat numbers** (`text-3xl`, 30px): become `text-2xl` (31).
- **The five `text-xl` uses** (20px): each takes the class of its role.
- **Section and modal headings** (`text-lg`): keep the class and grow from 18 to 20px.
- **One use grows by design:**
  - the login and setup codes' digits (`text-2xl` in `apps/accounts/forms.py`), 24 → 31
- **Every `text-xs`** either stays (13px, a label on a graphic or badge) or moves to `text-sm`
  (14px). A use moves when it is read as a sentence: help, explanations, dates, "actualizado…"
  lines, card metadata, participation notes, errors.
- **Pills** (`.pill`) stay at 13px.
- **The styleguide's type section** lists the seven steps with their roles.

### The survey

| Element | Size | Weight and ink |
|---|---|---|
| Question (`legend`) | 16px (`text-base`) | 600, `neutral-900` |
| Answer options (Sí/No, choices, likert rows) | 16px (`text-base`) | 400, `neutral-800` |
| Likert labels under the radios, desktop | 14px (`text-sm`) | 400, `neutral-600` |
| Help and an error under a question | 14px (`text-sm`) | the error in `danger-600`, with its icon |
| Text, number and select inputs | 16px, through `control` | — |
| Progress and pending-panel text | 14px (`text-sm`) | — |

- **Questions stand out by weight, not size.** At 16px a question is a body-size line set apart by
  its weight and ink.
- **Answers add no height.** Answer rows keep their 44px minimum, so a larger size makes no row
  taller.
- **The cost.** Over the 80+ questions the survey grows by a few lines, not several screens.
- **Survey inputs adopt `control`.** Their layout widths (`w-40`, `w-48`) stay as utilities, and
  their `id`, `name` and `data-*` hooks are unchanged.

### Decisions

- **The class names stay; their values change.** Each use moves to the class of its role, rather
  than every heading growing a full step. A 31px page title wraps to three or more lines at 360px.
- **The survey's question and answers are 16px.** That is the floor for phone reading text, and it
  matches GOV.UK's body-size bold questions on pages that hold many questions. Larger text that a
  reader needs comes from their own text-size setting, which the `rem` sizes honor.
- **13px is for labels on a graphic or badge, never for a sentence.**

### Tests

- **Theme.** A test reads the `@theme` block of `main.css` and checks each `--text-*` size and
  line height against the table.
- **Small text.** A guard fails when a `text-xs` element's own text reads as a sentence: five words
  or more, or ending in a period. It is a heuristic; the doc says so.
- **Survey.** The question form renders its legend with `text-base font-semibold`, its option
  labels with `text-base`, and its inputs with `control`.
- **Existing guards.** `test_responsive.py` and the design-token guards keep passing.
- **By hand.** Every page at 360px and on desktop, in both palettes. On the survey, scroll a full
  module on a phone.

### Out of scope

- The PDF report's stylesheet (`static/css/report*.css`).
- The chart SVG label sizes, which are pixel attributes the PDF reads.
- The Django admin.
- Layout, spacing and copy changes beyond what a size change forces.

---

# Type Scale Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** The scale above as theme tokens, every size class on its role, no sentence at 13px, and the survey at the 16px floor.

**Architecture:** `--text-*` values in the `@theme` block of `static/css/main.css` override Tailwind's defaults under the same class names; templates move between classes by role; two guards in `apps/core/tests/test_design_tokens.py` pin the theme and the small-text rule.

**Tech Stack:** Tailwind v4 CLI (`@theme`), Django templates, pytest.

**Spec:** the brief above.

## Global Constraints

- Sizes: xs 13/1.4 · sm 14/1.5 · base 16/1.5 · lg 20/1.4 · xl 25/1.25 · 2xl 31/1.2 · 3xl 39/1.15, in `rem` (÷16).
- No layout, spacing or copy change beyond what a size change forces.
- The PDF stylesheets, chart SVG `font-size` attributes and the admin are untouched.
- After any change to `templates/` or `static/`: `npm run build:css`; after `static/ts/`: `npm run build:js`.
- Never commit without asking.

## Review Focus

- A page title that wraps on a 360px phone at 25px (the login screen's long heading) must still read as one heading, not push the form below the fold by more than a line or two.
- A `text-xs` string built from template variables (`{{ count }} respuestas`) has no literal words for the guard to count; check those by hand.
- A `text-xs` set by TypeScript (`static/ts/survey_progress.ts`) is assembled as a string, which the guard cannot read; it is checked in review.
- Dashboard stat numbers at 31px in a narrow card must not overflow at 360px (`test_responsive.py` does not see it).
- The OTP digits at 31px with `tracking-widest` must fit a 6- and a 9-digit code in the card at 360px.

---

### Task 1: The scale as theme tokens

**Files:**
- Modify: `static/css/main.css` (the plain `@theme` block)
- Test: `apps/core/tests/test_design_tokens.py`

- [x] **Step 1: Write the failing test:**

```python
TYPE_SCALE = {
    "xs": ("0.8125rem", "1.4"),
    "sm": ("0.875rem", "1.5"),
    "base": ("1rem", "1.5"),
    "lg": ("1.25rem", "1.4"),
    "xl": ("1.5625rem", "1.25"),
    "2xl": ("1.9375rem", "1.2"),
    "3xl": ("2.4375rem", "1.15"),
}


@pytest.mark.parametrize("step", TYPE_SCALE)
def test_the_type_scale_is_the_theme(step):
    size, leading = TYPE_SCALE[step]
    assert f"--text-{step}: {size};" in MAIN_CSS
    assert f"--text-{step}--line-height: {leading};" in MAIN_CSS
```

- [x] **Step 2: Run** `pytest apps/core/tests/test_design_tokens.py -k type_scale` — FAIL.
- [x] **Step 3: Implement:** add the 14 declarations to the plain `@theme` block with a comment naming the roles and pointing at design-system.md. Run `npm run build:css`; confirm `output.css` has `--text-xl: 1.5625rem`.
- [x] **Step 4: Run** `pytest -q` — PASS.

### Task 2: Sizes on their roles

**Files:**
- Modify: every template using `text-2xl`, `text-3xl`, `text-xl` (inventory: 23 / 11 / 5 uses), `templates/core/styleguide.html` (type section)

- [x] **Step 1:** List the uses: `grep -rn "text-\(xl\|2xl\|3xl\)" templates apps static/ts`.
- [x] **Step 2:** Replace:
  - every page-title `h1` `text-2xl` → `text-xl`, and the survey title `text-3xl` → `text-xl`
  - every stat number `text-3xl` → `text-2xl`
  - each `text-xl` by role: the header brand name and the survey module intro (`h3`) → `text-lg`; `employee_detail`'s two → whichever role they hold (read them)
  - leave the `text-2xl` in `apps/accounts/forms.py` (login code digits)
- [x] **Step 3:** Rewrite the styleguide's type section as seven rows, one per step: `13 · etiqueta`, `14 · secundario`, `16 · cuerpo`, `20 · sección`, `25 · título`, `31 · cifra`, `39 · reservado`, each with its class and a sample in the app's own copy.
- [x] **Step 4:** `npm run build:css && pytest -q` — PASS (`test_responsive.py` included).

### Task 3: Sentences leave 13px

**Files:**
- Modify: templates and `static/ts/survey_progress.ts` with `text-xs` used for sentences
- Test: `apps/core/tests/test_design_tokens.py`

- [x] **Step 1: Write the failing guard:**

```python
# An element sized text-xs and the text it holds directly, up to its first tag.
SMALL_TEXT = re.compile(
    r'class="(?=[^"]*(?<![\w:-])text-xs\b)[^"]*"[^>]*>\s*([^<{]+?)\s*(?=<|\{)', re.DOTALL
)


def test_no_sentence_is_set_at_the_smallest_size():
    """13px is for a label on a graphic or a badge. A heuristic: five words or a period."""
    hits = [
        f"{path.relative_to(REPO_ROOT)}: {text}"
        for path in SCANNED
        for text in SMALL_TEXT.findall(path.read_text())
        if len(text.split()) >= 5 or text.rstrip().endswith(".")
    ]
    assert not hits, "use text-sm for a sentence:\n" + "\n".join(hits)
```

- [x] **Step 2: Run** — FAIL with the list.
- [x] **Step 3:** For each of the 92 `text-xs` uses, read it in place and decide: a label on a graphic or badge stays; a sentence, date, note, help or error moves to `text-sm`. Uses the guard cannot see (built from variables, set in TS) are decided by the same rule.
- [x] **Step 4:** `npm run build:css && npm run build:js && pytest -q` — PASS.

### Task 4: The survey at the floor

**Files:**
- Modify: `templates/surveys/_question.html`, `templates/surveys/survey_detail.html`, the survey modals
- Test: `apps/surveys/tests/test_views.py`

- [x] **Step 1: Write the failing test:** GET the survey form for an employee (reuse the existing survey-detail fixture in that file) and assert:
  - the question legend's class holds `text-base` and `font-semibold`
  - every option label's text span holds `text-base`
  - every survey `<input type="text|number|date">` and `<textarea>` carries `control`
  - no `text-xs` appears inside a `question-card`
- [x] **Step 2: Run** — FAIL.
- [x] **Step 3: Implement** in `_question.html`:
  - legend: `text-sm font-medium text-neutral-800` → `text-base font-semibold text-neutral-900`
  - option spans: `text-sm text-neutral-700` → `text-base text-neutral-800`; likert `lg:text-xs lg:text-neutral-600` → `lg:text-sm lg:text-neutral-600`; rating numbers → `text-base`
  - text/number/date inputs and textarea: their hand-made classes → `control` plus their width (`w-40`, `w-48`); keep `name`, `value`, `placeholder`, `step`
  - the error line: `text-xs` → `text-sm`, with `{% icon "exclamation-circle" %}` as in `forms/field.html`
  - in `survey_detail.html` and the modals: help and body text → `text-base` where it is instructions, progress and pending text → `text-sm`
- [x] **Step 4:** `npm run build:css && pytest -q` — PASS.

### Task 5: Documentation

**Files:**
- Modify: `docs/platform/design-system.md`, `.claude/CLAUDE.md` (Design-system bullet), `apps/surveys/CLAUDE.md` if it describes question markup

- [x] **Step 1:** `design-system.md`, present tense:
  - *Type scale*: the table from the brief, the rem note, the 13px rule, and the survey floor
  - *The form control*: survey inputs use it
  - *Key decisions*: the three from the brief
  - *Enforcement*: the theme test and the small-text heuristic, named as a heuristic
- [x] **Step 2:** `.claude/CLAUDE.md`: one sentence. Size classes name a role (`text-xl` page title, `text-lg` section, `text-sm` secondary, `text-xs` only for a label on a graphic or badge), and the survey's questions and answers are `text-base`.
- [x] **Step 3:** `pytest -q && ruff check . && ruff format --check .` — PASS.
