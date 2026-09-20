# Employee demographics at activation — implementation plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Collect apellido paterno, apellido materno, sexo and fecha de nacimiento from every employee at activation, so NOM-035 results can later be segmented by age and sex.

**Architecture:** `User.last_name` is removed and replaced by `paternal_last_name` + `maternal_last_name`; `UserProfile` gains `sex` and `date_of_birth` plus a derived `age` property. All four are nullable/blank at the model layer (the CSV importer creates both rows before the employee answers anything) and required in `ProfileActivationForm`. No aggregation code changes.

**Tech Stack:** Django 6.0, PostgreSQL 17 (`es-MX-x-icu` collation), pytest + pytest-django, TailwindCSS v4.

**Spec:** [`docs/platform/wip/auth-and-onboarding-change.md`](auth-and-onboarding-change.md) · [ADR-0005](../../adr/adr-0005-two-surname-names-and-profile-demographics.md)

## Global Constraints

- **Spanish UI, English code.** Every model field needs an explicit lowercase Spanish `verbose_name`; every `TextChoices` member needs a Spanish label. `conftest.py`'s `assert_explicit_labels` fails the build on a missing `verbose_name` but does **not** check `TextChoices` labels.
- **No `gettext`, no `.po` files.** All Spanish strings are hardcoded.
- **Spanish-text columns that appear in sorted lists carry `db_collation=SPANISH_COLLATION`** (`es-MX-x-icu`, defined in `apps/accounts/models.py`).
- **`pytest` runs with `--reuse-db -x`** — the first failure stops the suite, so every task must end green.
- **Run `npm run build:css` after any change to `templates/` or to widget `attrs` in `apps/**/*.py`**, and commit `static/css/output.css`. Tailwind only compiles classes found in the sources listed in `static/css/main.css`.
- **There is no JavaScript test runner.** Python tests assert the server-rendered contract only.
- **Live docs describe only the current implementation** — no "formerly", no before/after commentary. `docs/adr/` is the exception.

---

### Task 1: Replace `User.last_name` with the two-surname pair

This is one task rather than several because removing the column breaks
`views.py`, `admin.py` and the roster in the same commit. A reviewer cannot
accept the model change while rejecting the view change.

**Files:**
- Modify: `apps/accounts/models.py:65-71`
- Create: `apps/accounts/migrations/0007_*.py` (generated)
- Modify: `apps/accounts/forms.py:236-243`, `apps/accounts/views.py:294-299,320-324`, `apps/accounts/admin.py:29-37`
- Modify: `apps/core/views.py:303-305`
- Modify: `templates/accounts/profile_setup.html:54-62`, `templates/core/employee_list.html:38-40`, `templates/core/employee_detail.html:4,37-38,45-47`
- Test: `apps/accounts/tests/test_models.py:127-134`, `apps/accounts/tests/test_forms.py`, `apps/accounts/tests/test_views.py`

**Interfaces:**
- Consumes: nothing — first task.
- Produces: `User.paternal_last_name: str`, `User.maternal_last_name: str`, `User.get_full_name() -> str` (joins first/paternal/maternal, skipping empties). `ProfileActivationForm` fields `paternal_last_name` (required) and `maternal_last_name` (optional). Tasks 2–4 rely on these names.

- [ ] **Step 1: Write the failing model tests**

In `apps/accounts/tests/test_models.py`, replace the body of
`test_employee_roster_orders_surnames_as_spanish` (currently at line 127) and add
a new class beside it:

```python
    def test_employee_roster_orders_surnames_as_spanish(self, make_user):
        for i, surname in enumerate(("Zamora", "Álvarez", "Núñez", "Nogales")):
            make_user(email=f"user{i}@example.com", paternal_last_name=surname)

        assert [
            u.paternal_last_name
            for u in User.objects.exclude(paternal_last_name="").order_by(
                "paternal_last_name"
            )
        ] == ["Álvarez", "Nogales", "Núñez", "Zamora"]


@pytest.mark.django_db
class TestUserFullName:
    def test_joins_both_surnames(self, make_user):
        user = make_user(
            email="full@example.com",
            first_name="Ana María",
            paternal_last_name="López",
            maternal_last_name="Núñez",
        )
        assert user.get_full_name() == "Ana María López Núñez"

    def test_omits_a_missing_maternal_surname(self, make_user):
        user = make_user(
            email="one@example.com", first_name="Ana", paternal_last_name="López"
        )
        assert user.get_full_name() == "Ana López"

    def test_is_empty_when_nothing_is_recorded(self, make_user):
        assert make_user(email="blank@example.com").get_full_name() == ""

    def test_has_no_last_name_field(self):
        with pytest.raises(FieldDoesNotExist):
            User._meta.get_field("last_name")
```

Add the import at the top of the file:

```python
from django.core.exceptions import FieldDoesNotExist
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `pytest apps/accounts/tests/test_models.py -k "surnames_as_spanish or TestUserFullName" -v`
Expected: FAIL — `TypeError: User() got unexpected keyword arguments: 'paternal_last_name'`

- [ ] **Step 3: Change the model**

In `apps/accounts/models.py`, replace the `first_name`/`last_name` block inside
`class User` (lines 65-71) with:

```python
    # `AbstractUser` is abstract, so setting an inherited field to None removes
    # the column outright. A Mexican name is nombre(s) + paterno + materno, and
    # the two surnames are not interchangeable: the roster sorts by the paternal
    # one.
    last_name = None

    # These carry the collation because the employee roster orders by them, and
    # an "Álvarez" sorting below every ASCII surname is the most visible
    # instance of the byte-order problem.
    first_name = models.CharField(
        "nombre(s)", max_length=150, blank=True, db_collation=SPANISH_COLLATION
    )
    paternal_last_name = models.CharField(
        "apellido paterno", max_length=150, blank=True, db_collation=SPANISH_COLLATION
    )
    maternal_last_name = models.CharField(
        "apellido materno", max_length=150, blank=True, db_collation=SPANISH_COLLATION
    )

    def get_full_name(self):
        parts = (self.first_name, self.paternal_last_name, self.maternal_last_name)
        return " ".join(part for part in parts if part)
