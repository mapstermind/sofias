from django.urls import path

from . import views

app_name = "surveys"
urlpatterns = [
    path("asignados/<int:assignment_id>/", views.survey_detail, name="survey_detail"),
    path("asignados/<int:assignment_id>/autoguardar/", views.autosave_survey, name="autosave_survey"),
    path("asignados/<int:assignment_id>/enviada/", views.survey_submitted, name="survey_submitted"),
]
