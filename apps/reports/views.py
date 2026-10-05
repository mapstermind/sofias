"""Report pages: Administrador (any company) and Ejecutivo principal (own company)."""

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views import View

from apps.accounts.models import Company
from apps.nom035.results import NOM035_SURVEY_KEY, assignment_options
from apps.reports import publishing
from apps.reports.forms import ReportForm, SignatoryFormSet
from apps.reports.models import Report
from apps.reports.sections import context_for, render_sections
from apps.surveys.models import SurveyAssignment


class AdminMixin(LoginRequiredMixin):
    def dispatch(self, request, *args, **kwargs):
        user = request.user
        if user.is_authenticated and not (
            user.has_perm("accounts.can_manage_surveys")
            and user.has_perm("accounts.can_view_insights")
        ):
            raise PermissionDenied
        return super().dispatch(request, *args, **kwargs)

    def company(self):
        return get_object_or_404(Company, reference_code=self.kwargs["reference_code"])

    def assignment(self):
        return get_object_or_404(
            SurveyAssignment.objects.select_related("company"),
            pk=self.kwargs["assignment_id"],
            company__reference_code=self.kwargs["reference_code"],
            survey__key=NOM035_SURVEY_KEY,
        )

    def report(self, assignment):
        return Report.objects.filter(assignment=assignment).first() or Report(
            assignment=assignment
        )


class AdminReportListView(AdminMixin, View):
    def get(self, request, reference_code):
        company = self.company()
        reports = {
            r.assignment_id: r
            for r in Report.objects.filter(assignment__company=company)
        }
        rows = [
            {"option": o, "report": reports.get(o.assignment.pk)}
            for o in assignment_options(company)
        ]
        return render(
            request,
            "reports/report_list.html",
            {"company": company, "rows": rows, "is_admin_view": True},
        )


class AdminReportDetailView(AdminMixin, View):
    def get(self, request, reference_code, assignment_id):
        assignment = self.assignment()
        report = self.report(assignment)
        ctx = context_for(report)
        return render(
            request,
            "reports/report_detail.html",
            {
                "company": assignment.company,
                "report": report,
                "ctx": ctx,
                "sections": render_sections(ctx),
                "blockers": publishing.blockers(report)
                if report.status == Report.Status.DRAFT
                else [],
                "is_admin_view": True,
            },
        )


class AdminReportEditView(AdminMixin, View):
    template_name = "reports/report_form.html"

    def _locked(self, report):
        if report.status == Report.Status.PUBLISHED:
            messages.error(self.request, "Despublica el reporte para editarlo.")
            return redirect(self._detail_url())
        return None

    def _detail_url(self):
        return reverse(
            "reports:admin_detail",
            args=[self.kwargs["reference_code"], self.kwargs["assignment_id"]],
        )

    def _previous(self, assignment):
        return (
            Report.objects.filter(assignment__company=assignment.company)
            .exclude(assignment=assignment)
            .order_by("-created_at")
            .first()
        )

    def get(self, request, reference_code, assignment_id):
        assignment = self.assignment()
        report = self.report(assignment)
        if (locked := self._locked(report)) is not None:
            return locked
        initial, sig_initial = {}, []
        if report.pk is None and (prev := self._previous(assignment)) is not None:
            initial = {
                "evaluator_name": prev.evaluator_name,
                "evaluator_license": prev.evaluator_license,
            }
            sig_initial = [
                {"title": s.title, "name": s.name} for s in prev.signatories.all()
            ]
        form = ReportForm(instance=report, initial=initial)
        formset = SignatoryFormSet(
            instance=report, prefix="signatories", initial=sig_initial
        )
        formset.extra = len(sig_initial) + 1  # always one blank row
        return render(
            request,
            self.template_name,
            {
                "form": form,
                "formset": formset,
                "company": assignment.company,
                "report": report,
                "is_admin_view": True,
            },
        )

    def post(self, request, reference_code, assignment_id):
        assignment = self.assignment()
        report = self.report(assignment)
        if (locked := self._locked(report)) is not None:
            return locked
        form = ReportForm(request.POST, instance=report)
        formset = SignatoryFormSet(request.POST, instance=report, prefix="signatories")
        if form.is_valid() and formset.is_valid():
            report = form.save()
            formset.instance = report
            formset.save()  # see forms.py for ORDER → order
            messages.success(request, "Reporte guardado.")
            return redirect(self._detail_url())
        return render(
            request,
            self.template_name,
            {
                "form": form,
                "formset": formset,
                "company": assignment.company,
                "report": report,
                "is_admin_view": True,
            },
        )


class AdminPublishView(AdminMixin, View):
    def post(self, request, reference_code, assignment_id):
        report = self.report(self.assignment())
        if report.pk is None:
            problems = publishing.blockers(report)
        else:
            problems = publishing.publish(report, request.user)
        if problems:
            for p in problems:
                messages.error(request, p)
        else:
            messages.success(request, "Reporte publicado.")
        return redirect("reports:admin_detail", reference_code, assignment_id)


class AdminUnpublishView(AdminMixin, View):
    def post(self, request, reference_code, assignment_id):
        report = self.report(self.assignment())
        if report.pk is not None and report.status == Report.Status.PUBLISHED:
            publishing.unpublish(report)
            messages.success(request, "Reporte despublicado.")
        return redirect("reports:admin_detail", reference_code, assignment_id)


class ExecutiveMixin(LoginRequiredMixin):
    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated and not request.user.has_perm(
            "accounts.can_view_insights"
        ):
            raise PermissionDenied
        return super().dispatch(request, *args, **kwargs)

    def own_company(self):
        profile = getattr(self.request.user, "profile", None)
        return profile.company if profile is not None and profile.company_id else None

    def published(self, company):
        return get_object_or_404(
            Report.objects.select_related("assignment__company"),
            assignment_id=self.kwargs["assignment_id"],
            assignment__company=company,
            assignment__survey__key=NOM035_SURVEY_KEY,
            status=Report.Status.PUBLISHED,
        )


class ExecutiveReportListView(ExecutiveMixin, View):
    def get(self, request):
        company = self.own_company()
        if company is None:
            return redirect("accounts:setup_profile")
        published = {
            r.assignment_id: r
            for r in Report.objects.filter(
                assignment__company=company, status=Report.Status.PUBLISHED
            )
        }
        rows = [
            {"option": o, "report": published[o.assignment.pk]}
            for o in assignment_options(company)
            if o.assignment.pk in published
        ]
        return render(
            request,
            "reports/report_list.html",
            {"company": company, "rows": rows, "is_admin_view": False},
        )


class ExecutiveReportDetailView(ExecutiveMixin, View):
    def get(self, request, assignment_id):
        company = self.own_company()
        if company is None:
            return redirect("accounts:setup_profile")
        report = self.published(company)
        ctx = context_for(report)
        return render(
            request,
            "reports/report_detail.html",
            {
                "company": company,
                "report": report,
                "ctx": ctx,
                "sections": render_sections(ctx),
                "blockers": [],
                "is_admin_view": False,
            },
        )
