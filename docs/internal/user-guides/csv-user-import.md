# CSV User Import Reference

The CSV import is how every client user gets onto the platform: one row per person creates their account, links it to their company, gives it a role and, for people who cannot receive email, generates their código de acceso. This page is the reference for the file and the report. Where the import fits in a client's onboarding — and what to do after it — is [`user-onboarding.md`](user-onboarding.md#2-add-the-companys-users).

## Who can use it

Platform operators: an account with **Es staff** and permission to add users (a superuser has it). Client executives cannot import users.

## Before uploading

- **The company exists** and has **at least one área** ([`user-onboarding.md`, step 1](user-onboarding.md#1-create-the-company)). People imported into a company with no áreas cannot finish activating.
- **You have the company's Código de empresa**: **Cuentas → Empresas**, open the company, copy **Código de empresa**.
- **The groups exist.** They are created by `bootstrap_groups` during [platform setup](platform-setup.md#5-initialize-the-database).

The import creates neither companies nor groups. A row naming an unknown one is skipped and reported.

## Columns

The file has four columns, all required on every row:

| Column | Value |
|---|---|
| `email` | The person's work email. Stored in lowercase; it is what they log in with. |
| `company_reference_code` | The company's Código de empresa. Case doesn't matter. |
| `group` | The role, written exactly as below — capitalization and spaces included. |
| `auth_method` | `otp` or `password`. |

| `group` | Role |
|---|---|
| `Principal Exec` | Ejecutivo principal |
| `Secondary Exec` | Ejecutivo secundario |
| `Employees` | Empleado |

`Admins` also exists, but it is for platform operators, who are created by hand ([`user-onboarding.md`](user-onboarding.md#adding-another-operator)), never imported.

**`auth_method`:**

- `otp` — the person logs in with a code sent to their email. Use it whenever their email accepts external mail.
- `password` — for companies that block external email. The import generates a 9-digit **código de acceso**; the person uses it once at `/cuentas/primer-ingreso/` and sets their own password.

**Not in the file:** names, sexo, fecha de nacimiento, área and localidad. Each person enters these when they activate their account.

### Header rules

- The header row must contain the four column names exactly, in lowercase. A missing or misspelled header (`Email`, `grupo`) rejects the whole file, with a message naming what is missing — nothing is half-imported.
- Any extra column is ignored, so a roster exported from another system can be uploaded as is. That cuts both ways: an `area` column is not applied.
- Column order doesn't matter.

## Example

```csv
email,company_reference_code,group,auth_method
direccion@empresa.com,A1B2C,Principal Exec,otp
rh@empresa.com,A1B2C,Secondary Exec,otp
ana.lopez@empresa.com,A1B2C,Employees,otp
carlos.ruiz@empresa.com,A1B2C,Employees,password
```

## Uploading

1. In `/admin/`, go to **Cuentas → Usuarios**.
2. Click **Importar colaboradores**. The page lists the required columns.
3. Choose the `.csv` file and click **Importar colaboradores**.
4. Download the import report and review it.

## The import report

One line per row in the file:

| Column | |
|---|---|
| `row_number` | The row's line in your file. |
| `email` | |
| `status` | `created` or `skipped`. |
| `message` | Why a row was skipped (see below), or *Usuario creado.* |
| `username` | The generated username. Nobody needs it to log in. |
| `setup_access_code` | The 9-digit código de acceso, for `password` rows that were created. Empty otherwise. |

The report is the only place the códigos de acceso are handed to you. An unused code is also visible to operators under **Cuentas → Códigos de acceso**.

### Skipped rows

| `message` | Fix |
|---|---|
| *Falta valor requerido: …* | Fill in the named column on that row. |
| *Email inválido.* | Correct the address. |
| *auth_method debe ser otp o password.* | Use one of those two values. |
| *No existe una empresa con ese reference_code.* | Check the Código de empresa. |
| *No existe un grupo con ese nombre.* | Write the group exactly as in the table above. |
| *Ya existe un usuario con ese email.* | The person is already on the platform; nothing to do. To change their company, group or login method, delete the user and import them again. |

Fix the skipped rows and upload a file containing only those rows. Created rows are never touched by a later import, so re-uploading the whole file is also safe: the rows already created are simply skipped again.

## Security

- Do not put códigos de acceso in the upload file; the import generates them.
- Treat the report as sensitive while it holds códigos de acceso. Keep it out of shared folders unless access is restricted, and send the codes only to the company's trusted HR contact, through an internal channel.
- If a código de acceso is exposed before it is used, delete that user under **Cuentas → Usuarios** and import their row again. The import skips an email that already exists, so the delete comes first; the new import generates a new code.
