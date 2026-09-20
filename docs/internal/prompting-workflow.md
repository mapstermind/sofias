# Development Workflow Guide

This is how a change gets from request to merged — every change, from a typo to
a new feature. The difference between them is how many of the eight steps apply,
and the agent decides that in Step 0 rather than you deciding it up front.

Two things shape everything below:

**It is documentation-first.** For anything that changes what the platform does,
the feature doc in `docs/platform/` is written before the code and is the source
of truth for implementation. Agent sessions are oriented by `CLAUDE.md` and that
doc, not by verbal instruction at session start.

**It is continuous between gates.** The agent runs from one gate to the next
without asking permission to proceed. It announces what it did at each boundary
and keeps moving. Reviewing means reading what it posts and interrupting, not
being asked.

---

## Step 0 — The route

Every request starts the same way, whatever its size. The agent reads it, works
out how much process it needs, and posts a route block:

```
Route
  Change   Collect sexo y fecha de nacimiento when an employee activates
  Doc      docs/platform/auth-and-onboarding.md — extend
  Path     branch feat/employee-demographics → PR
  Plan     docs/platform/wip/employee-demographics-tasks.md
  Why      New fields on the activation form, inside that doc's existing scope.
           Carries a migration, so it goes through a PR.
```

Then it waits. Confirm it, correct a line, or say **"skip the process, just make
the change"** and it drops to the shortest route. This is the one stop that
happens on every request — including the small ones, so you always get to say
where a change lands before it lands there.

A one-line route is normal:

```
Route
  Change   Fix the typo in the OTP resend message
  Doc      none — copy fix
  Path     direct to main
  Plan     none
```

### Doc — none, extend, or new

The files in `docs/platform/` are the list of documented features. The agent
reads the one that matches before choosing.

| Doc | When | What it means |
|---|---|---|
| **none** | Bug fix restoring behavior the doc already describes · typo, copy or styling fix · dependency bump · asset rebuild · test-only change · refactor with no behavior change · edit to docs, comments or `CLAUDE.md` · answering a question | Steps 1–3 are skipped. Go build. |
| **extend** | A `docs/platform/<feature>.md` covers the thing being changed, and the change fits inside its declared `Scope` | Step 1 writes a change brief; that doc is rewritten as the last task of the plan. |
| **new** | No feature doc covers it, and it would need a `Scope` section of its own | Step 1 drafts `docs/platform/<feature>.md` from the template. **No code until you sign off on it.** |

When extend-or-new is genuinely ambiguous, the route names the candidate doc and
the agent asks — it does not guess. When the route says *extend* and you never
used a word like "refactor", "expand" or "change how X works", read that line
carefully before confirming: it is the line that keeps a genuinely new capability
from being quietly buried inside someone else's feature doc.

### Path — straight to main, or a branch and a PR

**Direct to main** when *all* of these hold: no feature doc is written or
rewritten, no migration, no new dependency, no change to authorization or the
NOM-035 scoring constants, and the whole thing is one commit's worth of work with
the suite green afterwards.

**Branch `feat/<name>` → PR** when *any* of these hold:

- a feature doc is created or rewritten
- there is a migration
- it touches authorization (permissions, groups, roles) or `apps/nom035` scoring constants
- it adds or bumps a dependency
- the plan runs to more than a couple of tasks
- you want to read it before it lands

The bias is deliberate: anything that would be awkward to unwind on `main` gets a
branch, and everything else does not need the ceremony. "Doc: none" does not
force "Path: direct to main" — a large behavior-preserving refactor needs no doc
and still belongs on a branch.

### Plan — with the branch

If there is a branch, there is a plan at
`docs/platform/wip/<feature>-tasks.md`. Direct-to-main work does not get one;
the change is small enough to be its own plan.

---

## The four gates

Four things stop the agent. Nothing else should.

1. **The route** (Step 0) — always, before any work.
2. **The documentation gate** (Step 1) — for a new feature, no code exists until the doc does and you have signed off on it.
3. **An unresolved decision** (Step 4) — implementation hits something the feature doc or change brief does not settle. The agent describes the options and its recommendation, and waits. It does not decide unilaterally.
4. **Shipping** (Step 6) — the PR is drafted, or the commit to `main` is staged, and then it waits for your word.

