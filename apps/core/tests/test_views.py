import pytest
from django.contrib.auth.models import Permission

pytestmark = pytest.mark.django_db


def _give_perm(user, codename):
    """Add a custom permission to a user and return a fresh instance (clears perm cache)."""
    from apps.accounts.models import User

    perm = Permission.objects.get(codename=codename)
    user.user_permissions.add(perm)
    return User.objects.get(pk=user.pk)


# ── CompanyListView ───────────────────────────────────────────────────────────


class TestCompanyListView:
    URL = "/empresas/"

    def test_unauthenticated_redirects_to_login(self, client):
        response = client.get(self.URL)
        assert response.status_code == 302
        assert "login" in response["Location"]

    def test_no_permission_returns_403(self, client, make_user):
        client.force_login(make_user())
        response = client.get(self.URL)
        assert response.status_code == 403

    def test_can_manage_surveys_returns_200(self, client, make_user):
        user = _give_perm(make_user(), "can_manage_surveys")
        client.force_login(user)
        response = client.get(self.URL)
        assert response.status_code == 200

    def test_member_count_annotation(self, client, make_user, make_company, make_user_with_profile):
        user = _give_perm(make_user(), "can_manage_surveys")
        company = make_company()
        make_user_with_profile(email="emp1@example.com", company=company)
        make_user_with_profile(email="emp2@example.com", company=company)

        client.force_login(user)
        response = client.get(self.URL)

        companies = list(response.context["companies"])
        match = next((c for c in companies if c.pk == company.pk), None)
        assert match is not None
        assert match.member_count == 2


# ── CompanyDashboardView ──────────────────────────────────────────────────────


class TestCompanyDashboardView:
    URL = "/tablero-empresa/"

    def test_unauthenticated_redirects_to_login(self, client):
        response = client.get(self.URL)
        assert response.status_code == 302
        assert "login" in response["Location"]

    def test_no_permission_returns_403(self, client, make_user):
        client.force_login(make_user())
        response = client.get(self.URL)
        assert response.status_code == 403

    def test_can_view_dashboard_returns_200(self, client, make_user, make_company, make_user_with_profile):
        company = make_company()
        user = _give_perm(make_user(), "can_view_dashboard")
        # Give the user a profile linked to the company so the view can find their company
        from apps.accounts.models import UserProfile

        profile, _ = UserProfile.objects.get_or_create(user=user)
        profile.company = company
        profile.position = "Analyst"
        profile.save()

        client.force_login(user)
        response = client.get(self.URL)
        assert response.status_code == 200


# ── HomeView ──────────────────────────────────────────────────────────────────


class TestHomeViewRouting:
    URL = "/"

    def test_unauthenticated_redirects(self, client):
        response = client.get(self.URL)
        assert response.status_code == 302

    def test_admin_group_redirects_to_company_list(self, client, make_user, bootstrap_groups):
        user = make_user()
        user.groups.add(bootstrap_groups["Admins"])
        client.force_login(user)
        response = client.get(self.URL)
        assert response.status_code == 302
        assert response["Location"].endswith("/empresas/")
