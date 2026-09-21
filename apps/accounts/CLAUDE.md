# accounts

Identity, authentication, authorization, and company/employee onboarding. Defines the custom user model and is the source of truth for who can do what. URL prefix: `/cuentas/` (`app_name = "accounts"`).

## Responsibilities

- **Custom user model** (`AUTH_USER_MODEL = "accounts.User"`) — extends `AbstractUser`, adds unique `email` and `must_change_password`.
- **Passwordless login via email OTP** — the primary login flow.
- **Fallback logins** — username/password and one-time "setup access codes" for users whose email cannot receive external OTP mail (see `docs/adr/adr-0001-setup-access-codes-for-blocked-email-login.md`).
- **Companies & profiles** — `Company` (with auto-generated 5-char `reference_code`) and `UserProfile` (links a user to a company, tracks activation).
- **Roles/permissions** — custom permissions + the groups that hold them.
- **Bulk user provisioning** — CSV import wired into Django admin.

## Models (`models.py`)

- `User` — custom user; login is by email, not username (`username` is auto-derived, see
  `utils.generate_unique_username`). A name is three fields —
  `first_name`/`paternal_last_name`/`maternal_last_name` — because the two surnames of a
  Mexican name are not interchangeable and the roster sorts on the paternal one.
  `get_full_name()` joins whichever are set, and `get_initials()` takes the first letter
  of the nombre and of the apellido paterno, so an avatar and a heading cannot disagree. See
  `docs/adr/adr-0005-two-surname-names-and-profile-demographics.md`.
- `Company` — `reference_code` is generated in `save()` if blank; used by employees to self-activate.
- `CompanyArea` / `CompanyLocation` — per-company catalogs (áreas, localidades) sharing
  the abstract `CompanyCatalogEntry` base (`name`, `is_active`). Unique per company via
  `UniqueConstraint(company, FoldCatalogName("name"))`, which folds case, Spanish vowel
  accents and whitespace runs into one key — `ñ` is left alone, being a letter rather
  than an accent. `catalog_name_key()` is the Python mirror of that fold and is what the
  admin inline formset dedupes on, so the two layers cannot disagree; `clean()`
  normalizes whitespace via `normalize_catalog_name()`. Curated **only** as
  inlines on `CompanyAdmin` (no standalone `ModelAdmin`), and offered to the employee as
  pickers at activation. Retire with `is_active=False` rather than deleting. See
  `docs/adr/adr-0004-per-company-area-and-locality-catalogs.md`.
- `UserProfile` — OneToOne with `User`; `is_activated` gates app access; FK to `Company`;
  free-text `position` (cargo); `sex` (`male`/`female`, labelled Masculino/Femenino);
  `date_of_birth`; `area` and `location` FKs (both `SET_NULL`, nullable). The cargo, sexo,
  fecha de nacimiento, área and localidad — along with the three `User` name fields — are
  all supplied by the employee at activation, not at import. `area` drives
  `apps/nom035`'s per-área company aggregation — a null área falls into a "Sin área"
  bucket. `age` is a **property** over `date_of_birth` and `timezone.localdate()`, never a
  column, so it cannot go stale. `clean()` rejects an área/localidad belonging to a
  different company, and a `date_of_birth` outside the
  `MIN_ACTIVATION_AGE`/`MAX_ACTIVATION_AGE` (15-99) working-age window — a future date
  fails on the lower bound.
- `EmailOTP` — 6-digit code keyed by **email string, not a User FK** (the user may not exist yet). Self-sets `expires_at` from `OTP_EXPIRY_MINUTES` (default 10).
- `SetupAccessCode` — one-time first-login code; partial unique constraints enforce "one active code globally" and "one unused code per user". `mark_used()` nulls the code.
- `Role` — **sentinel model, `managed = False`** (no DB table). Exists only to declare the project's custom permissions in `auth_permission`. The permission codenames it defines (e.g. `can_view_dashboard`, `can_manage_surveys`) are checked throughout `apps/core`.

## Authorization model

Permissions are defined on `Role.Meta.permissions`; groups that bundle them are created by `python manage.py bootstrap_groups` (idempotent). The four groups: **Admins, Principal Exec, Secondary Exec, Employees**.

