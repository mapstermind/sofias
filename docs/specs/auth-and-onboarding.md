# Spec: Auth and Onboarding

## Status

Current

## Overview

SOFIA-S uses pre-created user accounts. Users do not self-register from the public login flow.

The primary login path is email OTP. A fallback password path exists for users who cannot receive external email and have been given a temporary password by an administrator or trusted company contact.

After authentication, non-admin users must have an activated `UserProfile` linked to a `Company`. First-time activation is done by entering the company's 5-character `reference_code`.

## Product intent

The onboarding model keeps account creation under platform/admin control while giving employees and company executives a lightweight first-login experience:

- Preferred path: users receive a one-time code at their institutional email.
- Fallback path: users with blocked email delivery log in with a temporary password, then must immediately change it.
- Activation gate: users confirm their assigned company with the company reference code before entering normal app workflows.

Related user docs:

- `docs/user/user-onboarding.md`
- `docs/user/csv-user-import.md`

Related specs:

- `docs/specs/csv-user-import.md`

## Public behavior

### OTP login

1. A user opens `/cuentas/ingresar/`.
2. The user enters an email address.
3. If the email is invalid, the form is re-rendered with validation errors.
4. If the email does not belong to an existing `accounts.User`, the form is re-rendered with an error and no OTP is created.
5. If an OTP was recently created for that email, the request is rate-limited and no email is sent.
6. Existing unused OTPs for the email are deleted.
7. A new 6-digit OTP is created and sent by email.
8. The email is stored in the session as `otp_email`.
9. The user is redirected to `/cuentas/verificar/`.
10. The user enters the OTP.
11. The submitted hidden email must match the session `otp_email`.
12. If the OTP is valid, unused, and unexpired, SOFIA-S marks it used, logs the user in, removes `otp_email` from the session, and applies post-login routing.

OTP login does not create users.

In `settings.DEBUG`, the code `000000` may bypass OTP lookup for development use only. The submitted hidden email must still match the session `otp_email`.

### Password fallback login

1. A user opens `/cuentas/ingresar-con-contrasena/`.
2. The user enters email and password.
3. The form lowercases the email before lookup.
4. Login succeeds only when an active user exists, has a usable password, and the password is correct.
5. Invalid credentials, inactive users, and users with unusable passwords receive the same generic form error.
6. On success, SOFIA-S logs the user in through Django's `ModelBackend` and applies post-login routing.

The password fallback path does not currently have an application-level rate limit. This is acceptable for the current small deployment model and should be revisited if password fallback becomes a primary login path or is exposed to higher-volume traffic.

### Required password change

Temporary-password users have `User.must_change_password=True`.

When such a user is authenticated:

- `RequirePasswordChangeMiddleware` redirects most requests to `/cuentas/cambiar-contrasena/`.
- Allowed paths while the flag is set are the password-change URL, logout URL, static files, and admin URLs.
- The password-change form requires two matching password fields and uses Django's configured password validators.
- On successful change, SOFIA-S stores the new password hash, clears `must_change_password`, updates the session auth hash, and applies post-login routing.

### Profile activation

Non-admin users who do not have an activated profile are routed to `/cuentas/completar-perfil/`.

Activation behavior:

- Admin-group users skip profile activation and are redirected to the app home route.
- A user without a `UserProfile` sees the profile activation page with a generic account-not-linked error.
- A user whose profile has no company sees the profile activation page with the same generic account-not-linked error.
- A user whose profile is already activated is redirected to the app home route.
- A user with an inactive profile and linked company sees the company reference code form.
- The submitted reference code is stripped, uppercased, must be exactly 5 characters, and must be alphanumeric.
- If the code does not match the linked company's `reference_code`, the form is re-rendered and the profile remains inactive.
- If the code matches, `UserProfile.is_activated` is set to `True`, and the user is redirected to the app home route.

### Logout

Logout is POST-only at `/cuentas/cerrar-sesion/`.

- `POST` logs the user out and redirects to `/cuentas/ingresar/`.
- Non-POST requests return HTTP 405.

## Actors

- Platform admin: creates companies, users, profiles, groups, and temporary-password access through Django Admin or CSV import.
- Imported/pre-created user: logs in with OTP or temporary password and activates their profile.
- HR/company contact: receives and distributes temporary passwords when the fallback path is required.
- Admin-group user: can skip first-login profile activation.

## Inputs

- Login email.
- OTP code.
- Password fallback email and password.
- New password and confirmation.
- Company reference code.
- Session value `otp_email`.
- Environment-backed settings for email delivery, OTP expiry, session lifetime, and debug mode.

## Outputs

