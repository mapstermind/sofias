# Development Workflow Guide

This document describes the end-to-end process for developing a feature, from initial idea to post-merge cleanup. It applies to all engineers on the team and is written to be followed in order.

The workflow is documentation-first: you write before you code. The feature document is the source of truth for implementation. Agent sessions are oriented by `CLAUDE.md` and the feature doc — not by verbal instruction at session start.

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

## Step 0 — Triage the Request

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

---

## Step 1 — Establish the Document

### 1B — Refactor: write the change brief

**Who:** Human, or the agent working with you

The live feature doc stays untouched for now — it still describes how the platform behaves today, and it must keep doing that until the new behavior actually ships.

Instead, write a change brief at `docs/platform/wip/<feature-name>-change.md` covering:
- What changes, in behavior terms
- Why
- **Which sections of the live feature doc this makes wrong** — name them; this list becomes the doc rewrite in Step 4
- Whether it touches a decision recorded in an ADR

This file is disposable scaffolding. It is deleted at Step 10 and never becomes a permanent record of "how the feature used to work" — `docs/platform/` has no such record by design.
### 1C — New feature: draft the feature doc

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

---

## Step 2 — Expand the Document with the Agent

**Who:** Agent (supervised)
**Skill:** `superpowers:brainstorming`

The agent reads your draft or change brief and any relevant existing docs, then works with you to produce a concrete, complete description of the target behavior, written as if it already exists and is shipped.

**What "concrete" means here:** the finished document should include affected areas of the codebase (modules, routes, components, schema changes, API contracts) where known. It should close all open questions. It should be specific enough that a developer — or an agent — could implement from this document without needing to ask clarifying questions about intent.

This is the closest thing in this workflow to a spec. Treat it as such.

**Prompt — new feature (C):**

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

**Prompt — refactor (B):**

```
Use /brainstorming.

Read docs/platform/wip/[feature-name]-change.md, the live feature doc docs/platform/[feature-name].md, CLAUDE.md, and any other relevant docs in docs/platform/.

This is a change to an existing, documented feature. Work with me iteratively to pin down the target behavior — ask questions, surface edge cases, and identify decisions that need to be made before implementation.

When we're done, rewrite docs/platform/wip/[feature-name]-change.md so it fully specifies the target behavior and lists, by section, everything in docs/platform/[feature-name].md that will need rewriting once this ships.

Do NOT edit docs/platform/[feature-name].md in this session — it must keep describing current behavior until the new behavior actually ships.

Flag it if this change contradicts a decision recorded in docs/adr/.
```

**Exit criteria for this step:** No unresolved open questions. You can read the document and understand exactly what will be built. Sign off before moving to Step 3.

---

## Step 3 — Evaluate ADR Need

**Who:** Human
**When:** After the document is finalized, before task breakdown

Read the finished document and ask: does this involve any architectural decision that would affect future features, or that a new engineer would get wrong without knowing the history?

**Write an ADR if the decision:**
- Affects more than just this feature
- Would not be obvious from the code alone
- Overrides or extends an existing ADR

**Skip the ADR if** the decisions made are implementation details scoped entirely to this feature.

If an ADR is needed, write it now in `docs/adr/` before moving to Step 4, following `docs/adr/adr-0000-template.md`.

**A refactor is the common case for an ADR.** When a change reverses or replaces a decision an existing ADR records, do not edit that ADR to describe the new approach — its whole job is to preserve why the old approach was chosen. Instead:

1. Write a **new** ADR. This is the one place in the repo where before/after commentary belongs: state what the previous decision was, what changed, and why the tradeoff now falls differently.
2. Set the superseded ADR's `Status:` line to `Superseded by ADR-000X`. That line only — the rest of it is frozen.
3. Link the new ADR from the feature doc under `## Linked ADRs` when the doc is rewritten in Step 4.

Everywhere outside `docs/adr/` and `docs/archive/`, the history stays out: the feature doc describes only how the platform works now.

---

## Step 4 — Break Down the Work into Tasks

**Who:** Agent
**Skill:** `superpowers:writing-plans`