```

- [ ] **Step 4: Generate and run the migration**

```bash
source .venv/bin/activate
python manage.py makemigrations accounts
python manage.py migrate
```

Expected: a new `apps/accounts/migrations/0007_*.py` removing `last_name` and adding the two surname fields.

- [ ] **Step 5: Run the model tests to verify they pass**

Run: `pytest apps/accounts/tests/test_models.py -v`
Expected: PASS

- [ ] **Step 6: Update the activation form**

In `apps/accounts/forms.py`, replace the `last_name` field of
`ProfileActivationForm` (lines 236-243) with:

```python
    paternal_last_name = forms.CharField(
        label="Apellido paterno",
        max_length=150,
        error_messages={"required": "Escribe tu apellido paterno."},
        widget=forms.TextInput(
            attrs={"autocomplete": "family-name", "class": _TEXT_CLASSES}
        ),
    )
    # Optional: not everyone has two surnames, and requiring it would block a
    # foreign-national employee at the activation gate for no analytical gain.
    maternal_last_name = forms.CharField(
        label="Apellido materno",
        max_length=150,
        required=False,
        widget=forms.TextInput(
            attrs={
                "autocomplete": "additional-name",
                "placeholder": "Opcional",
                "class": _TEXT_CLASSES,
            }
        ),
    )
```

Also update the comment above `first_name` (line 232-234) to read:

```python
    # Name and cargo are collected here rather than at import: the admin's roster
    # only has to carry what identifies the account, and the employee is the
    # authority on their own name anyway.
```

- [ ] **Step 7: Update the view**

In `apps/accounts/views.py`, in the GET prefill block (lines 294-299), replace
the `"last_name"` entry:

```python
        initial = {
            "first_name": request.user.first_name,
            "paternal_last_name": request.user.paternal_last_name,
            "maternal_last_name": request.user.maternal_last_name,
            "position": profile.position,
        }
```

And in the transaction (lines 320-324):

```python
        user = request.user
        user.first_name = form.cleaned_data["first_name"]
        user.paternal_last_name = form.cleaned_data["paternal_last_name"]
        user.maternal_last_name = form.cleaned_data["maternal_last_name"]
        user.save(
            update_fields=["first_name", "paternal_last_name", "maternal_last_name"]
        )
```

- [ ] **Step 8: Update the admin**

In `apps/accounts/admin.py`, replace lines 31-34 of `CustomUserAdmin`. Django's
`UserAdmin` names `last_name` in `list_display`, `search_fields` and the personal-info
fieldset, so composing from its defaults now fails system checks:

```python
    # Declared in full rather than composed from UserAdmin's defaults: those name
    # `last_name`, which this project's User does not have.
    list_display = (
        "username",
        "email",
        "first_name",
        "paternal_last_name",
        "maternal_last_name",
        "is_staff",
        "must_change_password",
    )
    search_fields = (
        "username",
        "first_name",
        "paternal_last_name",
        "maternal_last_name",
        "email",
    )
    fieldsets = (
        (None, {"fields": ("username", "password")}),
        (
            "Información personal",
            {
                "fields": (
                    "first_name",
                    "paternal_last_name",
                    "maternal_last_name",
                    "email",
                )
            },
        ),
        (
            "Permisos",
            {
                "fields": (
                    "is_active",
                    "is_staff",
                    "is_superuser",
                    "groups",
                    "user_permissions",
                )
            },
        ),
        ("Fechas importantes", {"fields": ("last_login", "date_joined")}),
        ("Acceso SOFIA-S", {"fields": ("must_change_password",)}),
    )
```

Leave `add_fieldsets` as it is — Django's default does not reference `last_name`.

- [ ] **Step 9: Write the failing system-check test**

Create `apps/accounts/tests/test_admin_checks.py`:

```python
import pytest
from django.core.management import call_command


@pytest.mark.django_db
def test_django_system_checks_pass():
    """The admin composes field lists by hand, so a renamed field breaks silently
    until `check` runs. `admin.E108`/`E012` are the failures this catches."""
    call_command("check")
```

- [ ] **Step 10: Run it to verify it passes**

Run: `pytest apps/accounts/tests/test_admin_checks.py -v`
Expected: PASS. If it fails with `admin.E108` or `admin.E012`, a field list in Step 8 is wrong.

- [ ] **Step 11: Update the roster ordering**

In `apps/core/views.py`, replace lines 303-305:

```python
        # Paternal surname first: that is how a Mexican roster reads.
        profiles = company.members.select_related("user", "area", "location").order_by(
            "user__paternal_last_name",
            "user__maternal_last_name",
            "user__first_name",
        )
```

- [ ] **Step 12: Update the templates**

`templates/accounts/profile_setup.html` — replace the `last_name` block (lines 54-62) with two blocks:

```html
      <div class="mb-6">
        <label for="{{ form.paternal_last_name.id_for_label }}" class="block text-sm font-medium text-gray-700 mb-1">
          Apellido paterno
        </label>
        {{ form.paternal_last_name }}
        {% if form.paternal_last_name.errors %}
          <p class="mt-1 text-xs text-red-600">{{ form.paternal_last_name.errors.0 }}</p>
        {% endif %}
      </div>

      <div class="mb-6">
        <label for="{{ form.maternal_last_name.id_for_label }}" class="block text-sm font-medium text-gray-700 mb-1">
          Apellido materno
        </label>
        {{ form.maternal_last_name }}
        {% if form.maternal_last_name.errors %}
          <p class="mt-1 text-xs text-red-600">{{ form.maternal_last_name.errors.0 }}</p>
        {% endif %}
      </div>
