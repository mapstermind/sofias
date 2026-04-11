from django.urls import path

from . import views

app_name = "core"

urlpatterns = [
    path("", views.HomeView.as_view(), name="home"),
    path("tablero-empresa/", views.CompanyDashboardView.as_view(), name="company_dashboard"),
    path("encuestas/", views.EmployeeSurveyListView.as_view(), name="employee_survey_list"),
    path("empresas/", views.CompanyListView.as_view(), name="company_list"),
    path("empresas/<str:reference_code>/", views.CompanyDashboardView.as_view(), name="company_dashboard_for"),
]
