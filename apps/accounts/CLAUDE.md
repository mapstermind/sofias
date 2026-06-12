# accounts

Identity, authentication, authorization, and company/employee onboarding. Defines the custom user model and is the source of truth for who can do what. URL prefix: `/cuentas/` (`app_name = "accounts"`).

## Responsibilities

- **Custom user model** (`AUTH_USER_MODEL = "accounts.User"`) — extends `AbstractUser`, adds unique `email` and `must_change_password`.
- **Passwordless login via email OTP** — the primary login flow.
- **Fallback logins** — username/password and one-time "setup access codes" for users whose email cannot receive external OTP mail (see `docs/specs/adr-0001-setup-access-codes-for-blocked-email-login.md`).
- **Companies & profiles** — `Company` (with auto-generated 5-char `reference_code`) and `UserProfile` (links a user to a company, tracks activation).
- **Roles/permissions** — custom permissions + the groups that hold them.
- **Bulk user provisioning** — CSV import wired into Django admin.

## Models (`models.py`)

- `User` — custom user; login is by email, not username (`username` is auto-derived, see `utils.generate_unique_username`).
- `Company` — `reference_code` is generated in `save()` if blank; used by employees to self-activate.
- `UserProfile` — OneToOne with `User`; `is_activated` gates app access; FK to `Company`.
- `EmailOTP` — 6-digit code keyed by **email string, not a User FK** (the user may not exist yet). Self-sets `expires_at` from `OTP_EXPIRY_MINUTES` (default 10).
- `SetupAccessCode` — one-time first-login code; partial unique constraints enforce "one active code globally" and "one unused code per user". `mark_used()` nulls the code.
- `Role` — **sentinel model, `managed = False`** (no DB table). Exists only to declare the project's custom permissions in `auth_permission`. The permission codenames it defines (e.g. `can_view_dashboard`, `can_manage_surveys`) are checked throughout `apps/core`.

## Authorization model

Permissions are defined on `Role.Meta.permissions`; groups that bundle them are created by `python manage.py bootstrap_groups` (idempotent). The four groups: **Admins, Principal Exec, Secondary Exec, Employees**. Tests get the same setup via the `bootstrap_groups` fixture in `conftest.py`. When adding a permission, update **both** `Role.Meta.permissions` and `bootstrap_groups.GROUP_PERMISSIONS`, then the `conftest.py` fixture.

## Key files

- `backends.py` — `EmailOTPBackend`: a near-empty backend; OTP validation happens in the view, the backend exists only so `login()` can record it. `ModelBackend` stays first in `AUTHENTICATION_BACKENDS` to keep admin password login working.
- `middleware.py` — `RequirePasswordChangeMiddleware`: traps users with `must_change_password=True` on the change-password flow (admin/static/logout exempted).
- `views.py` — the auth flows: `request_otp` → `verify_otp`, `password_login`, `setup_access_code_login`, `change_password`, `setup_profile`, `logout_view` (POST-only). `_redirect_after_login` routes by group/profile state.
- `importers.py` — `import_users_from_csv`: transactional, per-row report; required CSV headers `email, company_reference_code, group, auth_method` (`otp`|`password`). Generates setup access codes for `password` users.
- `emails.py` — `send_otp_email`; raises `SMTPException` on failure (callers catch).
- `forms.py`, `utils.py`, `admin.py` (custom `User` admin with a `import-csv/` view).

## Conventions & gotchas

- **User-facing strings are in Spanish**; code/comments in English.
- Dev OTP bypass: when `DEBUG`, code `000000` logs in any existing user (`verify_otp`). Never rely on this in prod.
- OTP requests are rate-limited (one per email per 30s) and require an existing `User`.
- Tests live in `tests/` (split by concern: models, views, forms, importers, admin).