```

`templates/core/employee_list.html` — replace lines 38-40:

```html
                  {% if user.get_full_name %}
                    {{ user.get_full_name }}
                  {% else %}
                    <span class="text-gray-400 font-normal italic">Sin nombre</span>
                  {% endif %}
```

`templates/core/employee_detail.html` — line 4:

```html
{% block title %}{{ employee_profile.user.get_full_name }} — {{ company.name }} | SOFIA-S{% endblock %}
```

lines 37-38 (the avatar initials):

```html
        {% if emp.first_name or emp.paternal_last_name %}
          {{ emp.first_name|slice:":1" }}{{ emp.paternal_last_name|slice:":1" }}
```

and lines 45-47 (the heading):

```html
          {% if emp.get_full_name %}
            {{ emp.get_full_name }}
          {% else %}
            <span class="text-gray-400 font-normal italic">Sin nombre</span>
          {% endif %}
```

- [ ] **Step 13: Write the failing roster-ordering test**

Add to `TestCompanyEmployeeListView` in `apps/core/tests/test_views.py` (the class
starts at line 447 and already defines `URL` and `_make_viewer`):

```python
    def test_roster_is_ordered_by_paternal_surname(
        self, client, make_user, make_company, make_user_with_profile
    ):
        """A Mexican roster files under the apellido paterno, and the Spanish
        collation is what keeps "Álvarez" above "Barrios" instead of after "Z"."""
        company = make_company()
        viewer = self._make_viewer(make_user, company)
        for email, first, paternal in (
            ("z@example.com", "Ana", "Zamora"),
            ("a@example.com", "Bruno", "Álvarez"),
            ("n@example.com", "Carla", "Núñez"),
        ):
            make_user_with_profile(
                email=email,
                company=company,
                first_name=first,
                paternal_last_name=paternal,
            )

        client.force_login(viewer)
        members = client.get(self.URL).context["members"]

        surnames = [
            item["profile"].user.paternal_last_name
            for item in members
            if item["profile"].user.paternal_last_name
        ]
        assert surnames == ["Álvarez", "Núñez", "Zamora"]
```

- [ ] **Step 14: Run it to verify it passes**

Run: `pytest apps/core/tests/test_views.py::TestCompanyEmployeeListView::test_roster_is_ordered_by_paternal_surname -v`
Expected: PASS (Step 11 already changed the ordering). If it fails with the
surnames in a different order, `order_by` in Step 11 is wrong.

- [ ] **Step 15: Update the existing form and view tests**

In `apps/accounts/tests/test_forms.py`, replace every `"last_name": "López"` in
the `_form` and `_data` helpers (lines 53-54 and 96-97) with
`"paternal_last_name": "López"`, and rewrite the two identity tests:

```python
    def test_name_is_required(self, company_with_area):
        company, area = company_with_area
        form = ProfileActivationForm(
            data=self._data(company, area, first_name="", paternal_last_name=""),
            company=company,
        )
        assert not form.is_valid()
        assert "first_name" in form.errors
        assert "paternal_last_name" in form.errors

    def test_maternal_surname_is_optional(self, company_with_area):
        company, area = company_with_area
        form = ProfileActivationForm(data=self._data(company, area), company=company)
        assert form.is_valid(), form.errors
        assert form.cleaned_data["maternal_last_name"] == ""
```

and in `test_values_are_stripped` (lines 125-133) swap `last_name` for
`paternal_last_name` in both the input and the assertion.

In `apps/accounts/tests/test_views.py`, change `_activation_post` (line 557) to
carry `"paternal_last_name": "López"`, then update the assertions at lines
850-851, 866-872, 899-909 and 929 to use `paternal_last_name`. In
`test_form_prefills_details_already_on_record` also assert the maternal surname:

```python
        user.first_name = "Ana"
        user.paternal_last_name = "López"
        user.maternal_last_name = "Núñez"
        user.save(
            update_fields=["first_name", "paternal_last_name", "maternal_last_name"]
        )
        ...
        assert form.initial["paternal_last_name"] == "López"
        assert form.initial["maternal_last_name"] == "Núñez"
```

- [ ] **Step 16: Run the full suite**

Run: `pytest`
Expected: PASS. Any remaining `last_name` reference surfaces here.

- [ ] **Step 17: Rebuild the CSS**

```bash
npm run build:css
```

- [ ] **Step 18: Commit**

```bash
git add apps/ templates/ static/css/output.css
git commit -m "feat: split user surname into paterno and materno"
```

---

### Task 2: Add `sex` and `date_of_birth` to `UserProfile`

Model layer only. Both fields stay blank/null here — the CSV importer creates the
profile row before the employee has answered anything — and become required in
Task 3.

**Files:**
- Modify: `apps/accounts/models.py:176-229`
- Create: `apps/accounts/migrations/0008_*.py` (generated, then hand-edited)
- Test: `apps/accounts/tests/test_models.py`

**Interfaces:**
- Consumes: Task 1's `User` changes (unrelated, but the migration ordering depends on 0007).
- Produces: `UserProfile.Sex` (`TextChoices`, values `male`/`female`), `UserProfile.sex: str`, `UserProfile.date_of_birth: date | None`, `UserProfile.age -> int | None`, and the module constants `MIN_ACTIVATION_AGE = 15` / `MAX_ACTIVATION_AGE = 99`. Task 3's form imports both constants.

- [ ] **Step 1: Write the failing tests**

Append to `apps/accounts/tests/test_models.py`:

```python
def _years_ago(reference, years):
    """`reference` shifted back `years`.

    Feb 29 falls back to Feb 28 — earlier in the year, so a birthday built this
    way has always already passed. Without this the tests raise ValueError one
    day every four years.
    """
    try:
        return reference.replace(year=reference.year - years)
    except ValueError:
        return reference.replace(year=reference.year - years, month=2, day=28)


