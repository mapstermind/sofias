import pytest
from django.forms.models import inlineformset_factory
from django.urls import reverse
from django.utils import timezone

from apps.accounts.admin import CompanyCatalogInlineFormSet
from apps.accounts.models import (
    Company,
    CompanyArea,
    CompanyLocation,
    SetupAccessCode,
    UserProfile,
)

pytestmark = pytest.mark.django_db

# Both catalog inlines share one formset class, so every guard is exercised
# against both models — otherwise dropping `formset=` from one inline would
# silently pass.
CATALOGS = [
    pytest.param(CompanyArea, "areas", "make_area", id="area"),
    pytest.param(CompanyLocation, "locations", "make_location", id="location"),
]


def _catalog_formset(model, prefix, company, data):
    """Build the same formset class the Company admin inlines use."""
    FormSet = inlineformset_factory(
        Company,
        model,
        formset=CompanyCatalogInlineFormSet,
        fields=("name", "is_active"),
        extra=0,
        can_delete=True,
    )
    return FormSet(data, instance=company, prefix=prefix)


def _management_form(prefix, total, initial=0):
    return {
        f"{prefix}-TOTAL_FORMS": str(total),
        f"{prefix}-INITIAL_FORMS": str(initial),
        f"{prefix}-MIN_NUM_FORMS": "0",
        f"{prefix}-MAX_NUM_FORMS": "1000",
    }


