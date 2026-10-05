import pytest
from django.urls import reverse

from apps.accounts.roles import ROLES
from apps.reports import publishing
from apps.reports.models import Report

pytestmark = pytest.mark.django_db
READY = dict(
    issued_in="CDMX",
    activities_summary="A",
    evaluator_name="S",
    evaluator_license="1",
    conclusions="C",
)


@pytest.fixture
def exec_client(client, make_user_with_profile, bootstrap_groups, scored_assignment):
    user = make_user_with_profile(email="e@x.mx", company=scored_assignment.company)
    user.groups.add(bootstrap_groups[ROLES[1].name])
    client.force_login(user)
    return client


def _detail(a):
    return reverse("reports:exec_detail", args=[a.pk])


def test_anonymous_redirects_to_login(client):
    resp = client.get(reverse("reports:exec_list"))
    assert resp.status_code == 302
    assert "login" in resp["Location"] or "cuentas" in resp["Location"]


def test_draft_is_404(exec_client, scored_assignment):
    Report.objects.create(assignment=scored_assignment, **READY)
    assert exec_client.get(_detail(scored_assignment)).status_code == 404


def test_published_is_readable_and_listed(exec_client, scored_assignment, make_user):
    report = Report.objects.create(assignment=scored_assignment, **READY)
    publishing.publish(report, make_user(email="op@x.mx"))
    body = exec_client.get(reverse("reports:exec_list")).content.decode()
    assert "Abrir" in body
    resp = exec_client.get(_detail(scored_assignment))
    assert resp.status_code == 200
    html = resp.content.decode()
    assert "Despublicar" not in html and "Editar" not in html


def test_empty_list_message(exec_client):
    body = exec_client.get(reverse("reports:exec_list")).content.decode()
    assert "Aún no hay reportes publicados." in body


def test_other_company_is_404(
    client,
    make_user_with_profile,
    bootstrap_groups,
    make_company,
    scored_assignment,
    make_user,
):
    report = Report.objects.create(assignment=scored_assignment, **READY)
    publishing.publish(report, make_user(email="op@x.mx"))
    other = make_company(name="Otra", legal_name="Otra SA")
    user = make_user_with_profile(email="o@x.mx", company=other)
    user.groups.add(bootstrap_groups[ROLES[1].name])
    client.force_login(user)
    assert client.get(_detail(scored_assignment)).status_code == 404


def test_secondary_exec_is_403(
    client, make_user_with_profile, bootstrap_groups, scored_assignment
):
    user = make_user_with_profile(email="s@x.mx", company=scored_assignment.company)
    user.groups.add(bootstrap_groups[ROLES[2].name])
    client.force_login(user)
    assert client.get(reverse("reports:exec_list")).status_code == 403


def test_dashboard_card_links_to_reports(exec_client):
    body = exec_client.get(reverse("core:company_dashboard")).content.decode()
    assert reverse("reports:exec_list") in body
    assert "Reporte de resultados" in body
