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

The server must be built with **ICU** (the standard PGDG/Ubuntu packages are): the
Spanish-text columns declare the `es-MX-x-icu` collation, so migrations fail without
it. Check with `psql -c "select 1 from pg_collation where collname = 'es-MX-x-icu'"`.

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

Tailwind compiles **only the classes it finds in the sources listed in `static/css/main.css`**, and `static/css/output.css` is committed. A template edit that introduces a class not already used somewhere else (e.g. `max-w-6xl`, `w-96`, `max-h-[45vh]`) renders **unstyled** until the CSS is rebuilt — the browser silently ignores the class, so this does not fail any test.

Automatic source detection is off (`@import "tailwindcss" source(none)`), so the `@source` lines in `main.css` are the complete list of places a class may live: `templates/`, `apps/**/*.py` (widget `attrs`), `static/ts/`, plus `@source inline(...)` for names only assembled at runtime. **Putting a class anywhere else compiles nothing** — add the location to `main.css` instead.

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

**Live documentation describes only the current implementation.** After a refactor, rewrite the affected docs as if the new implementation were always the original. Do **not** leave migration commentary behind — no "replaces the old X", "formerly Y", "superseded Z", "deprecated alias", "no longer supported", or before/after comparisons. A reader should not be able to tell from a live doc that a previous implementation ever existed.

This applies to everything an agent or developer reads as current truth: `docs/platform/`, `docs/internal/` (including `user-guides/`), every `CLAUDE.md`, and code comments and test names.

**The only two exceptions are `docs/adr/` and `docs/archive/`**, whose entire purpose is to record why an approach was abandoned — they must describe the superseded implementation, and are where that history belongs. Link to the ADR instead of restating the history inline. Database migrations are also necessarily historical and may reference removed fields.

**Never edit a file under `docs/adr/` without explicit approval.** When a change makes an ADR inaccurate, describe the discrepancy and the proposed wording, then wait — do not fold it into the change silently. An ADR carries the reasoning behind a decision, so an unreviewed edit can erase why an approach was rejected while looking like routine upkeep.

What may be corrected once approved is the **Consequences** section, and only where a consequence describes a downstream implementation detail that has since changed. Context, Decision, and Alternatives considered are frozen: they state what was true and what was weighed at the time, and stay that way even when the code moves on. If the decision itself no longer holds, that calls for a new ADR superseding this one, not a rewrite of it.

Rationale: the platform is pre-production, so there are no external consumers to warn about a transition. Migration notes in live docs are pure noise that ages badly and misleads readers into thinking a compatibility path exists.

- **Settings module**: `config.settings` (referenced in `manage.py`).
- **Root URL conf**: `config.urls` — wires `admin/`, `core` at `/`, `accounts` at `/cuentas/`, `surveys` at `/encuestas/`.
- **Registered apps** (in `INSTALLED_APPS`): `apps.accounts`, `apps.core`, `apps.surveys`, `apps.responses`, `apps.nom035`. These use fully-qualified `AppConfig.name = "apps.<x>"` with an explicit short `label`. `reports` is an **empty stub, not registered**, and still uses a bare `AppConfig.name` — register it before use (see its CLAUDE.md).

## Cross-cutting concepts

- **Custom user model**: `AUTH_USER_MODEL = "accounts.User"`; login is by **email**, primarily via passwordless OTP. See `apps/accounts`.
- **Authorization**: custom permissions are declared on the unmanaged `accounts.Role` model and bundled into four groups (Admins / Principal Exec / Secondary Exec / Employees) by `python manage.py bootstrap_groups` (run this after migrating). Views authorize on permission codenames (e.g. `can_view_dashboard`). Tests get the groups via the `bootstrap_groups` fixture in `conftest.py`.
- **Spanish UI, English code**: `LANGUAGE_CODE = "es-mx"` and `TIME_ZONE = "America/Mexico_City"` (storage stays UTC via `USE_TZ`). Django ships layer 1 — its own chrome, validation and date formats. Everything else an operator reads is metadata we write, so **every model field carries an explicit lowercase Spanish `verbose_name`, every model a Spanish `Meta.verbose_name`/`verbose_name_plural`, and every `TextChoices` a Spanish label** — without them Django derives the label from the English attribute name and leaks it onto the screen. Strings are hardcoded; there is no `gettext`, no `.po` files and no second language. `apps/core/permissions.py` rewrites the auto-generated `auth_permission` names, which Django builds from an untranslated template. `conftest.py`'s `assert_explicit_labels` fixture fails a build that forgets one. See `docs/platform/localization.md`.
- **Survey platform shape**: `apps/surveys` is the shared, instrument-agnostic authoring/structure base for **all** instruments (`Survey → Module → Question`, keyed by stable `key`/`code`); it holds no scoring. Each instrument's scoring/processing lives in its **own engine app** that depends on `surveys`/`responses` one-way via `Question.code` — never the reverse. Today the only instrument is NOM-035 (`apps/nom035`); its instrument definition is seeded from `apps/core` (`seed_nom035_survey`) and its results are currently presented in `apps/core` dashboards (with `apps/reports` reserved as a future reporting home). A second instrument would get its own engine app; a shared engine library is a later call if duplication warrants it. See `docs/platform/overview.md` and `docs/adr/adr-0003-per-instrument-survey-processing-apps.md`.
- **Survey data flow**: a fixed `Survey` owns `Module`s (`applies_to` all/small/large) of `Question`s → a `SurveyAssignment` exposes the survey to a `Company` with a frozen `variant` (by headcount) → employees submit the variant's modules via `apps/surveys` views (conditional `visible_when` branching) → answers persist as `responses.Answer` (JSON value typed by question type) → `apps/nom035` materializes scores on completion → `apps/core` renders dashboards/progress and the valuation panels. No question library or versions (see `docs/adr/adr-0002-flatten-survey-authoring-model.md`).
- **NOM-035 valuation source of truth**: [`docs/internal/Guias de Referencia.md`](docs/internal/Guias de Referencia.md) is the **single authoritative reference** for all NOM-035 scoring data — item scoring direction (which items score 0→4 vs 4→0), the Categoría/Dominio/Dimensión taxonomy, the threshold tables (Guía II and Guía III, per dominio/categoría/final), and the Guía I clinical-referral rule. The `apps/nom035` scoring constants must match it. If any **other** document (e.g. `docs/platform/nom-035-valoracion-supuestos.md`, the feature doc) conflicts with it, treat `Guias de Referencia.md` as correct and **flag the discrepancy for the domain expert** rather than silently diverging.
- **Testing**: pytest + pytest-django, settings `config.settings`. Tests live in each app's `tests/` package; shared fixtures (users, companies, survey chains, groups) are in the root `conftest.py`. `addopts` use `--reuse-db -x`.