With a concrete document in place, turn it into an ordered implementation plan. This workflow is documentation-driven, not formal spec-driven: the feature doc in `docs/platform/` is the single source of truth, and the plan is a derived, disposable checklist the implementation session works through. There is no separate spec layer to maintain.

**The plan's last task is always a documentation task**, and it ships in the same diff as the code so it gets reviewed alongside it:

- **New feature (C):** trim `docs/platform/<feature>.md` to its post-ship form — drop the open-questions section, drop planning scaffolding, and convert anything phrased as *will be built* into *is*.
- **Refactor (B):** rewrite `docs/platform/<feature>.md` to describe the new behavior, in present tense, with **no** migration commentary — no "replaces the old X", no before/after comparison. A reader must not be able to tell from it that a previous implementation existed. Add any new ADR under `## Linked ADRs`.

**Prompt:**

```
Use /writing-plans.

Read [docs/platform/[feature-name].md | docs/platform/wip/[feature-name]-change.md] and any linked ADRs. Use this as the source of truth for what needs to be built — do not restate the design as a separate spec.

Produce an ordered implementation plan. For each task:
- State what needs to be done
- Identify the files or components affected
- Note any dependencies between tasks
- Flag any task that requires a decision or has meaningful implementation risk

Structure each task for test-driven development: write a failing test first, implement to pass, then confirm. Keep each task small enough to implement and verify in a single session.

The final task must be the documentation update: rewrite docs/platform/[feature-name].md so it describes the shipped behavior in present tense, with no migration commentary, and links any new ADR. This is part of the implementation, not a follow-up.

Write the plan to docs/platform/wip/[feature-name]-tasks.md as a checkbox list (one `- [ ]` per task, grouped under numbered headings). Do not write it anywhere else. Do not begin implementation. Output the plan for my review.
```

Review the generated plan before proceeding. Remove tasks that are out of scope, reorder if dependencies are wrong, and note anything you want the agent to checkpoint on during implementation. Everything in `docs/platform/wip/` is a working artifact — it is deleted at cleanup (Step 10), not kept as a long-term reference.

---

## Step 5 — Set Up the Branch

**Who:** Agent
**When:** After the plan is reviewed, before implementation

Create a feature branch off `main` to keep this work separate from the mainline history. By this point Steps 1–4 have already produced changes in the working tree (the feature doc or change brief, and the plan), so the branch should carry those uncommitted changes along rather than start from a clean tree. `git switch -c` (or `git checkout -b`) does this automatically — it moves your current, uncommitted changes onto the new branch.

**Prompt:**

```
Create a new branch called feature/[feature-name] from main and switch to it, bringing the current uncommitted changes (the feature doc or change brief, and the task plan from earlier steps) along onto the branch.

Run git status first and show me what's currently modified. Confirm all of that work is now on feature/[feature-name] before we proceed — nothing should be left behind on main.
```

---

## Step 6 — Implement

**Who:** Agent (with checkpoints)
**Skills:** `superpowers:executing-plans`, `superpowers:test-driven-development`, `superpowers:systematic-debugging`, `superpowers:dispatching-parallel-agents`

### 6a — Start implementation with TDD

Hand the agent the task list and instruct it to work through tasks autonomously, checkpoint on decisions, and follow failing-test-first discipline.

**Prompt:**

```
Use /executing-plans and /test-driven-development together.

The implementation plan is in docs/platform/wip/[feature-name]-tasks.md. The source of truth is [docs/platform/[feature-name].md | docs/platform/wip/[feature-name]-change.md].

Work through the tasks in order, checking off each `- [ ]` as you complete it. Follow test-driven development: write a failing test before implementing each piece of functionality, then implement to make it pass.

Rules for this session:
- Run autonomously through tasks, but stop and ask me before making any decision not covered by the source document or the plan
- If you hit a decision point the source document doesn't resolve, describe the options and your recommendation — do not decide unilaterally
- After completing each task, confirm it's done and what was changed before moving to the next
- The final documentation task is not optional and is not deferred to after the merge

Start with Task 1.
```

### 6b — Debugging (when needed)

When a task fails or produces unexpected behavior, switch to systematic debugging rather than letting the agent iterate blindly.

**Prompt:**

