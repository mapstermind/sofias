import secrets
from smtplib import SMTPException

from django.conf import settings
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import Group
from django.db import transaction
from django.http import HttpResponseNotAllowed
from django.shortcuts import redirect, render
from django.utils import timezone

from apps.accounts.emails import send_otp_email
from apps.accounts.forms import EmailRequestForm, OTPVerifyForm, ProfileSetupForm
from apps.accounts.models import Company, EmailOTP, User, UserProfile
from apps.accounts.utils import generate_unique_username

_RATE_LIMIT_SECONDS = 30


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

    # Rate limit: one OTP per email per 60 seconds.
    cutoff = timezone.now() - timezone.timedelta(seconds=_RATE_LIMIT_SECONDS)
    if EmailOTP.objects.filter(email=email, created_at__gte=cutoff).exists():
        form.add_error(
            None,
            f"Un código fue enviado recientemente. Por favor, espera {_RATE_LIMIT_SECONDS} segundos antes de solicitar uno nuevo.",
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

    with transaction.atomic():
        otp = (
            EmailOTP.objects.select_for_update()
            .filter(email=submitted_email, code=code, is_used=False)
            .first()
        )

        if otp is None or not otp.is_valid():
            form.add_error(None, "El código es inválido o ha expirado.")
            return render(
                request, "accounts/login_verify.html", {"form": form, "email": email}
            )

        otp.is_used = True
        otp.save(update_fields=["is_used"])

        user = User.objects.filter(email=submitted_email).first()
        if user is None:
            user = User(
                username=generate_unique_username(submitted_email),
                email=submitted_email,
            )
            user.set_unusable_password()
            user.save()
            user.groups.add(Group.objects.get(name="Employees"))

        profile, _ = UserProfile.objects.get_or_create(user=user)

    login(request, user, backend="apps.accounts.backends.EmailOTPBackend")

    try:
        del request.session["otp_email"]
    except KeyError:
        pass

    if user.groups.filter(name="Admins").exists():
        return redirect(settings.LOGIN_REDIRECT_URL)

    profile_complete = bool(profile.position and profile.company_id)
    if not profile_complete:
        return redirect("accounts:setup_profile")
    return redirect(settings.LOGIN_REDIRECT_URL)


@login_required
def setup_profile(request):
    """Step 3 (first login only) — user sets their position and company reference code."""
    if request.user.groups.filter(name="Admins").exists():
        return redirect(settings.LOGIN_REDIRECT_URL)

    profile, _ = UserProfile.objects.get_or_create(user=request.user)

    if profile.position and profile.company_id:
        return redirect(settings.LOGIN_REDIRECT_URL)

    if request.method == "GET":
        return render(
            request, "accounts/profile_setup.html", {"form": ProfileSetupForm()}
        )

    form = ProfileSetupForm(request.POST)
    if not form.is_valid():
        return render(request, "accounts/profile_setup.html", {"form": form})

    reference_code = form.cleaned_data["reference_code"]
    company = Company.objects.filter(reference_code=reference_code).first()
    if company is None:
        form.add_error(
            "reference_code",
            "No se encontró una empresa con ese código. Por favor, verifica con tu administrador.",
        )
        return render(request, "accounts/profile_setup.html", {"form": form})

    user = request.user
    user.first_name = form.cleaned_data["first_name"]
    user.last_name = form.cleaned_data["last_name"]
    user.save(update_fields=["first_name", "last_name"])

    profile.position = form.cleaned_data["position"]
    profile.company = company
    profile.save()

    return redirect(settings.LOGIN_REDIRECT_URL)


def logout_view(request):
    """POST-only logout to prevent CSRF-free session termination via GET."""
    if request.method != "POST":
        return HttpResponseNotAllowed(["POST"])
    logout(request)
    return redirect("accounts:request_otp")
