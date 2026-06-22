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
│   │   ├── data-model.md
│   │   ├── [feature-name].md            # The feature doc — source of truth (Steps 1–2)
│   │   └── [feature-name]-tasks.md      # Derived implementation plan — disposable, deleted at cleanup (Step 4 → 10)
│   ├── internal/                        # Human-only docs — not referenced by the agent
│   │   ├── prompting-workflow.md
│   │   ├── user-guides/
│   │   └── meetings/
│   └── archive/                         # Retired feature docs and deprecated content
└── README.md
```

---

## Before You Start

Read `CLAUDE.md` and the relevant docs in `docs/platform/` before starting any feature. If something in those documents is already wrong or outdated, fix it first. Starting a feature on top of stale context compounds the problem.

---

## Step 1 — Draft the Feature Doc

**Who:** Human  
**When:** Before any agent session is opened

Copy the template from `docs/platform/[new-feature]-template.md` and create a new file in `docs/platform/` named after the feature (e.g. `user-invitations.md`).

Fill it out to the best of your current understanding. It does not need to be complete or polished — this draft is a starting point, not a finished artifact. Write enough that someone unfamiliar with the idea could understand what you're trying to build and why.

At minimum, fill in:
- What the feature does
- Why it's being built
- What's in scope and what's explicitly out of scope
- Any constraints or decisions you already know

Leave open questions as open questions. The next step will resolve them.

> **Note:** The draft lives in `docs/platform/` from the start. There is no separate "drafts" location — the file is just incomplete until Step 2 is done.

---

## Step 2 — Expand the Feature Doc with the Agent

**Who:** Agent (supervised)  
**Skill:** `superpowers:brainstorming`

The agent reads your draft and any relevant existing docs, then works with you to produce a concrete, complete feature document written as if the feature already exists and is shipped.

**What "concrete" means here:** the finished doc should include affected areas of the codebase (modules, routes, components, schema changes, API contracts) where known. It should close all open questions. It should be specific enough that a developer — or an agent — could implement the feature from this document without needing to ask clarifying questions about intent.

This is the closest thing in this workflow to a spec. Treat it as such.

**Prompt:**

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

**Exit criteria for this step:** The feature doc has no unresolved open questions. You can read it and understand exactly what will be built. Sign off on it before moving to Step 3.

---

## Step 3 — Evaluate ADR Need

**Who:** Human  
**When:** After the feature doc is finalized, before task breakdown

Read the finished feature doc and ask: does this feature involve any architectural decision that would affect future features, or that a new engineer would get wrong without knowing the history?

**Write an ADR if the decision:**
- Affects more than just this feature
- Would not be obvious from the code alone
- Overrides or extends an existing ADR

**Skip the ADR if** the decisions made are implementation details scoped entirely to this feature.

If an ADR is needed, write it now in `docs/adr/` before moving to Step 4. Use the standard format:

```markdown
# ADR-[number]: [Title]

Date: YYYY-MM-DD  
Status: Accepted

## Context
[What situation forced this decision. One paragraph.]

## Decision
[What you decided. One or two sentences.]