@pytest.mark.django_db
class TestUserProfileDemographics:
    def test_sex_labels_are_spanish(self):
        assert UserProfile.Sex.MALE.label == "Masculino"
        assert UserProfile.Sex.FEMALE.label == "Femenino"

    def test_sex_values_are_english(self):
        assert UserProfile.Sex.MALE.value == "male"
        assert UserProfile.Sex.FEMALE.value == "female"

    def test_age_is_none_without_a_birth_date(self, make_user_with_profile):
        user = make_user_with_profile(email="nodob@example.com")
        assert user.profile.age is None

    def test_age_counts_completed_years(self, make_user_with_profile):
        user = make_user_with_profile(email="age@example.com")
        user.profile.date_of_birth = _years_ago(timezone.localdate(), 30)
        assert user.profile.age == 30

    def test_age_does_not_count_a_birthday_still_to_come(
        self, make_user_with_profile
    ):
        """A birthday one day away is still a year off, so the count is 29."""
        user = make_user_with_profile(email="tomorrow@example.com")
        user.profile.date_of_birth = _years_ago(timezone.localdate(), 30) + timedelta(
            days=1
        )
        assert user.profile.age == 29

    def test_clean_rejects_a_future_birth_date(self, make_user_with_profile):
        user = make_user_with_profile(email="future@example.com")
        user.profile.date_of_birth = timezone.localdate() + timedelta(days=1)
        with pytest.raises(ValidationError) as excinfo:
            user.profile.clean()
        assert "date_of_birth" in excinfo.value.error_dict

    def test_clean_rejects_an_implausible_age(self, make_user_with_profile):
        user = make_user_with_profile(email="old@example.com")
        user.profile.date_of_birth = _years_ago(timezone.localdate(), 120)
        with pytest.raises(ValidationError) as excinfo:
            user.profile.clean()
        assert "date_of_birth" in excinfo.value.error_dict

    def test_clean_accepts_a_working_age(self, make_user_with_profile):
        user = make_user_with_profile(email="ok@example.com")
        user.profile.date_of_birth = _years_ago(timezone.localdate(), 40)
        user.profile.clean()  # does not raise
```

Add these imports at the top of the file if they are not already there:

```python
from datetime import timedelta

from django.core.exceptions import ValidationError
from django.utils import timezone

from apps.accounts.models import UserProfile
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `pytest apps/accounts/tests/test_models.py::TestUserProfileDemographics -v`
Expected: FAIL — `AttributeError: type object 'UserProfile' has no attribute 'Sex'`

- [ ] **Step 3: Add the module constants**

Near the top of `apps/accounts/models.py`, below `SPANISH_COLLATION`:

```python
# The plausible working-age window an employee's date of birth must fall in. 15
# is Mexico's legal minimum working age; the upper bound only exists to catch a
# mistyped year.
MIN_ACTIVATION_AGE = 15
MAX_ACTIVATION_AGE = 99
```

- [ ] **Step 4: Add the fields, the `age` property and the validation**

In `apps/accounts/models.py`, inside `class UserProfile`, add the choices above
the field declarations:

```python
    class Sex(models.TextChoices):
        MALE = "male", "Masculino"
        FEMALE = "female", "Femenino"
```

add the two fields after `position` (line 180):

```python
    # Blank/null here and required in `ProfileActivationForm`: the CSV importer
    # creates this row before the employee has answered anything. This is the
    # same split `area` uses.
    sex = models.CharField("sexo", max_length=6, choices=Sex, blank=True)
    date_of_birth = models.DateField("fecha de nacimiento", null=True, blank=True)
```

add the property after `__str__` (line 219):

```python
    @property
    def age(self):
        """Completed years as of today in `America/Mexico_City`, or None.

        Derived rather than stored so it cannot go stale. A submission's age is
        therefore read live, matching how `apps/nom035` already reads área.
        """
        if self.date_of_birth is None:
            return None
        today = timezone.localdate()
        birthday_passed = (today.month, today.day) >= (
            self.date_of_birth.month,
            self.date_of_birth.day,
        )
        return today.year - self.date_of_birth.year - (0 if birthday_passed else 1)
```

and extend `clean()` (lines 221-229) — keep the existing área/localidad loop and
add the date check before the raise:

```python
    def clean(self):
        super().clean()
        errors = {}
        for field in ("area", "location"):
            entry = getattr(self, field, None)
            if entry is not None and entry.company_id != self.company_id:
                errors[field] = "Debe pertenecer a la misma empresa que el colaborador."
        # A future date lands below the minimum, so one bound covers both.
        if self.date_of_birth is not None and not (
            MIN_ACTIVATION_AGE <= self.age <= MAX_ACTIVATION_AGE
        ):
            errors["date_of_birth"] = (
                f"La fecha de nacimiento debe corresponder a una edad entre "
                f"{MIN_ACTIVATION_AGE} y {MAX_ACTIVATION_AGE} años."
            )
        if errors:
            raise ValidationError(errors)
```

- [ ] **Step 5: Generate the migration**

```bash
python manage.py makemigrations accounts
```

- [ ] **Step 6: Add the re-activation step to that migration**

Open the generated `apps/accounts/migrations/0008_*.py` and add, above
`class Migration`:

