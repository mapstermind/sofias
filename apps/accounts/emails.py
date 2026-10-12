from django.conf import settings
from django.core.mail import send_mail


def send_otp_email(email: str, code: str) -> None:
    """
    Send a one-time login code to the given email address.

    Raises smtplib.SMTPException (or subclasses) on delivery failure —
    callers are responsible for catching and handling the error.
    """
    brand = settings.BRAND["name"]
    expiry = getattr(settings, "OTP_EXPIRY_MINUTES", 10)
    body = (
        f"Tu código de inicio de sesión en {brand} es: {code}\n\n"
        f"Vence en {expiry} minuto{'s' if expiry != 1 else ''}.\n\n"
        "Si no lo pediste, ignora este correo: nadie puede entrar a tu cuenta "
        "sin el código."
    )
    send_mail(
        subject=f"Tu código para iniciar sesión en {brand}",
        message=body,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[email],
        fail_silently=False,
    )
