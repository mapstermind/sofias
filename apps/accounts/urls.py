from django.urls import path

from . import views

app_name = "accounts"

urlpatterns = [
    path("ingresar/", views.request_otp, name="request_otp"),
    path("ingresar-con-contrasena/", views.password_login, name="password_login"),
    path("verificar/", views.verify_otp, name="verify_otp"),
    path("cambiar-contrasena/", views.change_password, name="change_password"),
    path("completar-perfil/", views.setup_profile, name="setup_profile"),
    path("cerrar-sesion/", views.logout_view, name="logout"),
]
