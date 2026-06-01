---
name: characterization-test-writer
description: Use when replacing weak legacy tests or preparing for a refactor by writing characterization/golden-master tests that capture current Django behavior without modifying production code.
---

# Characterization Test Writer

Create characterization tests for current behavior.

Rules:

- Do not modify production code.
- Capture what the system currently does, even if awkward.
- Prefer tests at observable boundaries: HTTP endpoints, view behavior, serializers/forms, model constraints, management commands, async tasks, emitted events, external service boundaries, and database side effects.
- Avoid testing private methods.
- Avoid asserting internal call order unless it is part of an explicit contract.
- Mock external systems only at the boundary.
- Mark or locate characterization tests clearly.
- If existing tests are poor, quarantine them rather than deleting them.
- Document any captured behavior that appears undesirable or surprising.
