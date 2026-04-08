# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

SOFIA-S is a Django 6.0 web application for survey processing and reporting. It handles survey creation, response collection, data processing, and dynamic dashboard/report generation. Frontend uses Django templates with TailwindCSS.

## Tech Stack

- **Python 3.13** (managed via Poetry)
- **Django 6.0** with settings at `config/settings.py`
- **Database**: PostgreSQL 17 (via `psycopg` 3.x driver)
- **Frontend**: TailwindCSS (TypeScript toolchain present via `package.json`)
- **Dev tools**: black (formatter), ruff (linter), pytest + pytest-django (testing)

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
pytest apps/surveys/tests.py

# Run a single test
pytest apps/surveys/tests.py::TestClassName::test_method_name

# Formatting
black .

# Linting
ruff check .

# Django migrations
python manage.py makemigrations
python manage.py migrate
```

## Architecture

```
config/          # Django project config (settings, urls, wsgi, asgi)
apps/            # Django apps, each with standard structure (models, views, admin, tests, migrations)
  core/          # Shared/base functionality
  surveys/       # Survey form creation and management
  responses/     # Response collection and storage
  analytics/     # Data processing and aggregation
  reports/       # Dashboard and report generation
```

- **Settings module**: `config.settings` (referenced in `manage.py`)
- **Root URL conf**: `config.urls` — currently only admin is wired up
- Apps are in `apps/` directory but their `AppConfig.name` uses bare names (e.g., `name = "surveys"` not `apps.surveys`) — note that apps are not yet registered in `INSTALLED_APPS`
