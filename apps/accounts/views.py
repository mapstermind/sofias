import secrets
from smtplib import SMTPException

from django.conf import settings
from django.contrib.auth import login, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.http import HttpResponseNotAllowed
from django.shortcuts import redirect, render
from django.utils import timezone

from apps.accounts.emails import send_otp_email
from apps.accounts.forms import (
    EmailPasswordLoginForm,
    EmailRequestForm,
    OTPVerifyForm,
    ProfileActivationForm,
    RequiredPasswordChangeForm,
)
from apps.accounts.models import EmailOTP, User, UserProfile

_RATE_LIMIT_SECONDS = 30


def _redirect_after_login(user):
    if user.must_change_password:
        return redirect("accounts:change_password")

    if user.groups.filter(name="Admins").exists():
        return redirect(settings.LOGIN_REDIRECT_URL)

    try:
        profile = user.profile
    except UserProfile.DoesNotExist:
        return redirect("accounts:setup_profile")

    if not profile.is_activated:
        return redirect("accounts:setup_profile")
    return redirect(settings.LOGIN_REDIRECT_URL)


def request_otp(request):
    """Step 1 — user enters their email and receives a 6-digit code."""
    if request.user.is_authenticated:
        return redirect(settings.LOGIN_REDIRECT_URL)

    if request.method == "GET":
        return render(
            request, "accounts/login_request.html", {"form": EmailRequestForm()}
        )

    form = EmailRequestForm(request.POST)
    if not form.is_valid():
        return render(request, "accounts/login_request.html", {"form": form})

    email = form.cleaned_data["email"].lower()

    # Rate limit: one OTP per email per _RATE_LIMIT_SECONDS seconds.
    cutoff = timezone.now() - timezone.timedelta(seconds=_RATE_LIMIT_SECONDS)
    if EmailOTP.objects.filter(email=email, created_at__gte=cutoff).exists():
        form.add_error(
            None,
            f"Un código fue enviado recientemente. Por favor, espera {_RATE_LIMIT_SECONDS} segundos antes de solicitar uno nuevo.",
        )
        return render(request, "accounts/login_request.html", {"form": form})

    if not User.objects.filter(email=email).exists():
        form.add_error(
            None,
            "No se encontró una cuenta con este correo electrónico. Si esto es un error, por favor contacta a tu administrador.",
        )
        return render(request, "accounts/login_request.html", {"form": form})

    # Invalidate any previous unused OTPs for this email.
    EmailOTP.objects.filter(email=email, is_used=False).delete()

    code = f"{secrets.randbelow(1_000_000):06d}"
    otp = EmailOTP.objects.create(email=email, code=code)

    try:
        send_otp_email(email, code)
    except SMTPException:
        otp.delete()
        form.add_error(
            None, "No pudimos enviar el correo. Por favor, intenta de nuevo."
        )
        return render(request, "accounts/login_request.html", {"form": form})

    request.session["otp_email"] = email
    return redirect("accounts:verify_otp")


def password_login(request):
    """Fallback login for pre-created users with password auth enabled."""
    if request.user.is_authenticated:
        return redirect(settings.LOGIN_REDIRECT_URL)

    if request.method == "GET":
        return render(
            request,
            "accounts/login_password.html",
            {"form": EmailPasswordLoginForm()},
        )

    form = EmailPasswordLoginForm(request.POST)
    if not form.is_valid():
        return render(request, "accounts/login_password.html", {"form": form})

    user = form.cleaned_data["user"]
    login(request, user, backend="django.contrib.auth.backends.ModelBackend")
    return _redirect_after_login(user)


def verify_otp(request):
    """Step 2 — user enters the 6-digit code; account is created if needed."""
    if request.user.is_authenticated:
        return redirect(settings.LOGIN_REDIRECT_URL)

    email = request.session.get("otp_email")
    if not email:
        return redirect("accounts:request_otp")

    if request.method == "GET":
        form = OTPVerifyForm(initial={"email": email})
        return render(
            request, "accounts/login_verify.html", {"form": form, "email": email}
        )

    form = OTPVerifyForm(request.POST)
    if not form.is_valid():
        return render(
            request, "accounts/login_verify.html", {"form": form, "email": email}
        )

    submitted_email = form.cleaned_data["email"].lower()
    code = form.cleaned_data["code"]

    dev_bypass = settings.DEBUG and code == "000000"

    with transaction.atomic():
        if not dev_bypass:
            otp = (
                EmailOTP.objects.select_for_update()
                .filter(email=submitted_email, code=code, is_used=False)
                .first()
            )

            if otp is None or not otp.is_valid():
                form.add_error(None, "El código es inválido o ha expirado.")
                return render(
                    request,
                    "accounts/login_verify.html",
                    {"form": form, "email": email},
                )

        user = User.objects.get(email=submitted_email)

        if not dev_bypass:
            otp.is_used = True
            otp.save(update_fields=["is_used"])

    login(request, user, backend="apps.accounts.backends.EmailOTPBackend")

    try:
        del request.session["otp_email"]
    except KeyError:
        pass

    return _redirect_after_login(user)


@login_required
def change_password(request):
    """Required password change for users who received a temporary password."""
    if not request.user.must_change_password:
        return _redirect_after_login(request.user)

    if request.method == "GET":
        return render(
            request,
            "accounts/change_password.html",
            {"form": RequiredPasswordChangeForm(request.user)},
        )

    form = RequiredPasswordChangeForm(request.user, request.POST)
    if not form.is_valid():
        return render(request, "accounts/change_password.html", {"form": form})

    form.save()
    update_session_auth_hash(request, request.user)
    return _redirect_after_login(request.user)


@login_required
def setup_profile(request):
    """First-login activation — user confirms their company reference code."""
    if request.user.groups.filter(name="Admins").exists():
        return redirect(settings.LOGIN_REDIRECT_URL)

    try:
        profile = request.user.profile
    except UserProfile.DoesNotExist:
        return render(
            request,
            "accounts/profile_setup.html",
            {"form": ProfileActivationForm(), "no_profile": True},
        )

    if profile.is_activated:
        return redirect(settings.LOGIN_REDIRECT_URL)

    if profile.company is None:
        return render(
            request,
            "accounts/profile_setup.html",
            {"form": ProfileActivationForm(), "no_company": True},
        )

    if request.method == "GET":
        return render(
            request, "accounts/profile_setup.html", {"form": ProfileActivationForm()}
        )

    form = ProfileActivationForm(request.POST)
    if not form.is_valid():
        return render(request, "accounts/profile_setup.html", {"form": form})

    reference_code = form.cleaned_data["reference_code"]
    if reference_code != profile.company.reference_code:
        form.add_error(
            "reference_code",
            "El código no coincide con tu empresa asignada. Por favor, verifica con tu administrador.",
        )
        return render(request, "accounts/profile_setup.html", {"form": form})

    profile.is_activated = True
    profile.save(update_fields=["is_activated"])

    return redirect(settings.LOGIN_REDIRECT_URL)


def logout_view(request):
    """POST-only logout to prevent CSRF-free session termination via GET."""
    if request.method != "POST":
        return HttpResponseNotAllowed(["POST"])
    logout(request)
    return redirect("accounts:request_otp")
