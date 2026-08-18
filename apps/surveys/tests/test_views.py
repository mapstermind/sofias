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


def _answers_for(questions):
    """Minimal valid POST data answering every question in `questions`."""
    by_type = {
        "boolean": "true",
        "multiple_choice": ["a"],
        "single_choice": "a",
        "integer": "5",
        "decimal": "3.14",
        "date": "2025-01-01",
        "rating": "4",
        "likert": "3",
    }
    return {
        f"question_{q.id}": by_type.get(q.question_type, "Una respuesta")
        for q in questions
    }


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
        post_data["confirm"] = "1"

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


class TestSubmitConfirmation:
    """A finished survey locks only when the respondent confirms.

    `COMPLETED` is a one-way door — `survey_detail` turns a completed respondent
    away — so answering the last question must not lock the submission by
    itself. Completing takes two independent keys: the server finding every
    visible question answered, *and* an explicit `confirm` in the POST, which
    only the confirmation modal sends.
    """

    def test_complete_post_without_confirm_asks_to_confirm(
        self, client, active_assignment, survey_with_questions
    ):
        questions = survey_with_questions["questions"]

        response = client.post(
            _survey_url(active_assignment.pk), _answers_for(questions)
        )

        assert response["Location"] == f"{_survey_url(active_assignment.pk)}?confirm=1"
        submission = SurveySubmission.objects.get(assignment=active_assignment)
        assert submission.status == SurveySubmission.Status.IN_PROGRESS
        assert submission.completed_at is None

    def test_complete_post_without_confirm_still_saves_every_answer(
        self, client, active_assignment, survey_with_questions
    ):
        questions = survey_with_questions["questions"]

        client.post(_survey_url(active_assignment.pk), _answers_for(questions))

        submission = SurveySubmission.objects.get(assignment=active_assignment)
        assert submission.answers.count() == len(questions)

    def test_confirmed_post_completes_the_submission(
        self, client, active_assignment, survey_with_questions
    ):
        questions = survey_with_questions["questions"]
        post_data = _answers_for(questions) | {"confirm": "1"}

        response = client.post(_survey_url(active_assignment.pk), post_data)

        assert response["Location"].endswith(_submitted_url(active_assignment.pk))
        submission = SurveySubmission.objects.get(assignment=active_assignment)
        assert submission.status == SurveySubmission.Status.COMPLETED
        assert submission.completed_at is not None

    def test_confirm_cannot_complete_an_unfinished_survey(
        self, client, active_assignment, survey_with_questions
    ):
        """A forged `confirm` on a half-answered survey saves progress, nothing more."""
        first = survey_with_questions["questions"][0]

        response = client.post(
            _survey_url(active_assignment.pk),
            {f"question_{first.id}": "Una respuesta", "confirm": "1"},
        )

        assert response["Location"] == f"{_survey_url(active_assignment.pk)}?saved=1"
        submission = SurveySubmission.objects.get(assignment=active_assignment)
        assert submission.status == SurveySubmission.Status.IN_PROGRESS

    def test_unfinished_post_saves_progress(
        self, client, active_assignment, survey_with_questions
    ):
        """The half-answered path is untouched by the confirmation gate."""
        first = survey_with_questions["questions"][0]

        response = client.post(
            _survey_url(active_assignment.pk),
            {f"question_{first.id}": "Una respuesta"},
        )

        assert response["Location"] == f"{_survey_url(active_assignment.pk)}?saved=1"
        submission = SurveySubmission.objects.get(assignment=active_assignment)
        assert submission.status == SurveySubmission.Status.IN_PROGRESS


