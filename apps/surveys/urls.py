from django.urls import path

from . import views

app_name = "surveys"
urlpatterns = [
    path("assignments/<int:assignment_id>/", views.survey_detail, name="survey_detail"),
    path("assignments/<int:assignment_id>/submitted/", views.survey_submitted, name="survey_submitted"),
]
