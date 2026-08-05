import random
import string

from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Q
from django.db.models.functions import Lower
from django.utils import timezone


def _generate_reference_code() -> str:
    characters = string.ascii_uppercase + string.digits
    while True:
        code = "".join(random.choices(characters, k=5))
        if not Company.objects.filter(reference_code=code).exists():
            return code


class User(AbstractUser):
    email = models.EmailField(unique=True)
    must_change_password = models.BooleanField(default=False)


class Company(models.Model):
    name = models.CharField(max_length=255)
    legal_name = models.CharField(max_length=255)
    rfc = models.CharField("RFC", max_length=13, blank=True)
    address = models.CharField(max_length=500, blank=True)
    reference_code = models.CharField(max_length=5, unique=True, blank=True)
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


class CompanyCatalogEntry(models.Model):
    """Abstract base for the per-company preloaded lists (áreas, localidades).

    Entries are curated by an admin and are what an employee picks from when
    activating their account. Deliberately case-insensitively unique per company:
    "Ventas" and "ventas" must not become two separate dashboard buckets.
    """

    name = models.CharField(
        "nombre",
        max_length=120,
        help_text="Como debe aparecer en la lista que ve el colaborador.",
    )
    is_active = models.BooleanField(
        "activa",
        default=True,
        help_text=(
            "Desmarca para retirarla de la lista sin borrarla. "
            "Los colaboradores ya asignados la conservan."
        ),
    )

    class Meta:
        abstract = True
        ordering = ["name"]
        constraints = [
            models.UniqueConstraint(
                "company",
                Lower("name"),
                name="%(app_label)s_%(class)s_unique_name_per_company",
            )
        ]

    def __str__(self):
        return self.name

    def clean(self):
        super().clean()
        self.name = (self.name or "").strip()
        if not self.name:
            raise ValidationError({"name": "El nombre no puede estar vacío."})


class CompanyArea(CompanyCatalogEntry):
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name="areas")

    class Meta(CompanyCatalogEntry.Meta):
        verbose_name = "área"
        verbose_name_plural = "áreas"


class CompanyLocation(CompanyCatalogEntry):
    company = models.ForeignKey(
        Company, on_delete=models.CASCADE, related_name="locations"
    )

    class Meta(CompanyCatalogEntry.Meta):
        verbose_name = "localidad"
        verbose_name_plural = "localidades"


class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="profile")
    position = models.CharField(max_length=255, blank=True)
    is_activated = models.BooleanField(default=False)
    company = models.ForeignKey(
        Company,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="members",
    )
    # SET_NULL rather than PROTECT: Company -> catalog is CASCADE, so PROTECT here
    # would block deleting a Company outright. Accidental deletion is guarded in the
    # admin inline formset instead (retiring is `is_active=False`, not deletion).
    area = models.ForeignKey(
        CompanyArea,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="members",
        verbose_name="área",
    )
    location = models.ForeignKey(
        CompanyLocation,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="members",
        verbose_name="localidad",
    )

    def __str__(self):
        return f"{self.user.username} profile"

    def clean(self):
        super().clean()
        errors = {}
        for field in ("area", "location"):
            entry = getattr(self, field, None)
            if entry is not None and entry.company_id != self.company_id:
                errors[field] = "Debe pertenecer a la misma empresa que el colaborador."
        if errors:
            raise ValidationError(errors)


class SetupAccessCode(models.Model):
    """
    One-time first-login code for users who cannot receive external OTP email.
    """

    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="setup_access_codes"
    )
    code = models.CharField(max_length=9, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    used_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["code"],
                condition=Q(code__isnull=False),
                name="unique_active_setup_access_code",
            ),
            models.UniqueConstraint(
                fields=["user"],
                condition=Q(used_at__isnull=True),
                name="unique_unused_setup_access_code_per_user",
            ),
        ]

    def is_valid(self, submitted_code: str) -> bool:
        normalized_code = normalize_setup_access_code(submitted_code)
        return self.used_at is None and self.code == normalized_code

    def mark_used(self):
        self.used_at = timezone.now()
        self.code = None
        self.save(update_fields=["used_at", "code"])

    def __str__(self):
        return f"Setup access code for {self.user.email}"


def normalize_setup_access_code(code: str) -> str:
    return code.strip().replace("-", "").replace(" ", "")


class Role(models.Model):
    """
    Sentinel model. No database table is created (managed = False).
    Exists solely to host the project's custom permissions, which Django
    stores in auth_permission and assigns to Groups.
    """

    class Meta:
        managed = False
        permissions = [
            ("can_manage_surveys", "Can manage surveys"),
            ("can_view_dashboard", "Can view dashboard"),
            ("can_view_insights", "Can view insights"),
            ("can_take_assigned_surveys", "Can take assigned surveys"),
            ("can_manage_employees", "Can manage employees"),
            ("can_view_submissions", "Can view submissions"),
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
