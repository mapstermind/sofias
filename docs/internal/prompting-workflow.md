# Development Workflow Guide

This document describes the end-to-end process for developing a feature, from initial idea to post-merge cleanup. It applies to all engineers on the team and is written to be followed in order.

The workflow is documentation-first: you write before you code. The feature document is the source of truth for implementation. Agent sessions are oriented by `CLAUDE.md` and the feature doc — not by verbal instruction at session start.

It is also **continuous**. The agent runs from one gate to the next without asking permission to proceed; it announces what it did at each boundary and keeps moving. Reviewing means reading what it posts and interrupting, not being asked.

---

## Directory Reference

```
SOFIAS/
├── .claude/
│   └── CLAUDE.md                        # Agent orientation, read automatically by Claude Code
├── docs/
│   ├── adr/                             # Architectural decision records
│   ├── platform/                        # Feature docs and system-level docs (what the app does and how)
│   │   ├── overview.md
│   │   ├── database.md
│   │   ├── feature-template.md          # Copy this to start a feature doc — never edit it
│   │   ├── [feature-name].md            # The feature doc — source of truth, survives the branch
│   │   └── wip/                         # Disposable scaffolding, emptied at cleanup (Step 10)
│   │       ├── [feature-name]-change.md #   Change brief for a refactor (Step 1B)
│   │       └── [feature-name]-tasks.md  #   Derived implementation plan (Step 4)
│   ├── internal/                        # The human side of the process
│   │   ├── prompting-workflow.md
│   │   ├── user-guides/
│   │   └── meetings/
│   └── archive/                         # Retired feature docs and deprecated content
└── README.md
```

`docs/internal/` holds guides written for the team rather than descriptions of the running system. The agent does not read most of it in a normal session, but it is not off-limits: `CLAUDE.md` points here for the full process, and `Guias de Referencia.md` is the authoritative NOM-035 scoring reference the agent must consult.

---

## Before You Start

Read `CLAUDE.md` and the relevant docs in `docs/platform/` before starting any feature. If something in those documents is already wrong or outdated, fix it first. Starting a feature on top of stale context compounds the problem.

Check that `docs/platform/wip/` holds nothing but its README. Anything else there is scaffolding a previous branch left behind — clear it before adding more.

---

## How This Runs

Ten steps, three phases, three prompts. You paste one prompt per phase; the agent carries the whole phase.

| Phase | Steps | What it produces | Ends when |
|---|---|---|---|
| **A · Shape the work** | 0–2 | The document that says what will be built | You sign off on it |
| **B · Build it** | 3–9 | The branch, the code, the tests, the rewritten feature doc, a drafted PR | You confirm the PR |
| **C · Clean up** | 10 | An empty `wip/`, a current `CLAUDE.md` | — |

### The four gates

Everything else runs without asking. These four stop the agent, and nothing else should:

1. **The documentation gate.** No code for an undocumented feature. The agent stops at triage branch C and offers to draft the doc; implementation starts once the doc exists and you have signed off.
2. **The intent question.** On triage branch B, when you never said "refactor" or "expand", the agent asks one question to confirm you mean to change an existing feature rather than add a new one.
3. **An unresolved decision.** When implementation hits something the source document does not settle, the agent describes the options and its recommendation, and waits. It does not decide unilaterally.
4. **Opening the PR.** Drafted automatically, opened only on your confirmation.

Between them the agent moves on its own. Anything it produces along the way — the plan, verification findings, a proposed `CLAUDE.md` edit — lands in its reply as it starts on the next thing. If the plan is in the wrong order or a task is out of scope, interrupt; you do not have to wait to be asked.

---

## Phase A — Shape the Work

### Step 0 — Triage the Request

**Who:** Agent, at the top of the session (you can do it yourself before opening one)

Not every request is a feature. Before anything else, decide which of three branches the work falls into. `CLAUDE.md` carries this rule in full so the agent applies it without being asked; this section is the same rule for the human side.

| Branch | When | What happens |
|---|---|---|
| **A · No doc needed** | Bug fix restoring documented behavior, typo or copy fix, dependency bump, asset rebuild, test-only change, behavior-preserving refactor, doc edit — or a question | Skip this workflow. Make the change. |
| **B · Change to a documented feature** | A `docs/platform/<feature>.md` already covers the thing being changed | Refactor track: Steps 1B → 10 |
| **C · New, undocumented feature** | No feature doc covers it | New-feature track: Steps 1C → 10 |

