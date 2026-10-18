# SOFIA-S

SOFIA-S (Sistema de Obtención, Filtrado e Inteligencia Analítica de Sondeos) is a Django web application for creating surveys, collecting responses, and tracking completion across companies. It is built around the Mexican NOM-035 psychosocial-risk questionnaire, which ships as seed data.

The user-facing interface (copy and URLs) is in Spanish. Code, comments, and identifiers are in English.

## What it does today

- **Surveys** — a fixed instrument as a `Survey → Module → Question` tree, keyed by stable codes. The NOM-035 survey is seeded by `seed_nom035_survey`; the Django admin shows it for inspection.
- **Survey assignment** — a survey is assigned to a company with a variant fixed by headcount, making it available to that company's employees.
- **Survey taking** — employees answer assigned surveys in the browser, with autosave and resume of in-progress submissions. Answers are stored as JSON values typed by question type.
- **Dashboards** — per-company completion stats (registration rate, completion rate per survey, representative-sample minimum) and per-employee progress/answer views, gated by role permissions.
- **User onboarding** — passwordless email-OTP login (with password and one-time setup-access-code fallbacks), activation with the company code, and bulk user import from CSV via the admin.
- **NOM-035 results** — valuation (scores → Nivel de Riesgo, plus the Guía I referral flag) in `apps/nom035`, shown on a filterable results page with SVG charts and on each colaborador's detail page.
- **Results report** — a formal NOM-035 report per closed assignment, drafted, published and read by an Administrador and downloadable as a PDF (`apps/reports`).

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
  surveys/       # Survey → Module → Question, assignments, survey taking
  responses/     # SurveySubmission + Answer storage
  core/          # Home, dashboards, roster, results page, design system + NOM-035 seed command
  nom035/        # NOM-035 valuation engine (scores → NDR) + results-page data
  reports/       # NOM-035 results report: draft/publish, snapshot, PDF
templates/       # Django templates (Spanish UI)
static/          # CSS (Tailwind input/output), TS sources, compiled JS
docs/            # platform/ (feature docs), adr/, internal/ (operator guides)
```

Each app has its own `CLAUDE.md` with model and flow details.

## Setup

Needs Python 3.13, Poetry 2.x, PostgreSQL 17 built with ICU, and Pango (for the report PDF).
The full walkthrough — packages, `.env` variables, email, checks — is
[`docs/internal/user-guides/platform-setup.md`](docs/internal/user-guides/platform-setup.md).

```bash
sudo -u postgres psql -c "CREATE USER sofias WITH PASSWORD 'sofias';"
sudo -u postgres psql -c "CREATE DATABASE sofias OWNER sofias;"

cp .env.example .env              # then set DB_PASSWORD to the password above
poetry install && source .venv/bin/activate

python manage.py migrate
python manage.py bootstrap_groups     # the four role groups
python manage.py seed_nom035_survey   # the NOM-035 questionnaire
python manage.py createsuperuser      # use a lowercase email
python manage.py runserver
```

Then sign in at `/admin/` and add your superuser to the **Admins** group
(Cuentas → Usuarios → Grupos). To onboard a client company, follow
[`docs/internal/user-guides/user-onboarding.md`](docs/internal/user-guides/user-onboarding.md).

## Common commands

Most tasks have a `make` target (see the `Makefile`):

```bash
make serve              # run the dev server
make serve-lan          # run it on 0.0.0.0:8000 so another computer can reach it
make test               # run all tests
make lint               # ruff check --fix
make fmt                # ruff format
make migrate            # apply migrations
make bootstrap-groups   # create/re-sync permission groups
```

Frontend assets:

```bash
npm run build:css       # compile Tailwind (static/css/main.css → output.css)
npm run build:js        # compile TypeScript (static/ts → static/js)
npm run watch:css       # ...or watch variants (unminified; run build:css before committing)
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