## Consequences
[What gets easier, what gets harder, what tradeoff you're accepting.]
```

Link the ADR from the feature doc under a `## Linked ADRs` section.

---

## Step 4 — Break Down the Work into Tasks

**Who:** Agent  
**Skill:** `superpowers:writing-plans`

With a concrete feature doc in place, turn it into an ordered implementation plan. This workflow is documentation-driven, not formal spec-driven: the feature doc in `docs/platform/` is the single source of truth, and the plan is a derived, disposable checklist the implementation session works through. There is no separate spec layer to maintain.

**Prompt:**

```
Use /writing-plans.

Read docs/platform/[feature-name].md and any linked ADRs. Use this as the source of truth for what needs to be built — do not restate the design as a separate spec.

Produce an ordered implementation plan. For each task:
- State what needs to be done
- Identify the files or components affected
- Note any dependencies between tasks
- Flag any task that requires a decision or has meaningful implementation risk

Structure each task for test-driven development: write a failing test first, implement to pass, then confirm. Keep each task small enough to implement and verify in a single session.

Write the plan to docs/platform/[feature-name]-tasks.md as a checkbox list (one `- [ ]` per task, grouped under numbered headings). Do not write it anywhere else. Do not begin implementation. Output the plan for my review.
```

Review the generated plan before proceeding. Remove tasks that are out of scope, reorder if dependencies are wrong, and note anything you want the agent to checkpoint on during implementation. The `-tasks.md` file is a working artifact — it gets trimmed or deleted at cleanup (Step 10), not kept as a long-term reference.

---

## Step 5 — Set Up the Branch

**Who:** Agent  
**Skill:** `superpowers:using-git-worktrees` (recommended) or standard branch

Use a worktree to keep the feature branch isolated from your main working tree. This lets you switch context without stashing or committing incomplete work.

**Prompt:**

```
Use /using-git-worktrees.

Create a new worktree and branch for this feature. Branch name: [feature/feature-name].

Set it up so implementation work happens in the worktree. Confirm the worktree is ready before we proceed.
```

If you prefer a standard branch:

```
Create a new branch called feature/[feature-name] from main and switch to it.
Confirm the branch is ready before we proceed.
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

The implementation plan is in docs/platform/[feature-name]-tasks.md. The feature doc docs/platform/[feature-name].md is the source of truth.

Work through the tasks in order, checking off each `- [ ]` as you complete it. Follow test-driven development: write a failing test before implementing each piece of functionality, then implement to make it pass.

Rules for this session:
- Run autonomously through tasks, but stop and ask me before making any decision not covered by the feature doc or the plan
- If you hit a decision point the feature doc doesn't resolve, describe the options and your recommendation — do not decide unilaterally
- After completing each task, confirm it's done and what was changed before moving to the next
- Reference docs/platform/[feature-name].md as the source of truth throughout

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

Dispatch agents to handle each in parallel. Each agent should reference docs/platform/[feature-name].md as the source of truth. Coordinate results when both are complete.
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

Review the work done for this feature against the plan in docs/platform/[feature-name]-tasks.md and docs/platform/[feature-name].md.

Check:
- All tasks in the plan are complete
- Tests exist and pass
- Nothing in the feature doc was left unimplemented
- No debug code, TODOs, or placeholder content remains

Report findings before I move to code review.
```

### 7b — Code review

**Prompt:**

```
Use /requesting-code-review.

Review the implementation of [feature-name]. Focus on:
- Correctness relative to the feature doc
- Code quality and consistency with the rest of the codebase
- Test coverage
- Any edge cases the implementation may have missed

Output a structured list of findings with severity (must fix / should fix / consider).
```

### 7c — Human decision

Read the findings. Decide:
- **Must fix before PR:** address in Step 8
- **Should fix before PR:** your call — address now or log as follow-up
- **Follow-up work:** note these somewhere (a comment in the feature doc, a GitHub issue, or a note in `docs/internal/`) before moving on. Do not lose them.

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

### 10a — Agent: clean up implementation artifacts

**Prompt:**

```
The feature branch for [feature-name] has been merged.

Do the following cleanup:
1. If a worktree was used, remove it
2. Delete the merged feature branch locally and confirm it's gone on remote
3. Delete the implementation plan docs/platform/[feature-name]-tasks.md — it was disposable scaffolding, now superseded by the merged code and the feature doc
4. Check if any temporary files, debug scripts, or implementation notes were added to the repo that should not be committed long-term — list them for my review

Do not touch docs/platform/[feature-name].md or any other docs/ files yet.
```

### 10b — Human: update the feature doc

Open `docs/platform/[feature-name].md` and trim it to its post-ship form:

- Remove the open questions section (resolved)
- Remove implementation scaffolding notes
- Update any section that describes what *will* be built to describe what *was* built
- Keep: what the feature does, key decisions made, scope boundaries, linked ADRs

The post-ship feature doc is a reference artifact, not a planning artifact. It should be readable by a new engineer or agent session to understand how this feature works without reading the code.

### 10c — Agent: check if CLAUDE.md or system docs need updating

**Prompt:**

```
Read CLAUDE.md and docs/platform/overview.md.

Given the feature we just shipped ([brief description]), check whether either document needs updating — new dependencies, new constraints, structural changes to the codebase that aren't reflected there.

List what needs updating and proposed changes. Do not edit the files yet.
```

Review the proposed changes, then confirm or adjust before the agent writes them.

### 10d — Human: confirm ADR status

Check: were any architectural decisions made during implementation that weren't captured in Step 3? If yes, write the ADR now. Better late than never — and "during implementation we decided X" is a valid and honest ADR.

---

## Summary Table

| Step | Who | Skill / Tool | Output |
|---|---|---|---|
| 1. Draft feature doc | Human | — | `docs/platform/[feature].md` (draft) |
| 2. Expand feature doc | Agent | `superpowers:brainstorming` | `docs/platform/[feature].md` (complete) |
| 3. Write ADR if needed | Human | — | `docs/adr/ADR-[n].md` |
| 4. Task breakdown | Agent | `superpowers:writing-plans` | `docs/platform/[feature]-tasks.md` (reviewed plan) |
| 5. Set up branch | Agent | `superpowers:using-git-worktrees` | Feature branch / worktree |
| 6. Implement | Agent | `superpowers:executing-plans`, `/test-driven-development`, `/systematic-debugging`, `/dispatching-parallel-agents` | Working implementation with tests |
| 7. Pre-PR review | Agent + Human | `superpowers:verification-before-completion`, `/requesting-code-review` | Reviewed findings, human decision |
| 8. Act on findings | Agent | `superpowers:receiving-code-review` | Fixes applied |
| 9. Open PR | Agent | `superpowers:finishing-a-development-branch` | PR opened |
| 10. Cleanup | Human + Agent | — | Trimmed feature doc, updated CLAUDE.md, ADRs confirmed |

---

## Rules

1. **The feature doc is the source of truth.** If implementation diverges from it, update the doc — don't let them drift silently.
2. **No implementation without a complete feature doc.** If the doc has open questions, resolve them first.
3. **ADRs before implementation, not after.** Decisions that affect implementation should be documented before the agent starts work.
4. **The agent checkpoints on decisions, not on tasks.** Let it run through tasks autonomously. Stop it when it hits something the doc doesn't resolve.
5. **Cleanup is part of done.** A feature is not finished until Step 10 is complete.
6. **Archive, don't delete feature docs.** When a feature is retired, move its doc to `docs/archive/` with a note of when and why.
