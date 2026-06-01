# CSV User Import Procedure

This document explains how platform admins can bulk-create users from Django Admin using a CSV file. The importer creates both the `User` and the corresponding `UserProfile`, links the profile to a company, assigns one group, and supports either OTP-only login or temporary-password fallback.

## Who Can Use This

This process is intended for platform admins with access to Django Admin and permission to add users. It is not intended for company employees or regular managers.

## Before Uploading

Confirm the following records already exist:

- The target `Company` exists.
- The company has a valid `reference_code`.
- The target Django group exists, for example `Employees`, `Principal Exec`, or `Secondary Exec`.

The importer does not create companies or groups. Rows with unknown companies or groups are skipped and reported.

## CSV Columns

Required columns:

- `email`: the user’s institutional email. Must be unique.
- `company_reference_code`: the `Company.reference_code` used to link the profile.
- `group`: one Django group name to assign to the user.
- `auth_method`: either `otp` or `password`.

Optional columns:

- `first_name`
- `last_name`
- `position`

Blank optional values are allowed. Existing users are never updated; duplicate emails are skipped.

## CSV Example

```csv
email,company_reference_code,group,auth_method,first_name,last_name,position
ana.lopez@empresa.com,A1B2C,Employees,otp,Ana,Lopez,Analista
carlos.ruiz@empresa.com,A1B2C,Principal Exec,otp,Carlos,Ruiz,Director General
maria.santos@empresa.com,A1B2C,Employees,password,Maria,Santos,Coordinadora
sin.nombre@empresa.com,A1B2C,Employees,otp,,,
```

Use `otp` when the user can receive the login code by email. Use `password` only when the company blocks external email delivery and HR needs to distribute a temporary password internally.

## Upload Procedure

1. Open Django Admin.
2. Go to **Users**.
3. Click **Importar usuarios desde CSV**.
4. Review the required and optional columns shown on the page.
5. Select the `.csv` file.
6. Click **Importar usuarios**.
7. Download and review the generated import report.

## Import Results

The downloaded report includes:

- `row_number`
- `email`
- `status`: `created` or `skipped`
- `message`
- `username`
- `temporary_password`

For `auth_method=password` rows that are created successfully, `temporary_password` contains the generated password. This is the only time the password is shown in plaintext.

## After Import

For OTP users:

1. Tell the company contact that users can log in at `/cuentas/ingresar/`.
2. Share the company `reference_code` through the correct company contact.
3. Users enter their email, receive an OTP, and activate their profile with the company reference code.

For password fallback users:

1. Send the report, or only the relevant temporary passwords, to the company’s trusted HR contact through an approved internal channel.
2. HR distributes each temporary password to the correct employee.
3. Users log in at `/cuentas/ingresar-con-contrasena/`.
4. SOFIA-S forces them to change the temporary password before continuing.
5. Users then activate their profile with the company reference code.

## Security Rules

- Prefer `auth_method=otp` whenever possible.
- Do not include temporary passwords in the upload CSV; SOFIA-S generates them.
- Treat the downloaded report as sensitive.
- Do not store the report in shared folders unless access is restricted.
- Do not use the company reference code as a password.
- If a generated temporary password is exposed, reset that user’s password in Django Admin and keep `must_change_password` enabled.
