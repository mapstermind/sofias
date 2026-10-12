"""Every page has one title: see docs/platform/design-system.md (Page header).

Each main page is rendered for the role that sees it, and must carry exactly
one <h1>: a screen reader's "jump to the title" lands once, and a second one
is a heading the ladder has no room for.
"""

import pytest
from django.urls import reverse

pytestmark = pytest.mark.django_db


@pytest.fixture
def as_group(client, company, make_user_with_profile, bootstrap_groups):
    def login(group):
        user = make_user_with_profile(
            email=f"{group[:3].lower()}@acme.mx", company=company
        )
        user.groups.add(bootstrap_groups[group])
        client.force_login(user)
        return user

    return login


def _h1_count(client, url):
    response = client.get(url)
    assert response.status_code == 200, (url, response.status_code)
    return response.content.decode().count("<h1")


@pytest.mark.parametrize(
    "name",
    [
        "core:company_dashboard",
        "core:company_employee_list",
        "core:company_results",
        "reports:exec_list",
    ],
)
def test_an_executive_page_has_one_title(client, as_group, name):
    as_group("Principal Exec")
    assert _h1_count(client, reverse(name)) == 1


def test_the_employee_page_has_one_title(
    client, as_group, company, make_user_with_profile
):
    as_group("Principal Exec")
    employee = make_user_with_profile(email="emp@acme.mx", company=company)
    url = reverse("core:company_employee_detail", args=[employee.pk])
    assert _h1_count(client, url) == 1


def test_the_company_list_has_one_title(client, make_user, bootstrap_groups):
    admin = make_user(email="admin@x.mx")
    admin.groups.add(bootstrap_groups["Admins"])
    client.force_login(admin)
    assert _h1_count(client, reverse("core:company_list")) == 1


def test_a_respondents_pages_have_one_title(client, as_group, active_assignment):
    as_group("Employees")
    assert _h1_count(client, reverse("core:employee_survey_list")) == 1
    url = reverse("surveys:survey_detail", args=[active_assignment.pk])
    assert _h1_count(client, url) == 1


@pytest.mark.parametrize(
    "name",
    [
        "accounts:request_otp",
        "accounts:password_login",
        "accounts:setup_access_code_login",
        "core:about",
    ],
)
def test_a_signed_out_page_has_one_title(client, name):
    assert _h1_count(client, reverse(name)) == 1


def test_every_layout_opens_with_a_skip_link(client):
    import re

    html = client.get(reverse("accounts:request_otp")).content.decode()
    body = html[html.index("<body") :]
    first_link = re.search(r"<a [^>]*>", body).group(0)
    assert 'href="#main"' in first_link
    assert "Saltar al contenido" in body[: body.index("</a>")]
    assert 'id="main"' in body


def test_a_csrf_failure_is_a_spanish_page():
    from django.test import Client

    strict = Client(enforce_csrf_checks=True)
    response = strict.post(reverse("accounts:request_otp"), {"email": "a@x.mx"})
    assert response.status_code == 403
    html = response.content.decode()
    assert "Recárgala e intenta de nuevo." in html
    assert "Recargar" in html
