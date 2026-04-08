from django.contrib import admin

from apps.surveys.models import Choice, Question, Section, Survey, SurveyVersion


class SurveyVersionInline(admin.TabularInline):
    model = SurveyVersion
    extra = 0
    show_change_link = True


@admin.register(Survey)
class SurveyAdmin(admin.ModelAdmin):
    list_display = ["title", "status", "created_at", "updated_at"]
    list_filter = ["status"]
    search_fields = ["title"]
    inlines = [SurveyVersionInline]


class SectionInline(admin.TabularInline):
    model = Section
    extra = 0
    show_change_link = True


class QuestionInline(admin.StackedInline):
    model = Question
    extra = 0
    show_change_link = True


@admin.register(SurveyVersion)
class SurveyVersionAdmin(admin.ModelAdmin):
    list_display = ["survey", "version_number", "published_at", "created_at"]
    list_filter = ["survey"]
    inlines = [SectionInline, QuestionInline]


class ChoiceInline(admin.TabularInline):
    model = Choice
    extra = 0


@admin.register(Section)
class SectionAdmin(admin.ModelAdmin):
    list_display = ["title", "version", "order"]
    list_filter = ["version__survey"]


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ["text", "question_type", "version", "section", "required", "order"]
    list_filter = ["question_type", "required", "version__survey"]
    search_fields = ["text"]
    inlines = [ChoiceInline]


@admin.register(Choice)
class ChoiceAdmin(admin.ModelAdmin):
    list_display = ["label", "value", "question", "order"]
    list_filter = ["question__version__survey"]
