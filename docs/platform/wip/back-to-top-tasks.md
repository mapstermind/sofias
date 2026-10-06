# Back-to-top button — tasks

## What changes

**No live feature doc changes.** Route: `Doc: none`. The button is page chrome, like
the header. What a later reader needs from it goes in a template comment and in
`apps/core/CLAUDE.md` (Task 3). This file is deleted when `feat/back-to-top` merges.

**What it is.** Every page built on `templates/base_app.html` gets a round
"Volver arriba" button fixed near the bottom of the screen. A thin indigo ring
around it fills as the visitor scrolls, from 0% at the top to 100% at the bottom.
Clicking it scrolls to the top and moves keyboard focus to `<main>`.

**Why.** The company dashboard, the NOM-035 results page, the report and the
employee detail are long, and on a phone their stacked layout makes them much
longer. Getting back up to the header controls or the filters means a long
scroll.

**Decisions (settled in brainstorming, 2026-10-05):**

| Decision | Choice | Rationale |
|---|---|---|
| Visual approach | Round 44px button, white with a gray-300 border, an indigo-600 arrow, and an indigo-600 progress ring over a gray-200 track | Matches the report toolbar's white, bordered buttons. The ring is the one bold detail, and it tells you where you are on the report and employee detail |
| Which pages | Global: rendered by `base_app.html` inside `{% block back_to_top %}`. A page opts out by overriding the block with nothing | Short pages never reach the threshold, so being global costs them nothing |
| Survey form | Opted out (`templates/surveys/survey_detail.html`) | Respondents move forward through the survey, not back up. The phone bottom bar takes that corner, and the desktop sidebar is already the survey's navigation |
| When it appears | Once `scrollY` is at least one viewport height. It fades in and out on opacity (instant when the visitor prefers reduced motion) | Never shown on a page that doesn't scroll |
| Placement | `right: max(1rem, (100% − content width) / 2 − 3.75rem)`. In the gutter when there's room; otherwise 1rem from the right edge, in the corner over the content | No breakpoint. The button moves from gutter to corner continuously, whatever `container_width` the view passes |
| Content width | `--content-width: var(--container-<size>)` set inline, derived from the same `container_width` the header, `<main>` and footer use (`max-w-5xl` by default, `max-w-6xl` on results and survey pages) | One source of truth for width, so the gutter button always lines up with the column |
| Phones | Shown, bottom-right corner, bottom offset at least `env(safe-area-inset-bottom)` | Phones are where these pages are longest |
| Footer | When the footer scrolls into view, the button moves up by the footer's visible height | In corner mode it would otherwise cover the footer's "Desarrollado por PINIT" link |
| Click | `scrollTo({top: 0})`, smooth unless `prefers-reduced-motion: reduce`. Then `main.focus({preventScroll: true})`. `<main>` carries `tabindex="-1"` and `focus:outline-none` | Keyboard and screen-reader users aren't left at the bottom |
| Layer | `z-30` | Above the sticky report toolbar (`z-10`) and the roster filter bar (`z-20`); below the modals (`z-50`). `<dialog>` sits in the top layer anyway |
| Print | `print:hidden` | Hidden when the web report is printed from the browser. The PDF is rendered from `reports/base_report.html` and never includes `base_app` |
| No JavaScript | Rendered `invisible opacity-0`; only the script reveals it | A button that does nothing without JS is never shown |
| Copy | `aria-label` and `title` "Volver arriba" | Spanish UI |

**ADRs:** none affected.

---

# Back-to-top Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** A global, opt-out "Volver arriba" button with a scroll-progress ring on every `base_app.html` page except the survey form.

**Architecture:** A template partial `templates/_back_to_top.html`, included from a new `{% block back_to_top %}` in `base_app.html`. It holds the button markup and loads `static/js/back_to_top.js`. The script is compiled from `static/ts/back_to_top.ts`, which is DOM-in/value-out: three pure functions compute visibility, progress and footer lift, and one setup function wires them to `scroll`/`resize` through `requestAnimationFrame`. Placement is pure CSS.