```python
def deactivate_profiles(apps, schema_editor):
    """Send every employee back through activation.

    Sexo and fecha de nacimiento can only come from the employee, so there is
    nothing to backfill from.
    """
    UserProfile = apps.get_model("accounts", "UserProfile")
    UserProfile.objects.update(is_activated=False)
```

then append to the end of the `operations` list:

```python
        migrations.RunPython(deactivate_profiles, migrations.RunPython.noop),
```

- [ ] **Step 7: Apply the migration and run the tests**

```bash
python manage.py migrate
pytest apps/accounts/tests/test_models.py -v
```
Expected: PASS

- [ ] **Step 8: Commit**

```bash
git add apps/accounts/
git commit -m "feat: record employee sex and date of birth on the profile"
```

---

### Task 3: Collect the demographics at activation

**Files:**
- Modify: `apps/accounts/forms.py:194-320`
- Modify: `apps/accounts/views.py:294-299,326-331`
- Modify: `templates/accounts/profile_setup.html`
- Test: `apps/accounts/tests/test_forms.py`, `apps/accounts/tests/test_views.py`

**Interfaces:**
- Consumes: `UserProfile.Sex`, `MIN_ACTIVATION_AGE`, `MAX_ACTIVATION_AGE` from Task 2; `ProfileActivationForm` from Task 1.
- Produces: `ProfileActivationForm` fields `sex` (required) and `date_of_birth` (required via `clean_date_of_birth`).

- [ ] **Step 1: Write the failing form tests**

In `apps/accounts/tests/test_forms.py`, both existing helpers build a body that
is about to become incomplete — every test that asserts `form.is_valid()` fails
without the new fields. Add these four entries to **both** the `_form` helper of
`TestProfileActivationFormCleanReferenceCode` (line 48) and the `_data` helper of
`TestProfileActivationFormIdentityFields` (line 93):

```python
            "sex": "female",
            "date_of_birth_day": "15",
            "date_of_birth_month": "6",
            "date_of_birth_year": str(timezone.localdate().year - 30),
```

Then add a new class:

```python
@pytest.mark.django_db
class TestProfileActivationFormDemographics:
    @pytest.fixture
    def company_with_area(self, make_company, make_area):
        company = make_company()
        return company, make_area(company, name="Ventas")

    def _data(self, company, area, **overrides):
        today = timezone.localdate()
        data = {
            "reference_code": company.reference_code,
            "first_name": "Ana",
            "paternal_last_name": "López",
            "sex": "female",
            "date_of_birth_day": "15",
            "date_of_birth_month": "6",
            "date_of_birth_year": str(today.year - 30),
            "area": area.pk,
        }
        data.update(overrides)
        return data

    def test_valid_submission_passes(self, company_with_area):
        company, area = company_with_area
        form = ProfileActivationForm(data=self._data(company, area), company=company)
        assert form.is_valid(), form.errors
        assert form.cleaned_data["sex"] == "female"
        assert form.cleaned_data["date_of_birth"].year == timezone.localdate().year - 30

    def test_sex_is_required(self, company_with_area):
        company, area = company_with_area
        form = ProfileActivationForm(
            data=self._data(company, area, sex=""), company=company
        )
        assert not form.is_valid()
        assert "sex" in form.errors

    def test_sex_rejects_a_value_outside_the_choices(self, company_with_area):
        company, area = company_with_area
        form = ProfileActivationForm(
            data=self._data(company, area, sex="other"), company=company
        )
        assert not form.is_valid()
        assert "sex" in form.errors

    def test_date_of_birth_is_required(self, company_with_area):
        company, area = company_with_area
        form = ProfileActivationForm(
            data=self._data(
                company,
                area,
                date_of_birth_day="",
                date_of_birth_month="",
                date_of_birth_year="",
            ),
            company=company,
        )
        assert not form.is_valid()
        assert "date_of_birth" in form.errors

    def test_date_of_birth_rejects_an_age_below_the_minimum(self, company_with_area):
        company, area = company_with_area
        today = timezone.localdate()
        form = ProfileActivationForm(
            data=self._data(company, area, date_of_birth_year=str(today.year - 5)),
            company=company,
        )
        assert not form.is_valid()
        assert "date_of_birth" in form.errors

    def test_date_of_birth_dropdowns_offer_only_working_ages(self, company_with_area):
        """The widget must not offer a year the validator would reject."""
        company, _ = company_with_area
        form = ProfileActivationForm(company=company)
        years = form.fields["date_of_birth"].widget.years
        today = timezone.localdate()
        assert max(years) == today.year - MIN_ACTIVATION_AGE
        assert min(years) == today.year - MAX_ACTIVATION_AGE
```

Add the imports:

```python
from django.utils import timezone

from apps.accounts.models import MAX_ACTIVATION_AGE, MIN_ACTIVATION_AGE
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `pytest apps/accounts/tests/test_forms.py::TestProfileActivationFormDemographics -v`
Expected: FAIL — `KeyError: 'sex'`

- [ ] **Step 3: Add the widget class constant**

In `apps/accounts/forms.py`, beside `_TEXT_CLASSES` and `_SELECT_CLASSES` (lines 194-202):

```python
_DATE_SELECT_CLASSES = (
    "block w-full rounded-lg border border-gray-300 bg-white px-3 py-3 text-sm "
    "focus:border-indigo-500 focus:ring-indigo-500"
)
```

- [ ] **Step 4: Add the two form fields**

In `ProfileActivationForm`, after `position` and before `area`:

```python
    sex = forms.ChoiceField(
        label="Sexo",
        choices=[("", "Selecciona tu sexo"), *UserProfile.Sex.choices],
        error_messages={
            "required": "Selecciona tu sexo.",
            "invalid_choice": "Selecciona una opción válida.",
        },
        widget=forms.Select(attrs={"class": _SELECT_CLASSES}),
    )
    # `required=False` with a presence check in `clean_date_of_birth`, not
    # `required=True`: `SelectDateWidget` only renders the "Día/Mes/Año"
    # placeholder options when the field is optional. Left required, it would
    # pre-select the first year in the list, so skipping the question would
    # silently record a wrong birth date instead of raising an error.
    date_of_birth = forms.DateField(
        label="Fecha de nacimiento",
        required=False,
        error_messages={"invalid": "Escribe una fecha de nacimiento válida."},
    )
