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

# Frontend assets (Tailwind CSS / TypeScript → static/)
npm run build:css     # static/css/main.css  → static/css/output.css
npm run build:js      # static/ts/*.ts       → static/js/
```

## Frontend build — always run it

Tailwind compiles **only the classes it finds in the templates**, and `static/css/output.css` is committed. A template edit that introduces a class not already used somewhere else (e.g. `max-w-6xl`, `w-96`, `max-h-[45vh]`) renders **unstyled** until the CSS is rebuilt — the browser silently ignores the class, so this does not fail any test.

**As the final step of any change touching `templates/` or `static/`, run the matching build and commit the regenerated output:**
- Touched a template or any file with Tailwind classes → `npm run build:css`
- Touched `static/ts/*.ts` → `npm run build:js`

Do not assume a `watch:css`/`watch:js` process is running.

## Architecture

```
config/          # Django project config (settings, urls, wsgi, asgi)
templates/       # Project-level Django templates (Spanish UI, TailwindCSS)
docs/            # platform/ (feature & system docs), adr/ (architectural decisions), internal/ (operator guides) — read these for design intent
apps/            # Django apps; each app has its own CLAUDE.md with details
  accounts/      # Users, OTP/auth, companies, roles/permissions, CSV import  → apps/accounts/CLAUDE.md
  surveys/       # Survey instrument model (Survey→Module→Question) + taking  → apps/surveys/CLAUDE.md
  responses/     # SurveySubmission + Answer storage  → apps/responses/CLAUDE.md
  core/          # Home/dashboards + NOM-035 seed command  → apps/core/CLAUDE.md
  nom035/        # NOM-035 valuation engine (scores → NDR) + Insights  → apps/nom035/CLAUDE.md
  reports/       # Placeholder, not yet implemented  → apps/reports/CLAUDE.md
```

**When working inside an app, read that app's `CLAUDE.md` first** — it holds the model/flow details not repeated here.

**Feature docs live in `docs/platform/`.** This project is documentation-driven (see `docs/internal/prompting-workflow.md`): the per-feature doc `docs/platform/<feature>.md` is the source of truth, and its derived implementation plan is `docs/platform/<feature>-tasks.md`. When a skill (brainstorming, writing-plans, etc.) produces or rewrites either artifact, write it under `docs/platform/` — never under `docs/superpowers/`, a `specs/` folder, or a scratch path.

- **Settings module**: `config.settings` (referenced in `manage.py`).
- **Root URL conf**: `config.urls` — wires `admin/`, `core` at `/`, `accounts` at `/cuentas/`, `surveys` at `/encuestas/`.
- **Registered apps** (in `INSTALLED_APPS`): `apps.accounts`, `apps.core`, `apps.surveys`, `apps.responses`, `apps.nom035`. These use fully-qualified `AppConfig.name = "apps.<x>"` with an explicit short `label`. `reports` is an **empty stub, not registered**, and still uses a bare `AppConfig.name` — register it before use (see its CLAUDE.md).

## Cross-cutting concepts

- **Custom user model**: `AUTH_USER_MODEL = "accounts.User"`; login is by **email**, primarily via passwordless OTP. See `apps/accounts`.
- **Authorization**: custom permissions are declared on the unmanaged `accounts.Role` model and bundled into four groups (Admins / Principal Exec / Secondary Exec / Employees) by `python manage.py bootstrap_groups` (run this after migrating). Views authorize on permission codenames (e.g. `can_view_dashboard`). Tests get the groups via the `bootstrap_groups` fixture in `conftest.py`.
- **Survey platform shape**: `apps/surveys` is the shared, instrument-agnostic authoring/structure base for **all** instruments (`Survey → Module → Question`, keyed by stable `key`/`code`); it holds no scoring. Each instrument's scoring/processing lives in its **own engine app** that depends on `surveys`/`responses` one-way via `Question.code` — never the reverse. Today the only instrument is NOM-035 (`apps/nom035`); its instrument definition is seeded from `apps/core` (`seed_nom035_survey`) and its results are currently presented in `apps/core` dashboards (with `apps/reports` reserved as a future reporting home). A second instrument would get its own engine app; a shared engine library is a later call if duplication warrants it. See `docs/platform/overview.md` and `docs/adr/adr-0003-per-instrument-survey-processing-apps.md`.
- **Survey data flow**: a fixed `Survey` owns `Module`s (`applies_to` all/small/large) of `Question`s → a `SurveyAssignment` exposes the survey to a `Company` with a frozen `variant` (by headcount) → employees submit the variant's modules via `apps/surveys` views (conditional `visible_when` branching) → answers persist as `responses.Answer` (JSON value typed by question type) → `apps/nom035` materializes scores on completion → `apps/core` renders dashboards/progress and the valuation panels. No question library or versions (see `docs/adr/adr-0002-flatten-survey-authoring-model.md`).
- **NOM-035 valuation source of truth**: [`docs/internal/Guias de Referencia.md`](docs/internal/Guias de Referencia.md) is the **single authoritative reference** for all NOM-035 scoring data — item scoring direction (which items score 0→4 vs 4→0), the Categoría/Dominio/Dimensión taxonomy, the threshold tables (Guía II and Guía III, per dominio/categoría/final), and the Guía I clinical-referral rule. The `apps/nom035` scoring constants must match it. If any **other** document (e.g. `docs/platform/nom-035-valoracion-supuestos.md`, the feature doc) conflicts with it, treat `Guias de Referencia.md` as correct and **flag the discrepancy for the domain expert** rather than silently diverging.
- **Testing**: pytest + pytest-django, settings `config.settings`. Tests live in each app's `tests/` package; shared fixtures (users, companies, survey chains, groups) are in the root `conftest.py`. `addopts` use `--reuse-db -x`.