**Tech Stack:** Django templates, Tailwind v4 (`npm run build:css`), TypeScript (`npm run build:js`), pytest + pytest-django.

**Spec:** the `## What changes` section above.

## Global Constraints

- All user-visible copy is Spanish: the label is exactly `Volver arriba`.
- Mobile-first: unprefixed classes describe the phone. The button must not cause horizontal scroll at 360 × 640.
- Tap target at least 44px (`size-11`).
- Every new Tailwind class must live in a scanned source (`templates/`, `static/ts/`). Run `npm run build:css` and `npm run build:js` and include `static/css/output.css` and `static/js/back_to_top.js` in the diff.
- No commits without the user's approval (CLAUDE.md gate 4). Each task ends at a green suite with an uncommitted diff.

## Review Focus

1. **The survey form must not show the button.** Its phone bottom bar occupies the corner. → Task 1 test `test_the_survey_form_opts_out`.
2. **A `max-w-6xl` page must place the button against the 6xl column, not the 5xl default**, or it lands inside the results page's content. → Task 1 test `test_the_gutter_follows_the_pages_content_width`.
3. **Without JavaScript the button is never shown or focusable.** → Task 1 test `test_the_button_starts_hidden` (asserts `invisible`).
4. **A page that can't scroll** (`scrollHeight == innerHeight`) must not divide by zero when computing progress. → Task 2 `scrollProgress` clamps, covered by the browser checklist (no JS runner).
5. **At the bottom of a phone page the button must not cover the footer link.** → Task 2 `footerLift`, covered by the browser checklist at 360px.

---

### Task 1: Server-rendered contract

**Files:**
- Create: `templates/_back_to_top.html`
- Modify: `templates/base_app.html` (`<main>` attributes; new block after the footer include)
- Modify: `templates/surveys/survey_detail.html` (empty `back_to_top` block)
- Test: `apps/core/tests/test_back_to_top.py`

**Interfaces:**
- Produces, for Task 2: a `<button data-back-to-top>` containing an SVG `<circle data-back-to-top-ring pathLength="100">`; `<main id="main" tabindex="-1">`; `<footer>` (already exists, located with `document.querySelector("footer")`); the script tag `js/back_to_top.js`.

- [x] **Step 1: Write the failing tests**

`apps/core/tests/test_back_to_top.py`:

```python
"""The back-to-top button every signed-in page carries.

The button's behaviour lives in static/ts/back_to_top.ts, which no test can
run. These pin the server-rendered half: that the button and its hooks are
there, that it starts hidden, that it follows the page's content width, and
that the survey form opts out.
"""

import pytest

pytestmark = pytest.mark.django_db

DASHBOARD_URL = "/tablero-empresa/"
RESULTS_URL = "/tablero-empresa/resultados/"


def _button(html):
    start = html.index("<button", html.index("data-back-to-top-root"))
    return html[start : html.index("</button>", start)]


def _root(html):
    start = html.index("data-back-to-top-root")
    return html[html.rindex("<div", 0, start) : html.index(">", start)]


@pytest.fixture
def exec_client(client, make_company, make_user_with_profile, bootstrap_groups):
    """A principal executive, who can open the dashboard and the results page."""
    company = make_company(name="Acme México")
    viewer = make_user_with_profile(email="exec@acme.mx", company=company)
    viewer.groups.add(bootstrap_groups["Principal Exec"])
    client.force_login(viewer)
    return client


def _get(client, url):
    response = client.get(url)
    assert response.status_code == 200, f"got {response.status_code}"
    return response.content.decode()


def test_the_dashboard_offers_a_way_back_to_the_top(exec_client):
    html = _get(exec_client, DASHBOARD_URL)
    button = _button(html)

    assert 'aria-label="Volver arriba"' in button
    assert "data-back-to-top-ring" in button
    assert "js/back_to_top.js" in html


def test_the_button_starts_hidden(exec_client):
    """Only the script reveals it, so a page without JS never shows a dead button."""
    button = _button(_get(exec_client, DASHBOARD_URL))

    assert "invisible" in button
    assert "opacity-0" in button


def test_the_button_is_left_out_of_print(exec_client):
    assert "print:hidden" in _root(_get(exec_client, DASHBOARD_URL))


def test_main_can_receive_focus_after_the_jump(exec_client):
    html = _get(exec_client, DASHBOARD_URL)
    main = html[html.index("<main") : html.index(">", html.index("<main"))]

    assert 'id="main"' in main
    assert 'tabindex="-1"' in main


def test_the_gutter_follows_the_pages_content_width(exec_client):
    """The default column is 5xl; the results page widens to 6xl."""
    assert "--container-5xl" in _root(_get(exec_client, DASHBOARD_URL))
    assert "--container-6xl" in _root(_get(exec_client, RESULTS_URL))


def test_the_survey_form_opts_out(client, survey_page_html):
    assert "data-back-to-top" not in survey_page_html
    assert "back_to_top.js" not in survey_page_html
```

