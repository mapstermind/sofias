# Testing and Spec Migration

## Current state summary

SOFIA-S already uses pytest with pytest-django. Tests are colocated under app-level `tests/` packages for `accounts`, `core`, `surveys`, and `responses`. `apps/analytics/tests.py` and `apps/reports/tests.py` were empty Django-generated placeholders and were quarantined under `tests/legacy/`.

The repository had one durable spec at `specs/csv-user-import.md`, user/operator docs under `docs/`, root-level workflow/database docs, and temporary notes at the root. The main project README remains at the root.

## Target state

- Durable functional specs live under `docs/specs/`.
- User/operator docs live under `docs/user/`.
- Meaningful ADRs live under `docs/adr/`.
- Temporary PRDs, test plans, refactor plans, migration notes, and working notes live under `docs/workflow/`.
- New tests stay app-local unless there is a clear cross-app reason for a root-level test.
- Weak legacy tests live under `tests/legacy/` until their useful behavior has been replaced.

## Existing docs migration performed

- `specs/csv-user-import.md` -> `docs/specs/csv-user-import.md`
- `database.md` -> `docs/specs/database.md`
- `WORKFLOWS.md` -> `docs/user/interactive-workflows.md`
- `docs/CSV_USER_IMPORT.md` -> `docs/user/csv-user-import.md`
- `docs/USER_ONBOARDING.md` -> `docs/user/user-onboarding.md`
- `keep_in_mind.md` -> `docs/workflow/keep-in-mind.md`

`README.md` remains at the repository root. `CLAUDE.md` remains at the repository root because Claude Code tooling may expect it there, but it should be reconciled with `AGENTS.md` if still used.

Ignored personal notes in `client_meetings/` and `gerry_notas.md` were not moved because they are gitignored local notes. Review them manually and promote durable product intent into specs, user docs, tests, or ADRs before deleting or archiving them.

## Existing tests classification

Meaningful behavior tests:

- `apps/accounts/tests/test_importers.py`: CSV user import behavior, validation, group/profile creation, temporary password reporting.
- `apps/accounts/tests/test_models.py`: OTP validity, company reference code generation, unique username behavior.
- `apps/accounts/tests/test_forms.py`: OTP/email/reference-code form validation.
- `apps/accounts/tests/test_views.py`: OTP flow, password fallback, forced password change, profile activation, logout.
- `apps/core/tests/test_views.py`: auth/permission behavior, dashboard/list/detail views, representative minimum behavior, employee survey visibility and progress.
- `apps/surveys/tests/test_models.py`: template stamping and survey version uniqueness.
- `apps/surveys/tests/test_views.py`: survey display, submission, validation errors, closed assignments, submitted page.
- `apps/responses/tests/test_models.py`: answer uniqueness constraints.

Useful but implementation-coupled or smoke-style tests:

- `apps/core/tests/test_workflows.py::TestWorkflowImports`: import smoke tests.
- `apps/core/tests/test_workflows.py::TestRunCreateSurvey::test_answering_yes_chains_into_create_question`: asserts an internal function call.
- `apps/core/tests/test_views.py::test_representative_minimum_formula`: directly tests a private helper, though the formula appears to represent business behavior.

Quarantined legacy tests:

- `tests/legacy/analytics_tests.py`: empty placeholder from `apps/analytics/tests.py`.
- `tests/legacy/reports_tests.py`: empty placeholder from `apps/reports/tests.py`.

## Recommended first specs to write

- `docs/specs/auth-and-onboarding.md`: OTP login, password fallback, forced password change, profile activation, admin bypass, session behavior.
- `docs/specs/company-dashboard-and-employee-visibility.md`: company scoping, dashboard metrics, representative minimum, employee list/detail permissions.
- `docs/specs/survey-response-flow.md`: survey detail, autosave, in-progress vs completed submissions, closed/completed behavior, answer value parsing.
- `docs/specs/survey-builder-workflows.md`: interactive management commands and question/template/section/choice workflows.

## Recommended first characterization tests to write

- Autosave behavior in `apps/surveys/views.py`, including partial answer deletion, invalid numeric values, unauthenticated requests, and closed assignments.
- Employee detail answer visibility rules for `can_manage_employees` versus `can_view_submissions`.
- Admin CSV import view permission, UTF-8 handling, downloaded report response headers, and invalid file handling.
- Survey admin question template stamping with mismatched section/version behavior, if preserving current behavior before fixing it.

## Risks

- `analytics` and `reports` apps exist but are skeletons and are not currently installed in `INSTALLED_APPS`.
- `CLAUDE.md` contains stale notes about app registration and URL wiring.
- `docs/specs/database.md` and `docs/user/interactive-workflows.md` were moved as existing docs but need currentness review against the current models and workflow commands.
- Some tests assert template context shape rather than rendered public output; this is acceptable for Django server-rendered views but should be kept focused on behavior.
- Temporary planning notes may contain durable product intent that has not yet been promoted into specs.

## Next actions

1. Choose one high-value area, preferably auth/onboarding or survey response flow.
2. Write a durable spec from current behavior.
3. Add a temporary test plan only if the test surface is unclear.
4. Add characterization tests for current gaps before refactoring.
5. Replace implementation-coupled tests opportunistically only after behavior is covered.

## Deletion candidates after migration

- Feature-specific PRDs, test plans, and refactor plans under `docs/workflow/` once their durable value has moved into specs, tests, user docs, or ADRs.
- `docs/workflow/keep-in-mind.md` after its permission, verification, and admin-stamping notes are promoted into specs or user docs.
- Ignored personal notes in `client_meetings/` and `gerry_notas.md` after durable product intent is promoted.
