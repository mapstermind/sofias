# Spec: Setup Access Codes

## Status

Current

## Overview

Setup access codes are the planned backup first-login path for pre-created users
who cannot receive SOFIA-S email OTP messages because a client's email policies
block external senders.

Confirmed current behavior:

- Email OTP login is the primary login path.
- CSV import accepts `auth_method=otp` and `auth_method=password`.
- Current `auth_method=password` rows receive a generated temporary password
  stored as the user's real password hash.
- Current temporary-password users are forced to change their password through
  `User.must_change_password=True`.

Desired behavior after implementation:

- `auth_method=password` rows receive a one-time setup access code instead of a
  temporary password.
- Setup access codes bootstrap first login only.
- After setup-code verification, the user must create a permanent password.
- Future fallback logins use the normal password login path.

## Product intent

SOFIA-S should support first login for users whose client blocks external email
without treating the distributed first-login secret as a normal password.

The product keeps the existing CSV import contract for admins while changing the
fallback credential from "temporary password" to "setup access code."

Related ADR:

- `docs/adr/0001-setup-access-codes-for-blocked-email-login.md`

## Public behavior

### CSV-created setup-code users

When a platform admin imports a CSV row with `auth_method=password`, SOFIA-S
creates the user with an unusable password and `User.must_change_password=True`.
SOFIA-S also creates a one-time setup access code for that user.

The setup access code appears in the import report downloaded immediately after
the import. The report column is `setup_access_code`.

The setup access code also remains visible to authorized Django Admin users for
support purposes until it is used. This is an intentional support tradeoff:
support staff can help a trusted client contact recover an undistributed setup
code without regenerating it or re-running an import.

The CSV input value remains `password` because this value means "the user needs
password-based fallback after first setup." It does not mean SOFIA-S should
generate a temporary password.

### Setup-code first login

1. A fallback user opens `/cuentas/primer-ingreso/`.
2. The user enters their email address and setup access code.
3. SOFIA-S normalizes the email address and setup access code.
4. If the code is valid, unused, and assigned to the submitted email, SOFIA-S
   marks the code used and logs the user in.
5. SOFIA-S redirects the user to `/cuentas/cambiar-contrasena/`.
6. The user creates a permanent password through the existing required
   password-change flow.
7. SOFIA-S clears `User.must_change_password`.
8. Future password fallback logins use `/cuentas/ingresar-con-contrasena/`.

Setup access codes do not activate the user's company profile. After password
creation, normal post-login routing still requires non-admin users to complete
company profile activation when their `UserProfile.is_activated` flag is false.

### Setup-code format and lifetime

Generated setup access codes use exactly 9 numeric digits.

```text
123456789
```

The generated value may be displayed in grouped form with hyphens, for example:

```text
123-456-789
```

Verification normalizes submitted codes by:

- stripping leading and trailing whitespace
- removing spaces and hyphens

Setup access codes do not expire. They remain valid until successful use or
manual administrative removal.

### User-facing wording

Spanish user-facing copy must distinguish setup access codes from passwords:

- Use `código temporal de acceso` for setup access codes.
- Use `contraseña` for passwords.

## Actors

- **Platform admin:** imports users through Django Admin and receives the
  sensitive import report.
- **Trusted client contact:** receives setup access codes through an approved
  internal channel and distributes each code to the correct user.
- **Fallback user:** uses email plus setup access code for first login, then
  creates a permanent password.

## Inputs

- CSV import row:
  - `email`
  - `company_reference_code`
  - `group`
  - `auth_method=password`
  - optional profile/name fields already supported by CSV import
- Setup-code first-login form:
  - `email`
  - `setup_access_code`
- Password creation form:
  - `new_password1`
  - `new_password2`

## Outputs

- CSV import report with headers:

```text
row_number,email,status,message,username,setup_access_code
```

- Setup-code login page rendered for GET requests and invalid POST requests.
- Redirect to `/cuentas/cambiar-contrasena/` after successful setup-code
  verification.
- Redirects from required-password middleware until the user creates a permanent
  password.
- Existing password-change success redirect behavior after
  `User.must_change_password` is cleared.

## API / routes / commands