**Choosing between B and C.** Does the change fit inside the existing doc's declared `Scope`? Then it is B — extend that doc. Would it need a `Scope` section of its own? Then it is C — new doc. When it is genuinely ambiguous, the agent should ask one question naming the candidate doc rather than guessing.

**When the agent lands on C, it stops before writing any code** and offers to draft the feature doc with you. That gate is on implementation, not on the session — you do not have to leave and come back with a draft. If it has misread the request, say "skip triage" or "this is a chore" and it moves to branch A.

**When the agent lands on B and you never used the word "refactor",** it will ask you to confirm that you mean to change an existing feature rather than add a new one. Answer it — this is the question that keeps a genuinely new capability from being quietly buried inside someone else's feature doc.

### Step 1 — Establish the Document

#### 1B — Refactor: write the change brief

**Who:** Human, or the agent working with you

The live feature doc stays untouched for now — it still describes how the platform behaves today, and it must keep doing that until the new behavior actually ships.

Instead, write a change brief at `docs/platform/wip/<feature-name>-change.md` covering:
- What changes, in behavior terms
- Why
- **Which sections of the live feature doc this makes wrong** — name them; this list becomes the doc rewrite in Step 4
- Whether it touches a decision recorded in an ADR

This file is disposable scaffolding. It is deleted at Step 10 and never becomes a permanent record of "how the feature used to work" — `docs/platform/` has no such record by design.

#### 1C — New feature: draft the feature doc

**Who:** Human, or the agent working with you

Copy `docs/platform/feature-template.md` to a new file in `docs/platform/` named after the feature (e.g. `user-invitations.md`). **Never edit the template itself** — it is boilerplate, not a scratchpad.

Fill it out to the best of your current understanding. It does not need to be complete or polished — this draft is a starting point, not a finished artifact. Write enough that someone unfamiliar with the idea could understand what you're trying to build and why.

At minimum, fill in:
- What the feature does
- Why it's being built
- What's in scope and what's explicitly out of scope
- Any constraints or decisions you already know

Leave open questions as open questions. Step 2 will resolve them.

If you'd rather work from a blank page with the agent, let it produce this draft in-session — the point of the gate is that no code is written before the doc exists and you have signed off on it, not that you must type the first version yourself.

> **Note:** The draft lives in `docs/platform/` from the start. There is no separate "drafts" location — the file is just incomplete until Step 2 is done.

### Step 2 — Expand the Document with the Agent

**Who:** Agent (supervised)
**Skill:** `superpowers:brainstorming`

The agent reads your draft or change brief and any relevant existing docs, then works with you to produce a concrete, complete description of the target behavior, written as if it already exists and is shipped.

**What "concrete" means here:** the finished document should include affected areas of the codebase (modules, routes, components, schema changes, API contracts) where known. It should close all open questions. It should be specific enough that a developer — or an agent — could implement from this document without needing to ask clarifying questions about intent.

This is the closest thing in this workflow to a spec. Treat it as such.

This phase is interactive by design — brainstorming is a conversation, and it ends at the documentation gate. Nothing gets built until you sign off here.

**Phase A prompt — new feature (C):**

```
Use /brainstorming.

Read docs/platform/[feature-name].md. Also read CLAUDE.md and any other docs in docs/platform/ that are relevant to this feature.

Your goal is to expand and improve the feature doc I've drafted. Work with me iteratively — ask me questions to resolve open questions, surface edge cases I may not have considered, and identify decisions that need to be made before implementation.

When we're done, rewrite the feature doc as a concrete, complete document written in present tense as if the feature is already shipped. Include:
- What the feature does and how it works
- Affected files, modules, routes, or components (by name where known)
- Schema or API changes if applicable
- Key decisions made, with brief rationale
- Explicit scope boundaries

Do not leave open questions in the final document. If something cannot be resolved in this session, flag it clearly so I can decide whether to block on it or accept the uncertainty.

IMPORTANT: write the final document to docs/platform/[feature-name].md — overwrite the draft in place. Do not create it under any other path (not docs/superpowers/, not a specs/ folder, not a scratch location). This project keeps all feature docs in docs/platform/.
```