`roles.py` is where those four live — each one's `auth.Group.name` (the stored lookup key, English), its Spanish display label (*Administrador*, *Ejecutivo principal*, *Ejecutivo secundario*, *Empleado*), its URL slug (`administrador`, `ejecutivo-principal`, `ejecutivo-secundario`, `empleado`) and their display order, most authority first. Import `ROLES`, `ROLE_NAMES`, `label_for_name()` or `labels_for_names()` from there rather than retyping a name; anything a user reads goes through a label, never through the stored name. Renaming the stored names is open finding #1.

When adding a permission, update **both** `Role.Meta.permissions` and `bootstrap_groups.GROUP_PERMISSIONS` — two places, not three: the `bootstrap_groups` fixture in `conftest.py` imports `GROUP_PERMISSIONS` rather than restating it, so tests follow automatically.

## Key files

- `roles.py` — the four authorization groups declared once: stored name, Spanish label, URL slug, display order.
- `backends.py` — `EmailOTPBackend`: a near-empty backend; OTP validation happens in the view, the backend exists only so `login()` can record it. `ModelBackend` stays first in `AUTHENTICATION_BACKENDS` to keep admin password login working.
- `middleware.py` — two gates, applied in this order:
  - `RequirePasswordChangeMiddleware`: traps users with `must_change_password=True` on the change-password flow (admin/static/logout exempted).
  - `RequireProfileActivationMiddleware`: traps users whose profile is missing or `is_activated=False` on `setup_profile`. Login-time routing alone is not enough — it is escaped by typing any URL, and an unactivated profile has `area=None`, so anything it answers scores into the "Sin área" bucket ADR-0004 exists to prevent. The gate applies to holders of **`can_take_assigned_surveys`** — exactly the people who can create such a submission. Operators lack it and pass through, so no admin carve-out is needed and admins need no `UserProfile`. Exempt paths: the activation page itself, the change-password URL (so the two gates don't fight), logout, static, `/admin/`.
- `views.py` — the auth flows: `request_otp` → `verify_otp`, `password_login`, `setup_access_code_login`, `change_password`, `setup_profile`, `logout_view` (POST-only). `_redirect_after_login` routes by group/profile state. `setup_profile` blocks activation when the company has **no active áreas** (nothing to pick from), collects the employee's own details — nombre(s), apellido paterno, apellido materno, cargo, sexo and fecha de nacimiento — alongside the pickers, prefills all of them from whatever is already on record, and writes the `User` and `UserProfile` rows in one transaction. The localidad picker is only rendered when the company has more than one active localidad; `ProfileActivationForm` refuses a POST that carries a `location` while the picker is absent (the catalog shrank mid-session) rather than auto-assigning the survivor.
- `importers.py` — `import_users_from_csv`: transactional, per-row report. `REQUIRED_HEADERS` (`email, company_reference_code, group, auth_method`, the latter `otp`|`password`) is the **entire** contract — there are no optional headers, and any extra column is ignored. The importer sets nothing an employee reports about themselves (name, cargo, sexo, fecha de nacimiento, área, localidad); those are collected by `ProfileActivationForm`. `CustomUserAdmin.import_csv_view` reads `REQUIRED_HEADERS` for its help text, so the page cannot drift from the code. Generates setup access codes for `password` users.
- `emails.py` — `send_otp_email`; raises `SMTPException` on failure (callers catch).
- `forms.py`, `utils.py`, `admin.py` (custom `User` admin with a `import-csv/` view).

## Conventions & gotchas

- **User-facing strings are in Spanish**; code, identifiers and comments in English. Every field carries an explicit Spanish `verbose_name` and every model a Spanish `Meta.verbose_name` — that metadata is the only thing standing between an English attribute name and a Spanish admin screen. `Role.Meta.permissions` labels are Spanish too; they surface in the Groups permission picker. See `docs/platform/localization.md`.
- **Spanish-text columns carry `db_collation=SPANISH_COLLATION`** (`es-MX-x-icu`): `Company.name`/`legal_name`, `CompanyCatalogEntry.name`, and `User.first_name`/`paternal_last_name`/`maternal_last_name` (declared on `User` for exactly this reason). The database's collation is byte order, which sorts every accented name after `Z`. Any new column holding Spanish text that gets shown as a sorted list needs it too.
- Dev OTP bypass: when `DEBUG`, code `000000` logs in any existing user (`verify_otp`). Never rely on this in prod.
- OTP requests are rate-limited (one per email per 30s) and require an existing `User`.
- Tests live in `tests/` (split by concern: models, views, forms, importers, admin).
