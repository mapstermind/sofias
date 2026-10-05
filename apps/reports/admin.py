from django.contrib import admin

from apps.reports.models import Report, ReportSignatory


class ReportSignatoryInline(admin.TabularInline):
    model = ReportSignatory
    extra = 0


@admin.register(Report)
class ReportAdmin(admin.ModelAdmin):
    list_display = ("assignment", "status", "published_at")
    list_filter = ("status",)
    readonly_fields = ("status", "snapshot", "published_at", "published_by")
    inlines = [ReportSignatoryInline]
