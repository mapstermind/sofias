from django.contrib import admin

from apps.responses.models import Answer, Submission


class AnswerInline(admin.StackedInline):
    model = Answer
    extra = 0


@admin.register(Submission)
class SubmissionAdmin(admin.ModelAdmin):
    list_display = ["pk", "version", "respondent_identifier", "status", "started_at", "completed_at"]
    list_filter = ["status", "version__survey"]
    search_fields = ["respondent_identifier"]
    inlines = [AnswerInline]


@admin.register(Answer)
class AnswerAdmin(admin.ModelAdmin):
    list_display = ["pk", "submission", "question", "value"]
    list_filter = ["submission__version__survey"]
