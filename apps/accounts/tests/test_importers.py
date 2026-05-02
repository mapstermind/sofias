import csv
import io

import pytest

from apps.accounts.importers import import_users_from_csv, render_import_report_csv
from apps.accounts.models import User, UserProfile

pytestmark = pytest.mark.django_db


def _csv_text(rows):
    output = io.StringIO()
    writer = csv.DictWriter(
        output,
        fieldnames=[
            "email",
            "company_reference_code",
            "group",
            "auth_method",
            "first_name",
            "last_name",
            "position",
        ],
    )
    writer.writeheader()
    writer.writerows(rows)
    return output.getvalue()


class TestImportUsersFromCSV:
    def test_creates_otp_user_with_profile(self, make_company, bootstrap_groups):
        company = make_company()
        result = import_users_from_csv(
            _csv_text(
                [
                    {
                        "email": "ana@example.com",
                        "company_reference_code": company.reference_code,
                        "group": "Employees",
                        "auth_method": "otp",
                        "first_name": "Ana",
                        "last_name": "Lopez",
                        "position": "Analyst",
                    }
                ]
            )
        )

        user = User.objects.get(email="ana@example.com")
        profile = UserProfile.objects.get(user=user)
        assert result.created_count == 1
        assert user.username == "ana"
        assert user.has_usable_password() is False
        assert user.must_change_password is False
        assert user.groups.filter(name="Employees").exists()
        assert profile.company == company
        assert profile.position == "Analyst"
        assert profile.is_activated is False

    def test_creates_password_user_and_reports_temporary_password(
        self, make_company, bootstrap_groups
    ):
        company = make_company()
        result = import_users_from_csv(
            _csv_text(
                [
                    {
                        "email": "bea@example.com",
                        "company_reference_code": company.reference_code,
                        "group": "Employees",
                        "auth_method": "password",
                    }
                ]
            )
        )

        user = User.objects.get(email="bea@example.com")
        password = result.rows[0]["temporary_password"]
        assert result.created_count == 1
        assert password
        assert user.has_usable_password() is True
        assert user.check_password(password)
        assert user.must_change_password is True

    def test_missing_required_header_raises_error(self):
        with pytest.raises(ValueError, match="company_reference_code"):
            import_users_from_csv("email,group,auth_method\nana@example.com,Employees,otp\n")

    def test_skips_duplicate_email(self, make_user, make_company, bootstrap_groups):
        company = make_company()
        make_user(email="dupe@example.com")

        result = import_users_from_csv(
            _csv_text(
                [
                    {
                        "email": "dupe@example.com",
                        "company_reference_code": company.reference_code,
                        "group": "Employees",
                        "auth_method": "otp",
                    }
                ]
            )
        )

        assert result.created_count == 0
        assert result.skipped_count == 1
        assert result.rows[0]["status"] == "skipped"
        assert User.objects.filter(email="dupe@example.com").count() == 1

    def test_skips_invalid_rows_but_creates_valid_rows(
        self, make_company, bootstrap_groups
    ):
        company = make_company()
        result = import_users_from_csv(
            _csv_text(
                [
                    {
                        "email": "valid@example.com",
                        "company_reference_code": company.reference_code,
                        "group": "Employees",
                        "auth_method": "otp",
                    },
                    {
                        "email": "invalid@example.com",
                        "company_reference_code": "XXXXX",
                        "group": "Employees",
                        "auth_method": "otp",
                    },
                    {
                        "email": "bad-auth@example.com",
                        "company_reference_code": company.reference_code,
                        "group": "Employees",
                        "auth_method": "magic",
                    },
                ]
            )
        )

        assert result.created_count == 1
        assert result.skipped_count == 2
        assert User.objects.filter(email="valid@example.com").exists()
        assert not User.objects.filter(email="invalid@example.com").exists()
        assert not User.objects.filter(email="bad-auth@example.com").exists()

    def test_generates_unique_usernames(self, make_user, make_company, bootstrap_groups):
        company = make_company()
        make_user(email="other@example.com", username="sam")

        result = import_users_from_csv(
            _csv_text(
                [
                    {
                        "email": "sam@example.com",
                        "company_reference_code": company.reference_code,
                        "group": "Employees",
                        "auth_method": "otp",
                    }
                ]
            )
        )

        assert result.rows[0]["username"] == "sam1"
        assert User.objects.filter(username="sam1").exists()

    def test_report_csv_contains_expected_columns(self, make_company, bootstrap_groups):
        company = make_company()
        result = import_users_from_csv(
            _csv_text(
                [
                    {
                        "email": "report@example.com",
                        "company_reference_code": company.reference_code,
                        "group": "Employees",
                        "auth_method": "otp",
                    }
                ]
            )
        )

        report = render_import_report_csv(result)
        assert "row_number,email,status,message,username,temporary_password" in report
        assert "report@example.com,created" in report
