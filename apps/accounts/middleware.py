from django.conf import settings
from django.shortcuts import redirect
from django.urls import reverse


class RequireProfileActivationMiddleware:
    """Keep users who have not activated their profile on the activation flow.

    Activation is where an employee supplies their nombre, cargo, área and
    localidad. Routing them there at login is not enough on its own — a user can
    navigate away and reach the rest of the app with `is_activated=False`, and
    every survey they answer then scores with `area=None` and lands in the "Sin
    área" bucket. That is precisely the unfixable pile
    `docs/adr/adr-0004-per-company-area-and-locality-catalogs.md` chose to block
    activation over, so the gate has to hold on every request, not just the
    first one.

    Ordered after `RequirePasswordChangeMiddleware`, which owns the earlier step;
    the password-change URL is allowed through so the two do not fight.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        user = request.user
        if (
            user.is_authenticated
            and not self._is_allowed_path(request.path)
            and self._needs_activation(user)
        ):
            return redirect("accounts:setup_profile")

        return self.get_response(request)

    def _needs_activation(self, user):
        # `has_perm` answers True for every permission on a superuser, so it
        # cannot tell a root account from a respondent. Superusers are operators
        # by definition and never activate; without this they are locked out of
        # the whole front end, since they also have no profile to activate.
        if user.is_superuser:
            return False

        # Keyed on who *answers* surveys, which is exactly who the gate protects
        # against: only a respondent can create the unattributed submission this
        # exists to prevent. Operators hold no `can_take_assigned_surveys`, so
        # they fall out here without needing an admin carve-out — and without
        # needing a profile at all.
        if not user.has_perm("accounts.can_take_assigned_surveys"):
            return False

        # getattr covers a missing profile row, since RelatedObjectDoesNotExist
        # subclasses AttributeError. Django caches the related object on the
        # user, so an activated employee costs one query per request at most.
        profile = getattr(user, "profile", None)
        return profile is None or not profile.is_activated

    def _is_allowed_path(self, path):
        allowed_paths = {
            reverse("accounts:setup_profile"),
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


class RequirePasswordChangeMiddleware:
    """Keep users who must create/change a password on the password-change flow."""

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
