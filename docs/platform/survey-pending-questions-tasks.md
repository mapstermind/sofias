# Pending-questions panel — implementation plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Give a respondent on a long survey a way to find the questions they skipped, instead of hunting for them by scrolling.

**Architecture:** Purely additive to the existing take-survey page. `static/ts/survey_progress.ts` already recomputes the set of **visible and unanswered** question cards on every `change`/`input` — the same set that drives the progress bar. A new **Pendientes** panel renders that set into the sticky sidebar; the server contributes only a `pending_count` used by the saved-progress modal. No model, migration, URL, or new-view work.

**Tech Stack:** Django 6.0 templates, TypeScript (`tsconfig.browser.json` → `static/js/`), TailwindCSS v4 with explicit `@source` list, pytest + pytest-django.

## Global Constraints

- **User-facing copy is Spanish (es-MX); code, comments, identifiers and test names are English.** Every new string a respondent reads is Spanish.
- **Tailwind compiles only from the `@source` list in `static/css/main.css`**: `templates/`, three named `.py` files, and `static/ts`. A class written anywhere else compiles to nothing and renders unstyled — with no test failure. Classes in this plan live only in `templates/` and `static/ts/survey_progress.ts`, both already sourced.
- **The final step of any change touching `templates/` or `static/` is the matching build**, with regenerated output committed: `npm run build:css` for templates/classes, `npm run build:js` for `static/ts/*.ts`. Do not assume a watcher is running.
- **Live documentation describes only the current implementation** — no "replaces the old", "formerly", or before/after commentary. `docs/platform/survey-model.md` and `apps/surveys/CLAUDE.md` already document this feature in present tense; the code must match them.
- **Never edit anything under `docs/adr/`.**
- `tsconfig.browser.json` sets `strict` **and** `noUncheckedIndexedAccess`: indexing an array yields `T | undefined`. Bind `arr[0]` to a local and null-check it rather than using `!`.
- Run tests with `pytest` (settings `config.settings`, `addopts = --reuse-db -x`).

## File Structure

| File | Responsibility |
| --- | --- |
| `apps/surveys/views.py` | Add `pending_count` to the `survey_detail` render context. Nothing else changes. |
| `templates/surveys/_progress_saved_modal.html` | State the pending count when saving with questions left. |
| `templates/surveys/_question.html` | Tag the question-text `<label>` with `question-label` so the client can read it unambiguously. |
| `templates/surveys/survey_detail.html` | Static shell of the Pendientes panel (empty, `hidden`), plus the sticky column's height cap. |
| `static/ts/survey_progress.ts` | Compute the pending set, render the panel, and handle click / jump-button navigation. |
| `apps/surveys/tests/test_views.py` | Server-side coverage for `pending_count` and the modal copy. |

The panel's markup is split deliberately: the **shell** (card, heading, empty `<ul>`, counter line, jump button) is server-rendered so its classes are Tailwind-visible in `templates/`, while only the **list items** are built by TypeScript. Item classes are string literals in the `.ts` file, which is itself an `@source`.

---

### Task 1: Server-side pending count and saved-modal copy

**Files:**
- Modify: `apps/surveys/views.py:190-218` (the `survey_detail` render block)
- Modify: `templates/surveys/_progress_saved_modal.html:20-22`
- Test: `apps/surveys/tests/test_views.py`

**Interfaces:**
- Consumes: `progress_for_modules(modules, existing_answers) -> (answered, total)`, already called in `survey_detail`.
- Produces: template context key `pending_count: int` on `surveys/survey_detail.html`. Task 3 does **not** consume it — the client recomputes its own count from the DOM, because conditional visibility can change without a page load.

- [ ] **Step 1: Write the failing tests**

Append to `apps/surveys/tests/test_views.py`. The `survey_with_questions` fixture creates exactly 9 questions, so answering one leaves 8 pending and answering eight leaves 1.

