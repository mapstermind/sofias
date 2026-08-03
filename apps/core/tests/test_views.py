import math

import pytest
from django.contrib.auth.models import Permission
from django.db import connection
from django.test.utils import CaptureQueriesContext
from django.utils.html import strip_tags

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


@pytest.fixture
def gated_survey(db, survey):
    """Four questions, two of them behind a gate — the shape NOM-035 uses.

    Answering the gate "no" leaves a survey the backend calls completed with
    only 2 of the 4 authored questions answered.
    """
    from apps.surveys.models import Module, Question

    module = Module.objects.create(
        survey=survey, key="base", title="Base", applies_to="all", order=0
    )
    gate = Question.objects.create(
        module=module, code="gate-q", question_type="boolean", text="¿Es jefe?"
    )
    plain = Question.objects.create(
        module=module, code="plain", question_type="text", text="Puesto"
    )
    for n in (1, 2):
        Question.objects.create(
            module=module,
            code=f"f{n}",
            question_type="text",
            text=f"Follow {n}",
            visible_when={"question": "gate-q", "equals": True},
        )
    return {"survey": survey, "gate": gate, "plain": plain}


def _complete_with_gate_closed(company, employee, gated_survey):
    """A completed submission that answered only the 2 always-visible questions."""
    assignment = SurveyAssignment.objects.create(
        company=company, survey=gated_survey["survey"], variant="small"
    )
    submission = SurveySubmission.objects.create(
        assignment=assignment,
        user=employee,
        status=SurveySubmission.Status.COMPLETED,
    )
    Answer.objects.create(
        submission=submission, question=gated_survey["gate"], value=False
    )
    Answer.objects.create(
        submission=submission, question=gated_survey["plain"], value="Analista"
    )
    return assignment


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

    def test_summary_strip_shows_formula_action(self, client, make_user, make_company):
        company = make_company()

        response = self._login_with_company(client, make_user, company)

        assert response.status_code == 200
        assert "Ver fórmula".encode() in response.content
        assert "Mínimo representativo".encode() in response.content

    def test_summary_strip_shows_employee_action_with_permission(
        self, client, make_user, make_company
    ):
        company = make_company()
        user = _give_perm(make_user(), "can_view_dashboard")
        user = _give_perm(user, "can_manage_employees")
        profile, _ = UserProfile.objects.get_or_create(user=user)
        profile.company = company
        profile.position = "Analyst"
        profile.save()
        client.force_login(user)

        response = client.get(self.URL)

        assert response.status_code == 200
        assert "Ver empleados".encode() in response.content

    def test_summary_strip_hides_employee_action_without_permission(
        self, client, make_user, make_company
    ):
        company = make_company()

        response = self._login_with_company(client, make_user, company)

        assert response.status_code == 200
        assert "Ver empleados".encode() not in response.content


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
        self, client, make_user, make_company, bootstrap_groups, survey
    ):
        company = make_company()
        other_company = make_company(
            name="Other Corp", legal_name="Other Corp SA de CV"
        )
        user = self._make_employee(make_user, bootstrap_groups, company=company)

        own = SurveyAssignment.objects.create(
            company=company, survey=survey, variant="small"
        )
        SurveyAssignment.objects.create(
            company=other_company, survey=survey, variant="small"
        )

        client.force_login(user)
        response = client.get(self.URL)

        ids = [item["assignment"].pk for item in response.context["assignment_data"]]
        assert own.pk in ids
        assert len(ids) == 1

    def test_completed_flag_true_when_user_has_completed_submission(
        self, client, make_user, make_company, bootstrap_groups, survey
    ):
        company = make_company()
        user = self._make_employee(make_user, bootstrap_groups, company=company)
        assignment = SurveyAssignment.objects.create(
            company=company, survey=survey, variant="small"
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
        self, client, make_user, make_company, bootstrap_groups, survey
    ):
        company = make_company()
        user = self._make_employee(make_user, bootstrap_groups, company=company)
        assignment = SurveyAssignment.objects.create(
            company=company, survey=survey, variant="small"
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
        self, client, make_user, make_company, bootstrap_groups, survey
    ):
        company = make_company()
        user = self._make_employee(make_user, bootstrap_groups, company=company)
        assignment = SurveyAssignment.objects.create(
            company=company, survey=survey, variant="small"
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


# ── CompanyEmployeeListView ──────────────────────────────────────────────────


class TestCompanyEmployeeListView:
    URL = "/tablero-empresa/empleados/"

    def _make_viewer(self, make_user, company):
        user = _give_perm(make_user(email="viewer@example.com"), "can_manage_employees")
        profile, _ = UserProfile.objects.get_or_create(user=user)
        profile.company = company
        profile.save()
        return User.objects.get(pk=user.pk)

    def test_activation_status_labels_render(
        self, client, make_user, make_company, make_user_with_profile
    ):
        company = make_company()
        viewer = self._make_viewer(make_user, company)
        active_user = make_user_with_profile(
            email="active@example.com", company=company
        )
        inactive_user = make_user_with_profile(
            email="inactive@example.com", company=company
        )
        active_user.profile.is_activated = True
        active_user.profile.save(update_fields=["is_activated"])

        client.force_login(viewer)
        response = client.get(self.URL)

        assert response.status_code == 200
        assert active_user.email.encode() in response.content
        assert inactive_user.email.encode() in response.content
        assert "Activado".encode() in response.content
        assert "No activado".encode() in response.content

    def test_completed_gated_survey_reads_100_percent(
        self, client, make_user, make_company, make_user_with_profile, gated_survey
    ):
        company = make_company()
        viewer = self._make_viewer(make_user, company)
        emp = make_user_with_profile(email="emp@example.com", company=company)
        _complete_with_gate_closed(company, emp, gated_survey)

        client.force_login(viewer)
        response = client.get(self.URL)

        entry = next(
            m for m in response.context["members"] if m["profile"].user_id == emp.id
        )
        prog = entry["survey_progress"][0]
        assert prog["percent"] == 100
        assert prog["answered"] == prog["total"] == 2
        assert prog["not_applicable"] == 2

    def test_query_count_does_not_grow_with_members(
        self, client, make_user, make_company, make_user_with_profile, gated_survey
    ):
        """Progress now needs answer values, not just counts — it must still be
        one sweep, with the module prefetch shared across every member."""
        company = make_company()
        viewer = self._make_viewer(make_user, company)
        assignment = SurveyAssignment.objects.create(
            company=company, survey=gated_survey["survey"], variant="small"
        )
        client.force_login(viewer)
        offset = 0

        def add_members(count):
            nonlocal offset
            for i in range(offset, offset + count):
                emp = make_user_with_profile(
                    email=f"bulk-{i}@example.com", company=company
                )
                submission = SurveySubmission.objects.create(
                    assignment=assignment,
                    user=emp,
                    status=SurveySubmission.Status.COMPLETED,
                )
                Answer.objects.create(
                    submission=submission, question=gated_survey["gate"], value=False
                )
            offset += count

        def query_count():
            with CaptureQueriesContext(connection) as captured:
                assert client.get(self.URL).status_code == 200
            return len(captured)

        add_members(2)
        baseline = query_count()
        add_members(8)
        assert query_count() == baseline


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
        self, client, make_user, make_company, make_user_with_profile, survey
    ):
        company = make_company()
        emp = self._make_employee(make_user_with_profile, company)
        SurveyAssignment.objects.create(company=company, survey=survey, variant="small")
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
        survey_obj = survey_with_questions["survey"]
        questions = survey_with_questions["questions"]
        assignment = SurveyAssignment.objects.create(
            company=company, survey=survey_obj, variant="small"
        )

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

    def test_completed_gated_survey_reads_100_percent(
        self, client, make_user, make_company, make_user_with_profile, gated_survey
    ):
        company = make_company()
        emp = self._make_employee(make_user_with_profile, company)
        _complete_with_gate_closed(company, emp, gated_survey)

        viewer = self._make_viewer(make_user, company)
        client.force_login(viewer)
        response = client.get(self._url(emp.id))

        prog = response.context["survey_progress"][0]
        assert prog["status"] == "completed"
        assert prog["percent"] == 100
        assert prog["answered"] == prog["total"] == 2
        # The two gated-out questions are reported, not silently dropped.
        assert prog["not_applicable"] == 2

    def test_gated_out_questions_explained_in_page(
        self, client, make_user, make_company, make_user_with_profile, gated_survey
    ):
        company = make_company()
        emp = self._make_employee(make_user_with_profile, company)
        _complete_with_gate_closed(company, emp, gated_survey)

        viewer = self._make_viewer(make_user, company)
        client.force_login(viewer)
        response = client.get(self._url(emp.id))

        # Collapse whitespace/markup so the assertion is on the visible copy.
        text = " ".join(strip_tags(response.content.decode()).split())
        assert "2 de 2 respondidas (2 no aplican)" in text

    # ── valoración panel ──────────────────────────────────────────────────────

    def test_valuation_panel_hidden_without_can_view_insights(
        self, client, make_user, make_company, make_user_with_profile
    ):
        company = make_company()
        emp = self._make_employee(make_user_with_profile, company)
        viewer = self._make_viewer(make_user, company)
        client.force_login(viewer)
        response = client.get(self._url(emp.id))
        assert response.context["valuation"] is None
        assert "Valoración de resultados" not in response.content.decode()

    def test_valuation_empty_state_points_at_completion(
        self, client, make_user, make_company, make_user_with_profile
    ):
        company = make_company()
        emp = self._make_employee(make_user_with_profile, company)
        viewer = self._make_viewer(make_user, company, "can_view_insights")
        client.force_login(viewer)
        response = client.get(self._url(emp.id))
        assert (
            "La valoración se genera al completar la encuesta."
            in response.content.decode()
        )

    def test_valuation_panel_renders_scale_and_categories(
        self, client, make_user, make_company, make_user_with_profile, survey
    ):
        from apps.nom035 import constants as nom
        from apps.nom035.models import GroupScore, SubmissionScore

        company = make_company()
        emp = self._make_employee(make_user_with_profile, company)
        assignment = SurveyAssignment.objects.create(
            company=company, survey=survey, variant=SurveyAssignment.Variant.LARGE
        )
        # In-progress so the completion signal does not overwrite these values.
        submission = SurveySubmission.objects.create(
            assignment=assignment, user=emp, status=SurveySubmission.Status.IN_PROGRESS
        )
        score = SubmissionScore.objects.create(
            submission=submission,
            final_score=160,
            final_ndr=nom.NDR_MUY_ALTO,
            guia1_positive=True,
        )
        for level, key, value, ndr in [
            (nom.LEVEL_CATEGORIA, "ambiente_de_trabajo", 13, nom.NDR_ALTO),
            (
                nom.LEVEL_DOMINIO,
                "condiciones_en_el_ambiente_de_trabajo",
                13,
                nom.NDR_ALTO,
            ),
            (nom.LEVEL_DIMENSION, "trabajos_peligrosos", 4, ""),
        ]:
            GroupScore.objects.create(
                submission_score=score, level=level, key=key, score=value, ndr=ndr
            )

        viewer = self._make_viewer(make_user, company, "can_view_insights")
        client.force_login(viewer)
        body = client.get(self._url(emp.id)).content.decode()

        assert "Nivel de riesgo final" in body
        assert "160 puntos" in body
        assert "Nivel de riesgo Muy alto" in body  # the 5-step scale's aria-label
        assert "Ambiente de trabajo" in body
        assert "Usuario positivo a un acontecimiento traumático severo." in body
        # The dominio row is itself the disclosure that reveals its dimensiones.
        assert "<details" in body
        assert "Trabajos peligrosos" in body
