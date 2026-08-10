import random
import string

from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Q
from django.utils import timezone

# Columns holding Spanish text an operator or employee reads as a sorted list.
# The database's own collation is byte order, which files every accented name
# after `Z` ("Álvaro Obregón" below "Zacatecas") and `ñ` after `z`; this ICU
# collation is what makes ORDER BY match what a Spanish speaker expects. It is
# deterministic, so equality and uniqueness are unaffected.
SPANISH_COLLATION = "es-MX-x-icu"

# Spanish vowel accents and the diaeresis carry no lexical weight — "Direccion"
# and "Dirección" are one área typed two ways — so catalog uniqueness folds them.
# `ñ` is deliberately absent: it is a distinct letter, and folding it would reject
# genuine pairs like "Cañada"/"Canada".
_ACCENT_FOLD = str.maketrans("áéíóúü", "aeiouu")


class FoldCatalogName(models.Func):
    """`name` reduced to its uniqueness key: lowercased, Spanish accents folded.

    `translate` is IMMUTABLE, which is what lets this sit in a unique index —
    Postgres' own `unaccent()` is only STABLE and could not.
    """

    template = "translate(lower(%(expressions)s), 'áéíóúü', 'aeiouu')"
    arity = 1
    output_field = models.CharField()


def normalize_catalog_name(name: str) -> str:
    """Collapse surrounding and internal whitespace to single spaces."""
    return " ".join((name or "").split())


def catalog_name_key(name: str) -> str:
    """The Python mirror of `FoldCatalogName`, for pre-save duplicate checks."""
    return normalize_catalog_name(name).casefold().translate(_ACCENT_FOLD)


def _generate_reference_code() -> str:
    characters = string.ascii_uppercase + string.digits
    while True:
        code = "".join(random.choices(characters, k=5))
        if not Company.objects.filter(reference_code=code).exists():
            return code


class User(AbstractUser):
    email = models.EmailField("correo electrónico", unique=True)
    must_change_password = models.BooleanField(
        "debe cambiar su contraseña",
        default=False,
        help_text="Obliga a definir una contraseña nueva en el siguiente ingreso.",
    )

    # Redeclared purely to carry the collation: the employee roster is ordered by
    # these two columns, and an "Álvarez" sorting below every ASCII surname is
    # the most visible instance of the byte-order problem.
    first_name = models.CharField(
        "nombre(s)", max_length=150, blank=True, db_collation=SPANISH_COLLATION
    )
    last_name = models.CharField(
        "apellidos", max_length=150, blank=True, db_collation=SPANISH_COLLATION
    )


class Company(models.Model):
    name = models.CharField(
        "nombre comercial", max_length=255, db_collation=SPANISH_COLLATION
    )
    legal_name = models.CharField(
        "razón social", max_length=255, db_collation=SPANISH_COLLATION
    )
    rfc = models.CharField("RFC", max_length=13, blank=True)
    address = models.CharField("domicilio", max_length=500, blank=True)
    reference_code = models.CharField(
        "código de referencia",
        max_length=5,
        unique=True,
        blank=True,
        help_text="Se genera solo. El colaborador lo captura al activar su cuenta.",
    )
    created_at = models.DateTimeField("fecha de alta", auto_now_add=True)
    updated_at = models.DateTimeField("última actualización", auto_now=True)

    class Meta:
        verbose_name = "empresa"
        verbose_name_plural = "empresas"

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.reference_code:
            self.reference_code = _generate_reference_code()
        super().save(*args, **kwargs)


