# Repository Guidelines

## Project Structure & Module Organization

SOFIA-S is a Django 6 survey and reporting application. Runtime configuration lives in `config/`, with feature apps under `apps/`: `accounts`, `core`, `surveys`, `responses`, `reports`, and `analytics`. Templates are in `templates/`. Static assets live in `static/`; edit Tailwind input in `static/css/main.css`, generated CSS in `static/css/output.css`, TypeScript in `static/ts/`, and compiled browser JavaScript in `static/js/`. Tests are colocated in app-level `tests/` packages or `tests.py`.

## Build, Test, and Development Commands

- `make install`: install Python dependencies with Poetry.
- `make serve`: run the local Django development server.
- `make migrate`: apply database migrations.
- `make makemigrations`: create migrations after model changes.
- `make test`: run the pytest suite with the configured Django settings.
- `make test-core`, `make test-surveys`, `make test-accounts`, `make test-responses`: run focused test groups.
- `npm run build:css` / `npm run watch:css`: compile Tailwind CSS once or in watch mode.
- `npm run build:js` / `npm run watch:js`: compile browser TypeScript.

Survey-building commands include `make survey`, `make question-templates`, `make question`, `make choices`, and `make sections`.

## Coding Style & Naming Conventions

Use Python 3.13 and existing Django conventions: modules use snake_case, classes use PascalCase, and tests use `test_*` names. Keep views, models, forms, and management commands inside their owning app. Run `make lint` before committing; Ruff checks `E`, `F`, and import ordering, ignores line length, and excludes migrations and URL modules. Run `make fmt` for Ruff formatting.

## Frontend Script Rules

Do not add inline JavaScript to templates. Put browser behavior in `static/ts/*.ts`, run `npm run build:js`, and load the compiled file from `static/js/*.js` with `{% static %}`. Commit both the TypeScript source and compiled JavaScript when behavior changes.

## Testing Guidelines

Pytest is configured in `pyproject.toml` with `DJANGO_SETTINGS_MODULE=config.settings`, `--reuse-db`, `-x`, and short tracebacks. Add tests next to the app being changed, preferably under `apps/<app>/tests/test_*.py`. Cover model behavior, permissions, workflows, and view responses for user-facing flows. Use focused `make test-<app>` commands during development, then `make test` before opening a PR.

## Commit & Pull Request Guidelines

Recent commits use short, imperative or descriptive summaries, for example `Added employee detail view + relevant tests` or `Autosave form feature + fmt`. Keep commits scoped and mention tests or formatting when relevant. PRs should include a concise description, affected apps, migration notes, commands run, linked issues, and screenshots for UI changes.

## Security & Configuration Tips

Do not commit secrets, local databases, or environment-specific settings. Database access is PostgreSQL-backed; keep local credentials in environment files loaded by `python-dotenv`. Review auth and role changes carefully, especially in `apps/accounts` and employee survey views.
