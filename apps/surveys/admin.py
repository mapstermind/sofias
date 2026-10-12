from django import forms
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


class SurveyAssignmentAdminForm(forms.ModelForm):
    """
    On a new assignment the variant may be left on *Automática*: it is then
    resolved from the company's headcount when the form validates. Picking a
    variant is the operator's override. Once saved, the variant is frozen and
    the change form shows it as a plain required choice.
    """

    AUTOMATIC_LABEL = "Automática (según número de colaboradores)"

    class Meta:
        model = SurveyAssignment
        fields = "__all__"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.variant_was_resolved = False
        if self.instance.pk is None:
            variant = self.fields["variant"]
            variant.required = False
            variant.choices = [
                ("", self.AUTOMATIC_LABEL),
                *SurveyAssignment.Variant.choices,
            ]
            variant.help_text = (
                "Automática elige Guía III si la empresa tiene más colaboradores "
                "que el umbral de plantilla de la encuesta, y Guía II si no. "
                "Importa a los colaboradores antes de asignar. "
                "Se fija al guardar."
            )

    def clean(self):
        cleaned = super().clean()
        company, survey = cleaned.get("company"), cleaned.get("survey")
        if (
            self.instance.pk is None
            and not cleaned.get("variant")
            and company
            and survey
        ):
            cleaned["variant"] = SurveyAssignment.resolve_default_variant(
                company, survey
            )
            self.variant_was_resolved = True
        return cleaned


@admin.register(SurveyAssignment)
class SurveyAssignmentAdmin(admin.ModelAdmin):
    form = SurveyAssignmentAdminForm
    list_display = ["company", "survey", "variant", "status", "due_date", "created_at"]
    list_filter = ["status", "variant", "company", "survey"]
    search_fields = ["company__name"]

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        if form.variant_was_resolved:
            members = obj.company.members.count()
            self.message_user(
                request,
                f"Variante asignada automáticamente: {obj.get_variant_display()} "
                f"({members} colaboradores en {obj.company}).",
            )