**Phase A prompt — refactor (B):**

```
Use /brainstorming.

Read docs/platform/wip/[feature-name]-change.md, the live feature doc docs/platform/[feature-name].md, CLAUDE.md, and any other relevant docs in docs/platform/.

This is a change to an existing, documented feature. Work with me iteratively to pin down the target behavior — ask questions, surface edge cases, and identify decisions that need to be made before implementation.

When we're done, rewrite docs/platform/wip/[feature-name]-change.md so it fully specifies the target behavior and lists, by section, everything in docs/platform/[feature-name].md that will need rewriting once this ships.

Do NOT edit docs/platform/[feature-name].md in this session — it must keep describing current behavior until the new behavior actually ships.

Flag it if this change contradicts a decision recorded in docs/adr/.
```

**Exit criteria:** No unresolved open questions. You can read the document and understand exactly what will be built. Sign off — that is the documentation gate, and Phase B starts on the other side of it.

---

## Phase B — Build It

One prompt carries Steps 3 through 9. The agent drafts the ADR, writes the plan, cuts the branch, implements against it with TDD, verifies, reviews its own work, acts on the findings, and arrives with a PR drafted. It announces at each boundary and keeps going.

**Phase B prompt:**

```
Read docs/platform/[feature-name].md [and docs/platform/wip/[feature-name]-change.md for a refactor] plus any linked ADRs. That is the source of truth for what gets built — do not restate it as a separate spec.

Run this through to a prepared PR without stopping for approval between steps. Announce each boundary in your reply and keep moving; I will interrupt if I want something changed.

1. ADR check. If this changes a decision recorded in docs/adr/, draft the new ADR — that is where before/after commentary belongs — and set the superseded ADR's Status line to `Superseded by ADR-000X`. That line only; the rest of the old ADR is frozen.

2. Use /writing-plans. Write an ordered implementation plan to docs/platform/wip/[feature-name]-tasks.md as a checkbox list (one `- [ ]` per task, grouped under numbered headings). For each task: what needs doing, the files affected, dependencies on other tasks, and a flag if it carries a decision or meaningful risk. Structure each for TDD — failing test first, then implement. The final task is always the documentation update: rewrite docs/platform/[feature-name].md to describe the shipped behavior in present tense, with no migration commentary, linking any new ADR. Summarize the plan in your reply, then continue.

3. Create branch feature/[feature-name] off main and switch to it, carrying the uncommitted feature doc, change brief and plan along. Show me git status first; nothing should be left behind on main.

4. Use /subagent-driven-development and /test-driven-development. Work the plan in order, checking off each `- [ ]` as you go. Dispatch parallel agents for tasks that share no files and have no ordering dependency between them.

5. Use /verification-before-completion, then /requesting-code-review, then /receiving-code-review on the findings you judge genuine. Verify that docs/platform/[feature-name].md describes the shipped behavior with no leftover open questions and no migration commentary. Report what you find and carry on.

6. Use /finishing-a-development-branch. Confirm tests pass, confirm the feature doc rewrite is in the diff, list what is currently in docs/platform/wip/, and draft the PR description.

Two things stop you:
- A decision the source document does not resolve. Describe the options and your recommendation, and wait. Do not decide unilaterally.
- Opening the PR. Draft it, then wait for my confirmation.
```

What each step in that run is doing, and what to watch for:

### Step 3 — Evaluate ADR Need

Does this involve an architectural decision that would affect future features, or that a new engineer would get wrong without knowing the history?

**Write an ADR if the decision:**
- Affects more than just this feature
- Would not be obvious from the code alone
- Overrides or extends an existing ADR

**Skip the ADR if** the decisions made are implementation details scoped entirely to this feature.

**A refactor is the common case for an ADR.** When a change reverses or replaces a decision an existing ADR records, that ADR is not edited to describe the new approach — its whole job is to preserve why the old approach was chosen. Instead:

1. A **new** ADR is written, following `docs/adr/adr-0000-template.md`. This is the one place in the repo where before/after commentary belongs: what the previous decision was, what changed, and why the tradeoff now falls differently.
2. The superseded ADR's `Status:` line is set to `Superseded by ADR-000X`. That line only — the rest of it is frozen.
3. The new ADR is linked from the feature doc under `## Linked ADRs` when the doc is rewritten in Step 4.

