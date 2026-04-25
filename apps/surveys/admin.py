from django.contrib import admin, messages
from django.db.models import Max
from django.shortcuts import render

from apps.surveys.models import (
    Choice,
    ChoiceTemplate,
    Question,
    QuestionTemplate,
    Section,
    SurveyAssignment,
    SurveyTemplate,
    SurveyVersion,
)

# ---------------------------------------------------------------------------
# Question library
# ---------------------------------------------------------------------------


class ChoiceTemplateInline(admin.TabularInline):
    model = ChoiceTemplate
    extra = 1


@admin.register(QuestionTemplate)
class QuestionTemplateAdmin(admin.ModelAdmin):
    list_display = ["text", "question_type", "updated_at"]
    list_filter = ["question_type"]
    search_fields = ["text"]
    inlines = [ChoiceTemplateInline]
    actions = ["stamp_into_version"]

    @admin.action(description="Stamp into survey version")
    def stamp_into_version(self, request, queryset):
        if request.POST.get("confirm"):
            version = SurveyVersion.objects.get(pk=request.POST["version_id"])
            section_id = request.POST.get("section_id") or None
            section = Section.objects.get(pk=section_id) if section_id else None

            current_max = version.questions.aggregate(Max("order"))["order__max"] or -1
            next_order = current_max + 1

            for template in queryset:
                template.stamp_into(version=version, section=section, order=next_order)
                next_order += 1

            self.message_user(
                request,
                f"{queryset.count()} question(s) stamped into {version}.",
                messages.SUCCESS,
            )
            return

        return render(
            request,
            "admin/surveys/stamp_into_version.html",
            {
                "queryset": queryset,
                "versions": SurveyVersion.objects.select_related("template").order_by(
                    "template__title", "version_number"
                ),
                "sections": Section.objects.select_related(
                    "version__template"
                ).order_by("version__template__title", "title"),
                "opts": self.model._meta,
            },
        )


# ---------------------------------------------------------------------------
# Survey templates & versions
# ---------------------------------------------------------------------------


class SurveyVersionInline(admin.TabularInline):
    model = SurveyVersion
    extra = 0
    show_change_link = True


@admin.register(SurveyTemplate)
class SurveyTemplateAdmin(admin.ModelAdmin):
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
    list_display = ["template", "version_number", "published_at", "created_at"]
    list_filter = ["template"]
    inlines = [SectionInline, QuestionInline]


class ChoiceInline(admin.TabularInline):
    model = Choice
    extra = 0


@admin.register(Section)
class SectionAdmin(admin.ModelAdmin):
    list_display = ["title", "version", "order"]
    list_filter = ["version__template"]


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ["text", "question_type", "version", "section", "source", "order"]
    list_filter = ["question_type", "version__template"]
    search_fields = ["text"]
    autocomplete_fields = ["source"]
    inlines = [ChoiceInline]


@admin.register(Choice)
class ChoiceAdmin(admin.ModelAdmin):
    list_display = ["label", "value", "question", "source", "order"]
    list_filter = ["question__version__template"]


# ---------------------------------------------------------------------------
# Assignments
# ---------------------------------------------------------------------------


class SurveyAssignmentInline(admin.TabularInline):
    model = SurveyAssignment
    extra = 0
    show_change_link = True


@admin.register(SurveyAssignment)
class SurveyAssignmentAdmin(admin.ModelAdmin):
    list_display = ["company", "version", "status", "due_date", "created_at"]
    list_filter = ["status", "company", "version__template"]
    search_fields = ["company__name"]
