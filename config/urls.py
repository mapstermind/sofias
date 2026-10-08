"""
URL configuration for config project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.conf import settings
from django.contrib import admin
from django.urls import include, path

# Django's default chrome names the framework; operators should see the product.
admin.site.site_header = f"Administración {settings.BRAND['name']}"
admin.site.site_title = settings.BRAND["name"]
admin.site.index_title = "Panel de administración"

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include(("apps.core.urls", "core"))),
    path("", include(("apps.reports.urls", "reports"))),
    path("cuentas/", include(("apps.accounts.urls", "accounts"))),
    path("encuestas/", include(("apps.surveys.urls", "surveys"))),
]
