import math

import pytest
from django.contrib.auth.models import Permission

from apps.accounts.models import User, UserProfile
from apps.core.views import _representative_minimum
from apps.responses.models import Answer, SurveySubmission
from apps.surveys.models import SurveyAssignment

pytestmark = pytest.mark.django_db


def _give_perm(user, codename):
    """Add a custom permission to a user and return a fresh instance (clears perm cache)."""
    perm = Permission.objects.get(codename=codename)
    user.user_permissions.add(perm)
    return User.objects.get(pk=user.pk)


# ── _representative_minimum ───────────────────────────────────────────────────


def test_representative_minimum_zero_returns_none():
    assert _representative_minimum(0) is None


def test_representative_minimum_formula():
    n = 100
    expected = math.ceil(0.9604 * n / (0.0025 * (n - 1) + 0.9604))
    assert _representative_minimum(n) == expected


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

    def test_member_count_annotation(
        self, client, make_user, make_company, make_user_with_profile
    ):
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

    def test_can_view_dashboard_returns_200(
        self, client, make_user, make_company, make_user_with_profile
    ):
        company = make_company()
        user = _give_perm(make_user(), "can_view_dashboard")
        # Give the user a profile linked to the company so the view can find their company
        profile, _ = UserProfile.objects.get_or_create(user=user)
        profile.company = company
        profile.position = "Analyst"
        profile.save()

        client.force_login(user)
        response = client.get(self.URL)
        assert response.status_code == 200

    def _login_with_company(self, client, make_user, company):
        user = _give_perm(make_user(), "can_view_dashboard")
        profile, _ = UserProfile.objects.get_or_create(user=user)
        profile.company = company
        profile.position = "Analyst"
        profile.save()
        client.force_login(user)
        return client.get(self.URL)

    def test_representative_minimum_in_context(
        self, client, make_user, make_company, make_user_with_profile
    ):
        company = make_company()
        for i in range(9):
            make_user_with_profile(email=f"emp{i}@example.com", company=company)

        response = self._login_with_company(client, make_user, company)

        # 9 employees + 1 logged-in user profile = 10 total members
        n = 10
        expected = math.ceil(0.9604 * n / (0.0025 * (n - 1) + 0.9604))
        assert response.context["representative_minimum"] == expected


# ── HomeView ──────────────────────────────────────────────────────────────────


class TestHomeViewRouting:
    URL = "/"

    def test_unauthenticated_redirects(self, client):
        response = client.get(self.URL)
        assert response.status_code == 302

    def test_admin_group_redirects_to_company_list(
        self, client, make_user, bootstrap_groups
    ):
        user = make_user()
        user.groups.add(bootstrap_groups["Admins"])
        client.force_login(user)
        response = client.get(self.URL)
        assert response.status_code == 302
        assert response["Location"].endswith("/empresas/")

    def test_employee_group_redirects_to_survey_list(
        self, client, make_user, bootstrap_groups
    ):
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

    def test_employee_without_profile_redirects_to_setup(
        self, client, make_user, bootstrap_groups
    ):
        user = make_user()
        user.groups.add(bootstrap_groups["Employees"])
        client.force_login(user)
        response = client.get(self.URL)
        assert response.status_code == 302
        assert "perfil" in response["Location"]

    def test_employee_without_company_redirects_to_setup(
        self, client, make_user, bootstrap_groups
    ):
        user = make_user()
        user.groups.add(bootstrap_groups["Employees"])
        UserProfile.objects.create(user=user, company=None)
        client.force_login(user)
        response = client.get(self.URL)
        assert response.status_code == 302
        assert "perfil" in response["Location"]

    def test_employee_with_company_returns_200(
        self, client, make_user, make_company, bootstrap_groups
    ):
        company = make_company()
        user = self._make_employee(make_user, bootstrap_groups, company=company)
        client.force_login(user)
        response = client.get(self.URL)
        assert response.status_code == 200

    def test_only_company_assignments_appear(
        self, client, make_user, make_company, bootstrap_groups, survey_version
    ):
        company = make_company()
        other_company = make_company(
            name="Other Corp", legal_name="Other Corp SA de CV"
        )
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
        company = make_company()
        user = self._make_employee(make_user, bootstrap_groups, company=company)
        assignment = SurveyAssignment.objects.create(
            company=company, version=survey_version
        )
        SurveySubmission.objects.create(
            assignment=assignment, user=user, status=SurveySubmission.Status.COMPLETED
        )

        client.force_login(user)
        response = client.get(self.URL)

        item = next(
            i
            for i in response.context["assignment_data"]
            if i["assignment"].pk == assignment.pk
        )
        assert item["completed"] is True

    def test_completed_flag_false_when_no_submission(
        self, client, make_user, make_company, bootstrap_groups, survey_version
    ):
        company = make_company()
        user = self._make_employee(make_user, bootstrap_groups, company=company)
        assignment = SurveyAssignment.objects.create(
            company=company, version=survey_version
        )

        client.force_login(user)
        response = client.get(self.URL)

        item = next(
            i
            for i in response.context["assignment_data"]
            if i["assignment"].pk == assignment.pk
        )
        assert item["completed"] is False

    def test_completed_flag_false_for_in_progress_submission(
        self, client, make_user, make_company, bootstrap_groups, survey_version
    ):
        company = make_company()
        user = self._make_employee(make_user, bootstrap_groups, company=company)
        assignment = SurveyAssignment.objects.create(
            company=company, version=survey_version
        )
        SurveySubmission.objects.create(
            assignment=assignment, user=user, status=SurveySubmission.Status.IN_PROGRESS
        )

        client.force_login(user)
        response = client.get(self.URL)

        item = next(
            i
            for i in response.context["assignment_data"]
            if i["assignment"].pk == assignment.pk
        )
        assert item["completed"] is False


