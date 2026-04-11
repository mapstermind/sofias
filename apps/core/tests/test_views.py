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
        assert "ingresar" in response["Location"]

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
        assert "ingresar" in response["Location"]

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

    def test_employee_group_redirects_to_survey_list(self, client, make_user, bootstrap_groups):
        user = make_user()
        user.groups.add(bootstrap_groups["Employees"])
        client.force_login(user)
        response = client.get(self.URL)
        assert response.status_code == 302
        assert response["Location"].endswith("/encuestas/")


# ── EmployeeSurveyListView ────────────────────────────────────────────────────


class TestEmployeeSurveyListView:
    URL = "/encuestas/"

    def _make_employee(self, make_user, bootstrap_groups, company=None):
        from apps.accounts.models import UserProfile

        user = make_user()
        user.groups.add(bootstrap_groups["Employees"])
        if company is not None:
            profile, _ = UserProfile.objects.get_or_create(user=user)
            profile.company = company
            profile.save()
        return user

    def test_unauthenticated_redirects_to_login(self, client):
        response = client.get(self.URL)
        assert response.status_code == 302
        assert "ingresar" in response["Location"]

    def test_non_employee_returns_403(self, client, make_user):
        client.force_login(make_user())
        response = client.get(self.URL)
        assert response.status_code == 403

    def test_employee_without_profile_redirects_to_setup(self, client, make_user, bootstrap_groups):
        user = make_user()
        user.groups.add(bootstrap_groups["Employees"])
        client.force_login(user)
        response = client.get(self.URL)
        assert response.status_code == 302
        assert "perfil" in response["Location"]

    def test_employee_without_company_redirects_to_setup(self, client, make_user, bootstrap_groups):
        from apps.accounts.models import UserProfile

        user = make_user()
        user.groups.add(bootstrap_groups["Employees"])
        UserProfile.objects.create(user=user, company=None)
        client.force_login(user)
        response = client.get(self.URL)
        assert response.status_code == 302
        assert "perfil" in response["Location"]

    def test_employee_with_company_returns_200(self, client, make_user, make_company, bootstrap_groups):
        company = make_company()
        user = self._make_employee(make_user, bootstrap_groups, company=company)
        client.force_login(user)
        response = client.get(self.URL)
        assert response.status_code == 200

    def test_only_company_assignments_appear(
        self, client, make_user, make_company, bootstrap_groups, survey_version
    ):
        from apps.surveys.models import SurveyAssignment

        company = make_company()
        other_company = make_company(name="Other Corp", legal_name="Other Corp SA de CV")
        user = self._make_employee(make_user, bootstrap_groups, company=company)

        own = SurveyAssignment.objects.create(company=company, version=survey_version)
        SurveyAssignment.objects.create(company=other_company, version=survey_version)

        client.force_login(user)
        response = client.get(self.URL)

        ids = [item["assignment"].pk for item in response.context["assignment_data"]]
        assert own.pk in ids
        assert len(ids) == 1

    def test_completed_flag_true_when_user_has_completed_submission(
        self, client, make_user, make_company, bootstrap_groups, survey_version
    ):
        from apps.responses.models import SurveySubmission
        from apps.surveys.models import SurveyAssignment

        company = make_company()
        user = self._make_employee(make_user, bootstrap_groups, company=company)
        assignment = SurveyAssignment.objects.create(company=company, version=survey_version)
        SurveySubmission.objects.create(
            assignment=assignment, user=user, status=SurveySubmission.Status.COMPLETED
        )

        client.force_login(user)
        response = client.get(self.URL)

        item = next(i for i in response.context["assignment_data"] if i["assignment"].pk == assignment.pk)
        assert item["completed"] is True

    def test_completed_flag_false_when_no_submission(
        self, client, make_user, make_company, bootstrap_groups, survey_version
    ):
        from apps.surveys.models import SurveyAssignment

        company = make_company()
        user = self._make_employee(make_user, bootstrap_groups, company=company)
        assignment = SurveyAssignment.objects.create(company=company, version=survey_version)

        client.force_login(user)
        response = client.get(self.URL)

        item = next(i for i in response.context["assignment_data"] if i["assignment"].pk == assignment.pk)
        assert item["completed"] is False

    def test_completed_flag_false_for_in_progress_submission(
        self, client, make_user, make_company, bootstrap_groups, survey_version
    ):
        from apps.responses.models import SurveySubmission
        from apps.surveys.models import SurveyAssignment

        company = make_company()
        user = self._make_employee(make_user, bootstrap_groups, company=company)
        assignment = SurveyAssignment.objects.create(company=company, version=survey_version)
        SurveySubmission.objects.create(
            assignment=assignment, user=user, status=SurveySubmission.Status.IN_PROGRESS
        )

        client.force_login(user)
        response = client.get(self.URL)

        item = next(i for i in response.context["assignment_data"] if i["assignment"].pk == assignment.pk)
        assert item["completed"] is False
