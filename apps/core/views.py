import math

from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied
from django.db.models import Count, Q
from django.shortcuts import get_object_or_404, redirect, render
from django.views import View

from apps.accounts.models import Company, UserProfile
from apps.responses.models import Answer, SurveySubmission
from apps.surveys.models import Module, SurveyAssignment
from apps.surveys.visibility import progress_for_modules


def _representative_minimum(n: int) -> int | None:
    if n == 0:
        return None
    return math.ceil(0.9604 * n / (0.0025 * (n - 1) + 0.9604))


def _variant_question_count(assignment) -> int:
    """Total questions presented for an assignment's variant (modules tagged
    `all` plus the assignment's variant). Ignores per-respondent conditional
    visibility, which varies by answer."""
    return assignment.survey.questions.filter(
        module__applies_to__in=[Module.AppliesTo.ALL, assignment.variant]
    ).count()


def _progress_entry(assignment, modules, nominal_total, answers_by_qid, status):
    """One `survey_progress` row.

    `answered`/`total` come from `progress_for_modules`, so they count only the
    questions that apply given the answers so far — the same rule the
    survey-taking page uses. `not_applicable` is the remainder of the variant's
    questions that a gate answer ruled out, which is what lets the UI explain a
    completed survey that answered fewer questions than the instrument holds.
    """
    answered, total = progress_for_modules(modules, answers_by_qid)
    return {
        "assignment": assignment,
        "answered": answered,
        "total": total,
        "percent": round(answered / total * 100) if total > 0 else 0,
        "not_applicable": max(nominal_total - total, 0),
        "status": status,
    }


class HomeView(LoginRequiredMixin, View):
    def get(self, request):
        user = request.user
        if user.groups.filter(name="Admins").exists():
            return redirect("core:company_list")
        if user.has_perm("accounts.can_view_dashboard"):
            return redirect("core:company_dashboard")
        if user.has_perm("accounts.can_take_assigned_surveys"):
            return redirect("core:employee_survey_list")
        return redirect("accounts:request_otp")


class EmployeeSurveyListView(LoginRequiredMixin, View):
    """List surveys assigned to the employee's company."""

    def get(self, request):
        if not request.user.has_perm("accounts.can_take_assigned_surveys"):
            raise PermissionDenied

        try:
            profile = request.user.profile
        except UserProfile.DoesNotExist:
            return redirect("accounts:setup_profile")

        if not profile.company_id:
            return redirect("accounts:setup_profile")

        company = profile.company

        assignments = (
            SurveyAssignment.objects.filter(company=company)
            .select_related("survey")
            .order_by("-created_at")
        )

        user_completed_ids = set(
            request.user.submissions.filter(
                assignment__in=assignments,
                status="completed",
            ).values_list("assignment_id", flat=True)
        )

        assignment_data = [
            {
                "assignment": a,
                "completed": a.id in user_completed_ids,
            }
            for a in assignments
        ]

        return render(
            request,
            "core/employee_survey_list.html",
            {
                "company": company,
                "assignment_data": assignment_data,
            },
        )


class CompanyListView(LoginRequiredMixin, View):
    """List all companies for admin users."""

    def get(self, request):
        if not request.user.has_perm("accounts.can_manage_surveys"):
            raise PermissionDenied

        companies = Company.objects.annotate(
            member_count=Count("members", distinct=True),
            active_assignment_count=Count(
                "survey_assignments",
                filter=Q(survey_assignments__status=SurveyAssignment.Status.ACTIVE),
                distinct=True,
            ),
            completed_submission_count=Count(
                "survey_assignments__submissions",
                filter=Q(
                    survey_assignments__submissions__status=SurveySubmission.Status.COMPLETED
                ),
                distinct=True,
            ),
        ).order_by("name")

        return render(request, "core/company_list.html", {"companies": companies})


