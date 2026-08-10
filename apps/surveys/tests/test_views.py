import pytest

from apps.responses.models import Answer, SurveySubmission
from apps.surveys.models import SurveyAssignment

pytestmark = pytest.mark.django_db


def _survey_url(assignment_id):
    return f"/encuestas/asignados/{assignment_id}/"


def _submitted_url(assignment_id):
    return f"/encuestas/asignados/{assignment_id}/enviada/"


def _autosave_url(assignment_id):
    return f"/encuestas/asignados/{assignment_id}/autoguardar/"


@pytest.fixture(autouse=True)
def respondent(client, company, make_user_with_profile, bootstrap_groups):
    """Every test here gets a logged-in employee **of the assignment's company**.

    Both halves matter: the views require `can_take_assigned_surveys` and scope
    the assignment lookup to the caller's own company, so a bare user with no
    profile or group would 404 out of every test in this module.
    """
    user = make_user_with_profile(email="respondent@example.com", company=company)
    user.groups.add(bootstrap_groups["Employees"])
    client.force_login(user)
    return user


class TestSurveyDetailView:
    def test_get_returns_200(self, client, active_assignment):
        response = client.get(_survey_url(active_assignment.pk))
        assert response.status_code == 200

    def test_anonymous_redirects_to_login(self, client, active_assignment):
        client.logout()
        response = client.get(_survey_url(active_assignment.pk))
        assert response.status_code == 302
        assert response["Location"].startswith("/cuentas/ingresar/")

    def test_closed_assignment_redirects_to_home(self, client, active_assignment):
        active_assignment.status = SurveyAssignment.Status.CLOSED
        active_assignment.save()
        response = client.get(_survey_url(active_assignment.pk))
        assert response.status_code == 302
        assert response["Location"] == "/"

    def test_nonexistent_assignment_returns_404(self, client):
        response = client.get(_survey_url(99999))
        assert response.status_code == 404

    def test_instructions_shown_on_first_visit(self, client, active_assignment):
        response = client.get(_survey_url(active_assignment.pk))
        assert response.context["show_instructions"] is True

    def test_instructions_not_shown_once_an_answer_exists(
        self, client, active_assignment, survey_with_questions, respondent
    ):
        submission = SurveySubmission.objects.create(
            assignment=active_assignment,
            user=respondent,
            status=SurveySubmission.Status.IN_PROGRESS,
        )
        Answer.objects.create(
            submission=submission,
            question=survey_with_questions["questions"][0],
            value="una respuesta",
        )

        response = client.get(_survey_url(active_assignment.pk))
        assert response.context["show_instructions"] is False

    def test_post_all_question_types_creates_submission(
        self, client, active_assignment, survey_with_questions
    ):
        questions = survey_with_questions["questions"]
        post_data = {}
        for q in questions:
            key = f"question_{q.id}"
            if q.question_type == "boolean":
                post_data[key] = "true"
            elif q.question_type == "multiple_choice":
                post_data[key] = ["a"]
            elif q.question_type == "integer":
                post_data[key] = "5"
            elif q.question_type == "decimal":
                post_data[key] = "3.14"
            elif q.question_type == "date":
                post_data[key] = "2025-01-01"
            elif q.question_type == "rating":
                post_data[key] = "4"
            elif q.question_type == "likert":
                post_data[key] = "3"
            else:
                post_data[key] = "Some text answer"

        response = client.post(_survey_url(active_assignment.pk), post_data)
        assert response.status_code == 302

        submission = SurveySubmission.objects.filter(
            assignment=active_assignment
        ).first()
        assert submission is not None
        assert submission.answers.count() == len(questions)

    def test_post_all_question_types_redirects_to_submitted(
        self, client, active_assignment, survey_with_questions
    ):
        questions = survey_with_questions["questions"]
        post_data = {}
        # Fill all types minimally
        for q in questions:
            key = f"question_{q.id}"
            if q.question_type == "boolean":
                post_data[key] = "true"
            elif q.question_type == "multiple_choice":
                post_data[key] = ["a"]
            elif q.question_type == "integer":
                post_data[key] = "1"
            elif q.question_type == "decimal":
                post_data[key] = "1.0"
            elif q.question_type == "date":
                post_data[key] = "2025-06-01"
            elif q.question_type == "rating":
                post_data[key] = "3"
            elif q.question_type == "likert":
                post_data[key] = "2"
            else:
                post_data[key] = "text"

        response = client.post(_survey_url(active_assignment.pk), post_data)
        assert response["Location"].endswith(_submitted_url(active_assignment.pk))

    def test_post_invalid_integer_shows_error_for_that_question(
        self, client, active_assignment, survey_with_questions
    ):
        questions = survey_with_questions["questions"]
        int_q = next(q for q in questions if q.question_type == "integer")

        response = client.post(
            _survey_url(active_assignment.pk),
            {f"question_{int_q.id}": "not-a-number"},
        )
        assert response.status_code == 200
        assert int_q.id in response.context["errors"]

    def test_post_invalid_decimal_shows_error(
        self, client, active_assignment, survey_with_questions
    ):
        questions = survey_with_questions["questions"]
        dec_q = next(q for q in questions if q.question_type == "decimal")

        response = client.post(
            _survey_url(active_assignment.pk),
            {f"question_{dec_q.id}": "abc"},
        )
        assert response.status_code == 200
        assert dec_q.id in response.context["errors"]