class CompanyCatalogEntry(models.Model):
    """Abstract base for the per-company preloaded lists (áreas, localidades).

    Entries are curated by an admin and are what an employee picks from when
    activating their account. Uniqueness per company ignores case, Spanish vowel
    accents and whitespace runs: "Ventas", "ventas" and "Dirección"/"Direccion"
    must not become two separate dashboard buckets. `apps/nom035` groups its
    per-área breakdown by pk, so a near-duplicate splits one área into two rows
    that no one can merge afterwards.
    """

    name = models.CharField(
        "nombre",
        max_length=120,
        help_text="Como debe aparecer en la lista que ve el colaborador.",
        db_collation=SPANISH_COLLATION,
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
                FoldCatalogName("name"),
                name="%(app_label)s_%(class)s_unique_name_per_company",
            )
        ]

    def __str__(self):
        return self.name

    def clean(self):
        super().clean()
        self.name = normalize_catalog_name(self.name)
        if not self.name:
            raise ValidationError({"name": "El nombre no puede estar vacío."})


class CompanyArea(CompanyCatalogEntry):
    company = models.ForeignKey(
        Company, on_delete=models.CASCADE, related_name="areas", verbose_name="empresa"
    )

    class Meta(CompanyCatalogEntry.Meta):
        verbose_name = "área"
        verbose_name_plural = "áreas"


class CompanyLocation(CompanyCatalogEntry):
    company = models.ForeignKey(
        Company,
        on_delete=models.CASCADE,
        related_name="locations",
        verbose_name="empresa",
    )

    class Meta(CompanyCatalogEntry.Meta):
        verbose_name = "localidad"
        verbose_name_plural = "localidades"


class UserProfile(models.Model):
    user = models.OneToOneField(
        User, on_delete=models.CASCADE, related_name="profile", verbose_name="usuario"
    )
    position = models.CharField("cargo", max_length=255, blank=True)
    is_activated = models.BooleanField(
        "cuenta activada",
        default=False,
        help_text="Se marca sola cuando el colaborador completa su activación.",
    )
    company = models.ForeignKey(
        Company,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="members",
        verbose_name="empresa",
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

    class Meta:
        verbose_name = "perfil de colaborador"
        verbose_name_plural = "perfiles de colaborador"

    def __str__(self):
        return f"Perfil de {self.user.email}"

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
        User,
        on_delete=models.CASCADE,
        related_name="setup_access_codes",
        verbose_name="usuario",
    )
    code = models.CharField(
        "código",
        max_length=9,
        null=True,
        blank=True,
        help_text="Se borra en cuanto se usa.",
    )
    created_at = models.DateTimeField("fecha de creación", auto_now_add=True)
    used_at = models.DateTimeField("fecha de uso", null=True, blank=True)

    class Meta:
        verbose_name = "código temporal de acceso"
        verbose_name_plural = "códigos temporales de acceso"
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
        return f"Código temporal de acceso para {self.user.email}"


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
        verbose_name = "rol"
        verbose_name_plural = "roles"
        permissions = [
            ("can_manage_surveys", "Puede administrar encuestas"),
            ("can_view_dashboard", "Puede ver el tablero"),
            ("can_view_insights", "Puede ver la valoración de resultados"),
            ("can_take_assigned_surveys", "Puede contestar las encuestas asignadas"),
            ("can_manage_employees", "Puede administrar empleados"),
            ("can_view_submissions", "Puede ver los envíos"),
        ]


class EmailOTP(models.Model):
    """
    A one-time passcode sent to an email address for passwordless login.

    The email field is not a FK to User — the user may not exist yet when
    the OTP is created (first-time sign-up flow).
    """

    email = models.EmailField("correo electrónico", db_index=True)
    code = models.CharField("código", max_length=6)
    created_at = models.DateTimeField("fecha de creación", auto_now_add=True)
    expires_at = models.DateTimeField("expira el")
    is_used = models.BooleanField("usado", default=False)

    class Meta:
        verbose_name = "código OTP"
        verbose_name_plural = "códigos OTP"

    def save(self, *args, **kwargs):
        if not self.pk and not self.expires_at:
            expiry = getattr(settings, "OTP_EXPIRY_MINUTES", 10)
            self.expires_at = timezone.now() + timezone.timedelta(minutes=expiry)
        super().save(*args, **kwargs)

    def is_valid(self) -> bool:
        return not self.is_used and timezone.now() < self.expires_at

    def __str__(self):
        return f"OTP para {self.email} ({'usado' if self.is_used else 'vigente'})"
