from django.conf import settings
from django.shortcuts import redirect
from django.urls import reverse


class RequirePasswordChangeMiddleware:
    """Keep temporary-password users on the password-change flow."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        user = request.user
        if (
            user.is_authenticated
            and getattr(user, "must_change_password", False)
            and not self._is_allowed_path(request.path)
        ):
            return redirect("accounts:change_password")

        return self.get_response(request)

    def _is_allowed_path(self, path):
        allowed_paths = {
            reverse("accounts:change_password"),
            reverse("accounts:logout"),
        }
        static_url = settings.STATIC_URL
        if not static_url.startswith("/"):
            static_url = f"/{static_url}"

        return (
            path in allowed_paths
            or path.startswith(static_url)
            or path.startswith("/admin/")
        )