class TestCompanyCatalogAdmin:
    def test_company_change_page_renders_both_inlines(self, staff_client, make_company):
        company = make_company()
        response = staff_client.get(
            reverse("admin:accounts_company_change", args=[company.pk])
        )
        assert response.status_code == 200
        body = response.content.decode()
        assert "areas-TOTAL_FORMS" in body
        assert "locations-TOTAL_FORMS" in body

    @pytest.mark.parametrize("model,prefix,factory_name", CATALOGS)
    def test_deleting_an_entry_with_members_is_blocked(
        self, request, make_company, make_user_with_profile, model, prefix, factory_name
    ):
        company = make_company()
        entry = request.getfixturevalue(factory_name)(company, name="Ventas")
        field = "area" if model is CompanyArea else "location"
        make_user_with_profile(
            email=f"member-{prefix}@x.mx", company=company, **{field: entry}
        )

        formset = _catalog_formset(
            model,
            prefix,
            company,
            {
                **_management_form(prefix, total=1, initial=1),
                f"{prefix}-0-id": str(entry.pk),
                f"{prefix}-0-company": str(company.pk),
                f"{prefix}-0-name": "Ventas",
                f"{prefix}-0-is_active": "on",
                f"{prefix}-0-DELETE": "on",
            },
        )

        assert not formset.is_valid()
        assert "No puedes eliminar" in str(formset.non_form_errors())
        assert model.objects.filter(pk=entry.pk).exists()

    @pytest.mark.parametrize("model,prefix,factory_name", CATALOGS)
    def test_deleting_an_unused_entry_actually_deletes_it(
        self, request, make_company, model, prefix, factory_name
    ):
        company = make_company()
        entry = request.getfixturevalue(factory_name)(company, name="Sin gente")

        formset = _catalog_formset(
            model,
            prefix,
            company,
            {
                **_management_form(prefix, total=1, initial=1),
                f"{prefix}-0-id": str(entry.pk),
                f"{prefix}-0-company": str(company.pk),
                f"{prefix}-0-name": "Sin gente",
                f"{prefix}-0-is_active": "on",
                f"{prefix}-0-DELETE": "on",
            },
        )

        assert formset.is_valid(), formset.errors
        formset.save()
        assert not model.objects.filter(pk=entry.pk).exists()

    @pytest.mark.parametrize("model,prefix,factory_name", CATALOGS)
    def test_two_new_rows_differing_only_in_case_are_rejected(
        self, request, make_company, model, prefix, factory_name
    ):
        """Guards the DB constraint: validate_unique can't see intra-formset dupes."""
        company = make_company()

        formset = _catalog_formset(
            model,
            prefix,
            company,
            {
                **_management_form(prefix, total=2),
                f"{prefix}-0-name": "Ventas",
                f"{prefix}-0-is_active": "on",
                f"{prefix}-1-name": "ventas",
                f"{prefix}-1-is_active": "on",
            },
        )

        assert not formset.is_valid()
        assert "ya está en la lista" in str(formset.errors)

    @pytest.mark.parametrize("model,prefix,factory_name", CATALOGS)
    def test_two_new_rows_differing_only_in_accents_are_rejected(
        self, request, make_company, model, prefix, factory_name
    ):
        company = make_company()

        formset = _catalog_formset(
            model,
            prefix,
            company,
            {
                **_management_form(prefix, total=2),
                f"{prefix}-0-name": "Dirección",
                f"{prefix}-0-is_active": "on",
                f"{prefix}-1-name": "Direccion",
                f"{prefix}-1-is_active": "on",
            },
        )

        assert not formset.is_valid()
        assert "ya está en la lista" in str(formset.errors)

    @pytest.mark.parametrize("model,prefix,factory_name", CATALOGS)
    def test_two_new_rows_differing_only_in_spacing_are_rejected(
        self, request, make_company, model, prefix, factory_name
    ):
        company = make_company()

        formset = _catalog_formset(
            model,
            prefix,
            company,
            {
                **_management_form(prefix, total=2),
                f"{prefix}-0-name": "Recursos Humanos",
                f"{prefix}-0-is_active": "on",
                f"{prefix}-1-name": "Recursos  Humanos",
                f"{prefix}-1-is_active": "on",
            },
        )

        assert not formset.is_valid()
        assert "ya está en la lista" in str(formset.errors)

    @pytest.mark.parametrize("model,prefix,factory_name", CATALOGS)
    def test_names_differing_by_enye_are_both_accepted(
        self, request, make_company, model, prefix, factory_name
    ):
        company = make_company()

        formset = _catalog_formset(
            model,
            prefix,
            company,
            {
                **_management_form(prefix, total=2),
                f"{prefix}-0-name": "Cañada",
                f"{prefix}-0-is_active": "on",
                f"{prefix}-1-name": "Canada",
                f"{prefix}-1-is_active": "on",
            },
        )

        assert formset.is_valid(), formset.errors
        formset.save()
        assert model.objects.filter(company=company).count() == 2

    @pytest.mark.parametrize("model,prefix,factory_name", CATALOGS)
    def test_new_row_colliding_with_an_existing_one_is_rejected(
        self, request, make_company, model, prefix, factory_name
    ):
        """The formset is the ONLY guard here.

        `company` is not a form field, so it lands in the model's validation
        exclusions and `validate_constraints` skips the Lower(name) constraint —
        without this check the save reaches the DB and raises IntegrityError 500.
        """
        company = make_company()
        existing = request.getfixturevalue(factory_name)(company, name="Ventas")

        formset = _catalog_formset(
            model,
            prefix,
            company,
            {
                **_management_form(prefix, total=2, initial=1),
                f"{prefix}-0-id": str(existing.pk),
                f"{prefix}-0-company": str(company.pk),
                f"{prefix}-0-name": "Ventas",
                f"{prefix}-0-is_active": "on",
                f"{prefix}-1-name": "ventas",
                f"{prefix}-1-is_active": "on",
            },
        )

        assert not formset.is_valid()
        assert "ya está en la lista" in str(formset.errors)
        assert model.objects.filter(company=company).count() == 1

    def test_userprofile_form_does_not_offer_another_companys_area(
        self, staff_client, make_company, make_area, make_user_with_profile
    ):
        company = make_company(name="Cliente A")
        other = make_company(name="Cliente B")
        make_area(company, name="Propia")
        make_area(other, name="AreaAjenaDeOtroCliente")
        user = make_user_with_profile(email="scoped@x.mx", company=company)

        response = staff_client.get(
            reverse("admin:accounts_userprofile_change", args=[user.profile.pk])
        )

        assert response.status_code == 200
        body = response.content.decode()
        assert "Propia" in body
        assert "AreaAjenaDeOtroCliente" not in body

    def test_add_form_rejects_area_from_another_company(
        self, staff_client, make_company, make_area, make_user
    ):
        """The add form deliberately lists every company's áreas, so
        UserProfile.clean() is the only thing standing between the operator and a
        cross-company assignment."""
        company = make_company(name="Cliente A")
        other = make_company(name="Cliente B")
        foreign = make_area(other, name="Ajena")
        user = make_user(email="addform@x.mx")

        response = staff_client.post(
            reverse("admin:accounts_userprofile_add"),
            {
                "user": str(user.pk),
                "position": "Analista",
                "company": str(company.pk),
                "area": str(foreign.pk),
                "location": "",
            },
        )

        assert response.status_code == 200
        assert "Debe pertenecer a la misma empresa" in response.content.decode()
        assert not UserProfile.objects.filter(user=user).exists()

    def test_dropdowns_are_company_qualified_when_company_is_unknown(
        self, staff_client, make_company, make_area, make_user_with_profile
    ):
        """A profile whose company was deleted (SET_NULL) has no scope to filter
        by, so options must at least be labelled with their company."""
        company = make_company(name="Cliente A")
        make_area(company, name="Operaciones")
        user = make_user_with_profile(email="orphan@x.mx", company=company)
        company.delete()

        user.profile.refresh_from_db()
        assert user.profile.company is None

        response = staff_client.get(
            reverse("admin:accounts_userprofile_change", args=[user.profile.pk])
        )

        assert response.status_code == 200


def test_setup_access_code_admin_requires_staff(client, make_user):
    user = make_user(email="regular-admin-view@example.com", password="Pass12345!")
    client.force_login(user)

    response = client.get(reverse("admin:accounts_setupaccesscode_changelist"))

    assert response.status_code == 302


def test_setup_access_code_admin_shows_unused_code(client, make_user):
    staff = make_user(
        email="staff@example.com",
        password="Pass12345!",
        is_staff=True,
        is_superuser=True,
    )
    fallback_user = make_user(email="fallback-admin@example.com")
    SetupAccessCode.objects.create(user=fallback_user, code="123456789")
    client.force_login(staff)

    response = client.get(reverse("admin:accounts_setupaccesscode_changelist"))

    assert response.status_code == 200
    assert b"123456789" in response.content


def test_setup_access_code_admin_does_not_show_used_code_value(client, make_user):
    staff = make_user(
        email="staff-used@example.com",
        password="Pass12345!",
        is_staff=True,
        is_superuser=True,
    )
    fallback_user = make_user(email="used-admin@example.com")
    SetupAccessCode.objects.create(
        user=fallback_user,
        code=None,
        used_at=timezone.now(),
    )
    client.force_login(staff)

    response = client.get(reverse("admin:accounts_setupaccesscode_changelist"))

    assert response.status_code == 200
    assert b"123456789" not in response.content


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