```

Add `UserProfile` to the model imports at the top of `forms.py`:

```python
from apps.accounts.models import (
    CompanyArea,
    CompanyLocation,
    MAX_ACTIVATION_AGE,
    MIN_ACTIVATION_AGE,
    User,
    UserProfile,
    normalize_setup_access_code,
)
```

- [ ] **Step 5: Build the year range in `__init__`**

In `ProfileActivationForm.__init__`, after `self.company = company`:

```python
        # Built here rather than at import time so the offered years do not go
        # stale in a long-running process, and so the dropdown can never offer a
        # year `clean_date_of_birth` would reject.
        today = timezone.localdate()
        self.fields["date_of_birth"].widget = forms.SelectDateWidget(
            years=range(
                today.year - MIN_ACTIVATION_AGE, today.year - MAX_ACTIVATION_AGE - 1, -1
            ),
            empty_label=("Año", "Mes", "Día"),
            attrs={"class": _DATE_SELECT_CLASSES},
        )
```

Add `from django.utils import timezone` to the imports at the top of `forms.py`.

- [ ] **Step 6: Add the date validation**

Add to `ProfileActivationForm`, beside `clean_reference_code`:

```python
    def clean_date_of_birth(self):
        """`UserProfile.clean()` guards the admin and the shell; this guards the
        employee, who needs a Spanish message rather than a stack trace. The
        form is a plain `Form`, so the model's `clean()` never runs on POST."""
        date_of_birth = self.cleaned_data.get("date_of_birth")
        if date_of_birth is None:
            raise forms.ValidationError("Escribe tu fecha de nacimiento.")

        today = timezone.localdate()
        birthday_passed = (today.month, today.day) >= (
            date_of_birth.month,
            date_of_birth.day,
        )
        age = today.year - date_of_birth.year - (0 if birthday_passed else 1)
        if not MIN_ACTIVATION_AGE <= age <= MAX_ACTIVATION_AGE:
            raise forms.ValidationError(
                f"La fecha de nacimiento debe corresponder a una edad entre "
                f"{MIN_ACTIVATION_AGE} y {MAX_ACTIVATION_AGE} años."
            )
        return date_of_birth
```

- [ ] **Step 7: Run the form tests to verify they pass**

Run: `pytest apps/accounts/tests/test_forms.py -v`
Expected: PASS

- [ ] **Step 8: Write the failing view test**

In `apps/accounts/tests/test_views.py`, extend `_activation_post` (line 555) so
every activation POST carries the new fields:

```python
def _activation_post(company, **overrides):
    """A complete activation body. Every field but the maternal surname is
    required, so every POST carries them."""
    today = timezone.localdate()
    payload = {
        "reference_code": company.reference_code,
        "first_name": "Ana",
        "paternal_last_name": "López",
        "sex": "female",
        "date_of_birth_day": "15",
        "date_of_birth_month": "6",
        "date_of_birth_year": str(today.year - 30),
    }
    payload.update(overrides)
    return payload
```

then add to `TestSetupProfileView`:

```python
    def test_activation_saves_demographics(
        self, client, make_user_with_profile, make_company, make_area
    ):
        company = make_company()
        area = make_area(company, name="Ventas")
        user = make_user_with_profile(
            email="demog@example.com", company=company, is_activated=False
        )
        client.force_login(user)

        client.post(SETUP_PROFILE_URL, _activation_post(company, area=area.pk))

        user.profile.refresh_from_db()
        assert user.profile.is_activated is True
        assert user.profile.sex == "female"
        # The stored date, not the derived age: a June birthday reads as 29 for
        # half the year, which would make this test pass only after June 15.
        assert user.profile.date_of_birth == date(timezone.localdate().year - 30, 6, 15)

    def test_missing_sex_blocks_activation(
        self, client, make_user_with_profile, make_company, make_area
    ):
        company = make_company()
        area = make_area(company, name="Ventas")
        user = make_user_with_profile(
            email="nosex@example.com", company=company, is_activated=False
        )
        client.force_login(user)

        response = client.post(
            SETUP_PROFILE_URL, _activation_post(company, area=area.pk, sex="")
        )

        user.profile.refresh_from_db()
        assert user.profile.is_activated is False
        assert "sex" in response.context["form"].errors

    def test_form_prefills_demographics_already_on_record(
        self, client, make_user_with_profile, make_company, make_area
    ):
        company = make_company()
        make_area(company, name="Ventas")
        user = make_user_with_profile(
            email="prefilldemog@example.com", company=company, is_activated=False
        )
        user.profile.sex = "male"
        user.profile.date_of_birth = date(1990, 6, 15)
        user.profile.save(update_fields=["sex", "date_of_birth"])
        client.force_login(user)

        form = client.get(SETUP_PROFILE_URL).context["form"]

        assert form.initial["sex"] == "male"
        assert form.initial["date_of_birth"] == date(1990, 6, 15)