class CompanyDashboardView(LoginRequiredMixin, View):
    """Display company dashboard for admin users."""

    def get(self, request, reference_code=None):
        if not request.user.has_perm("accounts.can_view_dashboard"):
            raise PermissionDenied

        if reference_code is not None:
            if not request.user.has_perm("accounts.can_manage_surveys"):
                raise PermissionDenied
            company = get_object_or_404(Company, reference_code=reference_code)
        else:
            try:
                profile = request.user.profile
            except UserProfile.DoesNotExist:
                return redirect("accounts:setup_profile")
            if not profile.company_id:
                return redirect("accounts:setup_profile")
            company = profile.company

        member_count = company.members.count()
        activated_count = company.members.filter(is_activated=True).count()
        registration_rate = (
            round(activated_count / member_count * 100) if member_count > 0 else None
        )
        representative_minimum = _representative_minimum(member_count)
        representative_threshold_pct = (
            min(round(representative_minimum / member_count * 100), 100)
            if representative_minimum is not None
            else None
        )

        assignments = (
            SurveyAssignment.objects.filter(company=company)
            .select_related("survey")
            .annotate(
                completed_count=Count(
                    "submissions",
                    filter=Q(submissions__status=SurveySubmission.Status.COMPLETED),
                )
            )
            .order_by("-created_at")
        )

        user_completed_ids = set()
        if request.user.has_perm("accounts.can_take_assigned_surveys"):
            user_completed_ids = set(
                request.user.submissions.filter(
                    assignment__in=assignments,
                    status=SurveySubmission.Status.COMPLETED,
                ).values_list("assignment_id", flat=True)
            )

        assignment_data = []
        for assignment in assignments:
            rate = (
                round(assignment.completed_count / member_count * 100)
                if member_count > 0
                else 0
            )
            assignment_data.append(
                {
                    "assignment": assignment,
                    "completed_count": assignment.completed_count,
                    "member_count": member_count,
                    "completion_rate": rate,
                    "user_completed": assignment.id in user_completed_ids,
                }
            )

        company_valuation = None
        if request.user.has_perm("accounts.can_view_insights"):
            from apps.nom035.aggregates import company_valuation as _company_valuation

            company_valuation = _company_valuation(company)

        return render(
            request,
            "core/company_dashboard.html",
            {
                "company": company,
                "member_count": member_count,
                "activated_count": activated_count,
                "registration_rate": registration_rate,
                "representative_minimum": representative_minimum,
                "representative_threshold_pct": representative_threshold_pct,
                "assignment_data": assignment_data,
                "is_admin_view": reference_code is not None,
                "company_valuation": company_valuation,
            },
        )


class CompanyEmployeeListView(LoginRequiredMixin, View):
    """List all employees for a company with per-survey progress."""

    def get(self, request, reference_code=None):
        if not request.user.has_perm("accounts.can_manage_employees"):
            raise PermissionDenied

        if reference_code is not None:
            if not request.user.has_perm("accounts.can_manage_surveys"):
                raise PermissionDenied
            company = get_object_or_404(Company, reference_code=reference_code)
        else:
            try:
                profile = request.user.profile
            except UserProfile.DoesNotExist:
                return redirect("accounts:setup_profile")
            if not profile.company_id:
                return redirect("accounts:setup_profile")
            company = profile.company

        assignments = list(
            SurveyAssignment.objects.filter(company=company)
            .select_related("survey")
            .order_by("-created_at")
        )

        # Pre-fetch total question counts per assignment to avoid N+1
        total_questions_map = {a.id: _variant_question_count(a) for a in assignments}

        # One module prefetch per assignment, reused for every member below.
        modules_map = {
            a.id: list(a.modules_for_variant().prefetch_related("questions"))
            for a in assignments
        }

        # Pre-fetch all answers for this company's assignments in one query.
        # Values (not just counts) are needed to evaluate the `visible_when`
        # gates that decide which questions apply to each respondent.
        answers_map: dict[tuple[int, int], dict[int, object]] = {}
        answer_rows = Answer.objects.filter(
            submission__assignment__in=assignments
        ).values_list(
            "submission__user_id",
            "submission__assignment_id",
            "question_id",
            "value",
        )
        for user_id, assignment_id, question_id, value in answer_rows:
            answers_map.setdefault((user_id, assignment_id), {})[question_id] = value

        # Pre-fetch submission statuses per (user, assignment)
        submission_status_map: dict[tuple[int, int], str] = {}
        for sub in SurveySubmission.objects.filter(assignment__in=assignments).values(
            "user_id", "assignment_id", "status"
        ):
            submission_status_map[(sub["user_id"], sub["assignment_id"])] = sub[
                "status"
            ]

        profiles = company.members.select_related("user").order_by(
            "user__first_name", "user__last_name"
        )

        members_data = []
        for profile in profiles:
            user = profile.user
            survey_progress = [
                _progress_entry(
                    assignment,
                    modules_map[assignment.id],
                    total_questions_map[assignment.id],
                    answers_map.get((user.id, assignment.id), {}),
                    submission_status_map.get((user.id, assignment.id), "not_started"),
                )
                for assignment in assignments
            ]
            members_data.append(
                {
                    "profile": profile,
                    "is_self": profile.user_id == request.user.id,
                    "survey_progress": survey_progress,
                }
            )

        members_data.sort(key=lambda m: (not m["is_self"],))

        return render(
            request,
            "core/employee_list.html",
            {
                "company": company,
                "is_admin_view": reference_code is not None,
                "members": members_data,
            },
        )


