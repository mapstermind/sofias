# Localization (es-MX) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make the Django admin read as a coherent Spanish (es-MX) product — no auto-derived English labels, Spanish chrome and validation, Mexico City timestamps.

**Architecture:** Three layers, per [`docs/platform/localization.md`](localization.md). Layer 1 (Django's own strings) is bought with one settings line. Layer 2 (metadata we write) is hardcoded Spanish on every model `Meta`, field `verbose_name`/`help_text`, `TextChoices` label, `__str__`, and admin fieldset title. Layer 3 (Python identifiers) stays English and is never shown, because layer 2 covers every field. A `post_migrate` receiver rewrites the `auth_permission.name` rows Django builds from an untranslated `"Can %s %s"` template.

**Tech Stack:** Django 6.0, PostgreSQL 17, pytest + pytest-django.

## Global Constraints

- **No `gettext_lazy`.** Hardcode Spanish. There is one target language, no `LOCALE_PATHS`, no `.po` files, no `compilemessages` step. This plan *removes* the two existing `_()` calls in `apps/accounts/models.py`.
- **Code, identifiers, module names, comments and docstrings stay English.** Only user-visible strings become Spanish.
- **Presentation only.** No schema changes, no view logic, no URL changes. Every generated migration must be `AlterModelOptions` / `AlterField` and must not touch a column.
- **Field labels are lowercase**, matching Django's own convention (`verbose_name = "empresa"`, not `"Empresa"`) — Django capitalizes them at render time via `capfirst`. `Meta.verbose_name` likewise.
- **`USE_TZ` stays `True`.** Storage remains UTC; only display shifts.
- **Every field on every model in `apps.accounts`, `apps.surveys`, `apps.responses`, `apps.nom035` gets an explicit `verbose_name`** — including models with no registered `ModelAdmin` (`EmailOTP`, `Role`, `CompanyArea`, `CompanyLocation`), because their auto-generated permissions appear in the Groups permission picker.
- **Fields inherited from `AbstractUser`** (`username`, `password`, `is_staff`, `date_joined`, `groups`, …) are left alone: Django ships their Spanish translations and `LANGUAGE_CODE` picks them up for free.
- **No template or `static/` edits in this plan**, so `npm run build:css` / `npm run build:js` are **not** required. If a task ends up touching `templates/` after all, run the matching build and commit the regenerated output.
- Run `ruff format .` and `ruff check .` before every commit.

## Decisions already made

Recorded here so no task re-litigates them:

| Question | Answer |
|---|---|
| Sweep scope | **Every model in the four apps**, registered or not. |
| `TIME_ZONE` | `"America/Mexico_City"` (UTC−6 year-round; Mexico abolished DST in 2022). |
| App index names | `Cuentas`, `Encuestas`, `Respuestas`, `NOM-035`. `apps.core` has no models and never appears in the admin index — skip it. |
| `User.first_name` / `last_name` | Hardcode `"nombre(s)"` / `"apellidos"`. Django's `es_MX` catalog renders `last name` as the singular `"apellido"`, which is wrong for Mexican usage (paterno + materno). |
| `Role.Meta.permissions`, `EmailOTP`, `Role` | In scope — the Groups permission picker is an operator screen. |
| Date format | Accept Django's `es_MX` formats (`9 de agosto de 2026 a las 15:00`). No `FORMAT_MODULE_PATH`. Public templates already hardcode `\|date:"d/m/Y"` and are unaffected. |
| Admin chrome | Branded: `Administración SOFIA-S`. |

## Explicitly out of scope

- **Group names** (`Admins`, `Principal Exec`, `Secondary Exec`, `Employees`) stay English. They are `auth.Group.name` values looked up by string in `bootstrap_groups.py`, `importers.py`, `accounts/views.py` and `conftest.py` — renaming them is a behavior change, not presentation. Task 9 records this as a new open finding.
- `apps/reports` — an unregistered stub with no models.
- The public employee-facing app, which is already Spanish.

---

## 1. Foundation

### Task 1: Switch the project locale, timezone and admin branding

**Files:**
- Modify: `config/settings.py:132-138`
- Modify: `config/urls.py:18-26`
- Modify: `conftest.py` (add a shared `staff_client` fixture)
- Modify: `apps/accounts/tests/test_admin.py:26-35` (delete the now-duplicated local fixture)
- Test: `apps/core/tests/test_localization.py` (create)

**Interfaces:**
- Produces: `staff_client` fixture — a `django.test.Client` already logged in as a superuser. Tasks 3–8 use it. Signature: `staff_client(client, make_user) -> Client`.

- [x] **Step 1: Write the failing test**

Create `apps/core/tests/test_localization.py`:

```python
"""Project-wide localization guarantees: language, timezone, admin chrome."""

from datetime import datetime, timezone as dt_timezone

import pytest
from django.conf import settings
from django.urls import reverse

from apps.accounts.models import Company

pytestmark = pytest.mark.django_db


def test_project_language_is_mexican_spanish():
    assert settings.LANGUAGE_CODE == "es-mx"


def test_project_timezone_is_mexico_city_and_storage_stays_utc():
    assert settings.TIME_ZONE == "America/Mexico_City"
    assert settings.USE_TZ is True


def test_admin_login_page_is_branded_and_in_spanish(client):
    response = client.get(reverse("admin:login"))

    body = response.content.decode()
    assert "Administración SOFIA-S" in body
    assert "Django administration" not in body


def _empty_inline_management_form(prefix):
    """CompanyAdmin has two inlines; a POST without their management forms 500s."""
    return {
        f"{prefix}-TOTAL_FORMS": "0",
        f"{prefix}-INITIAL_FORMS": "0",
        f"{prefix}-MIN_NUM_FORMS": "0",
        f"{prefix}-MAX_NUM_FORMS": "1000",
    }


def test_django_validation_messages_render_in_spanish(staff_client):
    """Layer 1: Django's own strings, bought with LANGUAGE_CODE alone."""
    response = staff_client.post(
        reverse("admin:accounts_company_add"),
        {
            "name": "",
            "legal_name": "",
            "rfc": "",
            "address": "",
            **_empty_inline_management_form("areas"),
            **_empty_inline_management_form("locations"),
        },
    )

    assert response.status_code == 200
    assert "Este campo es obligatorio." in response.content.decode()


def test_admin_renders_timestamps_in_mexico_city_time(staff_client, make_company):
    """21:00 UTC is 15:00 in Mexico City, which has no DST since 2022."""
    company = make_company()
    Company.objects.filter(pk=company.pk).update(
        created_at=datetime(2026, 8, 9, 21, 0, tzinfo=dt_timezone.utc)
    )

    response = staff_client.get(reverse("admin:accounts_company_changelist"))

    body = response.content.decode()
    # Django's es_MX catalog capitalizes month names.
    assert "9 de Agosto de 2026 a las 15:00" in body
    assert "21:00" not in body
```

Add to `conftest.py`, under a new `# ── Admin ─────` banner comment matching the file's existing style:

```python
@pytest.fixture
def staff_client(client, make_user):
    """A test client logged in as a superuser, for exercising admin screens."""
    staff = make_user(
        email="admin-staff@example.com",
        password="Pass12345!",
        is_staff=True,
        is_superuser=True,
    )
    client.force_login(staff)
    return client
```

Delete the local `staff_client` fixture from `apps/accounts/tests/test_admin.py` (lines 26–35) — the root one replaces it. Leave every other line of that file alone.

- [x] **Step 2: Run the test to verify it fails**

Run: `pytest apps/core/tests/test_localization.py -v`
Expected: 4 failures — `LANGUAGE_CODE == "en-us"`, `TIME_ZONE == "UTC"`, no `Administración SOFIA-S` in the login page, `"This field is required."` instead of the Spanish message, and `"Aug. 9, 2026"` / `"21:00"` instead of the Mexico City rendering.

- [x] **Step 3: Write the implementation**

In `config/settings.py`, replace the two lines under `# Internationalization`:

```python
LANGUAGE_CODE = "es-mx"

# Storage stays UTC (USE_TZ). This only shifts what an operator reads: without
# it a 15:00 submission from a Mexican client displays as 21:00.
TIME_ZONE = "America/Mexico_City"
```

In `config/urls.py`, after the imports and before `urlpatterns`:

```python
# Django's default chrome names the framework; operators should see the product.
admin.site.site_header = "Administración SOFIA-S"
admin.site.site_title = "SOFIA-S"
admin.site.index_title = "Panel de administración"
```

- [x] **Step 4: Run the tests to verify they pass**

Run: `pytest apps/core/tests/test_localization.py -v`
Expected: PASS (5 tests)

- [x] **Step 5: Confirm nothing else regressed**

Run: `python manage.py check` — expected: `System check identified no issues`.
Run: `pytest` — expected: the full suite passes. No test asserts on an English Django string today, so this should be clean. If `apps/accounts/tests/test_admin.py` errors with `fixture 'staff_client' not found`, the root `conftest.py` fixture was not added.

- [x] **Step 6: Commit**

```bash
git add config/settings.py config/urls.py conftest.py \
        apps/core/tests/test_localization.py apps/accounts/tests/test_admin.py
git commit -m "Switch the project to es-MX and Mexico City time"
```

**Risk:** `TIME_ZONE` shifts displayed times in the **public** app too (survey timestamps, OTP expiry copy). No test covers a rendered timestamp there, and no view does date-boundary arithmetic (`apps/surveys/views.py:150` only stamps `completed_at`), so the change is display-only. Ask the user to eyeball `/` and a survey page in the browser before moving on.

---

## 2. Admin index grouping

### Task 2: Spanish app names in the admin index

**Files:**
- Modify: `apps/accounts/apps.py`, `apps/surveys/apps.py`, `apps/responses/apps.py`, `apps/nom035/apps.py`
- Test: `apps/core/tests/test_localization.py` (append)

**Interfaces:**
- Consumes: nothing from Task 1 beyond the test file existing.
- Produces: `AppConfig.verbose_name` on four apps, which `templates/admin/accounts/user/import_csv.html:8` already renders in its breadcrumb via `opts.app_config.verbose_name`.

- [x] **Step 1: Write the failing test**

Append to `apps/core/tests/test_localization.py`:

```python
@pytest.mark.parametrize(
    "app_label,expected",
    [
        ("accounts", "Cuentas"),
        ("surveys", "Encuestas"),
        ("responses", "Respuestas"),
        ("nom035", "NOM-035"),
    ],
)
def test_admin_index_groups_apps_under_spanish_names(app_label, expected):
    from django.apps import apps as django_apps

    assert django_apps.get_app_config(app_label).verbose_name == expected
```

- [x] **Step 2: Run the test to verify it fails**

Run: `pytest apps/core/tests/test_localization.py -k spanish_names -v`
Expected: 4 failures — Django derives `"Accounts"`, `"Surveys"`, `"Responses"`, `"Nom035"` from the class names.

- [x] **Step 3: Write the implementation**

Add one `verbose_name` line to each `AppConfig`, keeping the existing attribute order:

```python
# apps/accounts/apps.py
class AccountsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.accounts"
    label = "accounts"
    verbose_name = "Cuentas"
```

```python
# apps/surveys/apps.py
class SurveysConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.surveys"
    label = "surveys"
    verbose_name = "Encuestas"
```

```python
# apps/responses/apps.py
class ResponsesConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.responses"
    label = "responses"
    verbose_name = "Respuestas"
```

```python
# apps/nom035/apps.py
class Nom035Config(AppConfig):
    name = "apps.nom035"
    label = "nom035"
    verbose_name = "NOM-035"
    default_auto_field = "django.db.models.BigAutoField"

    def ready(self):
        from apps.nom035 import signals  # noqa: F401
```

- [x] **Step 4: Run the tests to verify they pass**

Run: `pytest apps/core/tests/test_localization.py -v`
Expected: PASS (9 tests)

- [x] **Step 5: Commit**

```bash
git add apps/accounts/apps.py apps/surveys/apps.py apps/responses/apps.py \
        apps/nom035/apps.py apps/core/tests/test_localization.py
git commit -m "Group the admin index under Spanish app names"
```

**Note:** `AppConfig.verbose_name` is not migration-tracked, so no migration is generated here.

---

## 3. Model metadata

Tasks 3–6 are independent of each other but all depend on the `assert_explicit_labels` fixture introduced in Task 3. Run Task 3 first.

### Task 3: Spanish metadata on every `apps.accounts` model

**Files:**
- Modify: `apps/accounts/models.py`
- Modify: `conftest.py` (add the `assert_explicit_labels` fixture)
- Create: `apps/accounts/migrations/0005_*.py` (generated)
- Test: `apps/accounts/tests/test_admin.py` (append a `TestSpanishAdminLabels` class)

**Interfaces:**
- Produces: `assert_explicit_labels` fixture — a callable `(app_label: str) -> None` that fails listing every field whose label Django auto-derived from its English attribute name, plus every model whose `Meta.verbose_name` is auto-derived. Tasks 4–6 consume it.

- [x] **Step 1: Write the failing test**

Add to `conftest.py`, under the `# ── Admin ─────` banner from Task 1:

```python
@pytest.fixture
def assert_explicit_labels():
    """Fail listing every label Django derived from an English identifier.

    `verbose_name` is the bridge that keeps English code from leaking onto a
    Spanish screen, so a missing one is a UI bug, not a style nit. Plural forms
    are not checked: a correct Spanish plural is usually the singular plus "s",
    which is exactly what Django would have derived anyway.
    """
    from django.apps import apps as django_apps
    from django.utils.text import camel_case_to_spaces

    def _assert(app_label):
        offenders = []
        for model in django_apps.get_app_config(app_label).get_models():
            opts = model._meta
            if str(opts.verbose_name) == camel_case_to_spaces(model.__name__):
                offenders.append(f"{opts.label}.Meta.verbose_name")
            for field in opts.get_fields():
                verbose_name = getattr(field, "verbose_name", None)
                if verbose_name is None:
                    continue
                if str(verbose_name) == field.name.replace("_", " "):
                    offenders.append(f"{opts.label}.{field.name}")
        assert offenders == [], "Auto-derived English labels: " + ", ".join(offenders)

    return _assert
```

Append to `apps/accounts/tests/test_admin.py`:

```python
class TestSpanishAdminLabels:
    def test_no_accounts_model_shows_an_auto_derived_label(
        self, assert_explicit_labels
    ):
        assert_explicit_labels("accounts")

    def test_company_change_form_labels_are_spanish(self, staff_client, make_company):
        company = make_company()

        response = staff_client.get(
            reverse("admin:accounts_company_change", args=[company.pk])
        )

        body = response.content.decode()
        assert "Razón social" in body
        assert "Legal name" not in body

    def test_userprofile_str_is_spanish(self, make_user_with_profile):
        user = make_user_with_profile(email="etiqueta@x.mx")

        assert str(user.profile) == "Perfil de etiqueta@x.mx"
```

- [x] **Step 2: Run the test to verify it fails**

Run: `pytest apps/accounts/tests/test_admin.py::TestSpanishAdminLabels -v`
Expected: 3 failures. The first lists ~24 offenders including `accounts.company.name`, `accounts.userprofile.user`, `accounts.emailotp.email`, `accounts.Company.Meta.verbose_name`.

- [x] **Step 3: Write the implementation**

In `apps/accounts/models.py`:

Delete the now-unused import on line 10 (`from django.utils.translation import gettext_lazy as _`).

`User`:

```python
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
```

`Company` — keep `save()` and `__str__` as they are:

```python
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
```

`CompanyArea` / `CompanyLocation` — `name` and `is_active` are already Spanish on the abstract base; only the FK needs a label:

```python
class CompanyArea(CompanyCatalogEntry):
    company = models.ForeignKey(
        Company, on_delete=models.CASCADE, related_name="areas", verbose_name="empresa"
    )
```

```python
class CompanyLocation(CompanyCatalogEntry):
    company = models.ForeignKey(
        Company,
        on_delete=models.CASCADE,
        related_name="locations",
        verbose_name="empresa",
    )
```

`UserProfile` — keep `clean()` untouched:

```python
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
```

`SetupAccessCode`:

```python
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
```

Add the two names above its existing `constraints`, which stay byte-for-byte identical:

```python
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
```

And its `__str__`:

```python
    def __str__(self):
        return f"Código temporal de acceso para {self.user.email}"
```

`Role` — replace the permission labels and add a `Meta` name:

```python
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
```

`EmailOTP` — keep `save()`, `is_valid()` untouched:

```python
    email = models.EmailField("correo electrónico", db_index=True)
    code = models.CharField("código", max_length=6)
    created_at = models.DateTimeField("fecha de creación", auto_now_add=True)
    expires_at = models.DateTimeField("expira el")
    is_used = models.BooleanField("usado", default=False)

    class Meta:
        verbose_name = "código OTP"
        verbose_name_plural = "códigos OTP"

    def __str__(self):
        return f"OTP para {self.email} ({'usado' if self.is_used else 'vigente'})"
```

- [x] **Step 4: Generate the migration and confirm it is a no-op**

Run: `python manage.py makemigrations accounts`
Expected: `apps/accounts/migrations/0005_*.py` containing only `AlterModelOptions` and `AlterField` operations.

Read the generated file and confirm **every** `AlterField` preserves the original `max_length`, `db_collation`, `null`, `blank` and `unique`. Any operation that is not `AlterModelOptions` or `AlterField` means a field definition was altered by accident — fix the model, delete the migration, regenerate.

Run: `python manage.py migrate accounts`

- [x] **Step 5: Run the tests to verify they pass**

Run: `pytest apps/accounts -v`
Expected: PASS, including the three new tests.

- [x] **Step 6: Commit**

```bash
git add apps/accounts/models.py apps/accounts/migrations/ conftest.py \
        apps/accounts/tests/test_admin.py
git commit -m "Label every accounts model and field in Spanish"
```

**Risk:** `Role.Meta.permissions` changes the *name* text of six rows in `auth_permission`. Django's `create_permissions` only ever **creates** missing rows — it never renames existing ones — so the dev database keeps the English names until Task 8 lands. Do not treat that as a bug here.

---

### Task 4: Spanish metadata on every `apps.surveys` model

**Files:**
- Modify: `apps/surveys/models.py`
- Create: `apps/surveys/migrations/0002_*.py` (generated)
- Test: `apps/surveys/tests/test_admin.py` (create)

**Interfaces:**
- Consumes: `assert_explicit_labels` and `staff_client` fixtures from `conftest.py` (Tasks 1 and 3).

- [x] **Step 1: Write the failing test**

Create `apps/surveys/tests/test_admin.py`:

```python
import pytest
from django.urls import reverse

from apps.surveys.models import Module, Question, Survey, SurveyAssignment

pytestmark = pytest.mark.django_db


def test_no_surveys_model_shows_an_auto_derived_label(assert_explicit_labels):
    assert_explicit_labels("surveys")


@pytest.mark.parametrize(
    "model,field,value,expected",
    [
        (Survey, "status", Survey.Status.PUBLISHED, "Publicada"),
        (Module, "applies_to", Module.AppliesTo.SMALL, "Variante pequeña"),
        (Question, "question_type", Question.QuestionType.LIKERT, "Escala Likert"),
        (SurveyAssignment, "status", SurveyAssignment.Status.ACTIVE, "Activa"),
        (SurveyAssignment, "variant", SurveyAssignment.Variant.LARGE, "Guía III"),
    ],
)
def test_choice_labels_are_spanish(model, field, value, expected):
    """Choice labels reach the operator through changelists and filter sidebars."""
    assert dict(model._meta.get_field(field).choices)[value] == expected


def test_survey_change_form_labels_are_spanish(staff_client, survey):
    response = staff_client.get(reverse("admin:surveys_survey_change", args=[survey.pk]))

    body = response.content.decode()
    assert "Umbral de plantilla" in body
    assert "Headcount threshold" not in body
```

- [x] **Step 2: Run the test to verify it fails**

Run: `pytest apps/surveys/tests/test_admin.py -v`
Expected: 6 failures — 33 auto-derived labels, four English choice labels (`Published`, `Small variant`, `Likert Scale`, `Active`), and `Headcount threshold` on the change form. The `Guía III` case already passes.

- [x] **Step 3: Write the implementation**

In `apps/surveys/models.py`, keep every docstring, `save()`, `__str__`, `Meta.ordering`, `Meta.constraints` and `@staticmethod` exactly as they are. Change only labels, help texts and choice labels.

`Survey`:

```python
    class Status(models.TextChoices):
        DRAFT = "draft", "Borrador"
        PUBLISHED = "published", "Publicada"
        ARCHIVED = "archived", "Archivada"

    key = models.SlugField(
        "clave",
        max_length=64,
        unique=True,
        help_text="Identificador estable del instrumento, p. ej. 'nom035'.",
    )
    title = models.CharField("título", max_length=255)
    description = models.TextField("descripción", blank=True)
    status = models.CharField(
        "estado", max_length=20, choices=Status.choices, default=Status.DRAFT
    )
    headcount_threshold = models.PositiveIntegerField(
        "umbral de plantilla",
        default=50,
        help_text="Las empresas con más colaboradores que este número reciben la "
        "variante grande; las demás, la pequeña.",
    )
    created_at = models.DateTimeField("fecha de creación", auto_now_add=True)
    updated_at = models.DateTimeField("última actualización", auto_now=True)

    class Meta:
        verbose_name = "encuesta"
        verbose_name_plural = "encuestas"
        ordering = ["-created_at"]
```

`Module`:

```python
    class AppliesTo(models.TextChoices):
        ALL = "all", "Todos los participantes"
        SMALL = "small", "Variante pequeña"
        LARGE = "large", "Variante grande"

    survey = models.ForeignKey(
        Survey,
        on_delete=models.CASCADE,
        related_name="modules",
        verbose_name="encuesta",
    )
    key = models.SlugField(
        "clave",
        max_length=64,
        help_text="Identificador estable, único dentro de la encuesta. Lo "
        "referencian las reglas de visible_when (any_in_module).",
    )
    title = models.CharField(
        "título",
        max_length=255,
        blank=True,
        help_text="Encabezado divisor opcional, arriba de las preguntas del "
        "módulo. Déjalo vacío si el módulo solo presenta texto (ver descripción).",
    )
    intro = models.TextField(
        "introducción",
        blank=True,
        help_text="Encabezado opcional arriba del título o divisor, para el texto "
        "introductorio de una guía (p. ej. el nombre formal del cuestionario).",
    )
    description = models.TextField(
        "descripción",
        blank=True,
        help_text="Párrafo opcional. Se muestra como subtítulo bajo el título, o "
        "por sí solo cuando el título está vacío.",
    )
    order = models.PositiveIntegerField("orden", default=0)
    applies_to = models.CharField(
        "aplica a", max_length=10, choices=AppliesTo.choices, default=AppliesTo.ALL
    )
    visible_when = models.JSONField(
        "condición de visibilidad",
        null=True,
        blank=True,
        help_text="Regla opcional de visibilidad condicional. Vacío = siempre visible.",
    )

    class Meta:
        verbose_name = "módulo"
        verbose_name_plural = "módulos"
        ordering = ["order"]
        constraints = [
            models.UniqueConstraint(
                fields=["survey", "key"], name="unique_module_key_per_survey"
            ),
        ]
```

`Question`:

```python
    class QuestionType(models.TextChoices):
        TEXT = "text", "Texto"
        INTEGER = "integer", "Número entero"
        DECIMAL = "decimal", "Número decimal"
        DATE = "date", "Fecha"
        SINGLE_CHOICE = "single_choice", "Opción única"
        MULTIPLE_CHOICE = "multiple_choice", "Opción múltiple"
        BOOLEAN = "boolean", "Sí / No"
        RATING = "rating", "Calificación"
        LIKERT = "likert", "Escala Likert"

    module = models.ForeignKey(
        Module,
        on_delete=models.CASCADE,
        related_name="questions",
        verbose_name="módulo",
    )
    # Denormalized from module.survey so `code` can be unique per survey at the
    # database level. Kept in sync by save().
    survey = models.ForeignKey(
        Survey,
        on_delete=models.CASCADE,
        related_name="questions",
        editable=False,
        verbose_name="encuesta",
    )
    code = models.SlugField(
        "código",
        max_length=64,
        help_text="Identificador estable dentro de la encuesta, p. ej. 'g3-29'. Es "
        "la llave de integración que consume el motor de valoración.",
    )
    question_type = models.CharField(
        "tipo de pregunta", max_length=20, choices=QuestionType.choices
    )
    text = models.TextField("texto")
    order = models.PositiveIntegerField("orden", default=0)
    config = models.JSONField(
        "configuración",
        default=dict,
        blank=True,
        help_text="Configuración flexible por tipo: min, max, placeholder, labels, etc.",
    )
    visible_when = models.JSONField(
        "condición de visibilidad",
        null=True,
        blank=True,
        help_text="Regla opcional de visibilidad condicional. Vacío = siempre visible.",
    )

    class Meta:
        verbose_name = "pregunta"
        verbose_name_plural = "preguntas"
        ordering = ["order"]
        constraints = [
            models.UniqueConstraint(
                fields=["survey", "code"], name="unique_question_code_per_survey"
            ),
        ]
```

`Choice`:

```python
    question = models.ForeignKey(
        Question,
        on_delete=models.CASCADE,
        related_name="choices",
        verbose_name="pregunta",
    )
    label = models.CharField("etiqueta", max_length=255)
    value = models.CharField("valor", max_length=255)
    order = models.PositiveIntegerField("orden", default=0)

    class Meta:
        verbose_name = "opción"
        verbose_name_plural = "opciones"
        ordering = ["order"]
```

`SurveyAssignment`:

```python
    class Status(models.TextChoices):
        ACTIVE = "active", "Activa"
        CLOSED = "closed", "Cerrada"

    class Variant(models.TextChoices):
        SMALL = "small", "Guía II"
        LARGE = "large", "Guía III"

    company = models.ForeignKey(
        "accounts.Company",
        on_delete=models.CASCADE,
        related_name="survey_assignments",
        verbose_name="empresa",
    )
    survey = models.ForeignKey(
        Survey,
        on_delete=models.CASCADE,
        related_name="assignments",
        verbose_name="encuesta",
    )
    variant = models.CharField(
        "variante",
        max_length=10,
        choices=Variant.choices,
        help_text="Se fija al crear la asignación; no cambia si cambia la plantilla.",
    )
    status = models.CharField(
        "estado", max_length=20, choices=Status.choices, default=Status.ACTIVE
    )
    due_date = models.DateField("fecha límite", null=True, blank=True)
    created_at = models.DateTimeField("fecha de creación", auto_now_add=True)

    class Meta:
        verbose_name = "asignación de encuesta"
        verbose_name_plural = "asignaciones de encuesta"
        ordering = ["-created_at"]
```

- [x] **Step 4: Generate the migration and confirm it is a no-op**

Run: `python manage.py makemigrations surveys`
Expected: `apps/surveys/migrations/0002_*.py` with only `AlterModelOptions` and `AlterField`. Confirm each `AlterField` preserves `max_length`, `null`, `blank`, `unique`, `editable` and `default`.

Run: `python manage.py migrate surveys`

- [x] **Step 5: Run the tests to verify they pass**

Run: `pytest apps/surveys apps/core -v`
Expected: PASS. `apps/core` is included because its templates call `get_variant_display` — the `Variant` labels are deliberately unchanged, and this proves it.

- [x] **Step 6: Commit**

```bash
git add apps/surveys/models.py apps/surveys/migrations/ apps/surveys/tests/test_admin.py
git commit -m "Label every surveys model, field and choice in Spanish"
```

**Risk:** `Variant.SMALL`/`LARGE` labels (`Guía II`/`Guía III`) are rendered in four public templates via `get_variant_display`. They are already Spanish — leave them byte-for-byte identical.

---

### Task 5: Spanish metadata on every `apps.responses` model

**Files:**
- Modify: `apps/responses/models.py`
- Create: `apps/responses/migrations/0002_*.py` (generated)
- Test: `apps/responses/tests/test_admin.py` (create)

**Interfaces:**
- Consumes: `assert_explicit_labels` from `conftest.py` (Task 3).
- Produces: the Spanish word for a submission — **"envío"** — which Task 6 reuses for `SubmissionScore.submission`.

- [x] **Step 1: Write the failing test**

Create `apps/responses/tests/test_admin.py`:

```python
import pytest

from apps.responses.models import SurveySubmission

pytestmark = pytest.mark.django_db


def test_no_responses_model_shows_an_auto_derived_label(assert_explicit_labels):
    assert_explicit_labels("responses")


@pytest.mark.parametrize(
    "value,expected",
    [
        (SurveySubmission.Status.IN_PROGRESS, "En progreso"),
        (SurveySubmission.Status.COMPLETED, "Completado"),
    ],
)
def test_submission_status_labels_are_spanish(value, expected):
    field = SurveySubmission._meta.get_field("status")
    assert dict(field.choices)[value] == expected


def test_submission_str_is_spanish(active_assignment, make_user):
    submission = SurveySubmission.objects.create(
        assignment=active_assignment, user=make_user(email="envio@x.mx")
    )

    assert str(submission).startswith(f"Envío {submission.pk} — ")
```

- [x] **Step 2: Run the test to verify it fails**

Run: `pytest apps/responses/tests/test_admin.py -v`
Expected: 4 failures — 8 auto-derived labels, `In Progress`/`Completed`, and `"Submission 1 — ..."`.

- [x] **Step 3: Write the implementation**

In `apps/responses/models.py`, keeping both `Meta.constraints` blocks and `Meta.ordering` unchanged:

```python
class SurveySubmission(models.Model):
    class Status(models.TextChoices):
        IN_PROGRESS = "in_progress", "En progreso"
        COMPLETED = "completed", "Completado"

    assignment = models.ForeignKey(
        "surveys.SurveyAssignment",
        on_delete=models.CASCADE,
        related_name="submissions",
        verbose_name="asignación",
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="submissions",
        verbose_name="colaborador",
    )
    status = models.CharField(
        "estado", max_length=20, choices=Status.choices, default=Status.IN_PROGRESS
    )
    started_at = models.DateTimeField("fecha de inicio", auto_now_add=True)
    completed_at = models.DateTimeField("fecha de término", null=True, blank=True)

    class Meta:
        verbose_name = "envío de encuesta"
        verbose_name_plural = "envíos de encuesta"
        ordering = ["-started_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["user", "assignment"],
                condition=models.Q(user__isnull=False),
                name="unique_submission_per_user_assignment",
            ),
        ]

    def __str__(self):
        return f"Envío {self.pk} — {self.assignment}"


class Answer(models.Model):
    submission = models.ForeignKey(
        SurveySubmission,
        on_delete=models.CASCADE,
        related_name="answers",
        verbose_name="envío",
    )
    question = models.ForeignKey(
        "surveys.Question",
        on_delete=models.CASCADE,
        related_name="answers",
        verbose_name="pregunta",
    )
    value = models.JSONField(
        "valor",
        help_text="Valor de la respuesta; su interpretación depende del tipo de "
        "pregunta.",
    )

    class Meta:
        verbose_name = "respuesta"
        verbose_name_plural = "respuestas"
        constraints = [
            models.UniqueConstraint(
                fields=["submission", "question"],
                name="unique_answer_per_question",
            ),
        ]

    def __str__(self):
        return f"Respuesta a la pregunta {self.question_id} del envío {self.submission_id}"
```

- [x] **Step 4: Generate the migration and confirm it is a no-op**

Run: `python manage.py makemigrations responses`
Expected: `apps/responses/migrations/0002_*.py` with only `AlterModelOptions` and `AlterField`.

Run: `python manage.py migrate responses`

- [x] **Step 5: Run the tests to verify they pass**

Run: `pytest apps/responses apps/surveys apps/nom035 -v`
Expected: PASS. `apps/surveys` and `apps/nom035` are included because they create submissions; nothing asserts on `str(submission)` today, so this is a regression check rather than an expected break.

- [x] **Step 6: Commit**

```bash
git add apps/responses/models.py apps/responses/migrations/ \
        apps/responses/tests/test_admin.py
git commit -m "Label every responses model and field in Spanish"
```

---

### Task 6: Spanish metadata on every `apps.nom035` model

**Files:**
- Modify: `apps/nom035/models.py`
- Create: `apps/nom035/migrations/0002_*.py` (generated)
- Test: `apps/nom035/tests/test_admin.py` (create)

**Interfaces:**
- Consumes: `assert_explicit_labels` from `conftest.py` (Task 3); the word "envío" settled in Task 5.

- [x] **Step 1: Write the failing test**

Create `apps/nom035/tests/test_admin.py`:

```python
import pytest

pytestmark = pytest.mark.django_db


def test_no_nom035_model_shows_an_auto_derived_label(assert_explicit_labels):
    assert_explicit_labels("nom035")
```

- [x] **Step 2: Run the test to verify it fails**

Run: `pytest apps/nom035/tests/test_admin.py -v`
Expected: FAIL listing 10 auto-derived field labels plus `nom035.SubmissionScore.Meta.verbose_name` and `nom035.GroupScore.Meta.verbose_name`. The `NDR` and `GroupLevel` choice labels are already Spanish and are not flagged.

- [x] **Step 3: Write the implementation**

In `apps/nom035/models.py`, keeping the `NDR` and `GroupLevel` choice classes, the `unique_together`, the indexes and both comments unchanged:

```python
class SubmissionScore(models.Model):
    submission = models.OneToOneField(
        "responses.SurveySubmission",
        on_delete=models.CASCADE,
        related_name="nom035_score",
        verbose_name="envío",
    )
    final_score = models.IntegerField("puntaje final", default=0)
    final_ndr = models.CharField(
        "nivel de riesgo final", max_length=10, choices=NDR.choices, default=NDR.NULO
    )
    # Official Guía I clinical-referral outcome (binary); see scoring.guia1_positive.
    guia1_positive = models.BooleanField("positivo en Guía I", default=False)
    computed_at = models.DateTimeField("fecha de cálculo", auto_now=True)

    class Meta:
        verbose_name = "valoración"
        verbose_name_plural = "valoraciones"

    def __str__(self):
        return f"Valoración({self.submission_id}={self.final_ndr})"


class GroupScore(models.Model):
    submission_score = models.ForeignKey(
        SubmissionScore,
        on_delete=models.CASCADE,
        related_name="groups",
        verbose_name="valoración",
    )
    level = models.CharField("nivel", max_length=12, choices=GroupLevel.choices)
    key = models.CharField("clave", max_length=64)
    score = models.IntegerField("puntaje", default=0)
    ndr = models.CharField(
        "nivel de riesgo",
        max_length=10,
        choices=NDR.choices,
        default=NDR.NULO,
        blank=True,
    )

    class Meta:
        verbose_name = "puntaje por grupo"
        verbose_name_plural = "puntajes por grupo"
        unique_together = ("submission_score", "level", "key")
        indexes = [
            models.Index(fields=["submission_score", "level"]),
            models.Index(fields=["level", "ndr"]),
        ]
```

- [x] **Step 4: Generate the migration and confirm it is a no-op**

Run: `python manage.py makemigrations nom035`
Expected: `apps/nom035/migrations/0002_*.py` with only `AlterModelOptions` and `AlterField`. The indexes and `unique_together` must **not** appear — if they do, the `Meta` block was reordered in a way that dropped one.

Run: `python manage.py migrate nom035`

- [x] **Step 5: Run the tests to verify they pass**

Run: `pytest apps/nom035 apps/core -v`
Expected: PASS. `apps/core` reads these models through `aggregates.py`.

- [x] **Step 6: Commit**

```bash
git add apps/nom035/models.py apps/nom035/migrations/ apps/nom035/tests/test_admin.py
git commit -m "Label every nom035 model and field in Spanish"
```

---

## 4. Admin-layer strings

### Task 7: Spanish fieldset titles on the User admin

**Files:**
- Modify: `apps/accounts/admin.py:32-37`
- Test: `apps/accounts/tests/test_admin.py` (append to `TestSpanishAdminLabels`)

**Interfaces:**
- Consumes: `staff_client` from `conftest.py` (Task 1).

Everything else in the admin layer already resolves to Spanish for free: inline headings (`ModuleInline`, `QuestionInline`, `ChoiceInline`, `AnswerInline`, `GroupScoreInline`) read their model's `Meta.verbose_name_plural`, and `CompanyAdmin.area_count` / `location_count` already declare `description="Áreas"` / `"Localidades"`. The two `"SOFIA-S access"` fieldset titles are the only hardcoded English left.

- [ ] **Step 1: Write the failing test**

Append to the `TestSpanishAdminLabels` class in `apps/accounts/tests/test_admin.py`:

```python
    def test_user_add_and_change_fieldsets_are_spanish(self, staff_client, make_user):
        user = make_user(email="fieldset@x.mx")

        for url in (
            reverse("admin:accounts_user_add"),
            reverse("admin:accounts_user_change", args=[user.pk]),
        ):
            body = staff_client.get(url).content.decode()
            assert "Acceso SOFIA-S" in body, url
            assert "SOFIA-S access" not in body, url
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `pytest apps/accounts/tests/test_admin.py -k fieldsets -v`
Expected: FAIL — `assert "Acceso SOFIA-S" in body`.

- [ ] **Step 3: Write the implementation**

In `apps/accounts/admin.py`:

```python
    fieldsets = UserAdmin.fieldsets + (
        ("Acceso SOFIA-S", {"fields": ("must_change_password",)}),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        ("Acceso SOFIA-S", {"fields": ("must_change_password",)}),
    )
```

- [ ] **Step 4: Run the tests to verify they pass**

Run: `pytest apps/accounts -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add apps/accounts/admin.py apps/accounts/tests/test_admin.py
git commit -m "Name the User admin fieldset in Spanish"
```

---

## 5. Permission names

### Task 8: Spanish permission names in the Groups picker

**Files:**
- Create: `apps/core/permissions.py`
- Modify: `apps/core/apps.py`
- Test: `apps/core/tests/test_localization.py` (append)

**Interfaces:**
- Consumes: the Spanish `Meta.verbose_name` set in Tasks 3–6. **This task must run last of the metadata tasks**, because the generated names are built from `verbose_name`.
- Produces: `apps.core.permissions.rename_permissions_to_spanish(sender, **kwargs)` — a `post_migrate` receiver.

**Why this exists:** Django builds the four built-in permission names from an untranslated `"Can %s %s"` template (`django/contrib/auth/management/__init__.py:32`), so a Spanish `verbose_name` alone yields `"Can add empresa"` — mixed English and Spanish on an operator screen. And `create_permissions` only *creates* missing rows: it never renames one whose label changed, so Task 3's new `Role.Meta.permissions` labels would never reach an existing database. One receiver fixes both.

- [ ] **Step 1: Write the failing test**

Append to `apps/core/tests/test_localization.py`:

```python
@pytest.mark.parametrize(
    "codename,expected",
    [
        # Built-in permissions: Django's "Can %s %s" template is not translated.
        ("add_company", "Puede agregar empresa"),
        ("view_surveyassignment", "Puede consultar asignación de encuesta"),
        ("change_submissionscore", "Puede modificar valoración"),
        ("delete_answer", "Puede eliminar respuesta"),
        # Custom permissions declared on Role.Meta.
        ("can_view_dashboard", "Puede ver el tablero"),
        ("can_view_insights", "Puede ver la valoración de resultados"),
    ],
)
def test_permission_names_in_the_groups_picker_are_spanish(codename, expected):
    from django.contrib.auth.models import Permission

    assert Permission.objects.get(codename=codename).name == expected


def test_permission_renaming_leaves_django_own_apps_alone():
    """Only the project's four apps are rewritten; auth/admin keep Django's names."""
    from django.contrib.auth.models import Permission

    perm = Permission.objects.get(
        content_type__app_label="auth", codename="add_group"
    )
    assert perm.name == "Can add group"
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `pytest apps/core/tests/test_localization.py -k permission --create-db -v`
Expected: 6 failures reading `"Can add empresa"`, `"Can view asignación de encuesta"`, `"Can manage surveys"`, etc.

`--create-db` is **mandatory** here. `addopts` carries `--reuse-db`, and permission rows are written by `post_migrate` at database-creation time only — a reused test database keeps whatever names it was born with, so without `--create-db` this test lies in both directions.

- [ ] **Step 3: Write the implementation**

Create `apps/core/permissions.py`:

```python
"""Rewrite auto-generated permission names into Spanish.

Django builds the four built-in permission names from a hardcoded, untranslated
`"Can %s %s"` template, so a Spanish `Meta.verbose_name` alone produces
"Can add empresa" in the Groups permission picker. `create_permissions` also
only ever *creates* missing rows — it never renames one whose label changed —
so an edit to `Role.Meta.permissions` would otherwise never reach a database
that already has the row.
"""

from django.contrib.auth import get_permission_codename

PROJECT_APP_LABELS = frozenset({"accounts", "surveys", "responses", "nom035"})

ACTION_VERBS = {
    "add": "Puede agregar",
    "change": "Puede modificar",
    "delete": "Puede eliminar",
    "view": "Puede consultar",
}


def _spanish_names(app_config):
    """{codename: Spanish name} for every permission the app declares."""
    names = {}
    for model in app_config.get_models():
        opts = model._meta
        for action in opts.default_permissions:
            verb = ACTION_VERBS.get(action)
            if verb is None:
                continue
            names[get_permission_codename(action, opts)] = (
                f"{verb} {opts.verbose_name_raw}"
            )
        names.update(dict(opts.permissions))
    return names


def rename_permissions_to_spanish(sender, apps=None, using=None, **kwargs):
    """`post_migrate` receiver. Display-only: codenames are never touched."""
    if sender.label not in PROJECT_APP_LABELS:
        return

    Permission = apps.get_model("auth", "Permission")
    names = _spanish_names(sender)
    queryset = Permission.objects.using(using).filter(
        content_type__app_label=sender.label, codename__in=names
    )
    stale = [p for p in queryset if p.name != names[p.codename]]
    for permission in stale:
        permission.name = names[permission.codename]
    Permission.objects.using(using).bulk_update(stale, ["name"])
```

Modify `apps/core/apps.py`:

```python
from django.apps import AppConfig
from django.db.models.signals import post_migrate


class CoreConfig(AppConfig):
    name = "apps.core"
    label = "core"
    default_auto_field = "django.db.models.BigAutoField"

    def ready(self):
        from apps.core.permissions import rename_permissions_to_spanish

        # Connected without a sender: the receiver filters to the project's apps
        # itself, and each app's permissions only exist once its own post_migrate
        # has fired. `django.contrib.auth` is earlier in INSTALLED_APPS, so its
        # create_permissions receiver always runs before this one.
        post_migrate.connect(rename_permissions_to_spanish)
```

- [ ] **Step 4: Run the tests to verify they pass**

Run: `pytest apps/core/tests/test_localization.py --create-db -v`
Expected: PASS (17 tests)

- [ ] **Step 5: Verify against a real database**

```bash
python manage.py migrate
python manage.py bootstrap_groups
python manage.py shell -c "
from django.contrib.auth.models import Permission
for p in Permission.objects.filter(content_type__app_label__in=['accounts','surveys','responses','nom035']).order_by('content_type__app_label','codename'):
    print(p.content_type.app_label, p.codename, '|', p.name)
"
```

Expected: `bootstrap_groups` runs clean (it matches on codename, which nothing here changes), and every printed name is Spanish. Then open `/admin/auth/group/add/` and confirm the permission picker shows no English.

- [ ] **Step 6: Run the whole suite**

Run: `pytest --create-db`
Expected: PASS. Use `--create-db` once here so the test database is rebuilt with the new permission rows; later runs can go back to the default `--reuse-db`.

- [ ] **Step 7: Commit**

```bash
git add apps/core/permissions.py apps/core/apps.py apps/core/tests/test_localization.py
git commit -m "Rewrite auto-generated permission names into Spanish"
```

**Risk:** this is the one task that writes rows rather than only changing metadata. It updates `auth_permission.name` and nothing else — no codename, no content type, no group membership. `bootstrap_groups.GROUP_PERMISSIONS` and `conftest.py`'s `bootstrap_groups` fixture both resolve by codename and need no change; Step 5 proves it.

---

## 6. Documentation

### Task 9: Record the convention and refresh the affected docs

**Files:**
- Modify: `.claude/CLAUDE.md` (Cross-cutting concepts)
- Modify: `docs/platform/localization.md`
- Modify: `docs/internal/open-findings.md`
- Modify: `docs/internal/user-guides/csv-user-import.md:25,59`
- Modify: `docs/internal/user-guides/user-onboarding.md:40,58`
- Modify: `apps/accounts/CLAUDE.md` (Conventions & gotchas)

**Interfaces:**
- Consumes: the final Spanish names chosen in Tasks 2–6.

Live docs describe only the current implementation. Write every edit below as if es-MX had always been the setup — no "formerly", no "now Spanish", no before/after. `docs/adr/` is untouched: this sets a convention rather than choosing between competing architectures, so no ADR is warranted and none becomes inaccurate.

- [ ] **Step 1: Record the convention in `.claude/CLAUDE.md`**

Add a bullet to **Cross-cutting concepts**, after the **Authorization** bullet:

```markdown
- **Spanish UI, English code**: `LANGUAGE_CODE = "es-mx"` and `TIME_ZONE = "America/Mexico_City"` (storage stays UTC via `USE_TZ`). Django ships layer 1 — its own chrome, validation and date formats. Everything else an operator reads is metadata we write, so **every model field carries an explicit lowercase Spanish `verbose_name`, every model a Spanish `Meta.verbose_name`/`verbose_name_plural`, and every `TextChoices` a Spanish label** — without them Django derives the label from the English attribute name and leaks it onto the screen. Strings are hardcoded; there is no `gettext`, no `.po` files and no second language. `apps/core/permissions.py` rewrites the auto-generated `auth_permission` names, which Django builds from an untranslated template. `conftest.py`'s `assert_explicit_labels` fixture fails a build that forgets one. See `docs/platform/localization.md`.
```

- [ ] **Step 2: Rewrite `docs/platform/localization.md` as shipped documentation**

- **Status** → `Implemented.`
- Delete **Open questions** entirely — all three are answered and now belong in **Key decisions**.
- Replace the "Current state, measured" table with the shipped rule: every model in the four apps carries explicit metadata, enforced by `assert_explicit_labels`.
- Under **Scope**, state the settled scope (every model in the four apps, registered or not) rather than the candidate scopes.
- Add to **Key decisions**: the `America/Mexico_City` timezone; the four `AppConfig.verbose_name` values; accepting Django's `es_MX` date formats instead of a `FORMAT_MODULE_PATH`; branding the admin chrome as SOFIA-S; hardcoding `"nombre(s)"`/`"apellidos"` over Django's singular `"apellido"`.
- Add a short **Permission names** section explaining `apps/core/permissions.py` and why it exists (untranslated `"Can %s %s"`; `create_permissions` never renames).
- Under **Test mapping**, list what actually exists: `apps/core/tests/test_localization.py` plus a `test_admin.py` per app.
- Keep the **Data model impact** wrinkle about `auth_permission` only as far as it is still true — the receiver now rewrites those rows on every `migrate`, so the "chore once there is data worth keeping" caveat goes away.

- [ ] **Step 3: Retire the open finding and record the new one**

In `docs/internal/open-findings.md`, delete section **1** in full and replace it with:

```markdown
## 1. Authorization group names are in English 🟡

**Where:** `apps/accounts/management/commands/bootstrap_groups.py`
(`GROUP_PERMISSIONS`), `apps/accounts/importers.py`, `apps/accounts/views.py`
(`_redirect_after_login`), `conftest.py` (`bootstrap_groups` fixture).

**What:** The four groups — `Admins`, `Principal Exec`, `Secondary Exec`,
`Employees` — appear in English in the admin's Groups list and in the CSV
importer's `group` column, on an otherwise Spanish operator surface.

**Why it was left alone:** `auth.Group.name` is looked up **by string** in four
places, and the CSV import contract accepts it as a column value. Renaming is a
behavior change with an input-format consequence, not the presentation-only
sweep that `docs/platform/localization.md` covers. Doing it properly means
picking Spanish names, updating all four call sites, and deciding whether the
importer keeps accepting the English spellings.
```

- [ ] **Step 4: Update the operator guides to the labels they now see**

In `docs/internal/user-guides/csv-user-import.md`: `**Companies**` → `**Empresas**` (line 25), `**Users**` → `**Usuarios**` (line 59).

In `docs/internal/user-guides/user-onboarding.md`: `**Users**` → `**Usuarios**` (line 40), `**User profiles**` → `**Perfiles de colaborador**` (line 58). At line 64, `` `is_activated` `` → `**Cuenta activada**`, since that is the field label the operator reads.

Re-read both guides end to end and fix any other reference to an admin screen or field label that no longer matches — including the *Áreas* count column mentioned at `user-onboarding.md:24` (unchanged, but confirm).

- [ ] **Step 5: Update `apps/accounts/CLAUDE.md`**

Replace the first bullet of **Conventions & gotchas** — currently "**User-facing strings are in Spanish**; code/comments in English" — with a version that names the mechanism:

```markdown
- **User-facing strings are in Spanish**; code, identifiers and comments in English. Every field carries an explicit Spanish `verbose_name` and every model a Spanish `Meta.verbose_name` — that metadata is the only thing standing between an English attribute name and a Spanish admin screen. `Role.Meta.permissions` labels are Spanish too; they surface in the Groups permission picker.
```

- [ ] **Step 6: Verify**

Run: `pytest`
Expected: PASS (docs-only step, but confirms the branch is green before finishing).

Run: `grep -rn "gettext\|_(\"" apps/ --include="*.py" | grep -v migrations`
Expected: no hits — the no-`gettext` constraint holds.

Run: `git diff --stat main -- docs/adr/`
Expected: empty. No ADR may be touched.

- [ ] **Step 7: Commit**

```bash
git add .claude/CLAUDE.md docs/platform/localization.md \
        docs/internal/open-findings.md docs/internal/user-guides/ \
        apps/accounts/CLAUDE.md
git commit -m "Document the es-MX localization convention"
```

---

## Final verification

- [ ] `ruff format --check .` and `ruff check .` are clean.
- [ ] `python manage.py check` reports no issues.
- [ ] `python manage.py makemigrations --check --dry-run` reports no pending changes.
- [ ] `pytest --create-db` passes end to end.
- [ ] On a freshly created database: `python manage.py migrate && python manage.py bootstrap_groups && python manage.py seed_nom035_survey` all run clean.
- [ ] Eyeball in a browser: `/admin/` index (Spanish app groups, `Administración SOFIA-S`), a Company change form (inlines, Spanish labels, Mexico City timestamps), the Groups permission picker, and the public app home + a survey page (unchanged except for displayed times).
