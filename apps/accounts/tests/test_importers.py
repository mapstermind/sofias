import csv
import io

import pytest

from apps.accounts.importers import import_users_from_csv, render_import_report_csv
from apps.accounts.models import SetupAccessCode, User, UserProfile

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

    def test_password_import_creates_setup_access_code_instead_of_password(
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
        setup_code = result.rows[0]["setup_access_code"]
        assert result.created_count == 1
        assert setup_code
        assert setup_code.isdigit()
        assert len(setup_code) == 9
        assert user.has_usable_password() is False
        assert user.must_change_password is True
        access_code = SetupAccessCode.objects.get(user=user)
        assert access_code.code == setup_code
        assert access_code.used_at is None

    def test_otp_import_does_not_create_setup_access_code(
        self, make_company, bootstrap_groups
    ):
        company = make_company()
        result = import_users_from_csv(
            _csv_text(
                [
                    {
                        "email": "otp-only@example.com",
                        "company_reference_code": company.reference_code,
                        "group": "Employees",
                        "auth_method": "otp",
                    }
                ]
            )
        )

        user = User.objects.get(email="otp-only@example.com")
        assert user.has_usable_password() is False
        assert user.must_change_password is False
        assert result.rows[0]["setup_access_code"] == ""
        assert not SetupAccessCode.objects.filter(user=user).exists()

    def test_missing_required_header_raises_error(self):
        with pytest.raises(ValueError, match="company_reference_code"):
            import_users_from_csv(
                "email,group,auth_method\nana@example.com,Employees,otp\n"
            )

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

    def test_generates_unique_usernames(
        self, make_user, make_company, bootstrap_groups
    ):
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

    def test_import_report_includes_setup_access_code_header(
        self, make_company, bootstrap_groups
    ):
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
        assert "row_number,email,status,message,username,setup_access_code" in report
        assert "report@example.com,created" in report

    def test_import_report_shows_nine_digit_setup_access_code(
        self, make_company, bootstrap_groups
    ):
        company = make_company()
        result = import_users_from_csv(
            _csv_text(
                [
                    {
                        "email": "digits@example.com",
                        "company_reference_code": company.reference_code,
                        "group": "Employees",
                        "auth_method": "password",
                    }
                ]
            )
        )

        setup_code = result.rows[0]["setup_access_code"]
        assert setup_code.isdigit()
        assert len(setup_code) == 9

    def test_password_import_generates_distinct_setup_access_codes(
        self, make_company, bootstrap_groups
    ):
        company = make_company()
        result = import_users_from_csv(
            _csv_text(
                [
                    {
                        "email": "first-password@example.com",
                        "company_reference_code": company.reference_code,
                        "group": "Employees",
                        "auth_method": "password",
                    },
                    {
                        "email": "second-password@example.com",
                        "company_reference_code": company.reference_code,
                        "group": "Employees",
                        "auth_method": "password",
                    },
                ]
            )
        )

        codes = [row["setup_access_code"] for row in result.rows]
        assert result.created_count == 2
        assert len(set(codes)) == 2

    def test_skipped_password_row_does_not_create_setup_access_code(
        self, make_company, bootstrap_groups
    ):
        company = make_company()
        result = import_users_from_csv(
            _csv_text(
                [
                    {
                        "email": "skipped-password@example.com",
                        "company_reference_code": company.reference_code,
                        "group": "Unknown Group",
                        "auth_method": "password",
                    }
                ]
            )
        )

        assert result.created_count == 0
        assert result.skipped_count == 1
        assert not User.objects.filter(email="skipped-password@example.com").exists()
        assert not SetupAccessCode.objects.exists()
