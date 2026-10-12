"""Copy that reaches a person outside a template: the sign-in email."""

from django.core import mail

from apps.accounts.emails import send_otp_email


def test_the_login_email_is_spanish_and_names_the_product(settings):
    send_otp_email("a@x.mx", "123456")
    msg = mail.outbox[-1]
    brand = settings.BRAND["name"]
    assert msg.subject == f"Tu código para iniciar sesión en {brand}"
    assert f"Tu código de inicio de sesión en {brand} es: 123456" in msg.body
    assert "Vence en" in msg.body
    assert "code" not in msg.body.replace("código", "")
