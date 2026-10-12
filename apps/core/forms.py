"""The project form renderer: every Django form draws its fields through
templates/forms/field.html, so no form carries widget classes. See
docs/platform/design-system.md (Components)."""

from django import forms
from django.forms.renderers import TemplatesSetting


class SofiaFormRenderer(TemplatesSetting):
    form_template_name = "forms/form.html"
    field_template_name = "forms/field.html"


class ErrorFocusMixin:
    """After a failed submit, autofocus moves to the first field in error.

    A form that autofocuses its first field would otherwise put the cursor
    back at the top, away from the message it just showed.
    """

    def full_clean(self):
        super().full_clean()
        # A form-wide error (wrong password) names no field: focus stays put.
        first = next((name for name in self._errors or {} if name in self.fields), None)
        if first is None:
            return
        for field in self.fields.values():
            field.widget.attrs.pop("autofocus", None)
        self.fields[first].widget.attrs["autofocus"] = True


class LabelledSelectDateWidget(forms.SelectDateWidget):
    """A date as three selects, each named for a screen reader (Día, Mes, Año):
    the field's legend names the group, not the parts."""

    PART_LABELS = {"_day": "Día", "_month": "Mes", "_year": "Año"}

    def get_context(self, name, value, attrs):
        context = super().get_context(name, value, attrs)
        for sub in context["widget"]["subwidgets"]:
            for suffix, label in self.PART_LABELS.items():
                if sub["name"].endswith(suffix):
                    sub["attrs"] = {**sub["attrs"], "aria-label": label}
        return context