class EmployeeDetailView(LoginRequiredMixin, View):
    """Detail view for a single employee: progress, answers, and insights."""

    def get(self, request, employee_id, reference_code=None):
        if not request.user.has_perm("accounts.can_manage_employees"):
            raise PermissionDenied

        if reference_code is not None:
            if not request.user.has_perm("accounts.can_manage_surveys"):
                raise PermissionDenied
            company = get_object_or_404(Company, reference_code=reference_code)
        else:
            try:
                profile = request.user.profile
            except UserProfile.DoesNotExist:
                return redirect("accounts:setup_profile")
            if not profile.company_id:
                return redirect("accounts:setup_profile")
            company = profile.company

        employee_profile = get_object_or_404(
            UserProfile.objects.select_related("user"),
            user_id=employee_id,
            company=company,
        )
        employee_user = employee_profile.user

        assignments = list(
            SurveyAssignment.objects.filter(company=company)
            .select_related("survey")
            .order_by("-created_at")
        )

        # Fetch all submissions for this employee in one query; prefetch answers.
        submissions_qs = SurveySubmission.objects.filter(
            assignment__in=assignments, user=employee_user
        ).prefetch_related("answers")
        submissions_by_aid = {s.assignment_id: s for s in submissions_qs}
        answers_by_aid = {
            aid: {a.question_id: a for a in submission.answers.all()}
            for aid, submission in submissions_by_aid.items()
        }

        # One module prefetch per assignment, shared by progress and answers.
        modules_map = {
            a.id: list(a.modules_for_variant().prefetch_related("questions__choices"))
            for a in assignments
        }

        # Progress rings (always visible to can_manage_employees users).
        total_questions_map = {a.id: _variant_question_count(a) for a in assignments}
        survey_progress = []
        for assignment in assignments:
            submission = submissions_by_aid.get(assignment.id)
            values_by_qid = {
                qid: answer.value
                for qid, answer in answers_by_aid.get(assignment.id, {}).items()
            }
            survey_progress.append(
                _progress_entry(
                    assignment,
                    modules_map[assignment.id],
                    total_questions_map[assignment.id],
                    values_by_qid,
                    submission.status if submission else "not_started",
                )
            )

        # Full answers breakdown (only for can_view_submissions).
        submissions_data = None
        if request.user.has_perm("accounts.can_view_submissions"):
            submissions_data = []
            for assignment in assignments:
                answers_by_qid = answers_by_aid.get(assignment.id, {})

                modules_with_answers = [
                    {
                        "module": module,
                        "items": [
                            {"question": q, "answer": answers_by_qid.get(q.id)}
                            for q in module.questions.all()
                        ],
                    }
                    for module in modules_map[assignment.id]
                ]

                submissions_data.append(
                    {
                        "assignment": assignment,
                        "submission": submissions_by_aid.get(assignment.id),
                        "modules": modules_with_answers,
                    }
                )

        valuation = None
        if request.user.has_perm("accounts.can_view_insights"):
            from apps.nom035.aggregates import employee_valuation

            valuation = employee_valuation(employee_user, company)

        return render(
            request,
            "core/employee_detail.html",
            {
                "company": company,
                "is_admin_view": reference_code is not None,
                "employee_profile": employee_profile,
                "survey_progress": survey_progress,
                "submissions_data": submissions_data,
                "valuation": valuation,
                "container_width": "max-w-6xl",
            },
        )
