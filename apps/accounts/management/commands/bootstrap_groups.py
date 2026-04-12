"""
Creates (or re-syncs) the four authorization groups and their permissions.

Safe to run multiple times — all operations are idempotent.

Usage:
    python manage.py bootstrap_groups
"""

from django.contrib.auth.models import Group, Permission
from django.core.management.base import BaseCommand

# Maps each group name to the permission codenames it should hold.
GROUP_PERMISSIONS: dict[str, list[str]] = {
    "Admins": [
        "can_manage_site_configuration",
        "can_manage_users",
        "can_manage_surveys",
        "can_assign_surveys",
        "can_view_dashboard",
        "can_view_reports",
        "can_view_insights",
    ],
    "Principal Exec": [
        "can_view_dashboard",
        "can_view_reports",
        "can_view_insights",
    ],
    "Secondary Exec": [
        "can_view_dashboard",
        "can_view_reports",
    ],
    "Employees": [
        "can_take_assigned_surveys",
    ],
}


class Command(BaseCommand):
    help = "Create authorization groups and assign their permissions. Safe to re-run."

    def handle(self, *args, **options):
        # Fetch all custom permissions defined on Role in one query.
        codenames = [p for perms in GROUP_PERMISSIONS.values() for p in perms]
        permissions = Permission.objects.filter(codename__in=codenames)
        perm_map = {p.codename: p for p in permissions}

        missing = set(codenames) - perm_map.keys()
        if missing:
            self.stderr.write(
                self.style.ERROR(
                    f"The following permissions were not found in the database: "
                    f"{', '.join(sorted(missing))}.\n"
                    f"Run 'python manage.py migrate' first to register them."
                )
            )
            return

        for group_name, codenames in GROUP_PERMISSIONS.items():
            group, created = Group.objects.get_or_create(name=group_name)
            expected = {perm_map[c] for c in codenames}
            group.permissions.set(expected)

            status = "created" if created else "updated"
            self.stdout.write(
                self.style.SUCCESS(f"  {status:7s}  {group_name}")
                + f"  ({len(expected)} permissions)"
            )

        self.stdout.write(self.style.SUCCESS("\nDone."))
