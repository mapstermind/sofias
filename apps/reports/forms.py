"""The Administrador's report form and its ordered signatory rows."""

from django import forms
from django.forms import BaseInlineFormSet, inlineformset_factory
from django.forms.formsets import ORDERING_FIELD_NAME

from apps.reports.models import Report, ReportSignatory
from apps.reports.publishing import REQUIRED


def _text(**attrs):
    return forms.TextInput(attrs=attrs)


def _number():
    return forms.NumberInput(attrs={"min": 0})


def _textarea():
    return forms.Textarea(attrs={"rows": 5})


class ReportForm(forms.ModelForm):
    class Meta:
        model = Report
        fields = (
            "issued_in",
            "activities_summary",
            "headcount_in_person",
            "headcount_home_office",
            "headcount_hybrid",
            "evaluator_name",
            "evaluator_license",
            "additional_recommendations",
            "conclusions",
        )
        widgets = {
            "issued_in": _text(),
            "activities_summary": _textarea(),
            "headcount_in_person": _number(),
            "headcount_home_office": _number(),
            "headcount_hybrid": _number(),
            "evaluator_name": _text(),
            "evaluator_license": _text(),
            "additional_recommendations": _textarea(),
            "conclusions": _textarea(),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Optional on save, so a draft can be half-written; publishing refuses
        # without them, so the form says so instead of "(opcional)".
        for name, _label in REQUIRED:
            field = self.fields[name]
            field.shown_as_required = True
            field.help_text = "Necesario para publicar."


class BaseSignatoryFormSet(BaseInlineFormSet):
    """Rows keep the order they are shown in; blank rows and DELETE are honoured."""

    ordering_widget = forms.HiddenInput

    def add_fields(self, form, index):
        super().add_fields(form, index)
        if index is not None:
            # Every row, extra rows included, starts at its position, so an
            # untouched blank row posts back unchanged and is skipped.
            form.fields[ORDERING_FIELD_NAME].initial = index + 1

    def save(self, commit=True):
        super().save(commit=False)
        for obj in self.deleted_objects:
            obj.delete()
        saved = []
        for position, form in enumerate(self.ordered_forms, start=1):
            obj = form.instance
            obj.report = self.instance
            obj.order = position
            obj.save()
            saved.append(obj)
        return saved


SignatoryFormSet = inlineformset_factory(
    Report,
    ReportSignatory,
    formset=BaseSignatoryFormSet,
    fields=("title", "name"),
    widgets={"title": _text(), "name": _text()},
    extra=1,
    can_delete=True,
    can_order=True,
)