class TestModalFlags:
    """`?confirm=1` / `?saved=1` are re-checked against stored answers on render.

    They only carry the *intent* of the POST that redirected here. A respondent
    who confirms, backs out, clears an answer and then reloads still holds a
    `?confirm=1` URL — the modal must not claim the survey is finished when it
    is not.
    """

    def test_confirm_flag_ignored_when_answers_are_incomplete(
        self, client, active_assignment, survey_with_questions
    ):
        first = survey_with_questions["questions"][0]
        client.post(
            _survey_url(active_assignment.pk),
            {f"question_{first.id}": "Una respuesta"},
        )

        response = client.get(f"{_survey_url(active_assignment.pk)}?confirm=1")

        assert response.context["show_confirm"] is False

    def test_confirm_flag_opens_the_modal_once_everything_is_answered(
        self, client, active_assignment, survey_with_questions
    ):
        questions = survey_with_questions["questions"]
        client.post(_survey_url(active_assignment.pk), _answers_for(questions))

        response = client.get(f"{_survey_url(active_assignment.pk)}?confirm=1")

        assert response.context["show_confirm"] is True

    def test_saved_flag_ignored_before_anything_is_saved(
        self, client, active_assignment, survey_with_questions
    ):
        response = client.get(f"{_survey_url(active_assignment.pk)}?saved=1")

        assert response.context["show_saved"] is False

    def test_saved_flag_opens_the_modal_after_a_save(
        self, client, active_assignment, survey_with_questions
    ):
        first = survey_with_questions["questions"][0]
        client.post(
            _survey_url(active_assignment.pk),
            {f"question_{first.id}": "Una respuesta"},
        )

        response = client.get(f"{_survey_url(active_assignment.pk)}?saved=1")

        assert response.context["show_saved"] is True


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
            "confirm": "1",
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

    def test_page_names_the_survey(self, client, active_assignment):
        body = client.get(_submitted_url(active_assignment.pk)).content.decode()
        assert active_assignment.survey.title in body

    def test_page_does_not_offer_editing(self, client, active_assignment):
        """The answers are locked, so the page must not invite an edit it can't honour."""
        body = client.get(_submitted_url(active_assignment.pk)).content.decode()
        assert _survey_url(active_assignment.pk) not in body


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


class TestPendingCount:
    """`pending_count` tells a respondent how many questions they still owe.

    Saving is the moment someone believes they are finished, so the saved
    modal is where the number has to appear — the confirmation modal only
    ever opens at zero pending.
    """

    def test_pending_count_is_the_unanswered_visible_total(
        self, client, active_assignment, survey_with_questions
    ):
        first = survey_with_questions["questions"][0]
        client.post(
            _survey_url(active_assignment.pk),
            {f"question_{first.id}": "Una respuesta"},
        )

        response = client.get(_survey_url(active_assignment.pk))

        assert response.context["pending_count"] == 8

    def test_pending_count_is_zero_once_everything_is_answered(
        self, client, active_assignment, survey_with_questions
    ):
        questions = survey_with_questions["questions"]
        client.post(_survey_url(active_assignment.pk), _answers_for(questions))

        response = client.get(_survey_url(active_assignment.pk))

        assert response.context["pending_count"] == 0

    def test_saved_modal_states_the_plural_count(
        self, client, active_assignment, survey_with_questions
    ):
        first = survey_with_questions["questions"][0]
        client.post(
            _survey_url(active_assignment.pk),
            {f"question_{first.id}": "Una respuesta"},
        )

        response = client.get(f"{_survey_url(active_assignment.pk)}?saved=1")

        assert "Te faltan 8 preguntas por responder." in response.content.decode()

    def test_saved_modal_states_the_singular_count(
        self, client, active_assignment, survey_with_questions
    ):
        """Spanish inflects the verb as well as the noun, so one pending
        question is `Te falta 1 pregunta`, not `Te faltan 1 preguntas`."""
        questions = survey_with_questions["questions"]
        answers = _answers_for(questions)
        answers.pop(f"question_{questions[-1].id}")
        client.post(_survey_url(active_assignment.pk), answers)

        response = client.get(f"{_survey_url(active_assignment.pk)}?saved=1")

        assert "Te falta 1 pregunta por responder." in response.content.decode()


class TestPendingPanelShell:
    """The panel's shell is server-rendered so Tailwind can see its classes;
    only the list items are built client-side."""

    def test_panel_shell_renders_hidden_and_empty(
        self, client, active_assignment, survey_with_questions
    ):
        response = client.get(_survey_url(active_assignment.pk))
        html = response.content.decode()

        assert 'id="pending-panel"' in html
        assert 'id="pending-list"' in html
        assert 'id="pending-next"' in html
        assert "Ir a la siguiente" in html

    def test_question_text_label_is_tagged_for_the_client(
        self, client, active_assignment, survey_with_questions
    ):
        """The client reads question text from this label. Choice options are
        `<label>`s too, so the hook has to be a class, not element order."""
        response = client.get(_survey_url(active_assignment.pk))

        assert "question-label" in response.content.decode()