```python
class TestPendingCount:
    """`pending_count` tells a respondent how many questions they still owe.

    Saving is the moment someone believes they are finished, so the saved
    modal is where the number has to appear — the confirmation modal only
    ever opens at zero pending.
    """

    def test_pending_count_is_the_unanswered_visible_total(
        self, client, active_assignment, survey_with_questions
    ):
        first = survey_with_questions["questions"][0]
        client.post(
            _survey_url(active_assignment.pk),
            {f"question_{first.id}": "Una respuesta"},
        )

        response = client.get(_survey_url(active_assignment.pk))

        assert response.context["pending_count"] == 8

    def test_pending_count_is_zero_once_everything_is_answered(
        self, client, active_assignment, survey_with_questions
    ):
        questions = survey_with_questions["questions"]
        client.post(_survey_url(active_assignment.pk), _answers_for(questions))

        response = client.get(_survey_url(active_assignment.pk))

        assert response.context["pending_count"] == 0

    def test_saved_modal_states_the_plural_count(
        self, client, active_assignment, survey_with_questions
    ):
        first = survey_with_questions["questions"][0]
        client.post(
            _survey_url(active_assignment.pk),
            {f"question_{first.id}": "Una respuesta"},
        )

        response = client.get(f"{_survey_url(active_assignment.pk)}?saved=1")

        assert "Te faltan 8 preguntas por responder." in response.content.decode()

    def test_saved_modal_states_the_singular_count(
        self, client, active_assignment, survey_with_questions
    ):
        """Spanish inflects the verb as well as the noun, so one pending
        question is `Te falta 1 pregunta`, not `Te faltan 1 preguntas`."""
        questions = survey_with_questions["questions"]
        answers = _answers_for(questions)
        answers.pop(f"question_{questions[-1].id}")
        client.post(_survey_url(active_assignment.pk), answers)

        response = client.get(f"{_survey_url(active_assignment.pk)}?saved=1")

        assert "Te falta 1 pregunta por responder." in response.content.decode()
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `pytest apps/surveys/tests/test_views.py::TestPendingCount -v`
Expected: FAIL — `KeyError: 'pending_count'` on the first two, and the copy assertions not found on the last two.

- [ ] **Step 3: Add `pending_count` to the view context**

In `apps/surveys/views.py`, immediately after the existing `is_complete` line:

```python
    # Progress: count visible questions answered (using stored answers).
    answered_count, total_questions = progress_for_modules(modules, existing_answers)
    is_complete = bool(total_questions) and answered_count == total_questions
    pending_count = total_questions - answered_count
```

and add the key to the context dict, next to `answered_count`:

```python
            "total_questions": total_questions,
            "answered_count": answered_count,
            "pending_count": pending_count,
```

- [ ] **Step 4: State the count in the saved modal**

In `templates/surveys/_progress_saved_modal.html`, directly after the existing `<p class="text-sm text-gray-600 text-center">…</p>` paragraph:

```html
    {% if pending_count %}
    <p class="mt-3 text-sm font-medium text-amber-700 text-center">
      {% if pending_count == 1 %}Te falta 1 pregunta por responder.{% else %}Te faltan {{ pending_count }} preguntas por responder.{% endif %}
    </p>
    {% endif %}
```

The `{% if pending_count %}` guard matters: a stale `?saved=1` left in the URL by the back button can render this modal at zero pending, and the sentence must not appear then.

- [ ] **Step 5: Run the tests to verify they pass**

Run: `pytest apps/surveys/tests/test_views.py::TestPendingCount -v`
Expected: 4 passed.

- [ ] **Step 6: Run the full survey suite for regressions**

Run: `pytest apps/surveys -q`
Expected: all pass. `--reuse-db -x` is already in `addopts`.

- [ ] **Step 7: Build CSS and commit**

`text-amber-700` is new to the project, so the stylesheet must be rebuilt or the sentence renders in the inherited colour.

```bash
npm run build:css
git add apps/surveys/views.py templates/surveys/_progress_saved_modal.html \
        apps/surveys/tests/test_views.py static/css/output.css
git commit -m "Tell a respondent how many questions are left when saving progress"
```

---

### Task 2: Panel shell and the question-label hook

**Files:**
- Modify: `templates/surveys/_question.html:8-10`
- Modify: `templates/surveys/survey_detail.html:18-42`
- Test: `apps/surveys/tests/test_views.py`

**Interfaces:**
- Produces, for Task 3 to query: `.question-label` (the question-text `<label>` inside every `.question-card`), `#pending-panel`, `#pending-count`, `#pending-list`, `#pending-more`, `#pending-next`.
- The panel ships `hidden` and empty. Task 3 is what fills and unhides it, so after this task the page looks unchanged — that is the expected outcome, not a bug.