# ── EmployeeDetailView ────────────────────────────────────────────────────────


class TestEmployeeDetailView:
    def _url(self, employee_id):
        return f"/tablero-empresa/empleados/{employee_id}/"

    def _url_admin(self, reference_code, employee_id):
        return f"/empresas/{reference_code}/empleados/{employee_id}/"

    def _make_viewer(self, make_user, company, *extra_perms):
        """User with can_manage_employees linked to company."""
        user = make_user(email="viewer@example.com")
        user = _give_perm(user, "can_manage_employees")
        for perm in extra_perms:
            user = _give_perm(user, perm)
        profile, _ = UserProfile.objects.get_or_create(user=user)
        profile.company = company
        profile.save()
        return User.objects.get(pk=user.pk)

    def _make_employee(self, make_user_with_profile, company):
        return make_user_with_profile(email="emp@example.com", company=company)

    # ── access control ────────────────────────────────────────────────────────

    def test_unauthenticated_redirects_to_login(
        self, client, make_user, make_company, make_user_with_profile
    ):
        company = make_company()
        emp = self._make_employee(make_user_with_profile, company)
        response = client.get(self._url(emp.id))
        assert response.status_code == 302
        assert "ingresar" in response["Location"]

    def test_no_permission_returns_403(
        self, client, make_user, make_company, make_user_with_profile
    ):
        company = make_company()
        emp = self._make_employee(make_user_with_profile, company)
        client.force_login(make_user(email="noperm@example.com"))
        response = client.get(self._url(emp.id))
        assert response.status_code == 403

    def test_viewer_without_profile_redirects_to_setup(
        self, client, make_user, make_company, make_user_with_profile
    ):
        company = make_company()
        emp = self._make_employee(make_user_with_profile, company)
        viewer = _give_perm(make_user(email="v@example.com"), "can_manage_employees")
        client.force_login(viewer)
        response = client.get(self._url(emp.id))
        assert response.status_code == 302
        assert "perfil" in response["Location"]

    def test_viewer_without_company_redirects_to_setup(
        self, client, make_user, make_company, make_user_with_profile
    ):
        company = make_company()
        emp = self._make_employee(make_user_with_profile, company)
        viewer = _give_perm(make_user(email="v@example.com"), "can_manage_employees")
        UserProfile.objects.create(user=viewer, company=None)
        client.force_login(viewer)
        response = client.get(self._url(emp.id))
        assert response.status_code == 302
        assert "perfil" in response["Location"]

    def test_viewer_with_company_returns_200(
        self, client, make_user, make_company, make_user_with_profile
    ):
        company = make_company()
        emp = self._make_employee(make_user_with_profile, company)
        viewer = self._make_viewer(make_user, company)
        client.force_login(viewer)
        response = client.get(self._url(emp.id))
        assert response.status_code == 200

    def test_admin_reference_code_path_returns_200(
        self, client, make_user, make_company, make_user_with_profile
    ):
        company = make_company()
        emp = self._make_employee(make_user_with_profile, company)
        admin = _give_perm(
            _give_perm(make_user(email="admin@example.com"), "can_manage_employees"),
            "can_manage_surveys",
        )
        client.force_login(admin)
        response = client.get(self._url_admin(company.reference_code, emp.id))
        assert response.status_code == 200

    def test_reference_code_path_without_can_manage_surveys_returns_403(
        self, client, make_user, make_company, make_user_with_profile
    ):
        company = make_company()
        emp = self._make_employee(make_user_with_profile, company)
        viewer = self._make_viewer(make_user, company)  # only can_manage_employees
        client.force_login(viewer)
        response = client.get(self._url_admin(company.reference_code, emp.id))
        assert response.status_code == 403

    # ── 404 cases ─────────────────────────────────────────────────────────────

    def test_nonexistent_employee_returns_404(self, client, make_user, make_company):
        company = make_company()
        viewer = self._make_viewer(make_user, company)
        client.force_login(viewer)
        response = client.get(self._url(99999))
        assert response.status_code == 404

    def test_employee_from_different_company_returns_404(
        self, client, make_user, make_company, make_user_with_profile
    ):
        company = make_company()
        other_company = make_company(
            name="Other Corp", legal_name="Other Corp SA de CV"
        )
        emp = self._make_employee(make_user_with_profile, other_company)
        viewer = self._make_viewer(make_user, company)
        client.force_login(viewer)
        response = client.get(self._url(emp.id))
        assert response.status_code == 404

    # ── submissions_data visibility ───────────────────────────────────────────

    def test_submissions_data_is_none_without_can_view_submissions(
        self, client, make_user, make_company, make_user_with_profile
    ):
        company = make_company()
        emp = self._make_employee(make_user_with_profile, company)
        viewer = self._make_viewer(make_user, company)
        client.force_login(viewer)
        response = client.get(self._url(emp.id))
        assert response.context["submissions_data"] is None

    def test_submissions_data_present_with_can_view_submissions(
        self, client, make_user, make_company, make_user_with_profile
    ):
        company = make_company()
        emp = self._make_employee(make_user_with_profile, company)
        viewer = self._make_viewer(make_user, company, "can_view_submissions")
        client.force_login(viewer)
        response = client.get(self._url(emp.id))
        assert response.context["submissions_data"] is not None

    # ── progress data accuracy ────────────────────────────────────────────────

    def test_progress_not_started_when_no_submission(
        self, client, make_user, make_company, make_user_with_profile, survey_version
    ):
        company = make_company()
        emp = self._make_employee(make_user_with_profile, company)
        SurveyAssignment.objects.create(company=company, version=survey_version)
        viewer = self._make_viewer(make_user, company)
        client.force_login(viewer)
        response = client.get(self._url(emp.id))
        prog = response.context["survey_progress"][0]
        assert prog["percent"] == 0
        assert prog["answered"] == 0
        assert prog["status"] == "not_started"

    def test_progress_reflects_employee_answers(
        self,
        client,
        make_user,
        make_company,
        make_user_with_profile,
        survey_with_questions,
    ):
        company = make_company()
        emp = self._make_employee(make_user_with_profile, company)
        version = survey_with_questions["version"]
        questions = survey_with_questions["questions"]
        assignment = SurveyAssignment.objects.create(company=company, version=version)

        submission = SurveySubmission.objects.create(
            assignment=assignment, user=emp, status=SurveySubmission.Status.IN_PROGRESS
        )
        # Answer 3 out of 9 questions
        for q in questions[:3]:
            Answer.objects.create(submission=submission, question=q, value="test")

        viewer = self._make_viewer(make_user, company)
        client.force_login(viewer)
        response = client.get(self._url(emp.id))

        prog = response.context["survey_progress"][0]
        assert prog["answered"] == 3
        assert prog["total"] == 9
        assert prog["percent"] == 33
        assert prog["status"] == "in_progress"
