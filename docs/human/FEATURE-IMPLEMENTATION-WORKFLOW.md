# How-to implement a new feature

## Feature Implementation Workflow

---

### Placeholder legend

The prompts below are templates. Replace each `<PLACEHOLDER>` with your own
values before sending:

| Placeholder | Replace with | Example |
|-------------|--------------|---------|
| `<FEATURE_NAME>` | Plain-English description of the feature | a user data export feature |
| `<feature-slug>` | kebab-case folder name for this feature's artifacts | user-export |
| `<SPEC_FILES>` | The existing spec file(s) relevant to this feature | docs/specs/auth.md, docs/specs/users.md |
| `<SPEC_FILE>` | The single spec file this feature updates or extends | docs/specs/users.md |
| `<TASK_N>` | The task number and its short description from `tasks.md` | task 1: create the ExportJob background job class |
| `<CONCERNS>` | The specific things the spec must cover | inputs/outputs, edge cases, rate limiting |

Anything in `<angle brackets>` is yours to overwrite. Everything else can be
sent as-is.

---

### Skills used in this workflow

This workflow assumes the **Superpowers** plugin is installed. Each step names
the specific skill to use (e.g. `superpowers:brainstorming`, reachable as
`/brainstorming`). Invoke it via the Skill tool or its slash command — when a
skill covers the step, use it rather than improvising. The skills enforce the
discipline the prompts describe (failing-test-first, review passes, clean
branch integration), so you don't have to spell it out every time.

---

### Step 1 — Capture the idea **[Human]**

Write a rough note. Doesn't need to be formal. Just enough that you won't lose the intent.

Look at `changes/0_example/proposal.md` to get an idea on what to create, then write your own at `changes/<feature-slug>/proposal.md`.

No agent involved. This is you thinking, not prompting.

---

### Step 2 — Explore and validate the idea with the agent

Open Claude Code and invoke `superpowers:brainstorming` (`/brainstorming`) to pressure-test the idea against your actual codebase before committing to an approach.

**Prompt:**
```
Use the superpowers:brainstorming skill.

Read <SPEC_FILES>, then read changes/<feature-slug>/proposal.md.

I want to add <FEATURE_NAME>. Before we plan anything:
- What parts of the codebase will this touch?
- Are there existing patterns I should follow?
- What edge cases or risks do you see that I haven't mentioned?

Do not write any code. Just analyze and report back.
```

**What this uses:** `superpowers:brainstorming`

**What you get back:** A list of files involved, risks flagged, existing patterns identified. You review this and update your `proposal.md` with anything you missed.

---

### Step 3 — Write the spec delta **[Human, with agent assist]**

Create or update the relevant entry in `docs/specs/` to describe how this feature *will* work once shipped. Write it as if it already exists.

**Prompt:**
```
Read changes/<feature-slug>/proposal.md.

Draft a spec section for <FEATURE_NAME>.
Match the style and structure of the existing specs in docs/specs/ (e.g. <SPEC_FILE>).
Cover: what it does, <CONCERNS>.

If the scope warrants its own file, create one under docs/specs/; otherwise
append the section to <SPEC_FILE>.
```

**What this uses:** Regular Claude Code prompt — no dedicated skill. The brainstorming output from Step 2 is your input.

**[Human step]:** You read the draft, edit it to match your actual decisions, and save it. Don't merge it yet — it reflects the intended state, not the current one.

---

### Step 4 — Break the work into tasks

Use `superpowers:writing-plans` (`/writing-plans`) to turn the spec into an ordered, atomic task list. This is the skill's exact purpose: a spec in, a reviewable plan out, before any code is touched.

**Prompt:**
```
Use the superpowers:writing-plans skill.

Read changes/<feature-slug>/proposal.md and the spec section in <SPEC_FILE>.

Create changes/<feature-slug>/tasks.md with atomic implementation tasks.
Each task should:
- Be completable in one focused session
- Have specific acceptance criteria
- Note which files it touches
- List dependencies on other tasks

Order them by dependency. Flag any that require a decision before starting.
```

**What this uses:** `superpowers:writing-plans` (Plan Mode so you can review before it writes the file).

**[Human step]:** Review the task list. Reorder or split anything that feels too large. A task that says "implement the whole feature" is too big. A task scoped to a single class, job, or endpoint is right-sized.

---

### Step 5 — Implement task by task

Before writing code, isolate the work with `superpowers:using-git-worktrees` (`/using-git-worktrees`) so your main workspace stays clean. Then drive the plan with `superpowers:executing-plans` (`/executing-plans`), which works through `tasks.md` one task at a time with a review checkpoint between each. Don't hand the agent the whole list at once.

**Prompt per task:**
```
Use the superpowers:executing-plans and superpowers:test-driven-development skills.

Read changes/<feature-slug>/tasks.md and <SPEC_FILE>.

Implement <TASK_N>.
- Write the failing test first
- Show me the test before writing any implementation
- Wait for my approval before continuing
```