- [ ] **Step 1: Write the failing test**

Append to `apps/surveys/tests/test_views.py`:

```python
class TestPendingPanelShell:
    """The panel's shell is server-rendered so Tailwind can see its classes;
    only the list items are built client-side."""

    def test_panel_shell_renders_hidden_and_empty(
        self, client, active_assignment, survey_with_questions
    ):
        response = client.get(_survey_url(active_assignment.pk))
        html = response.content.decode()

        assert 'id="pending-panel"' in html
        assert 'id="pending-list"' in html
        assert 'id="pending-next"' in html
        assert "Ir a la siguiente" in html

    def test_question_text_label_is_tagged_for_the_client(
        self, client, active_assignment, survey_with_questions
    ):
        """The client reads question text from this label. Choice options are
        `<label>`s too, so the hook has to be a class, not element order."""
        response = client.get(_survey_url(active_assignment.pk))

        assert "question-label" in response.content.decode()
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `pytest apps/surveys/tests/test_views.py::TestPendingPanelShell -v`
Expected: FAIL — both assertions missing.

- [ ] **Step 3: Tag the question-text label**

In `templates/surveys/_question.html`, change the question label's opening tag only (leave the choice `<label>`s alone):

```html
  <label class="question-label block text-sm font-medium text-gray-800 mb-3">
    {{ question.text }}
  </label>
```

- [ ] **Step 4: Add the panel shell to the sidebar**

In `templates/surveys/survey_detail.html`, change the sticky column's opening tag to cap its height, so a tall instructions card can never push the panel out of reach:

```html
  <div class="sticky top-6 w-full flex flex-col items-end gap-5 max-h-[calc(100vh-3rem)] overflow-y-auto">
```

The overflow sits on the sticky element itself, not an ancestor, so stickiness is unaffected.

Then insert this **after** the closing `</button>` of the `Guardar progreso` submit button and before the closing `</div>` of that sticky column:

```html
    <div id="pending-panel" class="w-full rounded-lg bg-white border border-amber-200 shadow-sm p-4" hidden>
      <h2 class="text-sm font-semibold text-gray-900 mb-2">
        Pendientes (<span id="pending-count">0</span>)
      </h2>
      <ul id="pending-list" class="space-y-1 max-h-[30vh] overflow-y-auto"></ul>
      <p id="pending-more" class="mt-2 text-xs text-gray-500" hidden></p>
      <button type="button" id="pending-next"
        class="mt-3 w-full rounded-lg border border-amber-300 bg-amber-50 px-3 py-2 text-xs font-medium text-amber-800 hover:bg-amber-100 transition-colors">
        Ir a la siguiente &darr;
      </button>
    </div>
```

Amber, not red: red is already the error state on `.question-card` and in the validation banner, and an unanswered question is not an error.

`#pending-more` sits **outside** `#pending-list`, so the "y N más" line stays visible when the list scrolls.

- [ ] **Step 5: Run the tests to verify they pass**

Run: `pytest apps/surveys/tests/test_views.py::TestPendingPanelShell -v`
Expected: 2 passed.

- [ ] **Step 6: Build CSS and commit**

```bash
npm run build:css
git add templates/surveys/_question.html templates/surveys/survey_detail.html \
        apps/surveys/tests/test_views.py static/css/output.css
git commit -m "Add the pending-questions panel shell to the survey sidebar"
```

---

### Task 3: Render the pending list and jump to a question

**Files:**
- Modify: `static/ts/survey_progress.ts` (new section after `// --- Progress ---` and before `// --- Auto-save ---`; plus the `refresh` function)

**Interfaces:**
- Consumes from the existing module: `questionCards(form): HTMLElement[]`, `isAnswered(name, form): boolean`, `refresh(form): void`. Consumes from Task 2: `#pending-panel`, `#pending-count`, `#pending-list`, `#pending-more`, `.question-label`.
- Produces for Task 4: `pendingCards(form: HTMLFormElement): HTMLElement[]` (visible-and-unanswered cards in document order), `revealCard(card: HTMLElement): void`, and the module-level `lastRevealed: HTMLElement | null`.