For `survey_page_html`, reuse the fixture the survey page tests already use to render `survey_detail.html` for a respondent. Look in `apps/surveys/tests/test_survey_page_contract.py` (it renders that exact page) and either import its fixture through `conftest.py` or copy its setup into a local fixture named `survey_page_html` that returns the decoded response body. If `RESULTS_URL` needs data the bare company lacks (an assignment), mirror the setup in `apps/core/tests/test_results_views.py`.

- [x] **Step 2: Run the tests and confirm they fail**

Run: `pytest apps/core/tests/test_back_to_top.py -v`
Expected: FAIL. `ValueError: substring not found` on `data-back-to-top-root`; the opt-out test passes trivially.

- [x] **Step 3: Write the partial**

`templates/_back_to_top.html`:

```django
{% load static %}
{% comment %}
The "Volver arriba" button. base_app.html renders it inside
{% block back_to_top %}; a page opts out by overriding that block with nothing
(the survey form does, its phone bar owns this corner).

Placement is CSS only. `right` resolves against the viewport, so
max(1rem, (100% - content width) / 2 - 3.75rem) parks the button in the side
gutter when the gutter is wide enough and in the screen's corner otherwise.
--content-width comes from the same `container_width` header, main and footer
use; --container-<size> is Tailwind's own theme variable for that max-w-*.

It starts invisible and static/ts/back_to_top.ts reveals it past one viewport
of scroll, fills the ring (pathLength="100", so dashoffset is the remaining
percent), and lifts it above the footer when the footer is on screen.
{% endcomment %}
{% with width=container_width|default:"max-w-5xl" %}
<div data-back-to-top-root
     class="pointer-events-none fixed inset-x-0 bottom-0 z-30 print:hidden"
     style="--content-width: var(--container-{{ width|cut:'max-w-' }})">
  <button type="button" data-back-to-top
          aria-label="Volver arriba" title="Volver arriba"
          class="pointer-events-auto invisible absolute bottom-[max(1rem,env(safe-area-inset-bottom))] right-[max(1rem,calc((100%-var(--content-width))/2-3.75rem))] grid size-11 place-items-center rounded-full border border-gray-300 bg-white text-indigo-600 opacity-0 shadow-sm transition-[opacity,visibility,translate] duration-200 hover:bg-indigo-50 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-indigo-600 motion-reduce:transition-none">
    <svg class="absolute inset-0 size-full -rotate-90" viewBox="0 0 44 44" aria-hidden="true">
      <circle cx="22" cy="22" r="20" fill="none" class="stroke-gray-200" stroke-width="2.5"/>
      <circle cx="22" cy="22" r="20" fill="none" class="stroke-indigo-600" stroke-width="2.5"
              stroke-linecap="round" pathLength="100" stroke-dasharray="100" stroke-dashoffset="100"
              data-back-to-top-ring/>
    </svg>
    <svg class="relative size-5" viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="2"
         stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
      <path d="M10 16V4M4.5 9.5 10 4l5.5 5.5"/>
    </svg>
  </button>
</div>
<script src="{% static 'js/back_to_top.js' %}"></script>
{% endwith %}
```

