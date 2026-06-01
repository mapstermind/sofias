---
name: behavior-test-writer
description: Use when writing real behavior tests from a spec or test plan for a Django feature, endpoint, model, serializer/form, permission rule, workflow, or bug fix before implementation.
---

# Behavior Test Writer

Write tests that describe intended behavior.

Rules:

- Use the spec and test plan as the source of truth.
- Tests should fail before implementation when behavior is missing or incorrect.
- Prefer clear test names that describe behavior.
- Test observable outputs and side effects.
- Avoid tests that only execute code for coverage.
- Avoid over-mocking internal implementation details.
- Use existing project test conventions and fixtures where possible.
- Do not modify production code.
- If the spec is ambiguous, add an open question rather than inventing behavior.