- [ ] **Step 1: Add the pending-set helpers**

Insert after `updateProgress()` and before `function refresh(`:

```ts
// --- Pending questions panel ------------------------------------------------

const PENDING_LIMIT = 6;
const HIGHLIGHT_MS = 1500;
const RING_CLASSES = ["ring-2", "ring-amber-400", "ring-offset-2"];

/** The card most recently jumped to, so the next-pending button (Task 4)
 *  advances instead of re-selecting whatever is already under the cursor. */
let lastRevealed: HTMLElement | null = null;

/** Visible, unanswered question cards in document order. */
function pendingCards(form: HTMLFormElement): HTMLElement[] {
  return questionCards(form).filter((card) => {
    if (card.hidden) return false;
    const name = card.dataset["questionName"];
    return name ? !isAnswered(name, form) : false;
  });
}

/** The question's own text. Choice options are `<label>`s too, so this reads
 *  the tagged one rather than trusting document order. */
function questionLabel(card: HTMLElement): string {
  const label = card.querySelector(".question-label");
  return (label?.textContent ?? "").trim();
}
```

`card.hidden` is set by `applyVisibility`, which `refresh` runs first — so a question gated out by `visible_when` is never listed, for free.

- [ ] **Step 2: Add the reveal behaviour**

Append directly below:

```ts
function revealCard(card: HTMLElement): void {
  lastRevealed = card;
  card.scrollIntoView({ behavior: "smooth", block: "center" });
  card.classList.add(...RING_CLASSES);
  window.setTimeout(() => card.classList.remove(...RING_CLASSES), HIGHLIGHT_MS);

  // Scrolling alone leaves the tab order untouched, so a keyboard or
  // screen-reader user would be looking at the question without being in it.
  // `preventScroll` keeps focus from snapping past the smooth scroll.
  const control = card.querySelector<HTMLElement>("input, textarea, select");
  if (control) control.focus({ preventScroll: true });
}
```

- [ ] **Step 3: Add the renderer**

Append directly below, still above `refresh`:

```ts
function pendingItem(card: HTMLElement): HTMLLIElement {
  const item = document.createElement("li");
  const button = document.createElement("button");
  button.type = "button";
  button.className =
    "w-full text-left text-xs text-gray-700 rounded-md px-2 py-1.5 " +
    "line-clamp-2 hover:bg-amber-50 transition-colors";
  // textContent, never innerHTML: question text is authored data.
  button.textContent = questionLabel(card);
  button.addEventListener("click", () => revealCard(card));
  item.appendChild(button);
  return item;
}

function renderPending(form: HTMLFormElement): void {
  const panel = document.getElementById("pending-panel");
  const list = document.getElementById("pending-list");
  const countEl = document.getElementById("pending-count");
  const moreEl = document.getElementById("pending-more");
  if (!panel || !list || !countEl || !moreEl) return;

  const pending = pendingCards(form);
  panel.hidden = pending.length === 0;
  if (pending.length === 0) {
    list.replaceChildren();
    return;
  }

  countEl.textContent = String(pending.length);

  const shown = pending.slice(0, PENDING_LIMIT);
  list.replaceChildren(...shown.map(pendingItem));

  const remaining = pending.length - shown.length;
  moreEl.hidden = remaining === 0;
  moreEl.textContent = `y ${remaining} más`;
}
```

- [ ] **Step 4: Drive it from the existing refresh cycle**

Extend `refresh` so the panel recomputes wherever the progress bar already does:

```ts
function refresh(form: HTMLFormElement): void {
  applyVisibility(form);
  updateProgress();
  renderPending(form);
}
```

- [ ] **Step 5: Compile**

Run: `npm run build:js`
Expected: no output, exit 0.

- [ ] **Step 6: Build CSS**

The item and ring classes are string literals in `static/ts/survey_progress.ts`, which `main.css` lists as an `@source` — but they are new to the project and stay uncompiled until the stylesheet is rebuilt.

Run: `npm run build:css`

- [ ] **Step 7: Verify the classes actually compiled**