(`container_width` is a context variable the view sets, and `{% include %}` passes the context through, so the partial sees the same value the header and footer do.)

- [x] **Step 4: Wire it into `base_app.html`**

Change the `<main>` line to:

```django
<main id="main" tabindex="-1" class="flex-1 mx-auto w-full {{ container_width|default:"max-w-5xl" }} px-4 py-10 focus:outline-none">
```

and after `{% include "_footer.html" %}`, before `{% endblock %}`:

```django
{% block back_to_top %}{% include "_back_to_top.html" %}{% endblock %}
```

- [x] **Step 5: Opt the survey form out**

In `templates/surveys/survey_detail.html`, directly after the `header_nav` block:

```django
{# The phone bottom bar owns the corner, and respondents move forward, not up. #}
{% block back_to_top %}{% endblock %}
```

- [x] **Step 6: Run the tests and confirm they pass**

Run: `pytest apps/core/tests/test_back_to_top.py -v`
Expected: PASS (6 tests).

- [x] **Step 7: Run the full suite**

Run: `pytest`
Expected: all green, including `apps/core/tests/test_responsive.py` and `apps/core/tests/test_app_header.py`. Stop here with an uncommitted diff.

---

### Task 2: Behaviour module and asset build

**Files:**
- Create: `static/ts/back_to_top.ts`
- Generated: `static/js/back_to_top.js`, `static/css/output.css`

**Interfaces:**
- Consumes: from Task 1, `[data-back-to-top]`, `[data-back-to-top-ring]`, `main#main`, `footer`.
- Produces: `shouldShow(scrollY: number, viewportHeight: number): boolean`, `scrollProgress(scrollY: number, scrollHeight: number, viewportHeight: number): number` (0–100), `footerLift(viewportHeight: number, footerTop: number): number` (px ≥ 0), `setupBackToTop(): void`.

- [x] **Step 1: Write the module**

`static/ts/back_to_top.ts`:

```ts
// The "Volver arriba" button rendered by templates/_back_to_top.html. The
// pure functions below take numbers and return numbers so they stay
// inspectable without a test runner; setupBackToTop only wires them to the DOM.

const HIDDEN_CLASSES = ["invisible", "opacity-0"];

function shouldShow(scrollY: number, viewportHeight: number): boolean {
  return scrollY >= viewportHeight;
}

// Percent of the scrollable distance covered, 0–100. A page that cannot
// scroll reports 0 rather than dividing by zero.
function scrollProgress(scrollY: number, scrollHeight: number, viewportHeight: number): number {
  const scrollable = scrollHeight - viewportHeight;
  if (scrollable <= 0) return 0;
  return Math.min(100, Math.max(0, (scrollY / scrollable) * 100));
}

// How far to raise the button so it clears a footer that has scrolled into view.
function footerLift(viewportHeight: number, footerTop: number): number {
  return Math.max(0, viewportHeight - footerTop);
}

function setupBackToTop(): void {
  const button = document.querySelector<HTMLButtonElement>("[data-back-to-top]");
  const ring = button?.querySelector<SVGCircleElement>("[data-back-to-top-ring]");
  const main = document.querySelector<HTMLElement>("main");
  const footer = document.querySelector<HTMLElement>("footer");
  if (!button || !ring || !main) return;

  const control = button;
  const progressRing = ring;
  const target = main;
  let queued = false;

  function update(): void {
    queued = false;
    const viewportHeight = window.innerHeight;
    const scrollY = window.scrollY;
    const visible = shouldShow(scrollY, viewportHeight);

    HIDDEN_CLASSES.forEach((name) => control.classList.toggle(name, !visible));
    const progress = scrollProgress(scrollY, document.documentElement.scrollHeight, viewportHeight);
    progressRing.style.strokeDashoffset = String(100 - progress);
    const lift = footer ? footerLift(viewportHeight, footer.getBoundingClientRect().top) : 0;
    control.style.translate = lift ? `0 -${lift}px` : "";
  }

  function schedule(): void {
    if (queued) return;
    queued = true;
    window.requestAnimationFrame(update);
  }

  window.addEventListener("scroll", schedule, { passive: true });
  window.addEventListener("resize", schedule);
  update();

  control.addEventListener("click", () => {
    const reduce = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    window.scrollTo({ top: 0, behavior: reduce ? "auto" : "smooth" });
    target.focus({ preventScroll: true });
  });
}

document.addEventListener("DOMContentLoaded", setupBackToTop);
```