```
Use /systematic-debugging.

[Describe the failure: what was expected, what happened, any error output.]

Work through this methodically. Identify the root cause before proposing a fix. Show me what you find before making changes.
```

### 6c — Parallel agents (for independent tasks)

If the task list contains tasks with no dependencies between them — for example, building the backend route and the frontend component independently — parallel agents can reduce total implementation time.

**Prompt:**

```
Use /dispatching-parallel-agents.

The following tasks from the task list are independent and can be worked on simultaneously:
- [Task A]
- [Task B]

Dispatch agents to handle each in parallel. Each agent should reference the source document for this work as the source of truth. Coordinate results when both are complete.
```

Use this selectively. Don't parallelize tasks that share files or have ordering dependencies — the coordination overhead outweighs the time saved.

---

## Step 7 — Pre-PR Review

**Who:** Agent, then Human
**Skills:** `superpowers:verification-before-completion`, `superpowers:requesting-code-review`

### 7a — Verification pass

Before requesting a code review, run a self-verification pass to catch obvious issues.

**Prompt:**

```
Use /verification-before-completion.

Review the work done for this feature against the plan in docs/platform/wip/[feature-name]-tasks.md and the source document for this work.

Check:
- All tasks in the plan are complete
- Tests exist and pass
- Nothing in the source document was left unimplemented
- docs/platform/[feature-name].md describes the shipped behavior, in present tense, with no migration commentary and no leftover open questions
- No debug code, TODOs, or placeholder content remains

Report findings before I move to code review.
```

### 7b — Code review

**Prompt:**

```
Use /requesting-code-review.

Review the implementation of [feature-name]. Focus on:
- Correctness relative to docs/platform/[feature-name].md as rewritten in this branch
- Whether that doc rewrite is accurate and complete — it is part of the diff, review it as such
- Code quality and consistency with the rest of the codebase
- Test coverage
- Any edge cases the implementation may have missed

Output a structured list of findings with severity (must fix / should fix / consider).
```

### 7c — Human decision

Read the findings. Decide:
- **Must fix before PR:** address in Step 8
- **Should fix before PR:** your call — address now or log as follow-up
- **Follow-up work:** note these in `docs/internal/open-findings.md` or a GitHub issue before moving on. Do not lose them.

---

## Step 8 — Act on Review Findings

**Who:** Agent
**Skill:** `superpowers:receiving-code-review`

**Prompt:**

```
Use /receiving-code-review.

Here are the review findings to act on:
[paste the findings you decided to fix]

For each finding: verify it's a genuine issue before acting on it. Implement sound suggestions. If a suggestion is questionable or conflicts with a decision in the feature doc, flag it and explain why rather than implementing it blindly.
```

---

## Step 9 — Open the PR

**Who:** Agent
**Skill:** `superpowers:finishing-a-development-branch`

**Prompt:**

```
Use /finishing-a-development-branch.

Feature branch: feature/[feature-name]
Feature doc: docs/platform/[feature-name].md

Verify that all tests pass and the work is complete. Then prepare the PR:
- Confirm docs/platform/[feature-name].md is updated in this branch and is part of the diff
- List what is currently in docs/platform/wip/ so I can see what still needs deleting at cleanup
- Write a PR description that summarizes what was built and references the feature doc
- Note any follow-up items identified during review
- Walk me through the merge checklist

Do not open the PR until I confirm.
```

Review the PR description before confirming. The description should be accurate enough that someone reviewing the PR without context can understand what changed and why.

---

## Step 10 — Post-Merge Cleanup

**Who:** Human and Agent

This step is not optional. Skipping it is how documentation goes stale.

The feature doc itself was already rewritten in Step 6 and reviewed in Step 7, so this step is about removing scaffolding rather than catching up on writing.

### 10a — Agent: clean up implementation artifacts

**Prompt:**

```
The feature branch for [feature-name] has been merged.

Do the following cleanup:
1. Switch back to main and pull the latest merged changes
2. Delete the merged feature branch locally and confirm it's gone on remote
3. Empty docs/platform/wip/ — delete [feature-name]-change.md and [feature-name]-tasks.md. Only README.md should remain. If anything else is in there, list it: it is scaffolding an earlier branch left behind.
4. Check if any temporary files, debug scripts, or implementation notes were added to the repo that should not be committed long-term — list them for my review

Do not touch docs/platform/[feature-name].md or any other docs/ files.
```