Everywhere outside `docs/adr/` and `docs/archive/`, the history stays out: the feature doc describes only how the platform works now.

### Step 4 — Break Down the Work into Tasks

**Skill:** `superpowers:writing-plans`

This workflow is documentation-driven, not formal spec-driven: the feature doc in `docs/platform/` is the single source of truth, and the plan is a derived, disposable checklist. There is no separate spec layer to maintain.

**The plan's last task is always a documentation task**, and it ships in the same diff as the code so it gets reviewed alongside it:

- **New feature (C):** trim `docs/platform/<feature>.md` to its post-ship form — drop the open-questions section, drop planning scaffolding, and convert anything phrased as *will be built* into *is*.
- **Refactor (B):** rewrite `docs/platform/<feature>.md` to describe the new behavior, in present tense, with **no** migration commentary — no "replaces the old X", no before/after comparison. A reader must not be able to tell from it that a previous implementation existed. Add any new ADR under `## Linked ADRs`.

The plan appears in the reply as the agent starts working it. Interrupt if the order is wrong, if a task is out of scope, or if you want it to checkpoint somewhere the plan doesn't. Everything in `docs/platform/wip/` is a working artifact — deleted at cleanup (Step 10), not kept as a long-term reference.

### Step 5 — Set Up the Branch

By this point Steps 1–4 have produced changes in the working tree (the feature doc or change brief, and the plan), so the branch carries those uncommitted changes rather than starting from a clean tree. `git switch -c` does this automatically — it moves the current, uncommitted changes onto the new branch.

### Step 6 — Implement

**Skills:** `superpowers:subagent-driven-development`, `superpowers:test-driven-development`, `superpowers:systematic-debugging`, `superpowers:dispatching-parallel-agents`

The agent works the task list in order, failing test first, checking off each `- [ ]`. It runs through tasks on its own; the thing that stops it is a **decision** the source document does not resolve — not the end of a task.

Parallel agents are worth it only for tasks that share no files and have no ordering dependency. Coordination overhead eats the gain otherwise.

**When something breaks,** switch to systematic debugging rather than letting it iterate blindly:

```
Use /systematic-debugging.

[Describe the failure: what was expected, what happened, any error output.]

Work through this methodically. Identify the root cause before proposing a fix. Show me what you find before making changes.
```

### Step 7 — Pre-PR Review

**Skills:** `superpowers:verification-before-completion`, `superpowers:requesting-code-review`

The verification pass checks that every task is complete, tests pass, nothing in the source document was left unimplemented, `docs/platform/<feature>.md` describes the shipped behavior in present tense with no migration commentary and no leftover open questions, and no debug code or placeholders remain. The code review then covers correctness against the feature doc as rewritten in this branch — **that doc rewrite is part of the diff and is reviewed as such** — plus code quality, test coverage, and missed edge cases.

Both land in the reply as the agent moves into acting on them. What you decide:

- **Must fix:** it is already fixing them
- **Should fix:** interrupt if you disagree with its call
- **Follow-up work:** note these in `docs/internal/open-findings.md` or a GitHub issue before moving on. Do not lose them.

### Step 8 — Act on Review Findings

**Skill:** `superpowers:receiving-code-review`

Each finding is verified as genuine before being acted on. A suggestion that conflicts with a decision in the feature doc gets flagged and explained, not implemented blindly.

### Step 9 — Open the PR

**Skill:** `superpowers:finishing-a-development-branch`

The PR is drafted and then the agent waits. Read the description before confirming — it should be accurate enough that someone reviewing without context can understand what changed and why. This is the last gate before the work leaves the branch.

---

## Phase C — Clean Up

This phase is not optional. Skipping it is how documentation goes stale.

The feature doc itself was rewritten in Phase B and reviewed in Step 7, so this is about removing scaffolding rather than catching up on writing.

**Phase C prompt:**

```
The feature branch for [feature-name] has been merged.

1. Switch back to main and pull the latest merged changes.
2. Delete the merged feature branch locally and confirm it's gone on remote.
3. Empty docs/platform/wip/ — delete [feature-name]-change.md and [feature-name]-tasks.md. Only README.md should remain. If anything else is in there, name it: it is scaffolding an earlier branch left behind.
4. List any temporary files, debug scripts, or implementation notes added to the repo that should not live there long-term, and keep going.
5. Read CLAUDE.md and docs/platform/overview.md. If shipping [brief description] made either one wrong — new dependencies, new constraints, structural changes to the codebase — make the updates and show me the diff.

Leave docs/platform/[feature-name].md alone. It was rewritten in Phase B.
```

