# Repository instructions

## Project

This is a Django project. Prefer Django-native patterns unless the repository already uses a different explicit convention.

SOFIA-S is a Django 6 survey and reporting application. Runtime configuration lives in `config/`, with feature apps under `apps/`: `accounts`, `core`, `surveys`, `responses`, `reports`, and `analytics`. Templates are in `templates/`. Static assets live in `static/`; edit Tailwind input in `static/css/main.css`, generated CSS in `static/css/output.css`, TypeScript in `static/ts/`, and compiled browser JavaScript in `static/js/`.

Tests are colocated in app-level `tests/` packages where practical. The root `tests/legacy/` directory is only for quarantined legacy tests.

## Development philosophy

Use lightweight spec-driven development and test-driven development.

Default order for meaningful changes:

1. Understand current behavior.
2. Clarify product intent.
3. Create a temporary PRD only when product intent is unclear or the change is feature-level.
4. Write or update the durable functional spec.
5. Write or update a temporary test plan if needed.
6. Write failing behavior tests.
7. Implement the smallest code change that satisfies the tests.
8. Refactor after tests pass.
9. Update durable docs.
10. Delete temporary planning artifacts once their useful information has been transferred into specs, tests, user docs, or ADRs.

Do not use vibe-coding as the primary workflow. Prompts may assist execution, but durable specs and tests define the work.

## Artifact lifecycle

This is a solo project, not a regulated or heavy product-management environment.

Keep the documentation lightweight.

Durable artifacts:

- Functional specs under `docs/specs/`
- User-facing documentation under `docs/user/`
- Tests as executable specifications
- ADRs under `docs/adr/` only for meaningful architectural, dependency, data-model, or infrastructure decisions

Temporary artifacts:

- PRDs
- implementation plans
- refactor plans
- temporary test plans
- migration notes

Temporary artifacts should live under `docs/workflow/` while active.

Temporary artifacts may be deleted after the feature/change is implemented, as long as their durable value has been transferred into specs, tests, user docs, or ADRs.

Do not preserve documents only for process reasons.

## Build, test, and development commands

- `make install`: install Python dependencies with Poetry.
- `make serve`: run the local Django development server.
- `make migrate`: apply database migrations.
- `make makemigrations`: create migrations after model changes.
- `make test`: run the pytest suite with the configured Django settings.
- `make test-core`, `make test-surveys`, `make test-accounts`, `make test-responses`: run focused test groups.
- `npm run build:css` / `npm run watch:css`: compile Tailwind CSS once or in watch mode.
- `npm run build:js` / `npm run watch:js`: compile browser TypeScript.

Survey-building commands include `make survey`, `make question-templates`, `make question`, `make choices`, and `make sections`.

## Coding style

Use Python 3.13 and existing Django conventions: modules use snake_case, classes use PascalCase, and tests use `test_*` names. Keep views, models, forms, and management commands inside their owning app.

Run `make lint` before committing when feasible; Ruff checks `E`, `F`, and import ordering, ignores line length, and excludes migrations and URL modules. Run `make fmt` for Ruff formatting.

## Frontend script rules

Do not add inline JavaScript to templates. Put browser behavior in `static/ts/*.ts`, run `npm run build:js`, and load the compiled file from `static/js/*.js` with `{% static %}`. Commit both the TypeScript source and compiled JavaScript when behavior changes.

## Testing rules

- Tests should describe observable behavior and contracts.
- Prefer API, view, service, model, serializer/form, permission, and integration tests over private-method tests.
- Avoid tests that only execute code for coverage.
- Avoid over-mocking internal implementation details.
- Mock external systems at the boundary.
- Characterization tests are allowed for legacy behavior, but label them clearly.
- Do not modify tests during refactoring unless the spec changes first.
- Do not delete legacy tests until their useful behavior has been replaced by better tests.
- Prefer behavior-focused tests over coverage-driven tests.
- Do not chase 100% coverage.

Pytest is configured in `pyproject.toml` with `DJANGO_SETTINGS_MODULE=config.settings`, `--reuse-db`, `-x`, and short tracebacks. Add tests next to the app being changed, preferably under `apps/<app>/tests/test_*.py`. Cover model behavior, permissions, workflows, and view responses for user-facing flows. Use focused `make test-<app>` commands during development, then `make test` before opening a PR.

## Refactoring rules

- During characterization and test-writing phases, do not modify production code.
- During refactoring phases, do not modify tests unless explicitly instructed.
- Refactors must preserve externally observable behavior unless a spec update explicitly changes behavior.
- Remove legacy packages only after tests pass and the removal is justified.

## Documentation rules

- Keep user-facing docs under `docs/user/`.
- Keep current functional specs under `docs/specs/`.
- Keep meaningful ADRs under `docs/adr/`.
- Keep temporary workflow artifacts under `docs/workflow/`.
- Do not create permanent PRD, product, testing-plan, or refactor-plan directories unless explicitly instructed.
- Delete temporary workflow documents after completion when their durable value has been transferred elsewhere.

## Dependency rules

Ask before adding new production or test dependencies.

## Suggested Codex skill usage

- Use `$prd-writer` before meaningful product changes when product intent is unclear.
- Use `$spec-writer` to turn PRDs, feature ideas, or existing behavior into durable specs.
- Use `$test-plan-writer` before writing tests when the required test coverage is not obvious.
- Use `$characterization-test-writer` before refactoring legacy behavior.
- Use `$behavior-test-writer` for intended behavior tests.
- Use `$test-first-implementation` to implement after tests exist.
- Use `$refactor-under-tests` for implementation-only refactors.

## Commit and pull request guidelines

Keep commits scoped with short imperative or descriptive summaries. PRs should include a concise description, affected apps, migration notes, commands run, linked issues, and screenshots for UI changes.

## Security and configuration

Do not commit secrets, local databases, or environment-specific settings. Database access is PostgreSQL-backed; keep local credentials in environment files loaded by `python-dotenv`. Review auth and role changes carefully, especially in `apps/accounts` and employee survey views.

## Completion criteria

Before declaring work complete:

- Summarize files changed.
- State whether production code was modified.
- State whether tests were modified.
- State the test command used.
- Report test results.
- List unresolved TODOs or assumptions.