| Interface | Method | Input | Output | Notes |
|---|---|---|---|---|
| `/admin/accounts/user/import-csv/` | POST | CSV file | CSV import report download | Existing admin import route. `auth_method=password` now creates setup access codes. |
| `/cuentas/primer-ingreso/` | GET | none | Setup-code first-login form | Public route for users with internally distributed setup access codes. |
| `/cuentas/primer-ingreso/` | POST | `email`, `setup_access_code` | Redirect to password change or form errors | Must not reveal whether the email, code, or account state caused failure. |
| `/cuentas/cambiar-contrasena/` | GET/POST | existing password-change fields | Existing password creation/change behavior | Used immediately after setup-code verification. |
| `/cuentas/ingresar-con-contrasena/` | GET/POST | email and password | Existing password login behavior | Used only after the user creates a permanent password. |

## Data model impact

- Models:
  - Add `accounts.SetupAccessCode`.
  - Keep `accounts.User.must_change_password`.
  - Keep `accounts.EmailOTP`.
- Fields:
  - `SetupAccessCode.user`: foreign key to `accounts.User`.
  - `SetupAccessCode.code`: nullable normalized 9-digit setup access code,
    populated while unused and cleared after successful use.
  - `SetupAccessCode.created_at`: timestamp when generated.
  - `SetupAccessCode.used_at`: nullable timestamp set on successful use.
- Constraints:
  - Setup access codes are sensitive and may be visible only in the import
    report and Django Admin.
  - A setup access code is valid only when `used_at` is null and `code` matches
    the normalized submitted code.
  - At most one usable setup access code should exist for a user at a time.
  - Generated unused setup access codes should be unique globally.
  - Historical used setup access code rows may remain for audit/debug context,
    but they must not retain the consumed plaintext code.
- Migrations:
  - Add a migration for `SetupAccessCode`.
  - No migration should rename or remove `User.must_change_password`.

## Side effects

- Database writes:
  - CSV import creates `SetupAccessCode` rows for created
    `auth_method=password` users.
  - Setup-code verification sets `SetupAccessCode.used_at` and clears
    `SetupAccessCode.code`.
  - Password creation saves the user's permanent password hash and clears
    `User.must_change_password`.
- Events/messages:
  - No application event bus behavior is required.
- Emails/notifications:
  - Setup access code creation sends no email.
  - Email OTP behavior is unchanged.
- External API calls:
  - No new external API calls.
- Files/storage:
  - No files are stored by SOFIA-S.
  - The CSV import report remains a sensitive downloaded artifact.
- Async tasks:
  - No async task is required.

## Permissions and authorization

- CSV import remains limited to users with Django Admin user-add permission.
- Django Admin visibility for `SetupAccessCode` is limited to authorized admin
  users. Admin screens must treat setup access codes as sensitive support data.
- Setup-code first login is public, like the existing login pages.
- Setup-code verification must authenticate only active users.
- Authenticated users visiting `/cuentas/primer-ingreso/` are redirected through
  the existing post-login routing.
- A user with `User.must_change_password=True` remains blocked from normal app
  workflows by the existing required-password middleware.

## Error behavior

| Case | Expected behavior |
|---|---|
| Unknown email on setup-code POST | Re-render setup-code form with a generic invalid setup-code error. |
| Inactive user on setup-code POST | Re-render setup-code form with a generic invalid setup-code error. |
| User has no setup access code | Re-render setup-code form with a generic invalid setup-code error. |
| Code belongs to another user | Re-render setup-code form with a generic invalid setup-code error. |
| Malformed setup access code | Re-render setup-code form with field validation errors. A valid normalized code is exactly 9 digits. |
| Already used setup access code | Re-render setup-code form with a generic invalid setup-code error. |
| Valid code submitted twice concurrently | Exactly one request succeeds; later verification fails because the code is used. |
| Setup access code submitted on password login form | Password login rejects it as invalid credentials. |
| CSV row with `auth_method=otp` | User is created with unusable password and no setup access code in the report. |
| CSV row with `auth_method=password` | User is created with unusable password, `must_change_password=True`, and one setup access code in the report. |

The generic invalid setup-code message should avoid confirming whether the email
address exists.

## Invariants

- Setup access codes are bootstrap credentials, not passwords.
- Setup access codes must only be accepted by the setup-code first-login route.
- Setup access codes must be single-use.
- Setup access codes must not expire automatically.
- Setup access codes must be visible only in the CSV import report and Django
  Admin.
- Used setup access code rows must not retain the consumed plaintext code.
- `auth_method=password` users must not receive a usable password at import
  time.
