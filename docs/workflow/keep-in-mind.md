One thing to keep in mind as you build views

  When checking permissions in a view, use the accounts. prefix because the permissions are owned by the accounts app:

  # decorator
  @permission_required("accounts.can_view_dashboard")

  # mixin
  class DashboardView(PermissionRequiredMixin, View):
      permission_required = "accounts.can_view_dashboard"

  # manual check
  if request.user.has_perm("accounts.can_view_dashboard"):
      ...

  And remember — the permission is the gate, the queryset is the scope. A Principal Exec and an Admin both pass can_view_dashboard,
  but the view filters Company objects differently depending on which group the user belongs to.



  -------------------


Verification

 # First run: creates test DB
 pytest

 # After setup, should see 0 failures from the config step:
 pytest --collect-only   # lists all discovered tests

 # Run by tier as you write them:
 pytest apps/accounts/tests/test_models.py   # Tier 1
 pytest apps/accounts/tests/test_views.py    # Tier 2
 pytest apps/core/tests/test_views.py        # Tier 3
 pytest apps/surveys/tests/                  # Tier 4

 # Force DB recreation after migrations change:
 pytest --create-db

 After all tiers: pytest with no args should pass with --reuse-db fast runs on subsequent executions


  -------------------
Note on using stamp_into() in admin console.

   One thing to watch out for: the Section dropdown shows all sections across all versions. Make sure the section you pick belongs to
  the same version you selected — there's no filtering between the two dropdowns yet. If you pick a mismatched section and version,
  Django will create the question linked to the section's version via the section FK, but the version FK will point elsewhere, which
  would be inconsistent. For now, either leave Section blank or double-check the pairing.