Between them the agent moves on its own. The plan, verification findings, a
proposed `CLAUDE.md` edit — all of it lands in its reply as it starts on the next
thing. If the plan is in the wrong order or a task is out of scope, interrupt;
you do not have to wait to be asked.

---

## The steps

| Step | Runs when | Skill | Output |
|---|---|---|---|
| 0. Route | always | — | The route block — **you confirm here** |
| 1. Document | Doc is extend or new | `superpowers:brainstorming` | The feature doc, or the change brief — **you sign off here (new only)** |
| 2. Plan | there is a branch | `superpowers:writing-plans` | `docs/platform/wip/<feature>-tasks.md` |
| 3. Branch | Path is a branch | — | `feat/<name>` off `main`, carrying the uncommitted docs |
| 4. Build | always | `superpowers:test-driven-development`, `subagent-driven-development` | Code, tests, **and the rewritten feature doc** |
| 5. Verify | always | `superpowers:verification-before-completion`, `requesting-code-review`, `receiving-code-review` | Findings, reported and acted on |
| 6. Ship | always | `superpowers:finishing-a-development-branch` | A drafted PR, or a staged commit — **you confirm here** |
| 7. Land | Path was a branch | — | `wip/` emptied, `CLAUDE.md` current |

### Step 1 — Document

**Doc: new.** Copy `docs/platform/feature-template.md` to
`docs/platform/<feature>.md` — **never edit the template itself**. Fill in what
the feature does, why, what is in and out of scope, and anything already decided.
Open questions stay open; brainstorming resolves them. The draft lives in
`docs/platform/` from the start — there is no separate drafts location, the file
is just incomplete until this step finishes.

You can hand the agent a draft or start from a blank page with it. The gate is on
implementation, not on the session: no code before the doc exists and you have
signed off, but you do not have to type the first version yourself.

The finished doc names affected modules, routes, components, schema changes and
API contracts where they are known, closes every open question, and is written in
present tense as if the feature already shipped. It should be specific enough
that someone could implement from it without asking what was meant.

**Doc: extend.** The live feature doc stays untouched — it describes how the
platform behaves today and must keep doing that until the new behavior ships.
Instead, the brief goes at the top of `docs/platform/wip/<feature>-tasks.md`,
under a `## What changes` heading: the target behavior, why, **which sections of
the live doc it makes wrong** (name them — this list becomes the last task of the
plan), and whether it touches a decision recorded in `docs/adr/`. The task list
is appended below it in Step 2. One file, written once, deleted at Step 7.

### Step 2 — Plan

An ordered checkbox list — one `- [ ]` per task, grouped under numbered
headings. Each task says what needs doing, the files affected, what it depends
on, and carries a flag if it holds a decision or meaningful risk. Each is
structured for TDD: failing test first, then implement.

**The last task is always the documentation task**, and it ships in the same diff
as the code so it gets reviewed alongside it:

- **Doc was new:** trim `docs/platform/<feature>.md` to its post-ship form — drop the open-questions section and the planning scaffolding, convert *will be built* into *is*.
- **Doc was extend:** rewrite `docs/platform/<feature>.md` to describe the new behavior in present tense, with **no** migration commentary — no "replaces the old X", no before/after table. A reader must not be able to tell a previous implementation existed. List any new ADR under `## Linked ADRs`.

**The ADR check belongs here**, before the first task. Write an ADR when the
decision affects more than this one feature, would not be obvious from the code,
or overrides an existing ADR; skip it when the decisions are implementation
details scoped to this feature.

A change that reverses a recorded decision is the common case. That ADR is not
edited to describe the new approach — its whole job is to preserve why the old
one was chosen. Instead a **new** ADR is written from
`docs/adr/adr-0000-template.md`; it is the one place in the repo where
before/after commentary belongs. The superseded ADR gets its `Status:` line set
to `Superseded by ADR-000X` — that line only, the rest is frozen. Everywhere
outside `docs/adr/` and `docs/archive/`, the history stays out.

