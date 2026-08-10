# User Onboarding Procedure

This document defines the end-to-end process for creating a pre-approved user and getting them through their first login. SOFIA-S supports two paths:

- **Preferred path:** email OTP login only. The user never receives or manages a password.
- **Fallback path:** código temporal de acceso for first login when the company blocks external email delivery, followed by user-created password login.

## Prerequisites

Before creating users, confirm the company already exists in Django Admin and has:

- **Nombre comercial**
- **Razón social**
- **RFC** (optional)
- **Domicilio** (optional)
- **Código de referencia**
- **Áreas** — at least one
- **Localidades** — optional

The **Código de referencia** is generated automatically and is required during first-time profile activation. Share this company reference code only with the correct company contact.

**Áreas and localidades are loaded on the company itself**, in the *Áreas* and *Localidades* sections at the bottom of the company page in Django Admin. Each company has its own lists. They must be loaded **before** employees try to activate their accounts, because the employee picks their área from this list.

> **At least one área is required.** An employee whose company has no áreas cannot finish activation — they will see a message asking them to contact their administrator. The company list in Django Admin shows an *Áreas* count column so you can spot companies that still need one.

Names are unique per company, ignoring capitalization, accents and extra spaces: adding `Ventas` and `ventas`, or `Dirección` and `Direccion`, to the same company is rejected — they are one entry typed two ways, and letting both through would split the área into two dashboard rows that nobody can merge later. The `ñ` is treated as the letter it is, so `Cañada` and `Canada` can both exist. To retire an área or localidad that is no longer used, **uncheck *activa*** instead of deleting it — that removes it from the picker while the employees already assigned to it keep their history. Deleting one that still has employees assigned is blocked.

Retiring an entry while someone has the activation page open is safe: their submission is rejected with a message asking them to review and confirm their data, never silently reassigned to a different área or localidad.

## Create the User

Setup access codes are generated only by the CSV importer. To create a
fallback-path user, use the CSV import with `auth_method=password` (see
`docs/internal/user-guides/csv-user-import.md`) — it creates the user, the profile, the group
assignment, and the setup access code in one step.

The manual procedure below is for OTP-only users:

1. Open Django Admin.
2. Go to **Usuarios**.
3. Click **Agregar usuario**.
4. Enter a unique **Nombre de usuario**.
   - Recommended pattern: use the email local part, for example `jane.doe` for `jane.doe@company.com`.
   - If that username already exists, append a number, for example `jane.doe1`.
5. Set **Autenticación basada en contraseña** to **Deshabilitado**. OTP users never need a password.
6. Save the user.
7. Open the saved user record and complete these fields:
   - **Correo electrónico**: the employee’s institutional email. This must be exact because login starts from this email.
   - **Nombre(s)** and **Apellidos**: optional. The employee is asked for these at activation, and anything you enter here is prefilled for them to confirm.
   - **Activo**: enabled.
   - **Grupos**: assign the correct role group, for example `Employees`, `Principal Exec`, `Secondary Exec`, or `Admins`.
8. Save again.

## Create or Update the User Profile

Each non-admin user needs a `UserProfile`.

1. In Django Admin, go to **Perfiles de colaborador**.
2. Create a profile for the user, or open the existing profile.
3. Set:
   - **Usuario**: the user created above.
   - **Empresa**: the company where the user works. This is the only field you have to set.
   - **Cargo**, **Área**, **Localidad**: optional here — the employee supplies these during activation, and anything you enter is prefilled for them. The dropdowns only offer entries belonging to the profile’s company.
   - **Cuenta activada**: leave disabled for first-time users.
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
9. The user enters the company `reference_code`, their **nombre(s)** and **apellidos** (both required) and an optional **cargo**, then selects their **área** from the company’s list. If the company has more than one localidad, they also select their **localidad**; with exactly one localidad it is assigned automatically and not shown.
10. If the code matches the company linked to their profile, **Cuenta activada** becomes enabled, the name, cargo, área and localidad are saved, and the user proceeds into the app. Until this happens the employee roster shows them as *Sin nombre*.

## Path B: Setup Access Code Fallback

Use this path only when the company blocks external email, so OTP messages never reach the user.

1. The platform admin imports the user through the CSV importer with `auth_method=password`. SOFIA-S creates the user with an unusable password, sets **Debe cambiar su contraseña**, and generates a 9-digit setup access code that appears in the import report.
2. The platform admin sends the código temporal de acceso to the company’s trusted HR or internal administrator through an approved internal channel.
3. HR gives the código temporal de acceso to the employee using the company’s internal process.
4. The user opens `/cuentas/primer-ingreso/`.
5. The user enters their institutional email and código temporal de acceso.
6. SOFIA-S logs the user in, marks the setup access code used, clears the stored code, and immediately redirects them to `/cuentas/cambiar-contrasena/`.
7. The user creates a contraseña. Django password validation rules apply.
8. SOFIA-S clears **Debe cambiar su contraseña**.
9. Future fallback logins use `/cuentas/ingresar-con-contrasena/`.
10. If this is the user’s first login, they are redirected to `/cuentas/completar-perfil/`.
11. The user enters the company `reference_code`.
12. If the code matches their linked company, **Cuenta activada** becomes enabled and the user proceeds into the app.

## Security Rules

- Prefer OTP login whenever possible.
- Do not create passwords for users who can receive OTP emails.
- Do not share setup access codes by email from SOFIA-S if email delivery is the problem.
- Do not use the company `reference_code` as a password.
- Set **Debe cambiar su contraseña** for every setup-code fallback user.
- Confirm the user’s profile is linked to the correct company before sharing either the reference code or a código temporal de acceso.
- If a setup access code may have been exposed before use, delete the code in Django Admin. There is no regeneration mechanism: if access is still required, delete the user and re-import them via CSV.

## Admin Checklist

For OTP-only onboarding:

- User exists with exact institutional email.
- Password-based authentication is disabled.
- User has the correct group.
- UserProfile exists and points to the correct company.
- UserProfile **Cuenta activada** is disabled.
- Company contact has the company **Código de referencia**.

For fallback onboarding:

- User exists with exact institutional email.
- Password-based authentication is disabled until the user creates a contraseña.
- Setup access code exists, is unused, and has 9 digits.
- **Debe cambiar su contraseña** is enabled.
- User has the correct group.
- UserProfile exists and points to the correct company.
- UserProfile **Cuenta activada** is disabled.
- HR has the código temporal de acceso through a trusted internal channel.
- Company contact has the company **Código de referencia**.