- Rendered login, verification, password-change, and activation forms.
- Redirects to verification, password change, activation, app home, or login routes.
- Created and updated `EmailOTP` records.
- Updated Django session authentication state.
- Updated `User.password` and `User.must_change_password`.
- Updated `UserProfile.is_activated`.
- OTP email sent through Django's configured email backend.

## API / routes / commands

| Interface | Method | Input | Output | Notes |
|---|---|---|---|---|
| `/cuentas/ingresar/` | GET | none | OTP email form | Authenticated users redirect to `settings.LOGIN_REDIRECT_URL`. |
| `/cuentas/ingresar/` | POST | `email` | Redirect to verify or form errors | Creates OTP only for existing users. |
| `/cuentas/verificar/` | GET | session `otp_email` | OTP form | Redirects to request-OTP page when session email is missing. Displays configured OTP expiry minutes. |
| `/cuentas/verificar/` | POST | hidden `email`, `code` | Login and post-login redirect or form errors | Hidden email must match session email. Marks valid OTP used unless debug bypass applies. |
| `/cuentas/ingresar-con-contrasena/` | GET | none | Password login form | Authenticated users redirect to `settings.LOGIN_REDIRECT_URL`. |
| `/cuentas/ingresar-con-contrasena/` | POST | `email`, `password` | Login and post-login redirect or form errors | Uses Django `ModelBackend`. |
| `/cuentas/cambiar-contrasena/` | GET | authenticated user | Password-change form or redirect | Requires login. Users without `must_change_password` are rerouted through post-login routing. |
| `/cuentas/cambiar-contrasena/` | POST | `new_password1`, `new_password2` | Redirect or form errors | Uses Django password validators. |
| `/cuentas/completar-perfil/` | GET | authenticated user | Activation form, account-linked error, or redirect | Requires login. Admins skip activation. |
| `/cuentas/completar-perfil/` | POST | `reference_code` | Activate profile and redirect or form errors | Admins skip activation even on POST. |
| `/cuentas/cerrar-sesion/` | POST | authenticated or anonymous session | Logout and redirect | GET and other methods return 405. |
| `python manage.py bootstrap_groups` | command | none | Creates or syncs auth groups | Idempotently assigns custom `accounts.Role` permissions. |

## Data model impact

- Models:
  - `accounts.User`
  - `accounts.Company`
  - `accounts.UserProfile`
  - `accounts.Role`
  - `accounts.EmailOTP`
- Fields:
  - `User.email`: unique email used by both login flows.
  - `User.must_change_password`: forces temporary-password users through password change.
  - `Company.reference_code`: unique 5-character company activation code, generated on save when blank.
  - `UserProfile.company`: company assignment for non-admin users.
  - `UserProfile.is_activated`: first-login activation state.
  - `EmailOTP.email`, `code`, `expires_at`, `is_used`.
- Constraints:
  - `User.email` must be unique.
  - `Company.reference_code` must be unique.
  - `UserProfile.user` is one-to-one.
- Migrations:
  - No migration is part of this spec. This documents current behavior.

## Side effects

- Database writes:
  - Delete previous unused OTPs for an email before creating a new OTP.
  - Create `EmailOTP` rows for valid OTP requests.
  - Mark valid OTPs as used.
  - Delete a just-created OTP if SMTP delivery fails with `SMTPException`.
  - Save password hash and clear `User.must_change_password` after password change.
  - Set `UserProfile.is_activated=True` after successful reference-code activation.
- Events/messages:
  - No domain events are emitted.
- Emails/notifications:
  - OTP email is sent through `apps.accounts.emails.send_otp_email`.
- External API calls:
  - No external API is called directly by the app code; email delivery depends on Django's configured email backend.
- Files/storage:
  - No files are written by these flows.
- Async tasks:
  - No async task or job is used.

## Permissions and authorization

- Public unauthenticated routes:
  - OTP request.
  - OTP verification, when session state exists.
  - Password fallback login.
- Login-required routes:
  - Password change.
  - Profile activation.
- Admin-group behavior:
  - Users in the `Admins` group skip profile activation. This is intentionally group-name based in the current system because the bootstrap command owns that canonical group contract.
- Middleware behavior:
  - Authenticated users with `must_change_password=True` are redirected to password change except on password-change, logout, static, and admin paths.
- Custom permissions:
  - `accounts.Role` defines project permissions used elsewhere in the app.
  - `bootstrap_groups` creates/syncs `Admins`, `Principal Exec`, `Secondary Exec`, and `Employees`.

## Error behavior

