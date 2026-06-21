from django.contrib import admin

from apps.surveys.models import (
    Choice,
    Module,
    Question,
    Survey,
    SurveyAssignment,
)

# ---------------------------------------------------------------------------
# Surveys, modules, questions
# ---------------------------------------------------------------------------


class ModuleInline(admin.TabularInline):
    model = Module
    extra = 0
    show_change_link = True


@admin.register(Survey)
class SurveyAdmin(admin.ModelAdmin):
    list_display = ["key", "title", "status", "headcount_threshold", "updated_at"]
    list_filter = ["status"]
    search_fields = ["key", "title"]
    prepopulated_fields = {"key": ("title",)}
    inlines = [ModuleInline]


class QuestionInline(admin.StackedInline):
    model = Question
    extra = 0
    show_change_link = True
    fields = ["code", "question_type", "text", "order", "config", "visible_when"]


@admin.register(Module)
class ModuleAdmin(admin.ModelAdmin):
    list_display = ["key", "survey", "title", "applies_to", "order"]
    list_filter = ["survey", "applies_to"]
    search_fields = ["key", "title"]
    inlines = [QuestionInline]


class ChoiceInline(admin.TabularInline):
    model = Choice
    extra = 0


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ["code", "text", "question_type", "module", "order"]
    list_filter = ["question_type", "survey", "module__applies_to"]
    search_fields = ["code", "text"]
    inlines = [ChoiceInline]


@admin.register(Choice)
class ChoiceAdmin(admin.ModelAdmin):
    list_display = ["label", "value", "question", "order"]
    list_filter = ["question__survey"]


# ---------------------------------------------------------------------------
# Assignments
# ---------------------------------------------------------------------------


@admin.register(SurveyAssignment)
class SurveyAssignmentAdmin(admin.ModelAdmin):
    list_display = ["company", "survey", "variant", "status", "due_date", "created_at"]
    list_filter = ["status", "variant", "company", "survey"]
    search_fields = ["company__name"]