### 10b — Human: confirm the feature doc landed correctly

Open `docs/platform/<feature-name>.md` on `main` and read it as a new engineer would:

- Does it describe what actually shipped, in present tense?
- Are the open questions gone?
- For a refactor: is there any trace of the old behavior — "replaces", "formerly", "used to", a before/after table? If so, remove it. That history belongs in the ADR, and only there.
- Are the linked ADRs listed?

If the answer to any of these is wrong, the Step 6 documentation task was done poorly. Fix it now and treat it as a signal for the next feature's plan.

### 10c — Agent: check if CLAUDE.md or system docs need updating

**Prompt:**

```
Read CLAUDE.md and docs/platform/overview.md.

Given the feature we just shipped ([brief description]), check whether either document needs updating — new dependencies, new constraints, structural changes to the codebase that aren't reflected there.

List what needs updating and proposed changes. Do not edit the files yet.
```

Review the proposed changes, then confirm or adjust before the agent writes them.

### 10d — Human: confirm ADR status

Check: were any architectural decisions made during implementation that weren't captured in Step 3? If yes, write the ADR now. Better late than never — and "during implementation we decided X" is a valid and honest ADR. If it supersedes an existing ADR, update that ADR's `Status:` line and nothing else.

---

## Summary Table

| Step | Who | Skill / Tool | Output |
|---|---|---|---|
| 0. Triage | Agent | — | Branch A (just do it), B (refactor), or C (new feature) |
| 1B. Write change brief | Human / Agent | — | `docs/platform/wip/[feature]-change.md` |
| 1C. Draft feature doc | Human / Agent | — | `docs/platform/[feature].md` (draft) |
| 2. Expand the document | Agent | `superpowers:brainstorming` | Complete, concrete target-behavior document |
| 3. Write ADR if needed | Human | — | `docs/adr/adr-NNNN-*.md`, superseded ADR's status updated |
| 4. Task breakdown | Agent | `superpowers:writing-plans` | `docs/platform/wip/[feature]-tasks.md`, ending in the doc-update task |
| 5. Set up branch | Agent | — | Feature branch off `main` |
| 6. Implement | Agent | `superpowers:executing-plans`, `/test-driven-development`, `/systematic-debugging`, `/dispatching-parallel-agents` | Working implementation with tests **and the rewritten feature doc** |
| 7. Pre-PR review | Agent + Human | `superpowers:verification-before-completion`, `/requesting-code-review` | Reviewed findings, human decision |
| 8. Act on findings | Agent | `superpowers:receiving-code-review` | Fixes applied |
| 9. Open PR | Agent | `superpowers:finishing-a-development-branch` | PR opened |
| 10. Cleanup | Human + Agent | — | `wip/` emptied, feature doc confirmed, `CLAUDE.md` updated, ADRs confirmed |

---

## Rules

1. **Triage first.** Not every request is a feature. Decide branch A, B or C before any code is written — the agent does this automatically and will stop rather than start an undocumented feature.
2. **The feature doc is the source of truth.** If implementation diverges from it, update the doc — don't let them drift silently.
3. **No implementation without a complete source document.** If it has open questions, resolve them first.
4. **`docs/platform/` describes only the present.** There is no ledger of how a feature used to behave. When a refactor makes the history worth keeping, it goes in an ADR, and the feature doc links to it.
5. **ADRs before implementation, not after.** Decisions that affect implementation should be documented before the agent starts work. A superseding ADR is written fresh; the superseded one has only its `Status:` line touched.
6. **The doc rewrite ships with the code.** It is the last task in the plan and part of the reviewed diff — never a post-merge chore.
7. **The agent checkpoints on decisions, not on tasks.** Let it run through tasks autonomously. Stop it when it hits something the doc doesn't resolve.
8. **Cleanup is part of done.** A feature is not finished until Step 10 is complete and `docs/platform/wip/` is empty again.
9. **Archive, don't delete feature docs.** When a feature is retired, move its doc to `docs/archive/` with a note of when and why.
