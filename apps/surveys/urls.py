from django.urls import path

from . import views

app_name = "surveys"
urlpatterns = [
    path("<int:survey_id>/", views.survey_detail, name="survey_detail"),
    path("<int:survey_id>/submitted/", views.survey_submitted, name="survey_submitted"),
]
