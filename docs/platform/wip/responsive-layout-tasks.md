# Responsive layout implementation plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make every page usable on a 360px phone, and make answering the
NOM-035 survey on one comfortable rather than merely possible.

**Architecture:** The survey page's two-column flex becomes mobile-first
(`flex-col lg:flex-row`). Progress and the save button move into a single DOM
node that renders as a fixed bottom bar below `lg:` and sits in the sidebar at
`lg:` — one node, so none of the element ids `survey_progress.ts` depends on are
duplicated and no TypeScript changes. Instructions reuse the modal that already
exists; the pendientes panel falls to the end of the document below `lg:`, where
a respondent looks before submitting. Answer options across all five question
types become full-width ≥44px rows on a phone.

**Tech Stack:** Django templates, TailwindCSS v4 (CLI build, committed
`output.css`), pytest + pytest-django. No JavaScript test runner.

**Spec:** [`docs/platform/responsive-layout.md`](../responsive-layout.md)

## Global Constraints

- Minimum supported viewport: **360 × 640 CSS pixels**. Phone content box is
  **328px** (360 less the shell's `px-4` on each side).
- Answer options: full-width rows, **≥44px** tall, whole row clickable.
- Mobile-first: unprefixed classes describe the phone; breakpoint prefixes add
  the wide layout. Never `flex-row` with a narrow override bolted on after.
- User-facing copy is **Spanish**; code, comments, identifiers, test names are
  **English**.
- Tailwind compiles only from the `@source` paths in `static/css/main.css`. A
  class introduced anywhere else compiles to nothing and fails no test.
- **Any task touching `templates/` runs `npm run build:css` and commits the
  regenerated `static/css/output.css` in the same commit.**
- `apps/nom035` scoring constants, migrations, authorization, and dependencies
  are untouched by every task here.

---

### Task 1: The width guard

Establishes the automated floor before any layout moves, so the sidebar fix has
something to prove itself against. The minimal change that greens the guard is
the one-line width fix; Task 2 does the real restructure on top of it.

**Files:**
- Create: `apps/core/tests/test_responsive.py`
- Modify: `templates/surveys/survey_detail.html:20`

**Interfaces:**
- Consumes: nothing.
- Produces: `PHONE_CONTENT_BOX_PX = 328` and `_width_px(value: str) -> float | None`
  in `apps/core/tests/test_responsive.py`. Task 2 and Task 3 rely on this test
  continuing to pass, not on importing from it.

- [ ] **Step 1: Write the failing test**

Create `apps/core/tests/test_responsive.py`:

```python
"""Project-wide responsive guarantees: see docs/platform/responsive-layout.md.

This module is a floor, not a guarantee. It reads class names, never a rendered
page, so it cannot see a width that only overflows when repeated, a row that
wraps into nonsense, or whether a control is comfortable to tap. Those are
verified by a human at 360px.
"""

import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]

# 360px, less the page shell's `px-4` on each side.
PHONE_CONTENT_BOX_PX = 328

REM_PX = 16
TAILWIND_UNIT_PX = 4  # w-1 == 0.25rem == 4px

# An *unprefixed* width class. The lookbehind does two jobs: it rejects a
# breakpoint prefix, because `lg:w-96` does not apply at 360px, and it rejects a
# longer token ending in the same letters — `max-w-lg` is a cap that shrinks,
# and `autocomplete="new-password"` is not a class at all.
WIDTH = re.compile(r"(?<![-\w:])(?:min-)?w-(\[[^\]\s]+\]|[a-z0-9./]+)")

# The documented places a Tailwind class may live (static/css/main.css).
SCANNED = (
    *sorted(REPO_ROOT.glob("templates/**/*.html")),
    *sorted(REPO_ROOT.glob("apps/*/forms.py")),
    *sorted(REPO_ROOT.glob("apps/*/templatetags/*.py")),
    *sorted(REPO_ROOT.glob("static/ts/*.ts")),
)


def _width_px(value: str) -> float | None:
    """Rendered width of a Tailwind width value, or None when it cannot overflow.

    `full`, `auto`, `screen`, fractions and viewport-relative `calc()` widths all
    shrink with their container, so none of them can push a page sideways.
    """
    if "/" in value:
        return None
    if value.startswith("["):
        literal = value[1:-1]
        if literal.endswith("rem"):
            return float(literal[:-3]) * REM_PX
        if literal.endswith("px"):
            return float(literal[:-2])
        return None
    try:
        return float(value) * TAILWIND_UNIT_PX
    except ValueError:
        return None


def test_no_unprefixed_width_exceeds_the_phone_content_box():
    """A fixed width wider than the phone refuses to shrink and pushes the page.

    `w-96 shrink-0` on a flex child is the shape of the failure: the sibling
    column is squeezed toward zero and the page scrolls sideways. Widen it under
    a breakpoint instead, so the phone keeps a width it can actually fit.
    """
    offenders = []
    for path in SCANNED:
        for line_no, line in enumerate(path.read_text().splitlines(), start=1):
            for value in WIDTH.findall(line):
                px = _width_px(value)
                if px is not None and px >= PHONE_CONTENT_BOX_PX:
                    rel = path.relative_to(REPO_ROOT)
                    offenders.append(f"{rel}:{line_no} w-{value} ({px:g}px)")

    assert offenders == [], (
        f"Unprefixed widths at or above {PHONE_CONTENT_BOX_PX}px "
        "(the 360px phone content box): " + ", ".join(offenders)
    )
```

- [ ] **Step 2: Run the test and watch it fail on the real defect**

Run: `pytest apps/core/tests/test_responsive.py -v`

Expected: FAIL, naming exactly one offender —
`templates/surveys/survey_detail.html:20 w-96 (384px)`.

If it names anything else, the regex is over-reaching: check that `max-w-5xl`,
`sm:w-[42rem]`, `w-[calc(100vw-2rem)]` and `w-full` are all absent from the
list, and fix `_width_px` rather than adding an allowlist.

- [ ] **Step 3: Make the minimal fix**

In `templates/surveys/survey_detail.html:20`, move the sidebar's fixed width
behind the breakpoint. Replace:

```html
<div class="flex flex-col items-end w-96 shrink-0 order-last">
```

with:

```html
<div class="flex flex-col items-end order-last w-full lg:w-96 lg:shrink-0">
```

- [ ] **Step 4: Run the test and the full suite**

Run: `pytest apps/core/tests/test_responsive.py -v`
Expected: PASS.

Run: `pytest`
Expected: PASS, no regressions.

- [ ] **Step 5: Rebuild CSS and commit**

```bash
npm run build:css
git add apps/core/tests/test_responsive.py templates/surveys/survey_detail.html static/css/output.css
git commit -m "test: fail on fixed widths that cannot fit a 360px phone"
```

---

### Task 2: The survey page shell

The layout restructure. The risk here is not visual — it is that moving elements
silently breaks `survey_progress.ts`, which finds everything by id and which no
test in this repository can exercise. So the DOM contract gets pinned first.

**Files:**
- Create: `apps/surveys/tests/test_survey_page_contract.py`
- Modify: `templates/surveys/survey_detail.html:17-66`

**Interfaces:**
- Consumes: the `lg:w-96` sidebar from Task 1.
- Produces: `#survey-actions`, the single node holding progress and the save
  button. Task 3 does not touch it.

- [ ] **Step 1: Write the failing test**

Create `apps/surveys/tests/test_survey_page_contract.py`:

```python
"""The DOM contract static/ts/survey_progress.ts depends on.

There is no JavaScript test runner, so nothing else in the suite notices when a
layout change renames an id or drops a data attribute. Autosave, the progress
bar, conditional visibility and the pendientes panel all go silently dead. This
module is the only thing standing between a CSS refactor and that outcome; the
lists below are transcribed from survey_progress.ts and must be kept in step
with it.
"""

import pytest

pytestmark = pytest.mark.django_db


def _survey_url(assignment_id):
    return f"/encuestas/asignados/{assignment_id}/"


# Every element survey_progress.ts resolves by id.
REQUIRED_IDS = [
    "survey-form",
    "progress-total",
    "progress-count",
    "progress-bar",
    "pending-panel",
    "pending-count",
    "pending-list",
    "pending-more",
    "pending-next",
    "session-expired-modal",
]

# Every attribute it reads off a card, and the hooks it selects them by.
REQUIRED_HOOKS = [
    'class="question-card',
    'class="module-card',
    "question-label",
    "data-question-code=",
    "data-question-name=",
    "data-module-key=",
    "data-visible-when=",
    "data-total=",
    "data-autosave-url=",
]


@pytest.fixture
def survey_page(client, company, survey_with_questions, active_assignment,
                make_user_with_profile, bootstrap_groups):
    """The survey page as a respondent of the assigned company sees it.

    The group membership is not decoration: `survey_detail` requires
    `can_take_assigned_surveys` and scopes the assignment to the caller's own
    company, so a user missing either lands on a redirect and every assertion
    below passes vacuously against an empty page.
    """
    user = make_user_with_profile(email="respondent@example.com", company=company)
    user.groups.add(bootstrap_groups["Employees"])
    client.force_login(user)

    response = client.get(_survey_url(active_assignment.pk))
    assert response.status_code == 200, (
        f"expected the survey page, got {response.status_code} — "
        "the respondent is probably missing its group or company"
    )
    return response.content.decode()


def test_every_id_the_progress_script_resolves_is_rendered(survey_page):
    missing = [i for i in REQUIRED_IDS if f'id="{i}"' not in survey_page]
    assert missing == [], (
        "survey_progress.ts resolves these by id and would fail silently: "
        + ", ".join(missing)
    )


def test_every_hook_the_progress_script_selects_by_is_rendered(survey_page):
    missing = [h for h in REQUIRED_HOOKS if h not in survey_page]
    assert missing == [], (
        "survey_progress.ts selects on these and would fail silently: "
        + ", ".join(missing)
    )


def test_progress_and_save_share_one_node_so_ids_stay_unique(survey_page):
    """The bottom bar is the sidebar block repositioned, never a second copy.

    Two copies would render `id="progress-bar"` twice; `getElementById` returns
    the first, so the visible one would freeze while the hidden one updated.
    """
    for element_id in REQUIRED_IDS:
        assert survey_page.count(f'id="{element_id}"') == 1, (
            f'id="{element_id}" is rendered more than once'
        )
```

- [ ] **Step 2: Run the test to establish the baseline**

Run: `pytest apps/surveys/tests/test_survey_page_contract.py -v`

Expected: PASS against the current template. That is the point — it is a
regression pin, written *before* the refactor so it can catch one. If the
fixture wiring is wrong it will error instead; fix the fixture, not the asserts.

- [ ] **Step 3: Commit the pin before changing anything**

```bash
git add apps/surveys/tests/test_survey_page_contract.py
git commit -m "test: pin the DOM contract survey_progress.ts depends on"
```

- [ ] **Step 4: Restructure the shell**

In `templates/surveys/survey_detail.html`, replace the wrapper at line 17:

```html
<div class="flex gap-6">
```

with:

```html
<div class="flex flex-col lg:flex-row gap-6">
```

Replace the sticky inner column (line 25) so it only sticks once there is a
column to stick in:

```html
  <div class="w-full flex flex-col items-end gap-5 lg:sticky lg:top-6 lg:max-h-[calc(100vh_-_3rem)] lg:overflow-y-auto lg:px-1">
```

Wrap the instructions card (lines 26-31) so it is the sidebar's on wide screens
only — below `lg:` the existing modal carries it:

```html
    <div class="hidden w-full rounded-lg bg-white border border-indigo-200 shadow-sm p-4 lg:block">
```

Replace the progress block and save button (lines 32-47) with the single
repositioning node. It is `fixed` on a phone and static in the sidebar at `lg:`:

```html
    <div id="survey-actions"
         class="fixed inset-x-0 bottom-0 z-40 flex flex-col gap-2 border-t border-gray-200 bg-white px-4 py-3 shadow-[0_-1px_3px_rgba(0,0,0,0.06)]
                lg:static lg:z-auto lg:w-full lg:gap-5 lg:border-0 lg:bg-transparent lg:px-1 lg:py-0 lg:shadow-none">
      {% if total_questions %}
      <div class="w-full" id="progress-total" data-total="{{ total_questions }}">
        <div class="flex justify-between text-xs text-gray-500 mb-1">
          <span>Progreso</span>
          <span id="progress-count">{{ answered_count }}/{{ total_questions }}</span>
        </div>
        <div class="w-full bg-gray-200 rounded-full h-2">
          <div id="progress-bar" class="bg-indigo-500 h-2 rounded-full transition-all"
               style="width: {% widthratio answered_count total_questions 100 %}%"></div>
        </div>
      </div>
      {% endif %}
      <div class="flex gap-2 lg:flex-col">
        <button type="button"
          onclick="document.getElementById('instrucciones-modal').style.display='flex'"
          class="shrink-0 rounded-lg border border-indigo-200 px-4 py-2.5 text-sm font-semibold text-indigo-700 transition-colors hover:bg-indigo-50 lg:hidden">
          Instrucciones
        </button>
        <button type="submit" form="survey-form"
          class="flex-1 rounded-lg bg-indigo-600 px-4 py-2.5 text-sm font-semibold text-white shadow-sm hover:bg-indigo-500 focus:outline-none focus:ring-2 focus:ring-indigo-600 focus:ring-offset-2 transition-colors lg:w-full">
          {% if is_edit %}Guardar cambios{% else %}Guardar progreso{% endif %}
        </button>
      </div>
    </div>
```

The pendientes panel (lines 51-62) keeps every id and attribute; it only loses
its sidebar-only assumption. Leave its markup as-is — `order-last` on the
sidebar column already places it after the form once the wrapper stacks.

- [ ] **Step 5: Keep the fixed bar from covering the last question**

The form column (line 66) needs clearance below `lg:`, where the action bar
floats over the page. Replace:

```html
<div class="max-w-2xl w-full mx-auto min-w-0">
```

with:

```html
<div class="max-w-2xl w-full mx-auto min-w-0 pb-40 lg:pb-0">
```

- [ ] **Step 6: Run the contract test and the full suite**

Run: `pytest apps/surveys/tests/test_survey_page_contract.py -v`
Expected: PASS — every id still present, each exactly once.

Run: `pytest`
Expected: PASS.

- [ ] **Step 7: Rebuild CSS and commit**

```bash
npm run build:css
git add templates/surveys/survey_detail.html static/css/output.css
git commit -m "feat: stack the survey page and float its actions on a phone"
```

---

### Task 3: Tappable answer controls

The part a respondent actually feels. Every option of every question type
becomes a full-width row at least 44px tall with the whole row as the hit
target, and the likert scale stops wrapping mid-scale.

**Files:**
- Create: `apps/surveys/tests/test_answer_controls.py`
- Modify: `templates/surveys/_question.html:19-33` (boolean), `:36-45`
  (single_choice), `:48-57` (multiple_choice), `:88-98` (rating), `:100-112`
  (likert)

**Interfaces:**
- Consumes: nothing from Tasks 1-2.
- Produces: no new identifiers. The `.question-card`, `.question-label` and
  `data-*` hooks Task 2 pinned are unchanged.

- [ ] **Step 1: Write the failing test**

Create `apps/surveys/tests/test_answer_controls.py`:

```python
"""Every answer option is a row the whole of which is tappable.

Rendered height comes from padding, line height and the preflight reset
together, so no test here computes 44px — that is checked by a finger at 360px.
What *is* checkable is the structural half of the contract: the input sits
inside a label, so the tap area is the row rather than the 16px control.
"""

from html.parser import HTMLParser

import pytest
from django.template.loader import render_to_string

pytestmark = pytest.mark.django_db

ANSWER_INPUT_TYPES = {"radio", "checkbox"}


class _UnlabelledInputFinder(HTMLParser):
    """Collects the name of every radio/checkbox not nested inside a <label>."""

    def __init__(self):
        super().__init__()
        self.label_depth = 0
        self.unlabelled = []

    def handle_starttag(self, tag, attrs):
        if tag == "label":
            self.label_depth += 1
            return
        if tag != "input":
            return
        attributes = dict(attrs)
        if attributes.get("type") in ANSWER_INPUT_TYPES and self.label_depth == 0:
            self.unlabelled.append(attributes.get("name", "?"))

    def handle_endtag(self, tag):
        if tag == "label" and self.label_depth:
            self.label_depth -= 1


def _render(question, existing_answers=None):
    return render_to_string(
        "surveys/_question.html",
        {
            "question": question,
            "existing_answers": existing_answers or {},
            "errors": {},
        },
    )


@pytest.mark.parametrize(
    "question_type",
    ["boolean", "single_choice", "multiple_choice", "rating", "likert"],
)
def test_every_option_is_wrapped_in_its_own_label(
    question_type, survey_with_questions
):
    """An input outside a label makes the 16px control the only hit target."""
    question = next(
        q for q in survey_with_questions["questions"]
        if q.question_type == question_type
    )

    finder = _UnlabelledInputFinder()
    finder.feed(_render(question))

    assert finder.unlabelled == [], (
        f"{question_type}: inputs rendered outside a <label>, so only the "
        f"control itself is tappable: {finder.unlabelled}"
    )


def test_likert_renders_one_row_per_label(survey_with_questions):
    """Five options, five rows, labels intact — the scale reads as a list."""
    question = next(
        q for q in survey_with_questions["questions"]
        if q.question_type == "likert"
    )
    # Set in memory, not saved: the template renders the object it is handed,
    # and `likert_pairs` reads `question.config` straight off it.
    question.config = {
        "labels": ["Siempre", "Casi siempre", "Algunas veces", "Casi nunca", "Nunca"]
    }

    html = _render(question)

    for label in question.config["labels"]:
        assert label in html, f"likert lost its {label!r} option label"
    assert html.count('type="radio"') == 5


def test_likert_options_carry_no_unprefixed_minimum_width(survey_with_questions):
    """A minimum width defeats shrinking; five of them overflow a phone.

    The horizontal scale survives behind `lg:`, where there is room for it.
    """
    question = next(
        q for q in survey_with_questions["questions"]
        if q.question_type == "likert"
    )

    html = _render(question)

    assert "min-w-[72px]" not in html.replace("lg:min-w-[72px]", "")
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `pytest apps/surveys/tests/test_answer_controls.py -v`

Expected: FAIL on `test_likert_options_carry_no_unprefixed_minimum_width` —
`_question.html:104` still carries a bare `min-w-[72px]`. The label-wrapping
tests should already PASS for every type, since each option is already inside a
`<label>`; that is the half of the contract this codebase got right, and the
test exists so a later rewrite cannot lose it.

- [ ] **Step 3: Give boolean full-width rows**

Replace `_question.html:20-33` — the two Sí/No labels — with:

```html
      <div class="flex flex-col gap-2 lg:flex-row lg:gap-6">
        <label class="flex min-h-11 items-center gap-3 cursor-pointer rounded-md border border-gray-200 px-3 py-2.5 transition-colors hover:bg-gray-50 lg:min-h-0 lg:border-0 lg:px-0 lg:py-0 lg:hover:bg-transparent">
          <input type="radio" name="question_{{ question.id }}" value="true"
            {% if ans == True %}checked{% endif %}
            class="h-4 w-4 text-indigo-600 border-gray-300 focus:ring-indigo-500">
          <span class="text-sm text-gray-700">Sí</span>
        </label>
        <label class="flex min-h-11 items-center gap-3 cursor-pointer rounded-md border border-gray-200 px-3 py-2.5 transition-colors hover:bg-gray-50 lg:min-h-0 lg:border-0 lg:px-0 lg:py-0 lg:hover:bg-transparent">
          <input type="radio" name="question_{{ question.id }}" value="false"
            {% if ans == False and ans is not None %}checked{% endif %}
            class="h-4 w-4 text-indigo-600 border-gray-300 focus:ring-indigo-500">
          <span class="text-sm text-gray-700">No</span>
        </label>
      </div>
```

- [ ] **Step 4: Raise single_choice and multiple_choice to 44px**

These are already full-width rows; they are 36px tall. In `_question.html:38`
replace `px-3 py-2` with `min-h-11 px-3 py-2.5`:

```html
          <label class="flex min-h-11 items-center gap-3 cursor-pointer rounded-md px-3 py-2.5 hover:bg-gray-50 transition-colors">
```

Make the identical change at `_question.html:50` for `multiple_choice`:

```html
          <label class="flex min-h-11 items-center gap-3 cursor-pointer rounded-md px-3 py-2.5 hover:bg-gray-50 transition-colors">
```

- [ ] **Step 5: Stack the rating scale**

Replace `_question.html:89-98`:

```html
      <div class="flex flex-col gap-2 lg:flex-row lg:gap-4">
        {% for i in "12345" %}
          <label class="flex min-h-11 items-center gap-3 cursor-pointer rounded-md border border-gray-200 px-3 py-2.5 transition-colors hover:bg-gray-50 lg:min-h-0 lg:flex-col lg:items-center lg:gap-1 lg:border-0 lg:px-0 lg:py-0 lg:hover:bg-transparent">
            <input type="radio" name="question_{{ question.id }}" value="{{ i }}"
              {% if ans == i %}checked{% endif %}
              class="h-4 w-4 text-indigo-600 border-gray-300 focus:ring-indigo-500">
            <span class="text-sm text-gray-600">{{ i }}</span>
          </label>
        {% endfor %}
      </div>
```

- [ ] **Step 6: Stack the likert scale**

Replace `_question.html:102-111`:

```html
      <div class="flex flex-col gap-2 lg:flex-row lg:flex-wrap lg:gap-2">
        {% for value, label in pairs %}
          <label class="flex min-h-11 items-center gap-3 cursor-pointer rounded-md border border-gray-200 px-3 py-2.5 transition-colors hover:bg-gray-50 lg:min-h-0 lg:min-w-[72px] lg:flex-col lg:items-center lg:gap-1 lg:border-0 lg:px-0 lg:py-0 lg:text-center lg:hover:bg-transparent">
            <input type="radio" name="question_{{ question.id }}" value="{{ value }}"
              {% if ans == value %}checked{% endif %}
              class="h-4 w-4 text-indigo-600 border-gray-300 focus:ring-indigo-500">
            <span class="text-sm text-gray-700 lg:text-xs lg:text-gray-600">{{ label }}</span>
          </label>
        {% endfor %}
      </div>
```

- [ ] **Step 7: Run the tests**

Run: `pytest apps/surveys/tests/test_answer_controls.py -v`
Expected: PASS, all seven.

Run: `pytest`
Expected: PASS. `apps/surveys/tests/test_views.py` posts answers by field name;
none of these edits touch a `name` or `value`, so nothing there should move.

- [ ] **Step 8: Rebuild CSS and commit**

```bash
npm run build:css
git add templates/surveys/_question.html apps/surveys/tests/test_answer_controls.py static/css/output.css
git commit -m "feat: answer every question type by tapping a full-width row"
```

---

### Task 4: The remaining narrow-viewport spots

Everything outside the survey flow. Scope is conformance only — the dashboards
are card-first already and are not being redesigned.

**Files:**
- Modify: `templates/accounts/profile_setup.html:104`
- Modify: `templates/core/employee_list.html:58-61`

- [ ] **Step 1: Stack the date-of-birth group on a phone**

Three selects side by side in 328px is about 100px each, which truncates the
month name. At `_question.html`'s sibling `templates/accounts/profile_setup.html:104`,
replace:

```html
        <div role="group" aria-labelledby="id_date_of_birth_label" class="grid grid-cols-3 gap-3">
```

with:

```html
        <div role="group" aria-labelledby="id_date_of_birth_label" class="grid grid-cols-1 gap-3 sm:grid-cols-3">
```

- [ ] **Step 2: Keep the roster filter bar from eating the screen**

`templates/core/employee_list.html:61` carries `min-w-48` on the search field
inside a `flex flex-wrap` row in a `sticky` strip. At 328px the row wraps to
several lines and the sticky bar swallows the viewport. Replace line 61:

```html
        <div class="relative min-w-48 flex-1">
```

with:

```html
        <div class="relative w-full flex-1 sm:min-w-48 sm:w-auto">
```

- [ ] **Step 3: Verify the guard and the suite**

Run: `pytest`
Expected: PASS, including `test_no_unprefixed_width_exceeds_the_phone_content_box`
and the roster tests in `apps/core/tests/test_roster.py`.

- [ ] **Step 4: Rebuild CSS and commit**

```bash
npm run build:css
git add templates/accounts/profile_setup.html templates/core/employee_list.html static/css/output.css
git commit -m "fix: stack the birth-date group and the roster search on a phone"
```

---

### Task 5: Human verification at 360px

The suite cannot see a rendered page. This task is the part of the contract that
only a person can sign off, and it runs before the PR, not after.

- [ ] **Step 1: Confirm the build is current**

```bash
npm run build:css
git status --short
```

Expected: no unstaged change to `static/css/output.css`. If there is one, a
previous task committed a stale build — commit the regenerated file.

- [ ] **Step 2: Serve the app and seed a survey**

```bash
python manage.py runserver
```

In a second shell, if no NOM-035 survey is seeded:

```bash
python manage.py seed_nom035_survey
python manage.py bootstrap_groups
```

- [ ] **Step 3: Hand the reviewer this list**

Ask the user to open the survey at a 360px-wide viewport (browser devtools,
responsive mode, 360 × 640) and confirm each item. Do not install a browser
automation dependency to do this.

On the **survey page**:
1. No horizontal scrollbar anywhere down the full length of the form.
2. The action bar is pinned to the bottom of the screen, showing the progress
   count, **Instrucciones** and **Guardar progreso**.
3. Scrolling to the very last question, the bar does not cover it.
4. **Instrucciones** opens the existing modal and closes again.
5. A likert question shows five stacked rows; tapping anywhere on a row —
   including the empty space right of the label — selects it.
6. The same for a Sí/No question and for a Guía I follow-up.
7. Answering a gate question (`En mi trabajo debo brindar servicio a clientes o
   usuarios`) still reveals its follow-up block, and the progress count moves.
8. Leaving a question unanswered and scrolling to the bottom shows the
   **Pendientes** panel after the form; **Ir a la siguiente** jumps to a
   question and rings it.
9. **Guardar progreso** saves and the confirmation modal fits the screen.

On the **header**, on every signed-in page (added after the first walkthrough
found it overflowing):
10. No sideways scroll from the header at 360px: logo only, no **SOFIA-S**
    wordmark, no back link, and **Cerrar sesión** as plain text on the right.
11. Tapping **Cerrar sesión** signs out; nothing else in the header is tappable,
    so there is no circle to tap by mistake.
12. Above `sm:` the wordmark and back link return, the right-hand side is the
    initials circle, and hovering it swaps to **Cerrar sesión** without the
    header shifting sideways.
13. Each page's title reads once, in the content, not twice — the company
    dashboard now shows the company name as its heading.

On **the rest**:
14. Login, OTP verification and the activation form each fit with no sideways
    scroll; the date-of-birth selects are stacked.
15. The roster's filter bar does not occupy more than roughly a third of the
    screen, and search still submits.
16. A company dashboard and an employee detail page read without sideways
    scroll.

- [ ] **Step 4: Record the outcome**

Note anything the reviewer rejects, fix it, rebuild CSS, and re-run the list for
the affected items only. Do not proceed to Task 6 with an open rejection.

---

### Task 6: The app header

The header is one `flex items-center justify-between` row with no wrapping and
no breakpoints: logo, a nav whose width is unbounded user data, and a `w-28`
logout control. Every width in it is harmless alone, which is why the guard
cannot see it and the 360px walkthrough could.

The page label leaves the header entirely. Four of the five templates already
render it in content, so this mostly deletes duplicates.

**Files:**
- Move: `templates/core/_avatar.html` → `templates/_avatar.html`
- Modify: `templates/core/employee_list.html` (include path, header_nav),
  `templates/core/employee_detail.html` (include path, header_nav),
  `templates/base_app.html`, `templates/surveys/survey_detail.html`,
  `templates/surveys/survey_submitted.html`,
  `templates/core/company_dashboard.html`
- Modify: `apps/core/tests/test_views.py` (the `_avatar` helper)
- Create: `apps/core/tests/test_app_header.py`

**Interfaces:**
- Produces: `templates/_avatar.html`, taking `person` (a `User`) plus optional
  `size` (default `size-12`) and `text` (default `text-sm`) Tailwind utilities.

- [ ] **Step 1: Stop the avatar helper from resolving to the header**

`apps/core/tests/test_views.py:41` takes the first `data-avatar` in the
document. The header is about to render one on every page, outside `<main>`, so
both sides of `test_the_avatar_is_one_component_on_both_pages` would resolve to
the same header element and the test would pass while asserting nothing.

Scope the helper to the content region:

```python
def _avatar(html):
    """The shared avatar element from the page content, whitespace-normalized.

    Scoped to `<main>` on purpose: the app header renders its own, smaller
    avatar outside it, and an unscoped search would match that one on every
    page — leaving this comparison true and meaningless.
    """
    content = html[html.index("<main") :]
    match = re.search(r"<span data-avatar\b.*?</span>", content, re.S)
    assert match, "no element carrying data-avatar was rendered in <main>"
    return " ".join(match.group(0).split())
```

- [ ] **Step 2: Move the avatar and make it sizeable**

```bash
git mv templates/core/_avatar.html templates/_avatar.html
```

Rewrite it. The root element becomes a `<span>` so it is valid phrasing content
inside the header's `<button>`; as a flex item its `inline-flex` is blockified,
so the roster and detail page render exactly as before:

```html
{% comment %}
The initials circle. Takes `person`, a User, and optionally `size` and `text`
(Tailwind utilities, defaulting to the 48px roster circle). Included by the app
header, the roster card and the colaborador detail page so none can drift away
from the others.

`aspect-square` beside the size is not redundant: the circle is a flex item in
its callers, and a long name beside it would squash the width below the height
and hand back an ellipse. `leading-none` seats the initials optically in the
middle — the default line box sits the glyphs low. A `<span>` rather than a
`<div>` so the header can nest it inside a button. The initials repeat the name
printed next to them, so they are decorative to a screen reader.
{% endcomment %}
<span data-avatar aria-hidden="true"
      class="inline-flex aspect-square {{ size|default:"size-12" }} shrink-0 select-none items-center justify-center rounded-full bg-indigo-50 {{ text|default:"text-sm" }} font-semibold uppercase leading-none text-indigo-700 ring-1 ring-inset ring-indigo-600/20">{% if person.get_initials %}{{ person.get_initials }}{% else %}{{ person.email|slice:":2" }}{% endif %}</span>
```

Update both existing callers to the new path, leaving their size at the default:

- `templates/core/employee_list.html:190` → `{% include "_avatar.html" with person=user %}`
- `templates/core/employee_detail.html:36` → `{% include "_avatar.html" with person=emp %}`

- [ ] **Step 3: Rebuild the header**

In `templates/base_app.html`, replace the header's inner row:

```html
  <div class="mx-auto {{ container_width|default:"max-w-5xl" }} px-4 py-4 flex items-center justify-between gap-3">
    <div class="flex min-w-0 items-center gap-3">
      <a href="{% url 'core:home' %}" class="flex shrink-0 items-center gap-2">
        <img src="{% static 'img/logo.svg' %}" alt="Logo SOFIA-S" class="h-8 mt-2 mb-3 w-auto">
        <span class="hidden text-xl font-semibold text-gray-900 sm:inline">SOFIA-S</span>
      </a>
      {% comment %}
      The back link is desktop-only. A phone goes back by swiping, and the logo
      is a link home for anyone who arrived from an emailed link with no history
      behind them. Hiding it here rather than in each template keeps the five
      header_nav blocks free of breakpoints.
      {% endcomment %}
      <div class="hidden min-w-0 items-center gap-3 sm:flex">
        {% block header_nav %}{% endblock %}
      </div>
    </div>
    <form method="post" action="{% url 'accounts:logout' %}" class="shrink-0">
      {% csrf_token %}
      {% comment %}
      `w-28` holds the width steady while the avatar and the label swap, so the
      header does not shift under the cursor. Below `sm:` there is no hover to
      reveal anything, and a bare circle would invite a tap that silently logs
      the visitor out — so the action names itself instead.
      {% endcomment %}
      <button type="submit"
              class="group flex w-28 items-center justify-end text-sm text-gray-500 transition-colors hover:text-gray-700">
        <span class="sm:hidden">Cerrar sesión</span>
        <span class="hidden sm:inline sm:group-hover:hidden">
          {% include "_avatar.html" with person=request.user size="size-8" text="text-xs" only %}
        </span>
        <span class="hidden sm:group-hover:inline">Cerrar sesión</span>
      </button>
    </form>
  </div>
```

- [ ] **Step 4: Drop the page label from all five header_nav blocks**

In each, delete the trailing separator `<span>` and the label `<span>`, keeping
the leading separator and the back link exactly as they are.

- `templates/surveys/survey_detail.html` — delete the second `|` and
  `<span class="font-semibold text-gray-800">{{ survey.title }}</span>`. The
  title already renders at `:99` as the content `<h1>`.
- `templates/surveys/survey_submitted.html` — same two lines. The title already
  appears in the sentence at `:26` beneath the `¡Gracias!` heading.
- `templates/core/employee_list.html` — delete the third `|` and
  `<span …>Colaboradores</span>`. Already the content `<h1>` at `:43`.
- `templates/core/employee_detail.html` — delete the second `|` and the whole
  `<span class="font-semibold text-gray-800">…{% endif %}</span>` label. The
  content `<h1>` at `:38` already shows the name, with a better fallback
  (`Sin nombre`) than the header's email.
- `templates/core/company_dashboard.html` — delete the second `|` and
  `<span …>{{ company.name }}</span>`. A non-admin then renders an empty
  `header_nav`, which is already the case for `company_list.html` and
  `employee_survey_list.html`.

- [ ] **Step 5: Give the company dashboard the title it never had**

It is the only one of the five with no heading in content — `{% block content %}`
opens straight into the stat grid. Insert above `{# Summary strip #}`:

```html
  <div class="mb-5">
    <h1 class="text-2xl font-bold text-gray-900">{{ company.name }}</h1>
  </div>
```

- [ ] **Step 6: Write the header tests**

Create `apps/core/tests/test_app_header.py`:

```python
"""The application header, which every signed-in page renders.

The header holds the only logout control in the product, so these assert that
it survives — a header regression is otherwise invisible to a suite with no
browser.
"""

import pytest

pytestmark = pytest.mark.django_db

DASHBOARD_URL = "/tablero-empresa/"


@pytest.fixture
def dashboard(client, make_company, make_user_with_profile, bootstrap_groups):
    """The company dashboard as its principal executive sees it."""
    company = make_company(name="Acme México")
    viewer = make_user_with_profile(
        email="exec@acme.mx",
        company=company,
        first_name="Laura",
        paternal_last_name="Torres",
    )
    viewer.groups.add(bootstrap_groups["Principal Exec"])
    client.force_login(viewer)

    response = client.get(DASHBOARD_URL)
    assert response.status_code == 200, f"got {response.status_code}"
    return response.content.decode()


def test_the_header_renders_the_viewers_initials(dashboard):
    """The circle stands in for the name the header used to print."""
    header = dashboard[: dashboard.index("<main")]

    assert "data-avatar" in header
    assert ">LT<" in header.replace(" ", "").replace("\n", "")


def test_the_header_always_offers_a_way_to_sign_out(dashboard):
    """Below `sm:` the label is the control; above it, hover reveals the label.

    Either way the words are in the markup — a header that renders only a
    circle would log a phone visitor out on a curious tap.
    """
    header = dashboard[: dashboard.index("<main")]

    assert header.count("Cerrar sesión") == 2


def test_the_company_name_is_the_page_title_not_a_header_crumb(dashboard):
    """The label moved out of the header and into the content as an <h1>."""
    header, content = dashboard.split("<main", 1)

    assert "Acme México" not in header
    assert "<h1" in content
    assert "Acme México" in content
```

- [ ] **Step 7: Run the tests**

Run: `pytest apps/core/tests/test_app_header.py -v`
Expected: PASS, all three.

Run: `pytest`
Expected: PASS. Watch `test_the_avatar_is_one_component_on_both_pages`
specifically — it exercises the moved include on both pages, so a stale
`core/_avatar.html` path would raise `TemplateDoesNotExist` there first.

If `DASHBOARD_URL` is wrong, read `apps/core/urls.py` and correct it.

- [ ] **Step 8: Rebuild CSS and commit**

Confirm the new utilities compiled — Tailwind escapes `:` in its selectors, so
grep the escaped form:

```bash
npm run build:css
grep -c 'sm\\:group-hover\\:inline' static/css/output.css   # expect 1
grep -c 'size-8' static/css/output.css                      # expect >= 1
```

```bash
git add -A
git commit -m "feat: rebuild the app header around the initials avatar"
```

---

### Task 7: Documentation

The last task, always. Both docs ship in this diff and are reviewed with the
code.

**Files:**
- Modify: `docs/platform/responsive-layout.md`
- Modify: `docs/platform/survey-model.md:143-147`
- Delete: `docs/platform/wip/responsive-layout-tasks.md` (this file, at merge)

- [ ] **Step 1: Trim the feature doc to its post-ship form**

In `docs/platform/responsive-layout.md`:

- Set `## Status` to `Current — implemented across `templates/`, guarded by
  `apps/core/tests/test_responsive.py``.
- Under `## Scope`, delete the bullet beginning "Bringing the existing templates
  into conformance". It describes a transition, and a live doc must read as
  though the current implementation were always the original.
- Under `## Enforcement`, name the test modules by path:
  `apps/core/tests/test_responsive.py` for the width guard,
  `apps/surveys/tests/test_survey_page_contract.py` for the DOM contract, and
  `apps/core/tests/test_app_header.py` for the header.
- Under `## Scope`, the out-of-scope touch-target bullet claims the header's
  logout control "keeps the sizes they have", which Task 6 makes false. The
  boundary still holds — nothing outside the survey form was enlarged for a
  thumb — so restate it without the false claim:

```markdown
- **Touch-target sizing outside the survey form.** The roster filter bar, the
  header controls and the dashboard cards are sized for reading rather than for
  a thumb. An administrator meets them rarely; a respondent meets an answer
  control 87 times.
```
- Re-read the whole file for any remaining before/after phrasing. There must be
  no "formerly", "no longer", "replaces" or "used to".

- [ ] **Step 2: Correct the survey-model doc**

`docs/platform/survey-model.md:143-147` currently describes the pendientes panel
as desktop-shaped and the sidebar as breakpoint-free. Replace that paragraph
with a present-tense description of what now exists:

```markdown
The panel is the sidebar's last card on a wide screen. Below `lg:` the sidebar
stacks after the form, so the panel is what a respondent meets on reaching the
end of the questions — where **Ir a la siguiente** walks them back through
whatever is still blank. Progress and **Guardar progreso** stay reachable
throughout in an action bar pinned to the bottom of the screen; it is the same
element as the sidebar block, repositioned, so the panel and the bar can never
disagree. See [`responsive-layout.md`](./responsive-layout.md).
```

- [ ] **Step 3: Verify no migration commentary survives**

```bash
grep -rniE "formerly|no longer|used to|replaces|previously|superseded|deprecated" docs/platform/responsive-layout.md docs/platform/survey-model.md
```

Expected: no output. `docs/adr/` and `docs/archive/` are the only places that
history belongs.

- [ ] **Step 4: Run the full suite one last time**

Run: `pytest`
Expected: PASS.

Run: `ruff check . && ruff format --check .`
Expected: clean.

- [ ] **Step 5: Commit**

```bash
git add docs/platform/responsive-layout.md docs/platform/survey-model.md
git commit -m "docs: describe the responsive contract and the survey page shape"
```

- [ ] **Step 6: Stop before shipping**

Opening the PR is a gate. Summarize the branch, confirm
`docs/platform/wip/` will be cleared as the landing step, and wait.
