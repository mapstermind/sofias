import pytest
from django.db import connection
from django.test.utils import CaptureQueriesContext
from django.urls import reverse

from apps.accounts.roles import ROLES
from apps.nom035 import constants as c
from apps.nom035.models import SubmissionScore
from apps.responses.models import SurveySubmission
from apps.surveys.models import Survey, SurveyAssignment

pytestmark = pytest.mark.django_db

MESSAGE = "Grupo demasiado pequeño para mostrar resultados sin identificar a las personas (mínimo 5)"


@pytest.fixture
def setup(company, make_user_with_profile, make_area, bootstrap_groups):
    survey = Survey.objects.create(
        key="nom035", title="NOM-035", status=Survey.Status.PUBLISHED
    )
    assignment = SurveyAssignment.objects.create(
        company=company,
        survey=survey,
        variant="large",
        status=SurveyAssignment.Status.ACTIVE,
    )
    area = make_area(company, name="Operaciones")
    exec_user = make_user_with_profile(email="exec@x.mx", company=company)
    exec_user.groups.add(bootstrap_groups[ROLES[1].name])
    admin = make_user_with_profile(email="admin@x.mx", company=company)
    admin.groups.add(bootstrap_groups[ROLES[0].name])
    employee = make_user_with_profile(email="emp@x.mx", company=company)
    employee.groups.add(bootstrap_groups[ROLES[3].name])
    return {
        "company": company,
        "assignment": assignment,
        "area": area,
        "exec": exec_user,
        "admin": admin,
        "employee": employee,
    }


def add_respondents(setup, make_user_with_profile, count, *, area=None, prefix="r"):
    for i in range(count):
        user = make_user_with_profile(
            email=f"{prefix}{i}@x.mx", company=setup["company"], area=area
        )
        sub = SurveySubmission.objects.create(
            assignment=setup["assignment"],
            user=user,
            status=SurveySubmission.Status.IN_PROGRESS,
        )
        SubmissionScore.objects.create(
            submission=sub, final_score=60, final_ndr=c.NDR_BAJO
        )


def test_employee_gets_403(client, setup):
    client.force_login(setup["employee"])
    assert client.get(reverse("core:company_results")).status_code == 403


def test_executive_sees_own_company_results(client, setup, make_user_with_profile):
    add_respondents(setup, make_user_with_profile, 6)
    client.force_login(setup["exec"])
    resp = client.get(reverse("core:company_results"))
    assert resp.status_code == 200
    body = resp.content.decode()
    assert "Participación por área" in body
    assert "Calificación final" in body
    assert 'id="results-body"' in body


def test_executive_cannot_use_admin_route(client, setup):
    client.force_login(setup["exec"])
    url = reverse("core:company_results_for", args=[setup["company"].reference_code])
    assert client.get(url).status_code == 403


def test_small_filtered_group_locked_for_executive_not_admin(
    client, setup, make_user_with_profile
):
    add_respondents(setup, make_user_with_profile, 3, area=setup["area"], prefix="ops")
    add_respondents(setup, make_user_with_profile, 10, prefix="rest")
    params = {"area": setup["area"].pk}

    client.force_login(setup["exec"])
    locked = client.get(
        reverse("core:company_results_fragment"), params
    ).content.decode()
    assert MESSAGE in locked
    assert "Distribución por categoría" not in locked

    client.force_login(setup["admin"])
    url = reverse(
        "core:company_results_fragment_for", args=[setup["company"].reference_code]
    )
    free = client.get(url, params).content.decode()
    assert MESSAGE not in free
    assert "Distribución por categoría" in free


def test_fragment_is_a_fragment(client, setup, make_user_with_profile):
    add_respondents(setup, make_user_with_profile, 5)
    client.force_login(setup["exec"])
    body = client.get(reverse("core:company_results_fragment")).content.decode()
    assert "<html" not in body
    assert "Toda la empresa" in body


def test_invalid_parameters_are_ignored(client, setup, make_user_with_profile):
    add_respondents(setup, make_user_with_profile, 5)
    client.force_login(setup["exec"])
    resp = client.get(
        reverse("core:company_results"),
        {"encuesta": "999", "edad": "nope", "area": "abc", "sexo": "x"},
    )
    assert resp.status_code == 200
    assert resp.context["query"].is_filtered is False


def test_no_nom035_assignment(
    client, company, make_user_with_profile, bootstrap_groups
):
    user = make_user_with_profile(email="solo@x.mx", company=company)
    user.groups.add(bootstrap_groups[ROLES[1].name])
    client.force_login(user)
    body = client.get(reverse("core:company_results")).content.decode()
    assert "Esta empresa aún no tiene encuestas NOM-035 asignadas." in body
    assert 'id="results-filters"' not in body


def test_query_count_is_independent_of_respondents(
    client, setup, make_user_with_profile
):
    client.force_login(setup["admin"])
    url = reverse(
        "core:company_results_fragment_for", args=[setup["company"].reference_code]
    )
    add_respondents(setup, make_user_with_profile, 3, prefix="a")
    client.get(url)  # warm session/permission caches
    with CaptureQueriesContext(connection) as small:
        client.get(url)
    add_respondents(setup, make_user_with_profile, 12, prefix="b")
    with CaptureQueriesContext(connection) as large:
        client.get(url)
    assert len(large.captured_queries) == len(small.captured_queries)


def test_unanswered_survey_says_so_instead_of_blaming_filters(client, setup):
    client.force_login(setup["exec"])
    body = client.get(reverse("core:company_results")).content.decode()
    assert "Esta encuesta aún no tiene cuestionarios contestados." in body
    assert "Ningún cuestionario coincide con los filtros." not in body


def test_filtered_empty_group_blames_the_filters(client, setup, make_user_with_profile):
    add_respondents(setup, make_user_with_profile, 6)
    client.force_login(setup["exec"])
    url = reverse("core:company_results") + f"?area={setup['area'].pk}"
    body = client.get(url).content.decode()
    assert "Ningún cuestionario coincide con los filtros." in body
    assert "Esta encuesta aún no tiene cuestionarios contestados." not in body
