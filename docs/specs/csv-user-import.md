# CSV User Import Specification

## Purpose

The CSV user import feature lets platform admins bulk-create pre-approved users from Django Admin. Each valid CSV row creates:

- one `accounts.User`
- one related `accounts.UserProfile`
- one group assignment
- optional password-fallback access for users who cannot receive OTP emails

This spec documents the current behavior so future refactors can safely add fields, rename columns, or move the feature to another UI without changing core guarantees unintentionally.

## Actors

- **Platform admin:** uploads the CSV from Django Admin.
- **Imported user:** receives access through OTP or temporary password fallback.
- **HR/company contact:** receives temporary passwords only when `auth_method=password`.

Company employees and normal company managers are out of scope for this version.

## Entry Point

The feature lives in Django Admin on the `User` changelist.

- Admin link label: `Importar usuarios desde CSV`
- Upload URL: `admin:accounts_user_import_csv`
- Upload template: `templates/admin/accounts/user/import_csv.html`
- Changelist override: `templates/admin/accounts/user/change_list.html`

The upload endpoint must require the same permission level as adding users.

## Input CSV Contract

Required headers:

```text
email,company_reference_code,group,auth_method
```

Optional headers:

```text
first_name,last_name,position
```

Current accepted `auth_method` values:

- `otp`
- `password`

Example:

```csv
email,company_reference_code,group,auth_method,first_name,last_name,position
ana.lopez@empresa.com,A1B2C,Employees,otp,Ana,Lopez,Analista
maria.santos@empresa.com,A1B2C,Employees,password,Maria,Santos,Coordinadora
```

Header names are part of the public import contract. Future changes should either preserve backward compatibility or include a migration/compatibility note in this spec.

## Normalization Rules

- Input files are decoded as UTF-8 with optional BOM support.
- Header names are stripped of surrounding whitespace.
- Row values are stripped of surrounding whitespace.
- `email` is lowercased before validation and storage.
- `company_reference_code` is uppercased before lookup.
- `auth_method` is lowercased before validation.
- Blank optional fields are saved as empty strings.
- Extra CSV columns are ignored.

## Validation Rules

File-level validation:

- Empty CSV files are rejected.
- Missing required headers reject the whole file.
- Non-UTF-8 files are rejected by the admin form view.
- Files must use the `.csv` extension.

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
- Save `first_name` and `last_name` from optional CSV fields or `""`.
- Assign exactly one Django group from the `group` column.
- Create `UserProfile` with:
  - `user`: the created user
  - `company`: company matched by `company_reference_code`
  - `position`: optional CSV value or `""`
  - `is_activated=False`

For `auth_method=otp`:

- Set an unusable password.
- Set `must_change_password=False`.
- Do not generate a temporary password.

For `auth_method=password`:

- Generate a strong temporary password.
- Store it using Django password hashing.
- Set `must_change_password=True`.
- Include the plaintext temporary password only in the downloaded report.

Existing users are never updated by this importer.

## Output Report Contract

After a successful upload, the admin receives a downloadable CSV report.

Report headers:

```text
row_number,email,status,message,username,temporary_password
```

Rules:

- `status` is either `created` or `skipped`.
- `row_number` uses spreadsheet-style numbering, where the first data row is `2`.
- `temporary_password` is populated only when a `password` row is created.
- Skipped rows include an explanatory `message`.
- The report is the only place generated temporary passwords are shown in plaintext.

## Security Invariants

- Generated temporary passwords must not be persisted in plaintext.
- Temporary passwords must be shown only in the report download.
- Users imported with temporary passwords must have `must_change_password=True`.
- OTP users must not receive usable passwords.
- The company reference code is not an authentication secret and must not be treated as a password.
- Import reports containing temporary passwords are sensitive operational artifacts.

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

## Acceptance Criteria

Given a valid `otp` row, when the CSV is imported, then a user is created with an unusable password, `must_change_password=False`, the selected group, and a linked inactive profile.

Given a valid `password` row, when the CSV is imported, then a user is created with a usable generated password, `must_change_password=True`, the selected group, a linked inactive profile, and the generated password in the report.

Given a CSV with a duplicate email, when the CSV is imported, then that row is skipped and the existing user is not modified.

Given a CSV with valid and invalid rows, when the CSV is imported, then valid rows are created and invalid rows are skipped with report messages.

Given a row with an unknown company reference code, unknown group, invalid email, missing required value, or invalid `auth_method`, when the CSV is imported, then that row is skipped.

Given optional fields are blank, when the row is valid, then the user/profile is created with empty strings for those fields.

Given an email local part collides with an existing username, when the row is valid, then the importer generates a unique username.

## Refactoring Guidelines

When adding fields:

- Decide whether the field is required or optional.
- Update the input CSV contract.
- Define normalization and blank-value behavior.
- Add row-level validation if needed.
- Update the report only if admins need visibility into the result.
- Add acceptance criteria and tests for the new field.

When renaming columns:

- Prefer accepting both old and new headers for at least one transition period.
- Document which header is canonical.
- Add tests for backward compatibility.

When moving to a platform UI:

- Preserve the importer service behavior.
- Add company scoping for non-platform admins.
- Decide whether company managers may assign groups or only import default employee users.
- Keep temporary password report handling explicit and secure.

When changing duplicate behavior:

- Update the non-goals and creation rules.
- Define exactly which fields can be updated.
- Ensure profile changes and group changes are transactional and auditable.