### Step 3 — Branch

Steps 1 and 2 have left the feature doc and the plan uncommitted in the working
tree. `git switch -c feat/<name>` carries them onto the branch. Nothing should be
left behind on `main`.

### Step 4 — Build

**Skills:** `superpowers:test-driven-development`,
`superpowers:subagent-driven-development`, `superpowers:systematic-debugging`,
`superpowers:dispatching-parallel-agents`

The agent works the list in order, failing test first, checking off each `- [ ]`.
It runs through tasks on its own — the thing that stops it is a decision the
source document does not resolve, not the end of a task.

Parallel agents are worth it only for tasks that share no files and have no
ordering dependency. Coordination overhead eats the gain otherwise.

When something breaks, it switches to systematic debugging rather than iterating
blindly: root cause first, then the fix.

### Step 5 — Verify

Verification checks that every task is done, the suite passes, nothing in the
source document was left unimplemented, no debug code or placeholders remain,
and — where a feature doc was in play — that it describes the shipped behavior in
present tense with no leftover open questions and no migration commentary.

The code review then covers correctness against the feature doc *as rewritten in
this branch* — that rewrite is part of the diff and is reviewed as such — plus
code quality, test coverage and missed edge cases. Each finding is verified as
genuine before being acted on; one that conflicts with a decision in the feature
doc gets flagged and explained, not implemented blindly.

Both land in your reply as the agent moves into acting on them:

- **Must fix:** it is already fixing them.
- **Should fix:** interrupt if you disagree with its call.
- **Follow-up work:** record it in `docs/internal/open-findings.md` or a GitHub issue before moving on. Do not lose it.

Anything touching `templates/` or `static/` gets its asset rebuild here —
`npm run build:css` and/or `npm run build:js`, with the regenerated output
committed. An uncompiled Tailwind class fails no test.

### Step 6 — Ship

**Branch:** the PR description is drafted and the agent waits. Read it before
confirming — it should be accurate enough that someone reviewing without context
understands what changed and why.

**Direct to main:** the commit is staged with its message and the agent waits.
Confirm, and it commits and pushes.

Either way this is the last gate before the work leaves your machine.

### Step 7 — Land

Only for branch work, after the PR merges:

1. Switch back to `main` and pull.
2. Delete the merged branch, locally and on the remote.
3. Empty `docs/platform/wip/` — only `README.md` remains. Anything else there is scaffolding an earlier branch left behind; the agent names it rather than silently deleting it.
4. List any temporary files, debug scripts or implementation notes that should not live in the repo long-term.
5. If shipping this made `CLAUDE.md` or `docs/platform/overview.md` wrong — new dependencies, new constraints, structural changes — fix them and show the diff.

Leave `docs/platform/<feature>.md` alone. It was rewritten in Step 4 and reviewed
in Step 5.

One thing is yours afterwards: open the feature doc on `main` and read it as a
new engineer would. Does it describe what shipped, in present tense? Are the open
questions gone? Is there any trace of the old behavior — "replaces", "formerly",
"used to", a before/after table? Are the linked ADRs listed? If any answer is
wrong, the Step 2 documentation task was written poorly. Fix it now and take it
as a signal for the next plan.

---

## Driving it

Small work needs no prompt at all: describe the change, read the route block,
confirm it. The agent runs Steps 4–6 and stops at the commit.

Anything with a feature doc takes two prompts — one per side of the
documentation gate.

**Prompt 1 — shape it**

```
[Describe what you want.]

Post your route first — doc, path, plan — and wait for me to confirm it.

Then, if a doc is involved: use /brainstorming. Read CLAUDE.md and every doc in
docs/platform/ relevant to this. Work with me iteratively — ask questions,
surface edge cases I have not considered, and name decisions that have to be
made before implementation.

Write the result where the route says it goes:
- New feature → docs/platform/[feature].md, overwriting the draft in place.
  Concrete and complete, present tense as if already shipped: what it does and
  how, affected files/modules/routes by name, schema or API changes, key
  decisions with brief rationale, explicit scope boundaries.
- Extending a doc → the `## What changes` header of
  docs/platform/wip/[feature]-tasks.md, fully specifying the target behavior and
  listing by section everything in docs/platform/[feature].md that will need
  rewriting once this ships. Do NOT edit the live feature doc in this session —
  it must keep describing current behavior until the new behavior actually ships.

