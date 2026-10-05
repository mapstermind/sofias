from django.contrib import admin

from apps.reports.models import Report, ReportSignatory


def _published(obj) -> bool:
    return obj is not None and obj.status == Report.Status.PUBLISHED


class ReportSignatoryInline(admin.TabularInline):
    """Signatories render live in the report, so a published one's are frozen."""

    model = ReportSignatory
    extra = 0

    def has_add_permission(self, request, obj=None):
        return not _published(obj) and super().has_add_permission(request, obj)

    def has_change_permission(self, request, obj=None):
        return not _published(obj) and super().has_change_permission(request, obj)

    def has_delete_permission(self, request, obj=None):
        return not _published(obj) and super().has_delete_permission(request, obj)


@admin.register(Report)
class ReportAdmin(admin.ModelAdmin):
    list_display = ("assignment", "status", "published_at")
    list_filter = ("status",)
    readonly_fields = ("status", "snapshot", "published_at", "published_by")
    inlines = [ReportSignatoryInline]

    def get_readonly_fields(self, request, obj=None):
        """A published report is frozen: every field is read-only."""
        if _published(obj):
            editable = [
                f.name
                for f in self.model._meta.fields
                if f.editable and not f.primary_key
            ]
            return [*editable, *(f for f in self.readonly_fields if f not in editable)]
        return super().get_readonly_fields(request, obj)
