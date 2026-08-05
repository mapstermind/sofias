# CSV User Import

## Purpose

The CSV user import feature lets platform admins bulk-create pre-approved users from Django Admin. Each valid CSV row creates:

- one `accounts.User`
- one related `accounts.UserProfile`
- one group assignment
- optional setup-code fallback access for users who cannot receive OTP emails

The import carries **only what grants access to an account**: who it is (`email`), which company it belongs to, what it may do (`group`), and how it logs in (`auth_method`). Everything an employee knows about themselves — nombre, cargo, área, localidad — is collected from them at activation instead, which keeps the admin's roster to four columns and makes the employee the source of their own details. See `docs/platform/auth-and-onboarding.md` §Profile activation for the other half of the flow.

This document captures the current behavior so future refactors can safely add fields, rename columns, or move the feature to another UI without changing core guarantees unintentionally.

## Actors

- **Platform admin:** uploads the CSV from Django Admin.
- **Imported user:** receives access through OTP or setup-code fallback.
- **HR/company contact:** receives setup access codes only when `auth_method=password`.

Company employees and normal company managers are out of scope for this version.

## Entry Point

The feature lives in Django Admin on the `User` changelist.

- Admin link label: `Importar usuarios desde CSV`
- Upload URL: `admin:accounts_user_import_csv`
- Upload template: `templates/admin/accounts/user/import_csv.html`
- Changelist override: `templates/admin/accounts/user/change_list.html`

The upload endpoint must require the same permission level as adding users.

## Input CSV Contract

These four headers are the whole contract, and all of them are required:

```text
email,company_reference_code,group,auth_method
```

There are no optional headers. Any additional column is ignored — a roster exported from another system can be uploaded as-is without stripping its extra columns first, and no extra column assigns anything. In particular an `area` column does **not** resolve to a `CompanyArea`; the employee picks their área at activation.

Current accepted `auth_method` values:

- `otp`
- `password`

Example:

```csv
email,company_reference_code,group,auth_method
ana.lopez@empresa.com,A1B2C,Employees,otp
maria.santos@empresa.com,A1B2C,Employees,password
```

Header names are part of the public import contract. Because every header is required, a misspelled one (`Email`, `grupo`) rejects the whole file with a message naming what is missing, rather than silently importing rows with a field unset.

## Normalization Rules

- Header names are stripped of surrounding whitespace.
- Row values are stripped of surrounding whitespace.
- `email` is lowercased before validation and storage.
- `company_reference_code` is uppercased before lookup.
- `auth_method` is lowercased before validation.
- Extra CSV columns are ignored.

## Validation Rules

File-level validation splits across two layers. `import_users_from_csv` receives an already-decoded `str`, so everything about the *file* is enforced by the admin upload form and view before the importer is called:

| Rule | Enforced by |
|---|---|
| Files must use the `.csv` extension | `UserCSVImportForm.clean_csv_file` |
| Files are decoded as UTF-8, BOM tolerated | `CustomUserAdmin.import_csv_view` (`utf-8-sig`) |
| Non-UTF-8 files are rejected with a field error | `CustomUserAdmin.import_csv_view` |
| Empty CSV files are rejected | `import_users_from_csv` |
| Missing required headers reject the whole file | `import_users_from_csv` |

A second entry point that calls the importer directly gets the last two rules and must supply the first three itself.

Row-level validation:

- Missing required values skip the row.
- Invalid email format skips the row.
- Unknown `Company.reference_code` skips the row.
- Unknown Django group name skips the row.
- Unsupported `auth_method` skips the row.
- Duplicate `User.email` skips the row.

Skipped rows must not create or update any database records.

## Creation Rules

Each valid row is processed independently. Valid rows are created even if other rows are skipped.

For every created row:

- Generate `username` from the email local part using `generate_unique_username`.
- Create `User.email` from the normalized email.
- Assign exactly one Django group from the `group` column.
- Create `UserProfile` with:
  - `user`: the created user
  - `company`: company matched by `company_reference_code`
  - `is_activated=False`

