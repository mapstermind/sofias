---
name: test-first-implementation
description: Use when implementing a Django feature or bug fix after a spec and failing tests already exist, following test-driven development. Temporary PRDs or test plans may exist but are not required once the spec and tests are clear.
---

# Test-First Implementation

Implement code after tests exist.

Rules:

- Read the relevant spec, tests, and any active temporary workflow documents before coding.
- Confirm which tests are expected to fail before implementation.
- Implement the smallest change that satisfies the tests.
- Preserve public behavior unless the spec explicitly changes it.
- Do not modify tests unless the spec is wrong or incomplete; if so, explain and ask before changing tests.
- Prefer simple Django-native implementation.
- Ask before adding dependencies.
- Run the relevant tests.
- Refactor only after tests pass.
- After implementation, remove temporary PRDs/test plans/refactor plans if their durable value has been transferred into specs, tests, user docs, or ADRs.