@pytest.fixture
def variant_survey(db, survey):
    """Survey with an `all` trigger+followup, a small-only and large-only question."""
    from apps.surveys.models import Module, Question

    trigger = Module.objects.create(
        survey=survey, key="trigger", title="T", applies_to="all", order=0
    )
    Question.objects.create(
        module=trigger, code="t1", question_type="boolean", text="Trigger?"
    )
    followup = Module.objects.create(
        survey=survey,
        key="followup",
        title="F",
        applies_to="all",
        order=1,
        visible_when={"any_in_module": "trigger", "equals": True},
    )
    Question.objects.create(
        module=followup, code="f1", question_type="text", text="Why?"
    )
    small = Module.objects.create(
        survey=survey, key="small", title="S", applies_to="small", order=2
    )
    Question.objects.create(
        module=small, code="s1", question_type="text", text="Small only"
    )
    large = Module.objects.create(
        survey=survey, key="large", title="L", applies_to="large", order=3
    )
    Question.objects.create(
        module=large, code="l1", question_type="text", text="Large only"
    )
    return survey


class TestVariantPresentation:
    def _assignment(self, survey, company, variant):
        return SurveyAssignment.objects.create(
            company=company, survey=survey, variant=variant
        )

    def test_small_shows_small_not_large(self, client, variant_survey, company):
        a = self._assignment(variant_survey, company, "small")
        body = client.get(_survey_url(a.pk)).content.decode()
        assert "Small only" in body
        assert "Large only" not in body

    def test_large_shows_large_not_small(self, client, variant_survey, company):
        a = self._assignment(variant_survey, company, "large")
        body = client.get(_survey_url(a.pk)).content.decode()
        assert "Large only" in body
        assert "Small only" not in body

    def test_skip_path_completes_without_hidden_followup(
        self, client, variant_survey, company, make_user_with_profile, bootstrap_groups
    ):
        a = self._assignment(variant_survey, company, "small")
        user = make_user_with_profile(email="emp@x.com", company=company)
        user.groups.add(bootstrap_groups["Employees"])
        client.force_login(user)
        # Trigger = No hides f1; answer the visible questions only.
        from apps.surveys.models import Question

        q = {x.code: x for x in Question.objects.filter(survey=variant_survey)}
        post = {
            f"question_{q['t1'].id}": "false",
            f"question_{q['s1'].id}": "answer",
        }
        response = client.post(_survey_url(a.pk), post)
        assert response["Location"].endswith(_submitted_url(a.pk))
        sub = SurveySubmission.objects.get(assignment=a, user=user)
        assert sub.status == SurveySubmission.Status.COMPLETED


class TestSurveySubmittedView:
    def test_get_returns_200(self, client, active_assignment):
        response = client.get(_submitted_url(active_assignment.pk))
        assert response.status_code == 200

    def test_closed_assignment_returns_200(self, client, active_assignment):
        active_assignment.status = SurveyAssignment.Status.CLOSED
        active_assignment.save()
        response = client.get(_submitted_url(active_assignment.pk))
        assert response.status_code == 200