| Case | Expected behavior |
|---|---|
| Invalid OTP request email format | Re-render OTP request form with field errors. |
| Unknown OTP request email | Re-render OTP request form with account-not-found error; create no OTP. |
| OTP requested again inside the rate-limit window | Re-render OTP request form with wait message; send no email. |
| SMTP failure while sending OTP | Delete created OTP and re-render request form with send-failure error. |
| Verify page opened without `otp_email` in session | Redirect to `/cuentas/ingresar/`. |
| Verify form submitted with hidden email different from session `otp_email` | Re-render verify form with invalid/expired error; do not log in. |
| OTP code contains non-digits or is not six characters | Re-render verify form with field errors. |
| OTP code is wrong, expired, or already used | Re-render verify form with invalid/expired error. |
| Password fallback credentials invalid | Re-render password form with generic invalid-login error. |
| Password fallback user has unusable password | Re-render password form with generic invalid-login error. |
| Password fallback user is inactive | Re-render password form with generic invalid-login error. |
| Temporary-password user visits another app page | Redirect to `/cuentas/cambiar-contrasena/`. |
| Password-change values do not match or fail validators | Re-render password-change form with errors. |
| Activation user has no profile | Render activation page with account-not-linked error. |
| Activation user has profile but no company | Render activation page with account-not-linked error. |
| Activation code is malformed | Re-render activation form with field errors. |
| Activation code does not match linked company | Re-render activation form with mismatch error. |
| Logout requested with GET | Return HTTP 405. |

## Invariants

- Public login flows must not create new users.
- OTPs are single-use and expire according to `EmailOTP.expires_at`.
- A successful normal OTP verification marks the OTP used.
- OTP verification must bind the hidden submitted email to the session `otp_email`.
- Unknown emails must not receive OTPs.
- Unused OTPs for an email are invalidated before a new OTP is created.
- Temporary-password users must change their password before using normal non-admin, non-static app routes.
- `must_change_password` must be cleared only after a valid password change.
- Non-admin users must not complete first-login activation unless their entered reference code matches their linked company.
- The company reference code is an activation check, not a password or authentication secret.
- Logout must not be possible by GET.

## Acceptance criteria

- Given an existing active user with no usable password, when they request an OTP with their email, then SOFIA-S creates and sends a 6-digit OTP and redirects to verification.
- Given an unknown email, when the user requests an OTP, then no OTP is created and the request form shows an error.
- Given a second OTP request for the same email inside the rate-limit window, when the user submits the form, then no new email is sent.
- Given a valid unexpired OTP, when the user verifies it, then the OTP is marked used, the user is logged in, and post-login routing is applied.
- Given a verification POST where the hidden email differs from the session `otp_email`, when the user submits any code, then the form is re-rendered and the user is not logged in.
- Given an expired or wrong OTP, when the user submits it, then the verification form is re-rendered with an error.
- Given an active user with a usable password, when they submit correct password fallback credentials, then they are logged in and post-login routing is applied.
- Given a temporary-password user, when they log in or visit protected app pages, then they are forced to change their password before continuing.
- Given a temporary-password user submits a valid new password twice, when the password-change form is posted, then the password changes, `must_change_password` is cleared, and the user is routed onward.
- Given a non-admin user with an inactive profile and linked company, when they submit the matching company reference code, then their profile is activated and they are routed onward.
- Given a non-admin user submits the wrong company reference code, when the activation form is posted, then the profile remains inactive.
- Given an admin-group user, when post-login routing or activation is reached, then they skip profile activation.
- Given any user requests logout by GET, then the response is HTTP 405.
- Given any user posts to logout, then the session is logged out and redirected to the OTP login page.

## Test mapping

