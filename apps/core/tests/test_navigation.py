"""Company navigation: see docs/platform/design-system.md (Navigation)."""

import pytest
from django.test import RequestFactory
from django.urls import resolve

from apps.core.templatetags.navigation import sections

pytestmark = pytest.mark.django_db

ALL = ["Tablero", "Colaboradores", "Resultados", "Reportes"]


@pytest.fixture
def member(make_user_with_profile, company, bootstrap_groups):
    def factory(group, email=None):
        user = make_user_with_profile(
            email=email or f"{group.replace(' ', '').lower()}@example.com",
            company=company,
        )
        user.groups.add(bootstrap_groups[group])
        return user

    return factory


@pytest.fixture
def admin(make_user, bootstrap_groups):
    user = make_user(email="admin@example.com")
    user.groups.add(bootstrap_groups["Admins"])
    return user


def _request(user, path):
    request = RequestFactory().get(path)
    request.user = user
    request.resolver_match = resolve(path)
    return request


def _own(path="/tablero-empresa/"):
    return path


def _for(company, rest=""):
    return f"/empresas/{company.reference_code}/{rest}"


def test_an_admin_sees_every_section(admin, company):
    items = sections(_request(admin, _for(company)), company, True)
    assert [i["label"] for i in items] == ALL


@pytest.mark.parametrize(
    "group, expected",
    [("Principal Exec", ALL), ("Secondary Exec", ["Tablero", "Colaboradores"])],
)
def test_an_executive_sees_the_sections_they_may_open(member, company, group, expected):
    user = member(group)
    items = sections(_request(user, _own()), company, False)
    assert [i["label"] for i in items] == expected


def test_an_employee_gets_no_sections(member, company):
    user = member("Employees")
    assert sections(_request(user, "/encuestas/"), company, False) == []


def test_no_company_gives_no_sections(admin):
    assert sections(_request(admin, "/empresas/"), None, True) == []


@pytest.mark.parametrize("group", ["Principal Exec", "Secondary Exec"])
def test_every_offered_section_opens_for_that_role(client, member, company, group):
    user = member(group)
    client.force_login(user)
    for item in sections(_request(user, _own()), company, False):
        assert client.get(item["url"]).status_code == 200, item


def test_every_offered_section_opens_for_an_admin(client, admin, company):
    client.force_login(admin)
    for item in sections(_request(admin, _for(company)), company, True):
        assert client.get(item["url"]).status_code == 200, item


@pytest.mark.parametrize(
    "path, active",
    [
        ("/tablero-empresa/", "Tablero"),
        ("/tablero-empresa/colaboradores/", "Colaboradores"),
        ("/tablero-empresa/colaboradores/1/", "Colaboradores"),
        ("/tablero-empresa/resultados/", "Resultados"),
        ("/tablero-empresa/resultados/fragmento/", "Resultados"),
        ("/tablero-empresa/reportes/", "Reportes"),
    ],
)
def test_the_page_lights_its_section(member, company, path, active):
    user = member("Principal Exec")
    items = sections(_request(user, path), company, False)
    assert [i["label"] for i in items if i["active"]] == [active]


# ── The header, the user menu and the page context ────────────────────────────

from pathlib import Path  # noqa: E402

TEMPLATES = Path(__file__).resolve().parents[3] / "templates"


def test_only_the_layout_draws_the_header():
    """Pages put context and back links in `page_context`, never in a header of their own."""
    hits = [
        str(p.relative_to(TEMPLATES))
        for p in TEMPLATES.rglob("*.html")
        if "<header" in p.read_text() and p.name != "base_app.html"
    ]
    assert not hits, hits


def test_a_survey_page_offers_the_way_back_to_an_executive(
    client, member, active_assignment
):
    """A survey page has no sections, so the header names the way to the viewer's surveys."""
    client.force_login(member("Principal Exec"))
    html = client.get(f"/encuestas/asignados/{active_assignment.pk}/").content.decode()
    assert 'href="/encuestas/"' in html and "Mis encuestas</a>" in html


def test_an_admin_sees_the_company_context_and_the_lit_section(client, admin, company):
    client.force_login(admin)
    html = client.get(_for(company, "resultados/")).content.decode()
    assert 'href="/empresas/"' in html and company.name in html
    # The switcher and the tabs both mark it.
    assert html.count('aria-current="page"') == 2
    assert html.index('aria-current="page"') < html.index("Resultados</a>")


def test_an_executive_gets_no_company_list_link(client, member, company):
    client.force_login(member("Principal Exec"))
    html = client.get("/tablero-empresa/").content.decode()
    assert 'href="/empresas/"' not in html
    assert "Secciones de la empresa" in html


def test_employee_detail_links_back_to_the_filtered_roster(client, member, company):
    viewer = member("Principal Exec")
    other = member("Employees", email="otra@example.com")
    client.force_login(viewer)
    html = client.get(
        f"/tablero-empresa/colaboradores/{other.pk}/?q=ana"
    ).content.decode()
    assert 'href="/tablero-empresa/colaboradores/?q=ana"' in html
    assert "Colaboradores</a>" in html


def test_a_respondent_gets_a_named_way_home(client, member, active_assignment):
    client.force_login(member("Employees"))
    on_list = client.get("/encuestas/").content.decode()
    on_form = client.get(
        f"/encuestas/asignados/{active_assignment.pk}/"
    ).content.decode()
    assert "Mis encuestas</a>" not in on_list
    assert 'href="/encuestas/"' in on_form and "Mis encuestas</a>" in on_form
    assert "Secciones de la empresa" not in on_form


def test_the_user_menu_names_the_role_and_logs_out(client, member, company):
    client.force_login(member("Principal Exec"))
    html = client.get("/tablero-empresa/").content.decode()
    assert "Ejecutivo principal" in html
    assert 'action="/cuentas/cerrar-sesion/"' in html