- [x] **Step 2: Build the assets**

Run: `npm run build:js && npm run build:css`
Expected: `static/js/back_to_top.js` created, with no `export` statement (it loads as a classic script). Then confirm the arbitrary classes compiled:

Run: `grep -c "safe-area-inset-bottom\|--content-width" static/css/output.css`
Expected: at least 2.

- [x] **Step 3: Run the full suite**

Run: `ruff check . && pytest`
Expected: green. Stop with an uncommitted diff.

- [ ] **Step 4: Hand the reviewer the browser checklist** (no JS runner — CLAUDE.md)

1. Dashboard, results page, report, employee detail at 1440px: the button appears after one screen of scroll, sits in the right gutter beside the column, and the ring fills to full at the bottom.
2. Results page (`6xl`) at 1280px: the button falls back to the corner and doesn't overlap the column's cards in an awkward way.
3. 360 × 640 (DevTools): bottom-right corner, no horizontal scroll. At the very bottom it sits above the footer and the "Desarrollado por PINIT" link is tappable.
4. Click with the keyboard (Tab to it, Enter): page scrolls to the top, and the next Tab lands on the first control inside the content.
5. OS "reduce motion" on: the jump is instant and there's no fade.
6. A short page (e.g. "¿Qué es SOFIA?"): no button ever.
7. A survey page: no button; the phone bottom bar is unchanged.
8. Report page → browser print preview: no button.
9. Roster filter dialog and dashboard Cochran modal open above the button.

---

### Task 3: Documentation

**Files:**
- Modify: `apps/core/CLAUDE.md`

- [x] **Step 1: Add a "Page chrome" section** after the "Web views" section:

```markdown
## Page chrome: back-to-top button

`templates/base_app.html` renders `templates/_back_to_top.html` inside
`{% block back_to_top %}` on every signed-in page: a "Volver arriba" button whose
ring shows scroll progress. It is placed in the side gutter beside the
`container_width` column when there is room and in the bottom-right corner
otherwise, appears after one viewport of scroll, lifts above the footer, and is
hidden in print. A page opts out by overriding the block with nothing — the
survey form does. Behaviour is `static/ts/back_to_top.ts` (**run `npm run
build:js` and commit `static/js/back_to_top.js` when touching it**);
`apps/core/tests/test_back_to_top.py` pins the server-rendered half. Clicking it
focuses `<main id="main" tabindex="-1">`, so keep those attributes.
```

- [x] **Step 2: Final check**

Run: `ruff check . && pytest`
Expected: green. Hand back the uncommitted diff with the proposed commit message:

```
feat(core): add a back-to-top button with a scroll-progress ring

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>
```

This file (`docs/platform/wip/back-to-top-tasks.md`) is deleted in the cleanup commit after the PR merges.