| Behavior | Test file | Test name |
|---|---|---|
| OTP request renders form | `apps/accounts/tests/test_views.py` | `TestRequestOTPView::test_get_renders_form` |
| Authenticated user redirected away from OTP request | `apps/accounts/tests/test_views.py` | `TestRequestOTPView::test_authenticated_user_is_redirected` |
| Valid OTP request creates OTP | `apps/accounts/tests/test_views.py` | `TestRequestOTPView::test_post_valid_email_creates_otp` |
| Valid OTP request redirects to verify | `apps/accounts/tests/test_views.py` | `TestRequestOTPView::test_post_valid_email_redirects_to_verify` |
| Unknown OTP request email rejected | `apps/accounts/tests/test_views.py` | `TestRequestOTPView::test_post_unknown_email_shows_error` |
| OTP request stores session email | `apps/accounts/tests/test_views.py` | `TestRequestOTPView::test_post_stores_email_in_session` |
| OTP email sender called | `apps/accounts/tests/test_views.py` | `TestRequestOTPView::test_post_calls_send_otp_email` |
| OTP request rate limit | `apps/accounts/tests/test_views.py` | `TestRequestOTPView::test_rate_limit_blocks_second_request` |
| SMTP failure deletes OTP | `apps/accounts/tests/test_views.py` | `TestRequestOTPView::test_smtp_failure_deletes_otp_and_shows_error` |
| Verify without session redirects | `apps/accounts/tests/test_views.py` | `TestVerifyOTPView::test_get_without_session_redirects_to_request_otp` |
| Verify with session renders form | `apps/accounts/tests/test_views.py` | `TestVerifyOTPView::test_get_with_session_renders_form` |
| Verify page displays configured expiry | `apps/accounts/tests/test_views.py` | `TestVerifyOTPView::test_get_uses_configured_otp_expiry_minutes` |
| Valid OTP is marked used | `apps/accounts/tests/test_views.py` | `TestVerifyOTPView::test_valid_otp_marks_otp_as_used` |
| Hidden email must match session email | `apps/accounts/tests/test_views.py` | `TestVerifyOTPView::test_mismatched_hidden_email_rerenders_with_error` |
| OTP login does not duplicate existing user | `apps/accounts/tests/test_views.py` | `TestVerifyOTPView::test_valid_otp_returning_user_no_duplicate` |
| Expired/wrong OTP rejected | `apps/accounts/tests/test_views.py` | `TestVerifyOTPView::test_expired_otp_rerenders_with_error`, `test_wrong_code_rerenders_with_error` |
| Post-login setup routing | `apps/accounts/tests/test_views.py` | `TestVerifyOTPView::test_non_activated_user_redirects_to_setup`, `test_activated_user_skips_setup`, `test_admin_user_skips_setup_profile_redirect`, `test_user_without_profile_redirects_to_setup` |
| Password login form renders | `apps/accounts/tests/test_views.py` | `TestPasswordLoginView::test_get_renders_form` |
| Unusable password cannot log in | `apps/accounts/tests/test_views.py` | `TestPasswordLoginView::test_unusable_password_cannot_login` |
| Valid password login | `apps/accounts/tests/test_views.py` | `TestPasswordLoginView::test_valid_password_logs_user_in` |
| Temporary password redirects to change password | `apps/accounts/tests/test_views.py` | `TestPasswordLoginView::test_temporary_password_redirects_to_change_password` |
| Middleware forces password change | `apps/accounts/tests/test_views.py` | `TestChangePasswordView::test_requires_password_change_before_other_pages` |
| Password change updates password and clears flag | `apps/accounts/tests/test_views.py` | `TestChangePasswordView::test_post_changes_password_and_clears_required_flag` |
| Admin skips activation | `apps/accounts/tests/test_views.py` | `TestSetupProfileView::test_admin_get_redirects_to_home`, `test_admin_post_redirects_to_home` |
| Activation requires login | `apps/accounts/tests/test_views.py` | `TestSetupProfileView::test_non_admin_unauthenticated_redirects_to_login` |
| Correct code activates profile | `apps/accounts/tests/test_views.py` | `TestSetupProfileView::test_correct_code_activates_and_redirects` |
| Wrong code rejected | `apps/accounts/tests/test_views.py` | `TestSetupProfileView::test_wrong_code_shows_error` |
| Activated profile redirects | `apps/accounts/tests/test_views.py` | `TestSetupProfileView::test_already_activated_redirects_to_home` |
| Missing company shows linked-account error | `apps/accounts/tests/test_views.py` | `TestSetupProfileView::test_no_company_linked_shows_error_page` |
| Logout is POST-only and clears session | `apps/accounts/tests/test_views.py` | `TestLogoutView::test_get_returns_405`, `test_post_logs_out_and_redirects` |
| OTP code validation | `apps/accounts/tests/test_forms.py` | `TestOTPVerifyFormCleanCode::*` |
| Reference code normalization and validation | `apps/accounts/tests/test_forms.py` | `TestProfileActivationFormCleanReferenceCode::*` |
| OTP validity rules | `apps/accounts/tests/test_models.py` | `TestEmailOTPIsValid::*` |
| Company reference code generation | `apps/accounts/tests/test_models.py` | `TestCompanyReferenceCode::*` |

## Decisions

- OTP login requires pre-created users. Any stale comments or docstrings that imply user creation should be corrected.
- The OTP verification screen must display `settings.OTP_EXPIRY_MINUTES` rather than hardcoded copy.
- The debug OTP bypass code `000000` remains allowed only when `settings.DEBUG` is true.
- OTP verification must reject a hidden email that differs from the session `otp_email`, including when debug bypass would otherwise apply.
- Missing profile and missing company remain intentionally indistinguishable to the user; both show the generic account-not-linked message.
- Password fallback has no application-level rate limit for now. Revisit if fallback password login becomes a common or higher-risk path.
- Admin activation bypass remains coupled to the canonical `Admins` group name for now.

## Open questions

- None.
