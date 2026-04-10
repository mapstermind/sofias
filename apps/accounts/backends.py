from apps.accounts.models import User


class EmailOTPBackend:
    """
    Minimal auth backend for passwordless OTP login.

    OTP validation is handled in the view. This backend exists solely so
    Django's login() can record which backend authenticated the user.
    ModelBackend (listed first in AUTHENTICATION_BACKENDS) keeps the
    admin username+password flow working independently.
    """

    def authenticate(self, request, **kwargs):
        # Authentication logic lives in the view, not here.
        return None

    def get_user(self, user_id):
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None
