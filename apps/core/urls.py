from django.urls import path
from django.views.generic import TemplateView

from . import views

app_name = "core"

urlpatterns = [
    path("", views.HomeView.as_view(), name="home"),
    path("tablero-empresa/", views.CompanyDashboardView.as_view(), name="company_dashboard"),
    path("encuestas/", views.EmployeeSurveyListView.as_view(), name="employee_survey_list"),
    path("empresas/", views.CompanyListView.as_view(), name="company_list"),
    path("empresas/<str:reference_code>/", views.CompanyDashboardView.as_view(), name="company_dashboard_for"),
    path("tablero-empresa/empleados/", views.CompanyEmployeeListView.as_view(), name="company_employee_list"),
    path("empresas/<str:reference_code>/empleados/", views.CompanyEmployeeListView.as_view(), name="company_employee_list_for"),
    path("que-es-sofia/", TemplateView.as_view(template_name="core/about.html"), name="about"),
]
