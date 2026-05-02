from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.core.exceptions import PermissionDenied
from django.http import HttpResponse
from django.template.response import TemplateResponse
from django.urls import path

from .forms import UserCSVImportForm
from .importers import import_users_from_csv, render_import_report_csv
from .models import Company, User, UserProfile


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
            "required_columns": [
                "email",
                "company_reference_code",
                "group",
                "auth_method",
            ],
            "optional_columns": ["first_name", "last_name", "position"],
        }
        return TemplateResponse(
            request,
            "admin/accounts/user/import_csv.html",
            context,
        )


@admin.register(Company)
class CompanyAdmin(admin.ModelAdmin):
    list_display = ("name", "legal_name", "rfc", "reference_code", "created_at")
    search_fields = ("name", "legal_name", "rfc", "reference_code")


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "position", "company", "is_activated")
    list_filter = ("is_activated",)
    search_fields = ("user__username", "user__email", "position")
    raw_id_fields = ("user",)