Do not leave open questions in the final document. If something cannot be
resolved here, flag it so I can decide whether to block on it.

Flag it if this contradicts a decision recorded in docs/adr/.
```

**Prompt 2 — build it**

```
Read docs/platform/[feature].md [and docs/platform/wip/[feature]-tasks.md] plus
any linked ADRs. That is the source of truth — do not restate it as a separate spec.

Run this through to shipping without stopping for approval between steps.
Announce each boundary in your reply and keep moving; I will interrupt if I want
something changed.

1. ADR check, then /writing-plans → docs/platform/wip/[feature]-tasks.md as a
   checkbox list. Last task is always the documentation update. Summarize the
   plan in your reply, then continue.
2. Cut the branch if the route called for one, carrying the uncommitted docs
   along. Show me git status first; nothing left behind on main.
3. /subagent-driven-development and /test-driven-development. Work the plan in
   order, checking off as you go. Parallel agents only for tasks that share no
   files and have no ordering dependency.
4. /verification-before-completion, then /requesting-code-review, then
   /receiving-code-review on the findings you judge genuine. Rebuild the CSS/JS
   if templates or static/ were touched. Report what you find and carry on.
5. /finishing-a-development-branch. Confirm tests pass, confirm the feature doc
   rewrite is in the diff, and draft the PR — or stage the commit, if the route
   was direct to main.

Two things stop you:
- A decision the source document does not resolve. Describe the options and your
  recommendation, and wait. Do not decide unilaterally.
- Shipping. Draft it, then wait for my confirmation.
```

After the merge, Step 7 is a sentence: *"The [feature] branch merged — run the
landing step."*

---

## Where things live

```
docs/
├── adr/                        # Architectural decisions. Never edited without approval.
├── platform/                   # What the app does and how — the source of truth
│   ├── overview.md
│   ├── feature-template.md     # Copy this to start a feature doc — never edit it
│   ├── <feature>.md            # Survives the branch
│   └── wip/
│       └── <feature>-tasks.md  # Change brief + plan. Deleted at Step 7.
├── internal/                   # The human side: this guide, operator guides, meeting notes
└── archive/                    # Retired feature docs
```

`docs/internal/` is written for the team rather than describing the running
system. The agent does not read most of it in a normal session, but it is not
off-limits: `CLAUDE.md` points here for the full process, and
`Guias de Referencia.md` is the authoritative NOM-035 scoring reference it must
consult.

Before starting anything, check that `docs/platform/wip/` holds nothing but its
README. Anything else is scaffolding a previous branch left behind — a stale
checklist describing steps that already happened. Clear it before adding more.

---

## Rules

1. **Route first.** Doc, path, plan — posted and confirmed before any work, on every request.
2. **The feature doc is the source of truth.** If implementation diverges from it, update the doc; don't let them drift silently.
3. **No implementation without a complete source document.** Open questions get resolved first.
4. **`docs/platform/` describes only the present.** There is no ledger of how a feature used to behave. When that history is worth keeping it goes in an ADR, and the feature doc links to it.
5. **ADRs before implementation, not after.** A superseding ADR is written fresh; the superseded one has only its `Status:` line touched.
6. **The doc rewrite ships with the code.** Last task in the plan, part of the reviewed diff — never a post-merge chore.
7. **The agent checkpoints on decisions, not on tasks.** Let it run. Stop it when it hits something the doc doesn't resolve.
8. **Four gates, and only four.** The route, the documentation gate, an unresolved decision, and shipping. Everything between runs continuously.
9. **A branch is not finished until `wip/` is empty again.**
10. **Archive, don't delete feature docs.** When a feature is retired, move its doc to `docs/archive/` with a note of when and why.
