# User Onboarding Procedure

This document defines the end-to-end process for creating a pre-approved user and getting them through their first login. SOFIA-S supports two paths:

- **Preferred path:** email OTP login only. The user never receives or manages a password.
- **Fallback path:** temporary password login when the company blocks external email delivery.

## Prerequisites

Before creating users, confirm the company already exists in Django Admin and has:

- `name`
- `legal_name`
- `RFC`
- `address`
- `reference_code`

The `reference_code` is generated automatically and is required during first-time profile activation. Share this company reference code only with the correct company contact.

## Create the User

1. Open Django Admin.
2. Go to **Users**.
3. Click **Add user**.
4. Enter a unique `username`.
   - Recommended pattern: use the email local part, for example `jane.doe` for `jane.doe@company.com`.
   - If that username already exists, append a number, for example `jane.doe1`.
5. Configure password-based authentication depending on the login path:
   - For OTP-only users, choose **disabled** password-based authentication.
   - For fallback users, choose **enabled** and set a strong temporary password.
6. If using the fallback path, set `must_change_password` to checked/enabled.
7. Save the user.
8. Open the saved user record and complete these fields:
   - `email`: the employee’s institutional email. This must be exact because login starts from this email.
   - `first_name` and `last_name`, if available.
   - `is_active`: enabled.
   - Groups/permissions: assign the correct role group, for example `Employees`, `Principal Exec`, `Secondary Exec`, or `Admins`.
9. Save again.

## Create or Update the User Profile

Each non-admin user needs a `UserProfile`.

1. In Django Admin, go to **User profiles**.
2. Create a profile for the user, or open the existing profile.
3. Set:
   - `user`: the user created above.
   - `position`: the employee’s role or job title.
   - `company`: the company where the user works.
   - `is_activated`: leave disabled for first-time users.
4. Save the profile.

Admins can skip profile activation, but company employees and executives must have a profile linked to their company.

## Path A: Email OTP Login

Use this path when the user can receive emails from SOFIA-S.

1. The admin does not send a password to HR or the user.
2. The user opens the login page: `/cuentas/ingresar/`.
3. The user enters their institutional email.
4. SOFIA-S checks that the email belongs to an existing user.
5. SOFIA-S sends a 6-digit one-time code to that email.
6. The user enters the code at `/cuentas/verificar/`.
7. After successful verification, SOFIA-S logs the user in.
8. If this is the user’s first login, they are redirected to `/cuentas/completar-perfil/`.
9. The user enters the company `reference_code`.
10. If the code matches the company linked to their profile, `is_activated` becomes enabled and the user proceeds into the app.

## Path B: Temporary Password Fallback

Use this path only when the company blocks external email, so OTP messages never reach the user.

1. The platform admin enables password-based authentication for the user.
2. The platform admin sets a strong temporary password.
3. The platform admin sets `must_change_password` to enabled.
4. The platform admin sends the temporary password to the company’s trusted HR or internal administrator through an approved internal channel.
5. HR gives the temporary password to the employee using the company’s internal process.
6. The user opens `/cuentas/ingresar-con-contrasena/`.
7. The user enters their institutional email and temporary password.
8. SOFIA-S logs the user in and immediately redirects them to `/cuentas/cambiar-contrasena/`.
9. The user creates a new password. Django password validation rules apply.
10. SOFIA-S clears `must_change_password`.
11. If this is the user’s first login, they are redirected to `/cuentas/completar-perfil/`.
12. The user enters the company `reference_code`.
13. If the code matches their linked company, `is_activated` becomes enabled and the user proceeds into the app.

## Security Rules

- Prefer OTP login whenever possible.
- Do not create passwords for users who can receive OTP emails.
- Do not share temporary passwords by email from SOFIA-S if email delivery is the problem.
- Do not use the company `reference_code` as a password.
- Set `must_change_password` for every temporary-password user.
- Confirm the user’s profile is linked to the correct company before sharing either the reference code or a temporary password.
- If a temporary password may have been exposed, reset it immediately in Django Admin and keep `must_change_password` enabled.

## Admin Checklist

For OTP-only onboarding:

- User exists with exact institutional email.
- Password-based authentication is disabled.
- User has the correct group.
- UserProfile exists and points to the correct company.
- UserProfile `is_activated` is disabled.
- Company contact has the company `reference_code`.

For fallback onboarding:

- User exists with exact institutional email.
- Password-based authentication is enabled.
- Temporary password is strong and unique.
- `must_change_password` is enabled.
- User has the correct group.
- UserProfile exists and points to the correct company.
- UserProfile `is_activated` is disabled.
- HR has the temporary password through a trusted internal channel.
- Company contact has the company `reference_code`.
