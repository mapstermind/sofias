# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

SOFIA-S is a Django 6.0 web application for survey processing and reporting. It handles survey creation, response collection, data processing, and dynamic dashboard/report generation — built around the Mexican NOM-035 psychosocial-risk questionnaire. Frontend uses Django templates with TailwindCSS. **User-facing copy and URLs are in Spanish; code, comments, and identifiers are in English.**

## Tech Stack

- **Python 3.13** (managed via Poetry)
- **Django 6.0** with settings at `config/settings.py`
- **Database**: PostgreSQL 17 (via `psycopg` 3.x driver)
- **Frontend**: TailwindCSS (TypeScript toolchain present via `package.json`)
- **Dev tools**: ruff (linter/formatter), pytest + pytest-django (testing)

## PostgreSQL Setup

```bash
# Install PostgreSQL 17 (Ubuntu/Debian)
sudo apt install -y postgresql-17

# Start the service
sudo systemctl start postgresql
sudo systemctl enable postgresql

# Create database and user
sudo -u postgres psql -c "CREATE USER sofias WITH PASSWORD 'sofias';"
sudo -u postgres psql -c "CREATE DATABASE sofias OWNER sofias;"
```

## Environment Variables

Configuration is loaded from `.env` at the project root via `python-dotenv`. Key variables:
- `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_HOST`, `DB_PORT` (all default to `sofias`/`localhost`/`5432`)
- `SECRET_KEY`
- `DEBUG` (default: `True`)
- `ALLOWED_HOSTS` (comma-separated, default: empty)

## Common Commands

```bash
# Activate virtualenv
source .venv/bin/activate

# Install dependencies (includes psycopg PostgreSQL driver)
poetry install

# Run dev server
python manage.py runserver

# Run all tests
pytest

# Run a single test file
pytest apps/surveys/tests/test_models.py

# Run a single test
pytest apps/surveys/tests/test_models.py::TestClassName::test_method_name

# Formatting
ruff format .

# Linting
ruff check .

# Django migrations
python manage.py makemigrations
python manage.py migrate
```

## Architecture

```
config/          # Django project config (settings, urls, wsgi, asgi)
templates/       # Project-level Django templates (Spanish UI, TailwindCSS)
docs/            # platform/ (feature & system docs), adr/ (architectural decisions), internal/ (operator guides) — read these for design intent
apps/            # Django apps; each app has its own CLAUDE.md with details
  accounts/      # Users, OTP/auth, companies, roles/permissions, CSV import  → apps/accounts/CLAUDE.md
  surveys/       # Survey authoring model (templates→versions→questions) + taking  → apps/surveys/CLAUDE.md
  responses/     # SurveySubmission + Answer storage  → apps/responses/CLAUDE.md
  core/          # Home/dashboards + interactive survey-authoring CLI/commands  → apps/core/CLAUDE.md
  analytics/     # Placeholder, not yet implemented  → apps/analytics/CLAUDE.md
  reports/       # Placeholder, not yet implemented  → apps/reports/CLAUDE.md
```

**When working inside an app, read that app's `CLAUDE.md` first** — it holds the model/flow details not repeated here.

- **Settings module**: `config.settings` (referenced in `manage.py`).
- **Root URL conf**: `config.urls` — wires `admin/`, `core` at `/`, `accounts` at `/cuentas/`, `surveys` at `/encuestas/`.
- **Registered apps** (in `INSTALLED_APPS`): `apps.accounts`, `apps.core`, `apps.surveys`, `apps.responses`. These use fully-qualified `AppConfig.name = "apps.<x>"` with an explicit short `label`. `analytics` and `reports` are **empty stubs, not registered**, and still use bare `AppConfig.name`s — register them before use (see their CLAUDE.md).

## Cross-cutting concepts

- **Custom user model**: `AUTH_USER_MODEL = "accounts.User"`; login is by **email**, primarily via passwordless OTP. See `apps/accounts`.
- **Authorization**: custom permissions are declared on the unmanaged `accounts.Role` model and bundled into four groups (Admins / Principal Exec / Secondary Exec / Employees) by `python manage.py bootstrap_groups` (run this after migrating). Views authorize on permission codenames (e.g. `can_view_dashboard`). Tests get the groups via the `bootstrap_groups` fixture in `conftest.py`.
- **Survey data flow**: library `QuestionTemplate`s are *stamped* into a `SurveyVersion` as independent `Question`s → a `SurveyAssignment` exposes a version to a `Company` → employees submit via `apps/surveys` views → answers persist as `responses.Answer` (JSON value typed by question type) → `apps/core` renders dashboards/progress.
- **Testing**: pytest + pytest-django, settings `config.settings`. Tests live in each app's `tests/` package; shared fixtures (users, companies, survey chains, groups) are in the root `conftest.py`. `addopts` use `--reuse-db -x`.
