# ADR 0001: Use Setup Access Codes for Blocked Email First Login

Date:
Status: Accepted (implemented)

## Context

SOFIA-S currently uses pre-created user accounts. The primary login path is email
OTP: a user enters their email address, SOFIA-S generates a short-lived code, and
the code is sent through Django's configured email backend.

Some client email policies may block messages from external senders, including
SOFIA-S. For those users, email OTP cannot be relied on for first login or later
login until the client allowlists SOFIA-S delivery.

The current CSV import fallback uses `auth_method=password`. For those rows,
SOFIA-S generates a temporary password, stores it as the user's real Django
password hash, includes the plaintext temporary password once in the import
report, and sets `User.must_change_password=True`. The user logs in through the
normal password form and must immediately change the password before continuing.

That approach works operationally, but the initial secret is still a normal
password until changed. It is accepted by the password login form, changes the
user's password state during import, and couples first-login bootstrap behavior
to the regular password authentication path.

The desired fallback should preserve the useful parts of the current flow:

- platform admins can bulk-create users from CSV
- client contacts can distribute first-login credentials through internal
  channels
- users blocked from receiving external email can still access SOFIA-S
- users must create a permanent password before normal application use
- future logins can use password login when email OTP remains unavailable

The implementation should use test-driven development. Behavior tests should be
written before production changes and should cover the importer, setup-code
verification, single-use guarantees, forced password creation, and future
password login.

## Decision

SOFIA-S will use one-time setup access codes as the backup first-login method for
users who cannot receive external OTP email.

The new model will be named `SetupAccessCode`.

CSV import will keep the existing `auth_method=password` value for backward
compatibility and operational clarity. However, its behavior will change:

- users imported with `auth_method=otp` continue to receive unusable passwords
  and use the email OTP path
- users imported with `auth_method=password` receive an unusable password at
  creation time
- SOFIA-S generates a one-time setup access code for each created
  `auth_method=password` user
- SOFIA-S stores the setup access code for support visibility
- the setup access code appears in the import report and Django Admin
- `User.must_change_password` remains the flag that forces password creation
  after setup-code verification

Setup access codes are bootstrap credentials, not passwords. They must only be
accepted by a dedicated first-login/setup-code flow. They must not work through
the normal password login form.

The setup-code flow will require the user to submit their email address and setup
access code. On valid verification, SOFIA-S will mark the code used, authenticate
the user, and redirect them to the existing required password-change flow. After
the user creates a permanent password, `User.must_change_password` is cleared and
future logins can use the normal password login path.

Setup access codes should be single-use and should not expire automatically.
Because unused codes remain visible in Django Admin for authorized support users,
the first implementation does not need setup-code regeneration.

## Consequences

Positive consequences:

- The fallback no longer stores the distributed first-login secret as the user's
  normal password.
- Setup access codes are limited to account bootstrap and cannot be reused for
  normal password login.
- Setup access codes are shorter and easier for non-technical users to handle.
- Authorized support users can recover unused setup codes from Django Admin
  without requiring regeneration or another client coordination step.
- The product language becomes clearer: client contacts distribute setup codes,
  while users create their own permanent passwords.
- Existing CSV files using `auth_method=password` can continue to work.
- The current `User.must_change_password` flow remains useful and does not need
  to be renamed for this change.
- Later enterprise options, such as SSO or email allowlisting, remain compatible
  with this decision.

Negative consequences:

- A new model, form, view, URL, template, and tests are required.
- CSV import behavior changes even though the `auth_method=password` value stays
  the same, so user-facing documentation must be explicit.
- Import reports and Django Admin records containing setup codes remain
  sensitive operational artifacts.
- Password login remains necessary for subsequent logins when email OTP delivery
  is blocked.
- Storing setup codes for admin visibility is less restrictive than hash-only
  storage and increases the importance of admin access control.

## Alternatives considered

- Keep the current temporary-password fallback.
  - This is simpler and already works, but the distributed first-login secret is
    a real password until changed.
- Generate email OTPs in bulk and distribute them internally.
  - This conflicts with the current OTP flow, which is request-time,
    session-bound, and short-lived. It also does not solve future logins unless
    the user creates a password or email delivery is fixed.
- Require client email allowlisting before launch.
  - This should remain a preferred operational step, but it cannot be the only
    fallback because client IT policies may delay or block allowlisting.
- Send codes through SMS or phone.
  - This avoids email policy issues, but it adds a new external dependency,
    phone-number handling, consent concerns, and privacy/security review.
- Use client SSO.
  - This is the best long-term enterprise authentication option for some
    clients, but it is too large to be the immediate backup for CSV-created
    users.

## Links

- Docs: `docs/platform/setup-access-codes.md`, `docs/platform/auth-and-onboarding.md`,
  `docs/platform/csv-user-import.md`
- User guides: `docs/internal/user-guides/csv-user-import.md`, `docs/internal/user-guides/user-onboarding.md`
