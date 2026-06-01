---
name: prd-writer
description: Use when clarifying product intent for a Django feature, workflow, user-facing behavior, or meaningful product change before writing specs, tests, or code. PRDs are temporary workflow artifacts in this repo and should not become permanent documentation by default.
---

# PRD Writer

Write or update a temporary PRD under `docs/workflow/`.

Follow `docs/workflow/prd-template.md`.

Rules:

- Capture product intent, not implementation details.
- Identify users, goals, non-goals, acceptance criteria, and open questions.
- If code inspection reveals existing behavior, distinguish current behavior from desired behavior.
- Link to related specs, ADRs, and test plans when they exist.
- Do not modify production code.
- Do not write implementation tests in this skill.
- After implementation, delete the PRD if its durable value has been transferred into specs, tests, user docs, or ADRs.