```

Add `from datetime import date` and `from django.utils import timezone` to the imports.

- [ ] **Step 9: Run it to verify it fails**

Run: `pytest apps/accounts/tests/test_views.py::TestSetupProfileView -v`
Expected: FAIL — `assert '' == 'female'`

- [ ] **Step 10: Update the view**

In `apps/accounts/views.py`, extend the GET prefill:

```python
        initial = {
            "first_name": request.user.first_name,
            "paternal_last_name": request.user.paternal_last_name,
            "maternal_last_name": request.user.maternal_last_name,
            "position": profile.position,
            "sex": profile.sex,
            "date_of_birth": profile.date_of_birth,
        }
```

and the profile write inside the transaction:

```python
        profile.position = form.cleaned_data["position"]
        profile.sex = form.cleaned_data["sex"]
        profile.date_of_birth = form.cleaned_data["date_of_birth"]
        profile.area = form.cleaned_data["area"]
        profile.location = form.cleaned_data.get("location") or form.implicit_location
        profile.is_activated = True
        profile.save(
            update_fields=[
                "position",
                "sex",
                "date_of_birth",
                "area",
                "location",
                "is_activated",
            ]
        )
```

- [ ] **Step 11: Run the view tests to verify they pass**

Run: `pytest apps/accounts/tests/test_views.py -v`
Expected: PASS

- [ ] **Step 12: Add the fields to the template**

In `templates/accounts/profile_setup.html`, insert after the cargo block (which
ends at line 75) and before the área block:

```html
      <div class="mb-6">
        <label for="{{ form.sex.id_for_label }}" class="block text-sm font-medium text-gray-700 mb-1">
          Sexo
        </label>
        {{ form.sex }}
        {% if form.sex.errors %}
          <p class="mt-1 text-xs text-red-600">{{ form.sex.errors.0 }}</p>
        {% endif %}
      </div>

      <div class="mb-6">
        <label class="block text-sm font-medium text-gray-700 mb-1">
          Fecha de nacimiento
        </label>
        <div class="grid grid-cols-3 gap-3">
          {{ form.date_of_birth }}
        </div>
        {% if form.date_of_birth.errors %}
          <p class="mt-1 text-xs text-red-600">{{ form.date_of_birth.errors.0 }}</p>
        {% endif %}
      </div>
```

The label has no `for` because `SelectDateWidget` renders three separate selects.

- [ ] **Step 13: Assert the rendered contract**

Add to `TestSetupProfileView` in `apps/accounts/tests/test_views.py`:

```python
    def test_activation_page_renders_the_demographic_inputs(
        self, client, make_user_with_profile, make_company, make_area
    ):
        """There is no JS test runner, so the rendered element names are the only
        automated check that the template and the form still agree."""
        company = make_company()
        make_area(company, name="Ventas")
        user = make_user_with_profile(
            email="render@example.com", company=company, is_activated=False
        )
        client.force_login(user)

        html = client.get(SETUP_PROFILE_URL).content.decode()

        assert 'name="sex"' in html
        assert 'name="date_of_birth_day"' in html
        assert 'name="date_of_birth_month"' in html
        assert 'name="date_of_birth_year"' in html
        assert 'name="paternal_last_name"' in html
        assert 'name="maternal_last_name"' in html
```

- [ ] **Step 14: Run the full suite**

Run: `pytest`
Expected: PASS

- [ ] **Step 15: Rebuild the CSS**

```bash
npm run build:css
```

`grid-cols-3` is new to this template — without the rebuild the three dropdowns stack.

- [ ] **Step 16: Commit**

```bash
git add apps/ templates/ static/css/output.css
git commit -m "feat: collect sexo and fecha de nacimiento at activation"
```

---

### Task 4: Surface the demographics in the admin

**Files:**
- Modify: `apps/accounts/admin.py:191-201`
- Test: `apps/accounts/tests/test_admin.py`

**Interfaces:**
- Consumes: `UserProfile.sex`, `UserProfile.date_of_birth` from Task 2.
- Produces: nothing later tasks depend on.

- [ ] **Step 1: Write the failing test**

Add to `apps/accounts/tests/test_admin.py`:

```python
@pytest.mark.django_db
def test_userprofile_admin_lists_demographics():
    from django.contrib import admin as django_admin

    from apps.accounts.models import UserProfile

    model_admin = django_admin.site._registry[UserProfile]
    assert "sex" in model_admin.list_display
    assert "date_of_birth" in model_admin.list_display
    assert "sex" in model_admin.list_filter
```

- [ ] **Step 2: Run it to verify it fails**

Run: `pytest apps/accounts/tests/test_admin.py::test_userprofile_admin_lists_demographics -v`
Expected: FAIL — `assert 'sex' in ('user', 'position', 'area', 'location', 'company', 'is_activated')`

- [ ] **Step 3: Update `UserProfileAdmin`**

In `apps/accounts/admin.py`, replace lines 191-201:

```python
    list_display = (
        "user",
        "position",
        "sex",
        "date_of_birth",
        "area",
        "location",
        "company",
        "is_activated",
    )
    # No `area` filter: CompanyArea has no registered admin, so the sidebar would
    # enumerate every client's área names. Filter by company, search by area__name.
    list_filter = ("is_activated", "sex", "company")