`User.first_name`, `User.last_name`, `UserProfile.position`, `UserProfile.area`, and `UserProfile.location` are left at their blank/null defaults. The employee fills them in at activation, and until they do the roster renders them as *Sin nombre* / *Sin cargo*.

For `auth_method=otp`:

- Set an unusable password.
- Set `must_change_password=False`.
- Do not generate a setup access code.

For `auth_method=password`:

- Generate a 9-digit setup access code.
- Create a linked `SetupAccessCode` with the generated code.
- Keep the user's password unusable at import time.
- Set `must_change_password=True`.
- Include the setup access code in the downloaded report.

Existing users are never updated by this importer.

## Output Report Contract

After a successful upload, the admin receives a downloadable CSV report.

Report headers:

```text
row_number,email,status,message,username,setup_access_code
```

Rules:

- `status` is either `created` or `skipped`.
- `row_number` uses spreadsheet-style numbering, where the first data row is `2`.
- `setup_access_code` is populated only when a `password` row is created.
- Every row includes a `message`: created rows carry a confirmation (e.g. `Usuario creado.`), and skipped rows carry an explanation of why they were skipped.
- The report includes generated setup access codes for created fallback users.

## Security Invariants

- Users imported with setup access codes must have unusable passwords until they create one.
- Users imported with setup access codes must have `must_change_password=True`.
- Used setup access code rows must clear the consumed code value.
- OTP users must not receive usable passwords.
- The company reference code is not an authentication secret and must not be treated as a password.
- Import reports containing setup access codes are sensitive operational artifacts.

## Non-Goals

The current feature does not:

- create companies
- create groups
- update existing users
- update existing profiles
- support multiple groups per row
- persist import batches or upload history
- preview imports before creation
- let company managers upload users from the platform UI
- carry any employee-supplied detail (nombre, cargo, área, localidad)

## Acceptance Criteria

Given a valid `otp` row, when the CSV is imported, then a user is created with an unusable password, `must_change_password=False`, the selected group, and a linked inactive profile.

Given a valid `password` row, when the CSV is imported, then a user is created with an unusable password, `must_change_password=True`, the selected group, a linked inactive profile, one setup access code, and the setup access code in the report.

Given a CSV with a duplicate email, when the CSV is imported, then that row is skipped and the existing user is not modified.

Given a CSV with valid and invalid rows, when the CSV is imported, then valid rows are created and invalid rows are skipped with report messages.

Given a row with an unknown company reference code, unknown group, invalid email, missing required value, or invalid `auth_method`, when the CSV is imported, then that row is skipped.

Given a CSV carrying extra columns, when the CSV is imported, then those columns are ignored, the rows are created, and no área is assigned from them.

Given a created row, when the import finishes, then the user has no name, cargo, área, or localidad, and the report message is exactly `Usuario creado.`

Given an email local part collides with an existing username, when the row is valid, then the importer generates a unique username.

## Refactoring Guidelines

When adding fields:

- First ask whether the admin can actually know the value. If it is something only the employee knows, it belongs on the activation form, not in the CSV.
- If it does belong here, make it required. There are no optional headers, and that is what lets a misspelled header fail loudly instead of importing a column's worth of blanks.
- Update the input CSV contract and `REQUIRED_HEADERS`, which the admin upload page reads directly so the two cannot drift.
- Define normalization behavior.
- Add row-level validation if needed.
- Update the report only if admins need visibility into the result.
- Add acceptance criteria and tests for the new field.

When renaming columns:

- Rename outright and update this document, the admin upload page, and the user guide together. The platform is pre-production, so there is no transition period to support and no back-compatibility alias to carry (see `.claude/CLAUDE.md`).
- Existing CSVs are re-exported, not migrated.

When moving to a platform UI:

- Preserve the importer service behavior.
- Add company scoping for non-platform admins.
- Decide whether company managers may assign groups or only import default employee users.
- Keep setup access code report handling explicit and secure.

When changing duplicate behavior:

- Update the non-goals and creation rules.
- Define exactly which fields can be updated.
- Ensure profile changes and group changes are transactional and auditable.
