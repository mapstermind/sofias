# Responsive layout

## Status

Current — implemented across `templates/`, guarded by
`apps/core/tests/test_responsive.py`.

## What this does

Every page in SOFIA-S renders on a phone. At any viewport 360 CSS pixels wide or
wider the page has no horizontal scrollbar, no control is clipped by the edge of
the screen, and nothing a visitor needs is placed out of reach.

That is the whole contract. It says what must be true, not how a page gets
there: a two-column layout may stack, a sidebar may collapse into a bar at the
bottom of the screen, a panel may become a sheet. Each page picks the shape that
suits it and is judged only on the result.

Layout is written mobile-first. Unprefixed Tailwind classes describe the phone,
and a breakpoint prefix adds the wider arrangement on top — `flex-col
lg:flex-row`, never `flex-row` with a narrow-screen override bolted on
afterwards. The phone case is therefore the default a new page falls into when
its author thinks about nothing, which is the point.

Fitting the screen is necessary and not sufficient. On the survey form, where a
respondent taps between 61 and 87 answers in a row, **every answer option is a
full-width row at phone width and the entire row is the hit target** — not the
radio button inside it. A row is at least 44px tall, and the padding that gets
it there is what the finger lands on.

## Why we're building it

Roughly half of the people who answer a survey do so on a phone. They are
employees who received a link, will answer 61 to 87 questions across one or two
sittings, and will never open the platform again — so there is no habit to form,
no second chance at a first impression, and no tolerance for friction that a
daily user would learn to absorb. A page that overflows horizontally is, for
them, the product. So is a 16px radio button they have to hit 87 times.

The administrators on the other side of the platform work mostly on a laptop.
Their dashboards are card-first and read comfortably at any width. The survey
form is where the constraint actually bites, and it is the page this contract is
written for.

## Scope

**In scope:**

- A stated minimum supported viewport of **360 × 640 CSS pixels**, and the
  no-horizontal-scroll contract above, applied to every page the platform
  serves.
- Mobile-first authoring as the house convention: base classes describe the
  phone, breakpoint prefixes widen it.
- A test that fails the suite when a template declares a fixed width that cannot
  fit the phone content box (see **Enforcement**).
- **Tappable answer controls.** Every option of every question type in
  `templates/surveys/_question.html` is a full-width row at phone width, at least
  44px tall, with the whole row clickable. This applies to `likert`, `boolean`,
  `rating`, `single_choice` and `multiple_choice` alike, so a question type added
  later inherits one pattern rather than inventing a sixth.

**Out of scope:**

- **Touch-target sizing outside the survey form.** The roster filter bar, the
  header controls and the dashboard cards are sized for reading rather than for a
  thumb. An administrator reads those on a laptop and meets them rarely; a
  respondent meets an answer control 87 times.
- **Tablet-specific layouts.** There are two cases — phone and desktop — and the
  breakpoint between them is chosen per page. Nothing is designed for the middle.
- **Per-page layout prescriptions.** This doc does not say when to use a bottom
  bar over a sheet over stacking. A page's own feature doc describes the shape it
  chose.
- **Offline support, installability, and push.** SOFIA-S is not a progressive web
  app and is not planned as one: respondents answer once from an office network,
  never install anything, and receive no notifications, which leaves a service
  worker with nothing to do but cache authenticated pages it should not cache.
- **Landscape phone and viewports narrower than 360px.** Neither is designed for;
  neither is deliberately broken.

## Enforcement

No test can see a rendered page. The suite has no browser and no JavaScript
runner, so a page that overflows at 360px passes every check in the repository —
the same blind spot [`localization.md`](./localization.md) names for English copy
left in a template. What follows is a floor, not a guarantee.

Three modules hold what can be held:
[`apps/core/tests/test_responsive.py`](../../apps/core/tests/test_responsive.py)
is the width guard below;
[`apps/surveys/tests/test_survey_page_contract.py`](../../apps/surveys/tests/test_survey_page_contract.py)
pins the element ids and data attributes `static/ts/survey_progress.ts` resolves,
which a layout change would otherwise break in silence; and
[`apps/core/tests/test_app_header.py`](../../apps/core/tests/test_app_header.py)
holds the header, which carries the product's only logout control.

