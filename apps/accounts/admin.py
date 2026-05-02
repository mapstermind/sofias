from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import Company, User, UserProfile


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = UserAdmin.list_display + ("must_change_password",)
    fieldsets = UserAdmin.fieldsets + (
        ("SOFIA-S access", {"fields": ("must_change_password",)}),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        ("SOFIA-S access", {"fields": ("must_change_password",)}),
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