**What this uses:** `superpowers:executing-plans` to sequence the work and `superpowers:test-driven-development` to enforce failing-test-first. With Superpowers installed the TDD discipline is applied automatically; the bullet points above just make the checkpoint explicit.

**Between tasks — [Human step]:** Review the diff. Run tests locally. Check off the completed task in `tasks.md` before moving on. If a test fails or something behaves unexpectedly, invoke `superpowers:systematic-debugging` (`/systematic-debugging`) rather than patching blindly.

**If the agent goes off-plan:**
```
Stop. You're modifying files not listed in this task.
Revert to only what <TASK_N> specifies. If you think those other
changes are necessary, explain why and wait for my approval.
```

> If several tasks are genuinely independent (no shared state, no ordering), `superpowers:dispatching-parallel-agents` can run them concurrently instead of one at a time.

---

### Step 6 — Self-review before PR

Once all tasks are checked off, run `superpowers:verification-before-completion` (`/verification-before-completion`) to confirm the suite actually passes — evidence before claims — then `superpowers:requesting-code-review` (`/requesting-code-review`) for the two-pass review.

**Prompt:**
```
Use the superpowers:verification-before-completion skill first, then the superpowers:requesting-code-review skill.

All tasks in changes/<feature-slug>/tasks.md are complete.

Do a two-pass review of everything changed in this branch:
Pass 1: Does the implementation match the acceptance criteria in tasks.md
         and the spec in <SPEC_FILE>?
Pass 2: Code quality — error handling, edge cases, security issues,
         anything that would fail a code review.

List findings by severity. Do not fix anything yet.
```

**What this uses:** `superpowers:verification-before-completion`, then `superpowers:requesting-code-review`.

**[Human step]:** Read the findings. Decide what to fix before the PR and what to note as follow-up work.

---

### Step 7 — Fix review findings

Use `superpowers:receiving-code-review` (`/receiving-code-review`) so each finding is verified before it's acted on — it implements sound suggestions and pushes back on questionable ones instead of agreeing reflexively.

**Prompt:**
```
Use the superpowers:receiving-code-review skill.

Address the critical and warning findings from the review.
Work through them one at a time. Show me each fix before applying it.
```

**What this uses:** `superpowers:receiving-code-review`.

---

### Step 8 — Open the PR **[Human, with agent assist]**

Use `superpowers:finishing-a-development-branch` (`/finishing-a-development-branch`) — it checks the work is complete and tests pass, then walks you through how to integrate (PR, merge, or cleanup).

**Prompt:**
```
Use the superpowers:finishing-a-development-branch skill.

Write a PR description for <FEATURE_NAME>.
Base it on changes/<feature-slug>/proposal.md and tasks.md.
Include: what changed, why, how to test it, any follow-up items noted
during review.
```

**What this uses:** `superpowers:finishing-a-development-branch`.

**[Human step]:** Edit the description, open the PR, assign reviewers. Code review by teammates happens here — this is a human process.

---

### Step 9 — Post-merge cleanup

After the PR merges:

**Prompt:**
```
The <FEATURE_NAME> work has merged.

1. Update <SPEC_FILE> to reflect the final implementation — the actual
   shipped state, not the pre-implementation draft. Check whether anything
   changed during implementation versus the original spec and reconcile it.

2. List any CLAUDE.md updates needed based on patterns or decisions
   made during this feature.
```

**What this uses:** Regular Claude Code prompt. If you kept the branch isolated with a worktree in Step 5, `superpowers:finishing-a-development-branch` also handles tearing it down.

**[Human step]:** Review the spec update. Apply any CLAUDE.md additions you agree with. Then:

```bash
rm -rf changes/<feature-slug>/
git add -A
git commit -m "docs: update specs and cleanup changes artifacts post <feature-slug> merge"
```

`changes/<feature-slug>/` is now gone. `docs/specs/` reflects reality. `CLAUDE.md` has any new rules. The codebase is clean.

---

## Summary Table

| Step | Who | Skill / Tool |
|------|-----|--------------|
| 1. Capture idea | Human | None |
| 2. Explore codebase | Agent | `superpowers:brainstorming` |
| 3. Write spec draft | Agent + Human edit | Claude Code (regular prompt) |
| 4. Break into tasks | Agent + Human review | `superpowers:writing-plans` + Plan Mode |
| 5. Implement per task | Agent + Human review each | `superpowers:executing-plans` + `superpowers:test-driven-development` |
| 6. Self-review | Agent | `superpowers:verification-before-completion` + `superpowers:requesting-code-review` |
| 7. Fix findings | Agent + Human approval | `superpowers:receiving-code-review` |
| 8. PR description | Agent + Human edits | `superpowers:finishing-a-development-branch` |
| 9. Post-merge cleanup | Agent + Human confirms | Claude Code (regular prompt) |

---
