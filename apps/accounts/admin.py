from django import forms
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.core.exceptions import PermissionDenied, ValidationError
from django.db.models import Count
from django.http import HttpResponse
from django.template.response import TemplateResponse
from django.urls import path

from .forms import UserCSVImportForm
from .importers import (
    REQUIRED_HEADERS,
    import_users_from_csv,
    render_import_report_csv,
)
from .models import (
    Company,
    CompanyArea,
    CompanyLocation,
    SetupAccessCode,
    User,
    UserProfile,
    catalog_name_key,
    normalize_catalog_name,
)


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    change_list_template = "admin/accounts/user/change_list.html"
    list_display = UserAdmin.list_display + ("must_change_password",)
    fieldsets = UserAdmin.fieldsets + (
        ("SOFIA-S access", {"fields": ("must_change_password",)}),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        ("SOFIA-S access", {"fields": ("must_change_password",)}),
    )

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path(
                "import-csv/",
                self.admin_site.admin_view(self.import_csv_view),
                name="accounts_user_import_csv",
            )
        ]
        return custom_urls + urls

    def import_csv_view(self, request):
        if not self.has_add_permission(request):
            raise PermissionDenied

        if request.method == "POST":
            form = UserCSVImportForm(request.POST, request.FILES)
            if form.is_valid():
                uploaded_file = form.cleaned_data["csv_file"]
                try:
                    csv_text = uploaded_file.read().decode("utf-8-sig")
                    result = import_users_from_csv(csv_text)
                except UnicodeDecodeError:
                    form.add_error(
                        "csv_file", "El archivo debe estar codificado en UTF-8."
                    )
                except ValueError as exc:
                    form.add_error("csv_file", str(exc))
                else:
                    report = render_import_report_csv(result)
                    response = HttpResponse(report, content_type="text/csv")
                    response["Content-Disposition"] = (
                        'attachment; filename="user_import_report.csv"'
                    )
                    return response
        else:
            form = UserCSVImportForm()

        context = {
            **self.admin_site.each_context(request),
            "title": "Importar usuarios desde CSV",
            "form": form,
            "opts": self.model._meta,
            "required_columns": REQUIRED_HEADERS,
        }
        return TemplateResponse(
            request,
            "admin/accounts/user/import_csv.html",
            context,
        )


class CompanyCatalogInlineFormSet(forms.BaseInlineFormSet):
    """Guards the two company catalog inlines.

    Deleting an entry that still has members is blocked with an actionable
    message, since the FK is SET_NULL and would otherwise silently orphan
    employees. Intra-formset duplicates are caught here too: Django's
    `validate_unique` only understands `unique_together`, so two new rows typed
    "Ventas"/"ventas" in one save would bypass validation and hit the DB
    constraint as an IntegrityError 500. `catalog_name_key` is the same fold the
    constraint applies, so the two layers cannot disagree about what collides.
    """

    def clean(self):
        super().clean()
        seen = set()
        blocked = []
        for form in self.forms:
            if not hasattr(form, "cleaned_data"):
                continue
            if form.cleaned_data.get("DELETE"):
                if form.instance.pk:
                    member_count = form.instance.members.count()
                    if member_count:
                        blocked.append(
                            f"No puedes eliminar «{form.instance.name}»: "
                            f"{member_count} colaborador(es) pertenecen a esta "
                            "entrada. Desmarca «activa» para retirarla de la lista."
                        )
                continue
            name = normalize_catalog_name(form.cleaned_data.get("name"))
            if not name:
                continue
            key = catalog_name_key(name)
            if key in seen:
                form.add_error("name", f"«{name}» ya está en la lista de esta empresa.")
            seen.add(key)

        # Must be a non-form error: BaseFormSet.is_valid() skips forms flagged for
        # deletion, so an error attached to the deleted row would be ignored and
        # the entry would be dropped anyway.
        if blocked:
            raise ValidationError(blocked)


class CompanyAreaInline(admin.TabularInline):
    model = CompanyArea
    formset = CompanyCatalogInlineFormSet
    fields = ("name", "is_active")
    extra = 1
    verbose_name = "área"
    verbose_name_plural = "Áreas (las que el colaborador podrá elegir al activarse)"


class CompanyLocationInline(admin.TabularInline):
    model = CompanyLocation
    formset = CompanyCatalogInlineFormSet
    fields = ("name", "is_active")
    extra = 1
    verbose_name = "localidad"
    verbose_name_plural = (
        "Localidades (si hay más de una, el colaborador elegirá la suya)"
    )


@admin.register(Company)
class CompanyAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "legal_name",
        "rfc",
        "reference_code",
        "area_count",
        "location_count",
        "created_at",
    )
    search_fields = ("name", "legal_name", "rfc", "reference_code")
    inlines = [CompanyAreaInline, CompanyLocationInline]

    def get_queryset(self, request):
        return (
            super()
            .get_queryset(request)
            .annotate(
                _area_count=Count("areas", distinct=True),
                _location_count=Count("locations", distinct=True),
            )
        )

    @admin.display(description="Áreas", ordering="_area_count")
    def area_count(self, obj):
        # A company showing 0 áreas is one whose employees cannot activate.
        return obj._area_count

    @admin.display(description="Localidades", ordering="_location_count")
    def location_count(self, obj):
        return obj._location_count


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "position", "area", "location", "company", "is_activated")
    # No `area` filter: CompanyArea has no registered admin, so the sidebar would
    # enumerate every client's área names. Filter by company, search by area__name.
    list_filter = ("is_activated", "company")
    search_fields = (
        "user__username",
        "user__email",
        "position",
        "area__name",
        "location__name",
    )
    raw_id_fields = ("user",)
    list_select_related = ("user", "company", "area", "location")

    def get_form(self, request, obj=None, **kwargs):
        # formfield_for_foreignkey isn't handed the edited object, so stash it.
        request._userprofile_obj = obj
        return super().get_form(request, obj, **kwargs)

    def _scoped_company_id(self, request):
        """The company to scope the catalog dropdowns to, or None if unknown.

        None covers both the add form and an existing profile whose company was
        deleted (`company` is SET_NULL), so both get the company-qualified labels.
        """
        obj = getattr(request, "_userprofile_obj", None)
        return obj.company_id if obj is not None else None

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name not in ("area", "location"):
            return super().formfield_for_foreignkey(db_field, request, **kwargs)

        company_id = self._scoped_company_id(request)
        model = db_field.remote_field.model
        if company_id:
            # Scope to the profile's own company so another client's área is not
            # even present in the HTML.
            kwargs["queryset"] = model.objects.filter(company_id=company_id)
        else:
            # Company unknown: show all, but qualify each option with its company
            # so identically named entries are distinguishable. UserProfile.clean()
            # rejects a mismatched pairing on save.
            kwargs["queryset"] = model.objects.select_related("company")

        formfield = super().formfield_for_foreignkey(db_field, request, **kwargs)
        if not company_id:
            formfield.label_from_instance = lambda o: f"{o.company.name} — {o.name}"
        return formfield


@admin.register(SetupAccessCode)
class SetupAccessCodeAdmin(admin.ModelAdmin):
    list_display = ("user", "code", "created_at", "used_at")
    search_fields = ("user__username", "user__email", "code")
    raw_id_fields = ("user",)
    readonly_fields = ("user", "code", "created_at", "used_at")
