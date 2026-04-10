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