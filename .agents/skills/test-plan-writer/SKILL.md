---
name: test-plan-writer
description: Use when creating a temporary test plan from a spec or PRD for a Django feature, service, endpoint, model behavior, permission rule, or refactor safety net before writing tests.
---

# Test Plan Writer

Write temporary test plans under `docs/workflow/` or directly inside the relevant feature/spec working document.

Follow `docs/workflow/test-plan-template.md`.

Rules:

- Map each important behavior to one or more tests.
- Prefer behavior-focused tests over line-coverage tests.
- Identify acceptance/API tests, integration tests, unit tests, model tests, serializer/form tests, permission tests, and edge cases.
- Identify external boundaries to mock.
- Explicitly list tests that are not worth writing.
- Do not modify production code.
- After implementation, delete the test plan once its useful information is represented by tests and specs.
