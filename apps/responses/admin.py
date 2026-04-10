from django.contrib import admin

from apps.responses.models import Answer, SurveySubmission


class AnswerInline(admin.StackedInline):
    model = Answer
    extra = 0


@admin.register(SurveySubmission)
class SurveySubmissionAdmin(admin.ModelAdmin):
    list_display = ["pk", "assignment", "user", "status", "started_at", "completed_at"]
    list_filter = ["status", "assignment__company", "assignment__version__template"]
    search_fields = ["user__username", "user__email"]
    inlines = [AnswerInline]


@admin.register(Answer)
class AnswerAdmin(admin.ModelAdmin):
    list_display = ["pk", "submission", "question", "value"]
    list_filter = ["submission__assignment__version__template"]