Run: `grep -c "line-clamp-2\|ring-amber-400" static/css/output.css`
Expected: a non-zero count. Zero means Tailwind did not see the source — check the `@source "../ts"` line in `static/css/main.css` before going further.

- [ ] **Step 8: Verify in the browser**

Run `python manage.py runserver`, open an assigned survey, and confirm:
1. With everything unanswered, the panel lists 6 questions and `y N más` below them.
2. Answering a listed question drops it from the list and the count falls.
3. Clicking an entry scrolls that card to centre, rings it for ~1.5 s, and puts focus on its first control.
4. A question hidden by `visible_when` never appears in the list.
5. Answering everything makes the panel disappear entirely.

This is a hand-off to the human reviewer — do not install a headless browser for it.

- [ ] **Step 9: Commit**

```bash
git add static/ts/survey_progress.ts static/js/ static/css/output.css
git commit -m "List the unanswered questions in the survey sidebar"
```

---

### Task 4: The next-pending button

**Files:**
- Modify: `static/ts/survey_progress.ts` (below `renderPending`, plus the `DOMContentLoaded` block at the end)

**Interfaces:**
- Consumes from Task 3: `pendingCards(form)`, `revealCard(card)`, `lastRevealed`. Consumes from Task 2: `#pending-next`.
- Produces: `goToNextPending(form: HTMLFormElement): void`.

- [ ] **Step 1: Add the next-pending walk**

Append below `renderPending`:

```ts
/** First pending question below the middle of the viewport, wrapping to the
 *  top when there is none — so repeated presses walk the form rather than
 *  returning to the same question. */
function goToNextPending(form: HTMLFormElement): void {
  const pending = pendingCards(form);
  const first = pending[0];
  if (!first) return;

  const cutoff = window.innerHeight / 2;
  const ahead = pending.find(
    (card) => card !== lastRevealed && card.getBoundingClientRect().top > cutoff
  );
  const wrapped = pending.find((card) => card !== lastRevealed);
  revealCard(ahead ?? wrapped ?? first);
}
```

`pending[0]` is bound to `first` and null-checked because `noUncheckedIndexedAccess` types it `HTMLElement | undefined`. The final `?? first` covers the one-pending-question case, where re-pulsing the same card is the correct answer — there is nowhere else to go.

- [ ] **Step 2: Wire the button**

In the `DOMContentLoaded` handler at the end of the file, after the existing `refresh(form);` call:

```ts
  const nextButton = document.getElementById("pending-next");
  if (nextButton) {
    nextButton.addEventListener("click", () => goToNextPending(form));
  }
```

- [ ] **Step 3: Compile**

Run: `npm run build:js`
Expected: no output, exit 0.

- [ ] **Step 4: Run the full test suite**

Run: `pytest -q`
Expected: all pass. The TypeScript has no test runner in this repo, which is why Step 5 is a human check.

- [ ] **Step 5: Verify in the browser**

With several questions unanswered — including at least one *above* the current scroll position — confirm:
1. `Ir a la siguiente ↓` advances to a different question on every press.
2. After the last pending question, the next press wraps to the top and reaches the ones above.
3. Clicking a list entry and then pressing the button advances past the clicked one rather than re-selecting it.
4. With exactly one question left, pressing the button re-rings that question rather than doing nothing.

- [ ] **Step 6: Commit**

```bash
git add static/ts/survey_progress.ts static/js/
git commit -m "Walk to the next unanswered question from the sidebar"
```

---

## Out of scope

- **Responsive / mobile layout.** `templates/surveys/survey_detail.html` lays the sidebar out as a fixed `w-96` flex column with no breakpoint, so it already overflows horizontally on a narrow viewport. The panel inherits that and is no worse than the rest of the sidebar. A partial fix here would be actively harmful: the column carries `order-last`, so simply stacking it would push the instructions, progress bar, save button *and* this panel below a 72-question form. This is deliberately left to a separate, focused responsive pass, and the panel's markup avoids fixed pixel widths so that pass can re-place it without a rewrite.
- **A JavaScript test runner.** None exists in this repo, and adding one is not part of this change.
- **`aria-live` on the panel.** It rebuilds on every keystroke; announcing each rebuild would make a screen reader chatter continuously. The focus move in `revealCard` is what carries the accessibility win.
