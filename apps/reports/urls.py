from django.urls import path

from . import views

app_name = "reports"

_ADMIN = "empresas/<str:reference_code>/reportes/"

urlpatterns = [
    path(_ADMIN, views.AdminReportListView.as_view(), name="admin_list"),
    path(f"{_ADMIN}<int:assignment_id>/", views.AdminReportDetailView.as_view(), name="admin_detail"),
    path(f"{_ADMIN}<int:assignment_id>/editar/", views.AdminReportEditView.as_view(), name="admin_edit"),
    path(f"{_ADMIN}<int:assignment_id>/publicar/", views.AdminPublishView.as_view(), name="admin_publish"),
    path(f"{_ADMIN}<int:assignment_id>/despublicar/", views.AdminUnpublishView.as_view(), name="admin_unpublish"),
]
