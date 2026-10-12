# Platform Setup

This guide takes a fresh machine to a running SOFIA-S instance with one operator account that can log in. It is the technical half of getting a client onto the platform; the operator half — creating a company, adding its users and assigning the survey — is [`user-onboarding.md`](user-onboarding.md).

The commands assume Ubuntu/Debian. Run every `python manage.py` command from the project root with the virtualenv active (`source .venv/bin/activate`), or prefix it with `poetry run`.

## 1. Install system packages

| Package | Why |
|---|---|
| Python 3.13 | The project pins 3.13 (`.python-version`, `pyproject.toml`). |
| Poetry 2.x | Installs the Python dependencies. |
| PostgreSQL 17, built with ICU | The database. Spanish-text columns use the `es-MX-x-icu` collation, so `migrate` fails on a server without ICU. The standard PGDG and Ubuntu packages include it. |
| Pango | WeasyPrint renders the report PDF with it. Without it everything works except the PDF download, which fails with a server error. |
| Node.js 20 or newer | **Optional.** The compiled CSS and JavaScript are committed, so the platform runs without Node. You only need it to rebuild them after editing templates or `static/ts/`. |

```bash
sudo apt install -y postgresql-17
sudo apt install -y libpango-1.0-0 libpangoft2-1.0-0 libharfbuzz-subset0

sudo systemctl start postgresql
sudo systemctl enable postgresql
```

Confirm the ICU collation exists:

```bash
sudo -u postgres psql -c "select 1 from pg_collation where collname = 'es-MX-x-icu'"
```

It must return one row.

## 2. Create the database

```bash
sudo -u postgres psql -c "CREATE USER sofias WITH PASSWORD 'sofias';"
sudo -u postgres psql -c "CREATE DATABASE sofias OWNER sofias;"
```

Choose a real password for anything other than a local machine; step 4 has to repeat it.

If you will run the test suite against this server, also let the user create the throwaway test database:

```bash
sudo -u postgres psql -c "ALTER USER sofias CREATEDB;"
```

## 3. Get the code and install Python dependencies

```bash
git clone <repository-url> sofias
cd sofias
poetry install
source .venv/bin/activate
```

`poetry.lock` is not committed, so `poetry install` resolves the dependencies fresh.

## 4. Configure `.env`

Settings are read from `.env` at the project root. Start from the example:

```bash
cp .env.example .env
```

Then edit it. `SECRET_KEY` and `DB_PASSWORD` have no default: if either is missing or empty, every `manage.py` command stops with an error naming it.

| Variable | What to set |
|---|---|
| `SECRET_KEY` | **Required.** A long random string. Generate one with `python -c "import secrets; print(secrets.token_urlsafe(50))"`. |
| `DEBUG` | `True` on a development machine, `False` anywhere real users connect. |
| `ALLOWED_HOSTS` | Comma-separated hostnames/IPs the server answers to. Required when `DEBUG=False`. To reach a development server from another device, add this machine's LAN IP. |
| `DB_PASSWORD` | **Required.** The password from step 2. The example's value is a placeholder — replace it, or the connection fails. |
| `DB_NAME`, `DB_USER`, `DB_HOST`, `DB_PORT` | The database from step 2. They default to `sofias`, `sofias`, `localhost` and `5432`. |
| `EMAIL_BACKEND` | `django.core.mail.backends.console.EmailBackend` prints every email to the terminal running the server. `django.core.mail.backends.smtp.EmailBackend` sends real email. |
| `EMAIL_HOST`, `EMAIL_PORT`, `EMAIL_USE_TLS`, `EMAIL_HOST_USER`, `EMAIL_HOST_PASSWORD` | The SMTP server, used only with the SMTP backend. `EMAIL_USE_TLS` accepts `True` or `1`. |
| `DEFAULT_FROM_EMAIL` | The sender address on login codes. |
| `OTP_EXPIRY_MINUTES` | How long a login code stays valid. Default `10`. |

**Email is how people log in.** The normal login sends a 6-digit code by email, so a server whose email does not reach its users is a server nobody can log into. On a development machine the console backend is enough: the code appears in the `runserver` terminal, and while `DEBUG=True` the code `000000` also logs in any existing user. Anywhere else, configure SMTP and send yourself a code before onboarding a client.

## 5. Initialize the database

Run these three commands, in this order:

```bash
python manage.py migrate
python manage.py bootstrap_groups
python manage.py seed_nom035_survey
```

- `migrate` creates the tables. It also gives the permissions their Spanish names.
- `bootstrap_groups` creates the four role groups — `Admins`, `Principal Exec`, `Secondary Exec`, `Employees` — and their permissions. It needs `migrate` to have run first.
- `seed_nom035_survey` loads the NOM-035 questionnaire. Without it there is no survey to assign to a company.

Both commands are safe to run again; they bring the groups and the survey back to their defined state.

## 6. Create the operator account

```bash
python manage.py createsuperuser
```

It asks for a username, an email and a password.

- **Type the email in lowercase.** The public login looks people up by their lowercased email, so `Ana@Empresa.com` would never match.
- The username is only used to sign in to the administration panel.

Then put that account in the `Admins` group:

1. Run the server (step 7) and sign in at `/admin/` with the username and password.
2. Go to **Cuentas → Usuarios** and open your account.
3. Under **Permisos → Grupos**, add **Admins** and save.

Without the group, the public login sends a superuser to the profile-activation page, which tells them their account has no company — operators do not belong to a company. With it, they land on the company list.

## 7. Run the server and check it works

```bash
python manage.py runserver
```

Or `make serve`. To reach it from another device on the network, use `make serve-lan` (port 8000 on all interfaces) and add the machine's LAN IP to `ALLOWED_HOSTS`.

Check:

- [ ] `http://localhost:8000/admin/` accepts the username and password.
- [ ] **Encuestas → Encuestas** in the admin lists *Encuesta NOM-035*.
- [ ] **Autenticación y Autorización → Grupos** lists the four groups.
- [ ] `http://localhost:8000/cuentas/ingresar/` accepts your email, the code arrives (in the terminal, with the console backend), and after entering it you land on **Empresas** (`/empresas/`).

The platform is ready. Continue with [`user-onboarding.md`](user-onboarding.md) to set up the first client.

## Before real users connect

The steps above produce a working development server. A server that clients reach also needs:

- `DEBUG=False`, a fresh `SECRET_KEY`, and `ALLOWED_HOSTS` naming the public hostname.
- SMTP email that delivers to the client's domain (step 4).
- Something that serves static files. `runserver` stops serving `static/` when `DEBUG=False`, and the settings define no `STATIC_ROOT` for `collectstatic`, so the deployment has to provide one.

## Optional: rebuild assets and run the tests

Only needed when you change the code:

```bash
npm ci
npm run build:css   # after editing templates or anything with Tailwind classes
npm run build:js    # after editing static/ts/*.ts

pytest              # needs the CREATEDB grant from step 2
```
