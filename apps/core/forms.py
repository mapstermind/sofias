"""The project form renderer: every Django form draws its fields through
templates/forms/field.html, so no form carries widget classes. See
docs/platform/design-system.md (Components)."""

from django.forms.renderers import TemplatesSetting


class SofiaFormRenderer(TemplatesSetting):
    form_template_name = "forms/form.html"
    field_template_name = "forms/field.html"