**The automated part.** A pytest check scans `templates/` and fails on a width
class that is both unprefixed and at least as wide as the phone content box
(~328px — 360px less the page shell's `px-4` on each side). `w-96` on a flex
child that also carries `shrink-0` is the shape of the failure: the element
refuses to shrink, so the column beside it is squeezed toward zero and the page
overflows. A breakpoint-prefixed class is exempt, because `lg:w-96` does not
apply at 360px. So are `max-w-*`, `w-full`, and viewport-relative widths, none of
which prevent shrinking.

**What the check cannot see.** It reads one class at a time, so it is blind to
everything that emerges from several of them together:

- Widths that overflow only when repeated. Five options each holding a 72px
  minimum are harmless one at a time and need 392px as a row.
- Whether a wrapped row still reads correctly. A five-point Siempre→Nunca scale
  laid out horizontally fits the viewport by wrapping onto two lines, and stops
  being a scale.
- Stacking order. A column that stacks in the wrong sequence overflows nothing
  and buries the thing the visitor came for.
- Whether a sticky or fixed element leaves enough screen behind it.
- Whether a control is comfortable to tap. Rendered height comes from padding,
  line height and the preflight reset together; no scan of class names computes
  it. The 44px rule is verified by a finger, not by the suite.

**The human part.** Those are found by a person resizing a browser to 360px and
using the page, before the change lands. A change that touches layout names in
its pull request what to open and what to click.

## Key decisions

- Decision: the contract is "no horizontal scroll at ≥360px" plus a tappable-row
  rule for survey answer controls, not a general mobile UX standard.
  Reason: the overflow rule is one bright line a reviewer can check in seconds.
  The answer-control rule is the second line because answering a survey on a
  phone is the reason this work exists — a page that fits the screen and cannot
  be tapped accurately has met the letter of the contract and failed its purpose.
  Neither rule prescribes a page's design beyond that.

- Decision: answer options are stacked full-width rows on a phone, accepting a
  much longer page.
  Reason: laid out horizontally, a five-point scale wraps mid-scale at phone
  width — it misreads as two scales and leaves five 72px targets. Stacking
  turns 64 likert questions into roughly five 44px rows each, so the form runs
  substantially taller — the sticky bottom bar, the progress count and the
  pendientes panel are what keep that navigable, which is why they are collapsed
  rather than dropped. Height costs scrolling; a mis-tap costs a wrong answer in
  a psychosocial risk assessment.

- Decision: stacked likert rows carry their labels and drop the horizontal scale
  reading.
  Reason: a five-point Siempre→Nunca scale conveys its order through sequence and
  through the words themselves. A vertical list keeps both. Laid out
  horizontally at phone width the row wraps onto two lines, which keeps neither.

- Decision: 360px is the floor, not 390px or 320px.
  Reason: 360px is the narrowest width in common use among current Android
  handsets; designing to it covers the iPhone widths above it, and the handful of
  devices below it are not worth the constraint.

- Decision: the guard test flags only widths that cannot fit, rather than every
  fixed width.
  Reason: most fixed widths in the templates are inputs and avatars that fit a
  phone with room to spare. A rule broad enough to flag them needs an allowlist
  longer than its findings, which turns the test into a formality nobody reads.
  A narrow rule that produces no false positives keeps its authority.

- Decision: SOFIA-S stays a plain responsive web application rather than becoming
  a progressive web app.
  Reason: installation and push are both explicitly unwanted, which leaves
  offline as the only remaining capability a service worker would add — and
  respondents answer from an office network. An offline survey would mean a
  client-side write queue, the least testable possible code in a repository with
  no JavaScript test runner, fighting a 30-minute server-side session timeout.

- Decision: mobile-first authoring, with breakpoint prefixes adding the wide
  layout.
  Reason: the unprefixed class is what an author writes without deciding
  anything, so the default has to be the case that is easiest to get wrong.

## Open questions

None.

## Linked ADRs

None. The decisions above constrain presentation only — no data model, no
authorization boundary, and no NOM-035 scoring behavior changes — so none of them
rises to an architectural decision record.
