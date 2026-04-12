from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied
from django.db.models import Count, Q
from django.shortcuts import get_object_or_404, redirect, render
from django.views import View

from apps.accounts.models import Company, UserProfile
from apps.responses.models import SurveySubmission
from apps.surveys.models import SurveyAssignment


class HomeView(LoginRequiredMixin, View):
    def get(self, request):
        user = request.user
        if user.groups.filter(name="Employees").exists():
            return redirect("core:employee_survey_list")
        if user.groups.filter(name="Admins").exists():
            return redirect("core:company_list")
        if user.has_perm("accounts.can_view_dashboard"):
            return redirect("core:company_dashboard")
        return redirect("accounts:request_otp")


class EmployeeSurveyListView(LoginRequiredMixin, View):
    """List surveys assigned to the employee's company."""

    def get(self, request):
        if not request.user.groups.filter(name="Employees").exists():
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

        companies = (
            Company.objects.annotate(
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
            )
            .order_by("name")
        )

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
        registration_rate = (
            round(member_count / expected * 100) if expected else None
        )

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