class TestCompanyScoping:
    """An assignment is reachable only by employees of its own company.

    The respondent fixture belongs to `company`; `foreign_assignment` belongs to
    a second one. Every check here is from the logged-in respondent's session.
    """

    @pytest.fixture
    def foreign_assignment(self, make_company, survey_with_questions):
        return SurveyAssignment.objects.create(
            company=make_company(name="Cliente B", legal_name="B SA de CV"),
            survey=survey_with_questions["survey"],
            variant=SurveyAssignment.Variant.SMALL,
            status=SurveyAssignment.Status.ACTIVE,
        )

    @pytest.fixture
    def foreign_question(self, survey_with_questions):
        return survey_with_questions["questions"][0]

    def test_detail_404s_on_another_companys_assignment(
        self, client, foreign_assignment
    ):
        response = client.get(_survey_url(foreign_assignment.pk))
        assert response.status_code == 404

    def test_submitted_404s_on_another_companys_assignment(
        self, client, foreign_assignment
    ):
        response = client.get(_submitted_url(foreign_assignment.pk))
        assert response.status_code == 404

    def test_autosave_404s_on_another_companys_assignment(
        self, client, foreign_assignment, foreign_question
    ):
        response = client.post(
            _autosave_url(foreign_assignment.pk),
            {f"question_{foreign_question.id}": "intruso"},
        )
        assert response.status_code == 404
        assert not Answer.objects.exists()

    def test_post_cannot_submit_into_another_companys_assignment(
        self, client, foreign_assignment, foreign_question
    ):
        """The consequential one: a submission here would enter another
        company's NOM-035 roll-up."""
        response = client.post(
            _survey_url(foreign_assignment.pk),
            {f"question_{foreign_question.id}": "intruso"},
        )
        assert response.status_code == 404
        assert not SurveySubmission.objects.filter(
            assignment=foreign_assignment
        ).exists()

    def test_enumeration_is_indistinguishable_from_a_missing_id(
        self, client, foreign_assignment
    ):
        """Same status for "exists but not yours" and "does not exist", so the
        id space cannot be walked to discover other companies' assignments."""
        foreign = client.get(_survey_url(foreign_assignment.pk))
        missing = client.get(_survey_url(foreign_assignment.pk + 10_000))
        assert foreign.status_code == missing.status_code == 404

    def test_user_without_a_profile_is_sent_to_activation(
        self, client, active_assignment, make_user, bootstrap_groups
    ):
        stray = make_user(email="sinperfil@example.com")
        stray.groups.add(bootstrap_groups["Employees"])
        client.force_login(stray)

        response = client.get(_survey_url(active_assignment.pk))

        assert response.status_code == 302
        assert response["Location"] == "/cuentas/completar-perfil/"

    def test_user_without_a_company_is_sent_to_activation(
        self, client, active_assignment, make_user_with_profile, bootstrap_groups
    ):
        stray = make_user_with_profile(email="sinempresa@example.com", company=None)
        stray.groups.add(bootstrap_groups["Employees"])
        client.force_login(stray)

        response = client.get(_survey_url(active_assignment.pk))

        assert response.status_code == 302
        assert response["Location"] == "/cuentas/completar-perfil/"

    def test_admin_cannot_open_a_survey(
        self, client, active_assignment, make_user, bootstrap_groups
    ):
        """Admins hold no `can_take_assigned_surveys` and answer no surveys."""
        admin = make_user(email="admin@example.com")
        admin.groups.add(bootstrap_groups["Admins"])
        client.force_login(admin)

        response = client.get(_survey_url(active_assignment.pk))

        assert response.status_code == 302
        assert response["Location"] == "/cuentas/completar-perfil/"

    def test_autosave_rejects_a_caller_who_cannot_take_surveys(
        self, client, active_assignment, make_user, bootstrap_groups
    ):
        admin = make_user(email="admin2@example.com")
        admin.groups.add(bootstrap_groups["Admins"])
        client.force_login(admin)

        response = client.post(_autosave_url(active_assignment.pk), {})

        assert response.status_code == 403
        assert response.json()["error"] == "forbidden"
