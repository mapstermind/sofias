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