```

- [ ] **Step 4: Run the admin tests to verify they pass**

Run: `pytest apps/accounts/tests/ -v`
Expected: PASS — including `test_django_system_checks_pass` from Task 1.

- [ ] **Step 5: Commit**

```bash
git add apps/accounts/admin.py apps/accounts/tests/test_admin.py
git commit -m "feat: show sexo and fecha de nacimiento in the profile admin"
```

---

### Task 5: Rewrite the documentation

Present tense, describing the implementation as if it were always this way. No
migration commentary anywhere outside `docs/adr/`.

**Files:**
- Modify: `docs/platform/auth-and-onboarding.md`
- Modify: `docs/platform/database.md:53`, `docs/platform/csv-user-import.md:108`, `docs/platform/localization.md:253`
- Modify: `apps/accounts/CLAUDE.md`
- Delete: `docs/platform/wip/auth-and-onboarding-change.md`, `docs/platform/wip/auth-and-onboarding-tasks.md`

**Interfaces:**
- Consumes: the finished implementation from Tasks 1-4.
- Produces: nothing.

- [ ] **Step 1: Rewrite `auth-and-onboarding.md`**

Work through the eight locations the change brief lists under "What this makes
wrong":

- `### Profile activation` — the form-fields bullet becomes "company reference
  code, nombre(s), apellido paterno, apellido materno, cargo, sexo, fecha de
  nacimiento, área picker, and — only when the company has more than one active
  localidad — a localidad picker". The requirements bullet becomes "Nombre(s),
  apellido paterno, sexo and fecha de nacimiento are required; apellido materno
  and cargo are optional and saved as empty when blank."
- Add a bullet: "Fecha de nacimiento is entered as three dropdowns and must fall
  in a 15-to-99-year working-age window; the dropdown offers no year outside it."
- The final bullet's field list becomes `User.first_name`/`paternal_last_name`/
  `maternal_last_name` and `UserProfile.position`/`sex`/`date_of_birth`/`area`/
  `location`/`is_activated`.
- `## Inputs` — "Nombre(s), apellido paterno, apellido materno opcional, y cargo
  opcional." plus "Sexo y fecha de nacimiento."
- `## Outputs` — both the `User` and `UserProfile` lines.
- `## API / routes / commands` — the `/cuentas/completar-perfil/` POST row's input
  column becomes `reference_code`, `first_name`, `paternal_last_name`, optional
  `maternal_last_name`, optional `position`, `sex`, `date_of_birth`, `area`,
  optional `location`.
- `## Data model impact` — add `User.paternal_last_name`, `User.maternal_last_name`,
  `UserProfile.sex`, `UserProfile.date_of_birth` to the Fields list, and replace
  the Migrations line with the two migrations added here.
- `## Invariants`, `## Acceptance criteria`, `## Test mapping` — update every
  reference to the old field set, and map the new tests from Tasks 1-3.
- `## Linked ADRs` — add ADR-0005.

- [ ] **Step 2: Update the cross-cutting docs**

- `docs/platform/database.md:53` — the row becomes
  `` `first_name` / `paternal_last_name` / `maternal_last_name` `` with the same
  collation note; add `sex` and `date_of_birth` to the `UserProfile` table below it.
- `docs/platform/database.md:360` — add the two surname columns to the list of
  columns declaring `db_collation`.
- `docs/platform/csv-user-import.md:108` — the sentence becomes
  "`User.first_name`, `User.paternal_last_name`, `User.maternal_last_name`,
  `UserProfile.position`, `UserProfile.sex`, `UserProfile.date_of_birth`,
  `UserProfile.area`, and `UserProfile.location` are left at their blank/null
  defaults."
- `docs/platform/localization.md:253` — the decision already explains that
  Django's `es_MX` renders `last name` as the singular `"apellido"`, "which is
  wrong for Mexican usage (paterno + materno)". Rewrite it to describe the two
  fields that now exist, and add the `UserProfile.Sex` labels as a decision:
  Spanish labels, English values.

- [ ] **Step 3: Update `apps/accounts/CLAUDE.md`**

Three places: the `User` bullet under Models, the `UserProfile` bullet (add sexo,
fecha de nacimiento, the derived `age`, and the working-age validation), and the
`db_collation` gotcha list under Conventions. Also note in the `views.py` bullet
that activation collects the demographics.

- [ ] **Step 4: Verify no stale references remain**

```bash
grep -rn "last_name" --include=*.py --include=*.html --include=*.md . \
  | grep -v "/migrations/\|node_modules\|\.venv\|paternal_last_name\|maternal_last_name\|docs/adr/"
```
Expected: no output.

- [ ] **Step 5: Run the full suite one last time**

```bash
pytest
ruff format . && ruff check .
```
Expected: PASS, no lint errors.

- [ ] **Step 6: Commit**

```bash
git add docs/ apps/accounts/CLAUDE.md
git commit -m "docs: describe employee demographics at activation"
```

---

## After the review, before the merge

The change brief and this plan are scaffolding for this branch, and the reviewer
needs both while reviewing. Delete them once the PR is approved, so `main` shows
`docs/platform/wip/` holding nothing but its README:

```bash
git rm docs/platform/wip/auth-and-onboarding-change.md \
       docs/platform/wip/auth-and-onboarding-tasks.md
git commit -m "chore: clear the employee-demographics scaffolding"
```

---

## Reviewer's browser check-list

There is no JS test runner, so these need human eyes at `/cuentas/completar-perfil/`
and `/tablero-empresa/empleados/`:

1. The activation form shows Apellido paterno and Apellido materno as separate
   inputs, with "Opcional" in the materno placeholder.
2. Fecha de nacimiento renders as three dropdowns side by side — not stacked —
   starting on "Día / Mes / Año" rather than pre-selecting a year.
3. Month names are Spanish (enero, febrero, …).
4. The year dropdown's newest option is 15 years ago and its oldest is 99.
5. Sexo offers Masculino and Femenino, starting on "Selecciona tu sexo".
6. Submitting with sexo or fecha de nacimiento blank shows a Spanish error under
   the right field and does not activate the account.
7. The Empleados list is ordered by apellido paterno, and each card shows the
   full three-part name.
8. The employee detail page's avatar shows the initials of nombre + apellido
   paterno.
