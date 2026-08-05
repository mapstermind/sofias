# Sample data

Hand-upload fixtures for the CSV user import at
**Django Admin → Users → Importar usuarios desde CSV**. They exist to exercise the
importer by hand; no test loads them.

The contract they follow is `docs/platform/csv-user-import.md`: four required
headers, no optional ones. Name, cargo, área and localidad are collected from the
employee at activation, so no fixture here carries them.

| File | What it exercises | Expected result |
|---|---|---|
| `users_seed.csv` | The happy path across two companies, three groups, and both `auth_method` values | 8 users created; the 3 `password` rows carry a setup access code in the report |
| `users_mixed_validation.csv` | Every row-level skip reason: duplicate email, unknown company, unknown group, malformed email, missing `auth_method`, unsupported `auth_method` | 2 created, 6 skipped, each skip with its reason in the report. The duplicate pair accounts for one of the creations — the first `duplicado@acme.mx` row creates the user and only the second is skipped |
| `users_extra_columns.csv` | Extra columns are ignored — including `area`, which must **not** resolve to a catalog entry | 2 users created with no name and `area=None` |
| `users_bad_header.csv` | A misspelled required header (`grupo` for `group`) | Whole file rejected before any row is read; no users created |

`users_seed.csv` and `users_mixed_validation.csv` expect companies with reference
codes `ACME1` and `GLOBX`, and the groups from `python manage.py bootstrap_groups`.
Reference codes are generated, not chosen, so create the companies first and edit
the codes in these files to match.

Load at least one **área** on each company before importing. Employees cannot
finish activation without one, so a company with no áreas leaves every imported
user stuck at the activation screen.
