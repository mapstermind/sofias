# SOFIA-S

SOFIA-S (Sistema de Obtención, Filtrado e Inteligencia Analítica de Sondeos) is a Django web application for creating surveys, collecting responses, and tracking completion across companies. It is built around the Mexican NOM-035 psychosocial-risk questionnaire, which ships as seed data.

The user-facing interface (copy and URLs) is in Spanish. Code, comments, and identifiers are in English.

## What it does today

- **Survey authoring** — a reusable question/choice library whose templates are "stamped" into versioned surveys. Authoring happens through interactive terminal commands and the Django admin.
- **Survey assignment** — a survey version is assigned to a company, making it available to that company's employees.
- **Survey taking** — employees answer assigned surveys in the browser, with autosave and resume of in-progress submissions. Answers are stored as JSON values typed by question type.
- **Dashboards** — per-company completion stats (registration rate, completion rate per survey, representative-sample minimum) and per-employee progress/answer views, gated by role permissions.
- **User onboarding** — passwordless email-OTP login (with password and one-time setup-access-code fallbacks), company reference-code activation, and bulk user import from CSV via the admin.

NOM-035 valuation (scores → Nivel de Riesgo, plus the Guía I referral flag) is implemented in `apps/nom035` and surfaced as text-only insights in the dashboards. Report generation (`apps/reports`) is still a placeholder — an empty app, not yet registered in `INSTALLED_APPS`.

## Tech stack

- Python 3.13, Django 6.0 (dependencies managed with Poetry)
- PostgreSQL 17 (`psycopg` 3 driver)
- Django templates + TailwindCSS 4; small TypeScript helpers compiled to plain JS
- ruff (lint/format), pytest + pytest-django (tests)

## Project layout

```
config/          # Django settings, root urls, wsgi/asgi
apps/
  accounts/      # Custom user, OTP/password/setup-code auth, companies, roles, CSV import
  surveys/       # Question library, survey templates/versions/questions, survey taking
  responses/     # SurveySubmission + Answer storage
  core/          # Home/dashboards + interactive survey-authoring commands
  nom035/        # NOM-035 valuation engine (scores → NDR) + Insights
  reports/       # Placeholder (not registered)
templates/       # Django templates (Spanish UI)
static/          # CSS (Tailwind input/output), TS sources, compiled JS
docs/            # Specs and human-facing docs
```

Each app has its own `CLAUDE.md` with model and flow details.

## Setup

1. **PostgreSQL** — create the database and user:

   ```bash
   sudo -u postgres psql -c "CREATE USER sofias WITH PASSWORD 'sofias';"
   sudo -u postgres psql -c "CREATE DATABASE sofias OWNER sofias;"
   ```

2. **Environment** — configuration is read from `.env` at the project root. All variables have development defaults; the main ones are `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_HOST`, `DB_PORT`, `SECRET_KEY`, `DEBUG`, `ALLOWED_HOSTS`, and the email settings (`EMAIL_*`). With no `.env`, OTP emails print to the console.

3. **Install and migrate:**

   ```bash
   poetry install
   python manage.py migrate
   python manage.py bootstrap_groups   # creates the four permission groups
   ```

4. **Seed survey content (optional):**

   ```bash
   python manage.py seed_likert_templates       # Likert question library
   python manage.py seed_demographic_templates  # demographic question library
   python manage.py seed_nom035_survey          # NOM-035 survey built from the library
   ```

   Run the two library seeds first — `seed_nom035_survey` links its questions to existing library templates.

5. **Run:**

   ```bash
   python manage.py runserver
   ```

## Common commands

Most tasks have a `make` target (see the `Makefile`):

```bash
make serve              # run the dev server
make test               # run all tests
make lint               # ruff check --fix
make fmt                # ruff format
make migrate            # apply migrations
make bootstrap-groups   # create/re-sync permission groups
```

Interactive survey authoring (terminal workflows over the surveys models):

```bash
make question-templates # manage the reusable question library
make survey             # create a survey + first version
make question           # add questions to a version
make choices            # manage choices on a question
make sections           # group questions into sections
```

Frontend assets:

```bash
npm run build:css       # compile Tailwind (static/css/main.css → output.css)
npm run build:js        # compile TypeScript (static/ts → static/js)
npm run watch:css       # ...or watch variants
npm run watch:js
```

## Authentication and roles

Login is by email. The primary flow is a 6-digit OTP sent by email; fallbacks exist for password login and one-time 9-digit setup access codes (for users whose email cannot receive external mail). In `DEBUG`, code `000000` logs in any existing user.

Authorization uses custom permissions (declared on `accounts.Role`) bundled into four groups created by `bootstrap_groups`: **Admins**, **Principal Exec**, **Secondary Exec**, and **Employees**. Views check permission codenames such as `can_view_dashboard` and `can_take_assigned_surveys`.

## Testing

```bash
pytest                                          # all tests
pytest apps/surveys/tests/test_models.py        # one file
pytest apps/surveys/tests/test_models.py::TestX # one test class/function
```

Tests live in each app's `tests/` package; shared fixtures are in the root `conftest.py`.