### Step 10 — Post-Merge Cleanup

Two things are yours after that run finishes.

**Confirm the feature doc landed correctly.** Open `docs/platform/<feature-name>.md` on `main` and read it as a new engineer would:

- Does it describe what actually shipped, in present tense?
- Are the open questions gone?
- For a refactor: is there any trace of the old behavior — "replaces", "formerly", "used to", a before/after table? If so, remove it. That history belongs in the ADR, and only there.
- Are the linked ADRs listed?

If the answer to any of these is wrong, the Step 4 documentation task was written poorly. Fix it now and treat it as a signal for the next feature's plan.

**Confirm ADR status.** Were any architectural decisions made during implementation that weren't captured in Step 3? If yes, write the ADR now. Better late than never — and "during implementation we decided X" is a valid and honest ADR. If it supersedes an existing ADR, update that ADR's `Status:` line and nothing else.

---

## Summary Table

| Phase | Step | Who | Skill / Tool | Output |
|---|---|---|---|---|
| **A** | 0. Triage | Agent | — | Branch A (just do it), B (refactor), or C (new feature) |
| **A** | 1B. Change brief | Human / Agent | — | `docs/platform/wip/[feature]-change.md` |
| **A** | 1C. Draft feature doc | Human / Agent | — | `docs/platform/[feature].md` (draft) |
| **A** | 2. Expand the document | Agent | `superpowers:brainstorming` | Complete target-behavior document — **you sign off here** |
| **B** | 3. ADR if needed | Agent | — | `docs/adr/adr-NNNN-*.md`, superseded ADR's status line updated |
| **B** | 4. Task breakdown | Agent | `superpowers:writing-plans` | `docs/platform/wip/[feature]-tasks.md`, ending in the doc-update task |
| **B** | 5. Set up branch | Agent | — | Feature branch off `main` |
| **B** | 6. Implement | Agent | `superpowers:subagent-driven-development`, `/test-driven-development`, `/systematic-debugging`, `/dispatching-parallel-agents` | Implementation, tests, **and the rewritten feature doc** |
| **B** | 7. Pre-PR review | Agent | `superpowers:verification-before-completion`, `/requesting-code-review` | Findings, reported and acted on |
| **B** | 8. Act on findings | Agent | `superpowers:receiving-code-review` | Fixes applied |
| **B** | 9. Open PR | Agent | `superpowers:finishing-a-development-branch` | PR drafted — **you confirm here** |
| **C** | 10. Cleanup | Agent + Human | — | `wip/` emptied, feature doc confirmed, `CLAUDE.md` updated, ADRs confirmed |

---

## Rules

1. **Triage first.** Not every request is a feature. Decide branch A, B or C before any code is written — the agent does this automatically and will stop rather than start an undocumented feature.
2. **The feature doc is the source of truth.** If implementation diverges from it, update the doc — don't let them drift silently.
3. **No implementation without a complete source document.** If it has open questions, resolve them first.
4. **`docs/platform/` describes only the present.** There is no ledger of how a feature used to behave. When a refactor makes the history worth keeping, it goes in an ADR, and the feature doc links to it.
5. **ADRs before implementation, not after.** Decisions that affect implementation are documented before the agent starts building. A superseding ADR is written fresh; the superseded one has only its `Status:` line touched.
6. **The doc rewrite ships with the code.** It is the last task in the plan and part of the reviewed diff — never a post-merge chore.
7. **The agent checkpoints on decisions, not on tasks.** Let it run. Stop it when it hits something the doc doesn't resolve — that is the one interruption it should be asking for mid-build.
8. **Four gates, and only four.** The documentation gate, the intent question, an unresolved decision, and opening the PR. Everything between them runs continuously and announces at the boundary; you interrupt rather than being asked.
9. **Cleanup is part of done.** A feature is not finished until Phase C is complete and `docs/platform/wip/` is empty again.
10. **Archive, don't delete feature docs.** When a feature is retired, move its doc to `docs/archive/` with a note of when and why.