- `auth_method=otp` users must not receive setup access codes.
- `User.must_change_password=True` must prevent access to normal app workflows
  until the user creates a permanent password.
- Password creation must use Django password validation.
- Company profile activation remains separate from first-login authentication.

## Acceptance criteria

- Given a valid CSV row with `auth_method=otp`, when the row is imported, then
  SOFIA-S creates the user with an unusable password, sets
  `must_change_password=False`, creates no setup access code, and leaves
  `setup_access_code` blank in the report.
- Given a valid CSV row with `auth_method=password`, when the row is imported,
  then SOFIA-S creates the user with an unusable password, sets
  `must_change_password=True`, creates one setup access code, and includes the
  plaintext setup access code in the report.
- Given a fallback user has a valid setup access code, when they submit their
  email and setup code to `/cuentas/primer-ingreso/`, then SOFIA-S marks the code
  used, clears the stored code, logs the user in, and redirects them to
  `/cuentas/cambiar-contrasena/`.
- Given a fallback user is authenticated through setup-code first login, when
  they try to access a normal app page before creating a permanent password,
  then SOFIA-S redirects them back to `/cuentas/cambiar-contrasena/`.
- Given a fallback user creates a valid permanent password, when the password
  change succeeds, then SOFIA-S clears `must_change_password`.
- Given a fallback user has created a permanent password, when they log out and
  submit the correct email and password, then SOFIA-S logs them in through the
  normal password login path.
- Given a setup access code has already been used, when any user submits that
  code again, then SOFIA-S rejects it.
- Given an authorized Django Admin user views setup access codes, when an unused
  code exists, then the admin can see the code for support visibility.
- Given a setup access code is submitted with spaces or hyphens, when it matches
  a valid generated code after normalization, then
  SOFIA-S accepts it.
- Given a setup access code is entered on the normal password login form, when
  the user submits it as the password, then SOFIA-S rejects the login.

## Test mapping

Write these tests before implementation.

| Behavior | Test file | Test name |
|---|---|---|
| `auth_method=otp` import creates no setup code | `apps/accounts/tests/test_importers.py` | `test_otp_import_does_not_create_setup_access_code` |
| `auth_method=password` import creates setup code and unusable password | `apps/accounts/tests/test_importers.py` | `test_password_import_creates_setup_access_code_instead_of_password` |
| Import report uses `setup_access_code` column | `apps/accounts/tests/test_importers.py` | `test_import_report_includes_setup_access_code_header` |
| Setup code model validates unused code | `apps/accounts/tests/test_models.py` | `test_setup_access_code_is_valid_when_unused` |
| Setup code model does not expire unused code | `apps/accounts/tests/test_models.py` | `test_setup_access_code_does_not_expire` |
| Setup-code GET renders form | `apps/accounts/tests/test_views.py` | `TestSetupAccessCodeLoginView::test_get_renders_form` |
| Valid setup-code POST logs in user and redirects to password change | `apps/accounts/tests/test_views.py` | `TestSetupAccessCodeLoginView::test_valid_code_redirects_to_password_change` |
| Valid setup-code POST marks code used and clears code | `apps/accounts/tests/test_views.py` | `TestSetupAccessCodeLoginView::test_valid_code_marks_code_used_and_clears_code` |
| Used setup code is rejected | `apps/accounts/tests/test_views.py` | `TestSetupAccessCodeLoginView::test_used_code_is_rejected` |
| Wrong email/code pairing is rejected | `apps/accounts/tests/test_views.py` | `TestSetupAccessCodeLoginView::test_code_for_other_user_is_rejected` |
| Setup code cannot be used as normal password | `apps/accounts/tests/test_views.py` | `TestPasswordLoginView::test_setup_access_code_cannot_login_as_password` |
| Password creation enables later password login | `apps/accounts/tests/test_views.py` | `TestSetupAccessCodeLoginView::test_user_can_login_with_created_password_after_setup` |
| Required-password middleware blocks normal pages after setup-code login | `apps/accounts/tests/test_views.py` | `TestSetupAccessCodeLoginView::test_setup_code_user_must_create_password_before_app_access` |
| Setup access code is visible in Django Admin | `apps/accounts/tests/test_admin.py` | `test_setup_access_code_admin_shows_unused_code` |

## Open questions

- None.
