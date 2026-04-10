from django.conf import settings
from django.core.mail import send_mail


def send_otp_email(email: str, code: str) -> None:
    """
    Send a one-time login code to the given email address.

    Raises smtplib.SMTPException (or subclasses) on delivery failure —
    callers are responsible for catching and handling the error.
    """
    expiry = getattr(settings, "OTP_EXPIRY_MINUTES", 10)
    body = (
        f"Your one-time login code is: {code}\n\n"
        f"This code expires in {expiry} minute{'s' if expiry != 1 else ''}.\n\n"
        "If you didn't request this code, you can safely ignore this email."
    )
    send_mail(
        subject="Your login code",
        message=body,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[email],
        fail_silently=False,
    )
