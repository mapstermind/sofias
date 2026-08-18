# CSV User Import Procedure

This document explains how platform admins can bulk-create users from Django Admin using a CSV file. The importer creates both the `User` and the corresponding `UserProfile`, links the profile to a company, assigns one group, and supports either OTP-only login or setup-code fallback.

## Who Can Use This

This process is intended for platform admins with access to Django Admin and permission to add users. It is not intended for company employees or regular managers.

## Before Uploading

Confirm the following records already exist:

- The target `Company` exists.
- The company has a valid `reference_code`.
- The company has at least one **área** loaded (see the company setup guide). Employees cannot activate their accounts without one, so importing them first only stalls them at activation.
- The target Django group exists, for example `Employees`, `Principal Exec`, or `Secondary Exec`.

The importer does not create companies or groups. Rows with unknown companies or groups are skipped and reported.

### Finding a company's `reference_code`

Each company's `reference_code` is an auto-generated 5-character code (uppercase letters and digits). You do not set it manually, so look it up before building the CSV:

1. Open Django Admin.
2. Go to **Empresas**.
3. Open the target company and copy its **Código de referencia**.

Case does not matter in the CSV — the importer uppercases `company_reference_code` before lookup — but the value must match an existing company exactly.

## CSV Columns

The file needs exactly four columns, and every one of them is required:

- `email`: the user’s institutional email. Must be unique.
- `company_reference_code`: the `Company.reference_code` used to link the profile.
- `group`: one Django group name to assign to the user.
- `auth_method`: either `otp` or `password`.

There are no optional columns. **You do not upload names, cargos, áreas or localidades** — each employee supplies those themselves when they activate their account, so you only need the list of who gets access and what kind.

Existing users are never updated; duplicate emails are skipped.

Any extra columns in the file are ignored, so a roster exported from another system can be uploaded without deleting its other columns first. Note this cuts both ways: an `area` column will be ignored, not applied. Because all four real columns are required, a misspelled header (`Email`, `grupo`) rejects the entire file with a message naming what is missing — you will not get a silent half-import.

## CSV Example

```csv
email,company_reference_code,group,auth_method
ana.lopez@empresa.com,A1B2C,Employees,otp
carlos.ruiz@empresa.com,A1B2C,Principal Exec,otp
maria.santos@empresa.com,A1B2C,Employees,password
```

Use `otp` when the user can receive the login code by email. Use `password` only when the company blocks external email delivery and HR needs to distribute a código temporal de acceso internally.

## Upload Procedure

1. Open Django Admin.
2. Go to **Usuarios**.
3. Click **Importar usuarios desde CSV**.
4. Review the required columns shown on the page.
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
- `setup_access_code`

For `auth_method=password` rows that are created successfully, `setup_access_code` contains the generated 9-digit código temporal de acceso. The unused code is also visible in Django Admin for authorized support users.

## After Import

For OTP users:

1. Tell the company contact that users can log in at `/cuentas/ingresar/`.
2. Share the company `reference_code` through the correct company contact.
3. Users enter their email, receive an OTP, and then complete activation: the company reference code, their nombre and apellidos, an optional cargo, their área, and their localidad when the company has more than one.

Until a user activates, the roster shows them as *Sin nombre* — that is expected, not a failed import.

For setup-code fallback users:

1. Send the report, or only the relevant setup access codes, to the company’s trusted HR contact through an approved internal channel.
2. HR distributes each código temporal de acceso to the correct employee.
3. Users log in at `/cuentas/primer-ingreso/`.
4. SOFIA-S forces them to create a contraseña before continuing.
5. Future fallback logins use `/cuentas/ingresar-con-contrasena/`.
6. Users then activate their profile with the company reference code.

## Security Rules

- Prefer `auth_method=otp` whenever possible.
- Do not include setup access codes in the upload CSV; SOFIA-S generates them.
- Treat the downloaded report as sensitive.
- Do not store the report in shared folders unless access is restricted.
- Do not use the company reference code as a password.
- If a generated setup access code is exposed before use, delete it in Django Admin and create a new user import only if access is still required.
