from django.urls import path

from . import views

app_name = "accounts"

urlpatterns = [
    path("ingresar/", views.request_otp, name="request_otp"),
    path("verificar/", views.verify_otp, name="verify_otp"),
    path("completar-perfil/", views.setup_profile, name="setup_profile"),
    path("cerrar-sesion/", views.logout_view, name="logout"),
]
