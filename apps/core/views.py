from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied
from django.db.models import Count, Q
from django.shortcuts import get_object_or_404, redirect, render
from django.views import View

from apps.accounts.models import Company, UserProfile
from apps.responses.models import Answer, SurveySubmission
from apps.surveys.models import SurveyAssignment, Question


class HomeView(LoginRequiredMixin, View):
    def get(self, request):
        user = request.user
        if user.groups.filter(name="Admins").exists():
            return redirect("core:company_list")
        if user.has_perm("accounts.can_take_assigned_surveys"):
            return redirect("core:employee_survey_list")
        if user.has_perm("accounts.can_view_dashboard"):
            return redirect("core:company_dashboard")
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
            .select_related("version__template")
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

        expected = company.expected_employee_count
        registration_rate = round(member_count / expected * 100) if expected else None

        assignments = (
            SurveyAssignment.objects.filter(company=company)
            .select_related("version__template")
            .annotate(
                completed_count=Count(
                    "submissions",
                    filter=Q(submissions__status=SurveySubmission.Status.COMPLETED),
                )
            )
            .order_by("-created_at")
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
                }
            )

        return render(
            request,
            "core/company_dashboard.html",
            {
                "company": company,
                "member_count": member_count,
                "expected_employee_count": expected,
                "registration_rate": registration_rate,
                "assignment_data": assignment_data,
                "is_admin_view": reference_code is not None,
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
            .select_related("version__template")
            .order_by("-created_at")
        )

        # Pre-fetch total question counts per assignment to avoid N+1
        total_questions_map = {
            a.id: a.version.questions.count() for a in assignments
        }

        # Pre-fetch all answers for this company's assignments in one query
        answered_map: dict[tuple[int, int], int] = {}
        answer_qs = (
            Answer.objects.filter(submission__assignment__in=assignments)
            .values("submission__user_id", "submission__assignment_id")
            .annotate(count=Count("id"))
        )
        for row in answer_qs:
            answered_map[(row["submission__user_id"], row["submission__assignment_id"])] = row["count"]

        # Pre-fetch submission statuses per (user, assignment)
        submission_status_map: dict[tuple[int, int], str] = {}
        for sub in SurveySubmission.objects.filter(assignment__in=assignments).values(
            "user_id", "assignment_id", "status"
        ):
            submission_status_map[(sub["user_id"], sub["assignment_id"])] = sub["status"]

        profiles = company.members.select_related("user").order_by(
            "user__first_name", "user__last_name"
        )

        members_data = []
        for profile in profiles:
            user = profile.user
            is_employee = user.groups.filter(name="Employees").exists()

            if is_employee:
                survey_progress = []
                for assignment in assignments:
                    total = total_questions_map[assignment.id]
                    answered = answered_map.get((user.id, assignment.id), 0)
                    percent = round(answered / total * 100) if total > 0 else 0
                    status = submission_status_map.get((user.id, assignment.id), "not_started")
                    survey_progress.append(
                        {
                            "assignment": assignment,
                            "answered": answered,
                            "total": total,
                            "percent": percent,
                            "status": status,
                        }
                    )
                members_data.append(
                    {
                        "profile": profile,
                        "has_surveys": True,
                        "survey_progress": survey_progress,
                    }
                )
            else:
                members_data.append(
                    {
                        "profile": profile,
                        "has_surveys": False,
                        "survey_progress": [],
                    }
                )

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
            .select_related("version__template")
            .order_by("-created_at")
        )

        # Fetch all submissions for this employee in one query; prefetch answers.
        submissions_qs = SurveySubmission.objects.filter(
            assignment__in=assignments, user=employee_user
        ).prefetch_related("answers")
        submissions_by_aid = {s.assignment_id: s for s in submissions_qs}

        # Progress bars (always visible to can_manage_employees users).
        total_questions_map = {a.id: a.version.questions.count() for a in assignments}
        survey_progress = []
        for assignment in assignments:
            submission = submissions_by_aid.get(assignment.id)
            total = total_questions_map[assignment.id]
            answered = submission.answers.count() if submission else 0
            percent = round(answered / total * 100) if total > 0 else 0
            status = submission.status if submission else "not_started"
            survey_progress.append(
                {
                    "assignment": assignment,
                    "answered": answered,
                    "total": total,
                    "percent": percent,
                    "status": status,
                }
            )

        # Full answers breakdown (only for can_view_submissions).
        submissions_data = None
        if request.user.has_perm("accounts.can_view_submissions"):
            submissions_data = []
            for assignment in assignments:
                submission = submissions_by_aid.get(assignment.id)
                answers_by_qid = (
                    {a.question_id: a for a in submission.answers.all()}
                    if submission
                    else {}
                )

                sections = list(
                    assignment.version.sections.prefetch_related(
                        "questions__choices"
                    ).order_by("order")
                )
                unsectioned = list(
                    assignment.version.questions.filter(section__isnull=True)
                    .prefetch_related("choices")
                    .order_by("order")
                )

                sections_with_answers = [
                    {
                        "section": section,
                        "items": [
                            {"question": q, "answer": answers_by_qid.get(q.id)}
                            for q in section.questions.all()
                        ],
                    }
                    for section in sections
                ]
                unsectioned_with_answers = [
                    {"question": q, "answer": answers_by_qid.get(q.id)}
                    for q in unsectioned
                ]

                submissions_data.append(
                    {
                        "assignment": assignment,
                        "submission": submission,
                        "sections": sections_with_answers,
                        "unsectioned": unsectioned_with_answers,
                    }
                )

        return render(
            request,
            "core/employee_detail.html",
            {
                "company": company,
                "is_admin_view": reference_code is not None,
                "employee_profile": employee_profile,
                "survey_progress": survey_progress,
                "submissions_data": submissions_data,
            },
        )
