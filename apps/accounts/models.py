import random
import string

from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone


def _generate_reference_code() -> str:
    characters = string.ascii_uppercase + string.digits
    while True:
        code = "".join(random.choices(characters, k=5))
        if not Company.objects.filter(reference_code=code).exists():
            return code


class User(AbstractUser):
    email = models.EmailField(unique=True)


class Company(models.Model):
    name = models.CharField(max_length=255)
    legal_name = models.CharField(max_length=255)
    reference_code = models.CharField(max_length=5, unique=True, blank=True)
    expected_employee_count = models.PositiveIntegerField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = "companies"

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.reference_code:
            self.reference_code = _generate_reference_code()
        super().save(*args, **kwargs)


class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="profile")
    position = models.CharField(max_length=255, blank=True)
    company = models.ForeignKey(
        Company,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="members",
    )

    def __str__(self):
        return f"{self.user.username} profile"


class Role(models.Model):
    """
    Sentinel model. No database table is created (managed = False).
    Exists solely to host the project's custom permissions, which Django
    stores in auth_permission and assigns to Groups.
    """

    class Meta:
        managed = False
        permissions = [
            ("can_manage_site_configuration", "Can manage site configuration"),
            ("can_manage_users", "Can manage users"),
            ("can_manage_surveys", "Can manage surveys"),
            ("can_assign_surveys", "Can assign surveys"),
            ("can_view_dashboard", "Can view dashboard"),
            ("can_view_reports", "Can view reports"),
            ("can_view_insights", "Can view insights"),
            ("can_take_assigned_surveys", "Can take assigned surveys"),
        ]


class EmailOTP(models.Model):
    """
    A one-time passcode sent to an email address for passwordless login.

    The email field is not a FK to User — the user may not exist yet when
    the OTP is created (first-time sign-up flow).
    """

    email = models.EmailField(db_index=True)
    code = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    is_used = models.BooleanField(default=False)

    def save(self, *args, **kwargs):
        if not self.pk and not self.expires_at:
            expiry = getattr(settings, "OTP_EXPIRY_MINUTES", 10)
            self.expires_at = timezone.now() + timezone.timedelta(minutes=expiry)
        super().save(*args, **kwargs)

    def is_valid(self) -> bool:
        return not self.is_used and timezone.now() < self.expires_at

    def __str__(self):
        return f"OTP for {self.email} ({'used' if self.is_used else 'active'})"
