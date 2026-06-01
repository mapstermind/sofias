---
name: refactor-under-tests
description: Use when refactoring Django production code after characterization or behavior tests already protect current behavior, especially for legacy cleanup, package removal, service extraction, or modernization.
---

# Refactor Under Tests

Refactor implementation without changing behavior.

Rules:

- Read relevant specs, ADRs, and tests first.
- Do not modify tests during refactoring unless explicitly instructed.
- Do not change externally observable behavior.
- Keep commits/changes small and reversible.
- Remove legacy packages only when tests prove behavior is preserved and the dependency is no longer used.
- Prefer Django-native, maintainable, modern patterns.
- Run the full relevant test suite after each meaningful refactor step.
- If behavior appears wrong but tests protect it, document the issue and propose a separate spec/change rather than silently changing it.
- Create an ADR only if the refactor includes a meaningful architectural, dependency, data-model, or infrastructure decision.
