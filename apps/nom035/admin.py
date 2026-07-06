from django.contrib import admin

from apps.nom035.models import GroupScore, SubmissionScore


class GroupScoreInline(admin.TabularInline):
    model = GroupScore
    extra = 0


@admin.register(SubmissionScore)
class SubmissionScoreAdmin(admin.ModelAdmin):
    list_display = (
        "submission",
        "final_ndr",
        "final_score",
        "guia1_positive",
        "computed_at",
    )
    inlines = [GroupScoreInline]
