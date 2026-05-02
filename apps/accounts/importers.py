import csv
import io
from dataclasses import dataclass

from django.contrib.auth.models import Group
from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from django.db import transaction
from django.utils.crypto import get_random_string

from apps.accounts.models import Company, User, UserProfile
from apps.accounts.utils import generate_unique_username

REQUIRED_HEADERS = {"email", "company_reference_code", "group", "auth_method"}
OPTIONAL_HEADERS = {"first_name", "last_name", "position"}
REPORT_HEADERS = [
    "row_number",
    "email",
    "status",
    "message",
    "username",
    "temporary_password",
]


@dataclass
class ImportResult:
    rows: list[dict[str, str]]
    created_count: int
    skipped_count: int


def import_users_from_csv(csv_text: str) -> ImportResult:
    reader = csv.DictReader(io.StringIO(csv_text))
    if reader.fieldnames is None:
        raise ValueError("El archivo CSV está vacío.")

    normalized_headers = [header.strip() for header in reader.fieldnames]
    missing_headers = REQUIRED_HEADERS - set(normalized_headers)
    if missing_headers:
        missing = ", ".join(sorted(missing_headers))
        raise ValueError(f"Faltan columnas requeridas: {missing}.")

    reader.fieldnames = normalized_headers

    report_rows = []
    created_count = 0
    skipped_count = 0

    for row_number, row in enumerate(reader, start=2):
        normalized_row = _normalize_row(row)
        report_row = _import_row(row_number, normalized_row)
        report_rows.append(report_row)

        if report_row["status"] == "created":
            created_count += 1
        else:
            skipped_count += 1

    return ImportResult(
        rows=report_rows,
        created_count=created_count,
        skipped_count=skipped_count,
    )


def render_import_report_csv(result: ImportResult) -> str:
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=REPORT_HEADERS)
    writer.writeheader()
    writer.writerows(result.rows)
    return output.getvalue()


def _normalize_row(row: dict[str, str | None]) -> dict[str, str]:
    normalized = {}
    for key, value in row.items():
        if key is None:
            continue
        normalized[key] = (value or "").strip()

    if "company_reference_code" in normalized:
        normalized["company_reference_code"] = normalized[
            "company_reference_code"
        ].upper()
    if "auth_method" in normalized:
        normalized["auth_method"] = normalized["auth_method"].lower()
    return normalized


def _import_row(row_number: int, row: dict[str, str]) -> dict[str, str]:
    email = row.get("email", "").lower()
    report_row = {
        "row_number": str(row_number),
        "email": email,
        "status": "skipped",
        "message": "",
        "username": "",
        "temporary_password": "",
    }

    validation_error = _validate_row(row)
    if validation_error:
        report_row["message"] = validation_error
        return report_row

    auth_method = row["auth_method"].lower()
    username = generate_unique_username(email)
    temporary_password = (
        _generate_temporary_password() if auth_method == "password" else ""
    )

    try:
        company = Company.objects.get(reference_code=row["company_reference_code"])
        group = Group.objects.get(name=row["group"])
    except Company.DoesNotExist:
        report_row["message"] = "No existe una empresa con ese reference_code."
        return report_row
    except Group.DoesNotExist:
        report_row["message"] = "No existe un grupo con ese nombre."
        return report_row

    with transaction.atomic():
        if User.objects.filter(email=email).exists():
            report_row["message"] = "Ya existe un usuario con ese email."
            return report_row

        user = User(
            username=username,
            email=email,
            first_name=row.get("first_name", ""),
            last_name=row.get("last_name", ""),
            must_change_password=auth_method == "password",
        )

        if auth_method == "password":
            user.set_password(temporary_password)
        else:
            user.set_unusable_password()

        user.save()
        user.groups.add(group)
        UserProfile.objects.create(
            user=user,
            position=row.get("position", ""),
            company=company,
            is_activated=False,
        )

    report_row.update(
        {
            "status": "created",
            "message": "Usuario creado.",
            "username": username,
            "temporary_password": temporary_password,
        }
    )
    return report_row


def _validate_row(row: dict[str, str]) -> str:
    for header in REQUIRED_HEADERS:
        if not row.get(header):
            return f"Falta valor requerido: {header}."

    try:
        validate_email(row["email"])
    except ValidationError:
        return "Email inválido."

    auth_method = row["auth_method"].lower()
    if auth_method not in {"otp", "password"}:
        return "auth_method debe ser otp o password."

    return ""


def _generate_temporary_password() -> str:
    chars = "abcdefghjkmnpqrstuvwxyzABCDEFGHJKLMNPQRSTUVWXYZ23456789!@#$%&*"
    return get_random_string(16, allowed_chars=chars)
