"""The results-dashboard proposal at /propuestas/resultados/ and its sample data."""

import pytest
from django.test import override_settings

from apps.core import results_proposal as rp

pytestmark = pytest.mark.django_db

URL = "/propuestas/resultados/"


@override_settings(DEBUG=False)
def test_an_anonymous_visitor_gets_a_404(client):
    assert client.get(URL).status_code == 404


@override_settings(DEBUG=False)
def test_an_employee_gets_a_404(
    client, make_user_with_profile, company, bootstrap_groups
):
    user = make_user_with_profile(email="empleado@example.com", company=company)
    user.groups.add(bootstrap_groups["Employees"])
    client.force_login(user)
    assert client.get(URL).status_code == 404


@pytest.fixture
def admin_page(client, make_user, bootstrap_groups):
    user = make_user(email="admin@example.com")
    user.groups.add(bootstrap_groups["Admins"])
    client.force_login(user)
    with override_settings(DEBUG=False):
        response = client.get(URL)
    assert response.status_code == 200
    return response.content.decode()


def test_it_has_one_h1(admin_page):
    assert admin_page.count("<h1") == 1


@pytest.mark.parametrize(
    "text",
    [
        "Tablero propuesto",
        "Vista Estadísticas",
        "Con una categoría elegida",
        "Decisiones por revisar",
        "Factores propios de la actividad",
        "Carga de trabajo",
        "Requiere valoración clínica",
        "Recursos Humanos",
    ],
)
def test_it_shows_every_section(admin_page, text):
    assert text in admin_page


def test_it_lists_every_decision(admin_page):
    for decision in rp.DECISIONS:
        assert decision["title"] in admin_page


def test_every_group_counts_the_same_questionnaires():
    groups = [rp.FINAL, *rp.CATEGORIAS]
    groups += [d for cat in rp.CATEGORIAS for d in cat.children]
    assert {g.n for g in groups} == {rp.TOTAL}


def test_the_areas_add_up_to_the_final_distribution():
    hidden = rp.TOTAL - sum(sum(a["counts"]) for a in rp.AREAS if a["counts"])
    assert hidden == next(a["responded"] for a in rp.AREAS if not a["counts"])
    assert sum(s["value"] for s in rp.SEX) == rp.TOTAL
    assert sum(n for _, n in rp.AGES) == rp.TOTAL
    assert sum(s["value"] for s in rp.GUIA1) == rp.TOTAL


def test_the_hero_scale_ends_at_the_next_ten_above_the_largest_share():
    hero = rp.hero(rp.FINAL)
    assert hero["ceiling"] == 40
    assert [g["label"] for g in hero["gridlines"]] == ["10 %", "20 %", "30 %", "40 %"]
    assert hero["selected"]["label"] == "Medio"
    assert sum(col["selected"] for col in hero["columns"]) == 1


def test_at_risk_is_the_share_in_alto_or_muy_alto():
    # Factores: 33 alto + 18 muy alto of 148.
    assert rp.CATEGORIAS[1].at_risk == 34
