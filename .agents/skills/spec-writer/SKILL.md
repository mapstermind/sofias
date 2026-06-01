---
name: spec-writer
description: Use when translating a PRD, feature idea, existing Django app, endpoint, command, task, or workflow into a durable functional spec under docs/specs before writing tests or implementation.
---

# Spec Writer

Write or update a functional spec under `docs/specs/`.

Follow `docs/specs/spec-template.md`.

Rules:

- Describe observable behavior and contracts.
- Include APIs, routes, commands, inputs, outputs, side effects, permissions, errors, invariants, and acceptance criteria.
- Inspect Django URLs, views/viewsets, serializers/forms, models, tasks, and commands as needed.
- Distinguish confirmed behavior from inferred behavior.
- Add open questions instead of guessing.
- Do not modify production code.
- Do not write implementation code.
- Treat specs as durable documentation that should remain current after implementation.
