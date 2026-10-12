"""The company dashboard's layout: see docs/platform/design-system.md (Dashboard)."""

import pytest
from django.urls import reverse

pytestmark = pytest.mark.django_db

DASHBOARD_URL = "/tablero-empresa/"


@pytest.fixture
def viewer(client, company, make_user_with_profile, bootstrap_groups):
    def login(*groups):
        user = make_user_with_profile(email="v@acme.mx", company=company)
        for group in groups:
            user.groups.add(bootstrap_groups[group])
        client.force_login(user)
        return user

    return login


def _get(client):
    """The page body: the header's navigation links to the same places."""
    response = client.get(DASHBOARD_URL)
    assert response.status_code == 200
    html = response.content.decode()
    return html[html.index("<main") :]


def test_the_dashboard_does_not_repeat_the_navigation(client, viewer):
    viewer("Principal Exec")
    html = _get(client)
    assert "Valoración de resultados" not in html
    assert "Ver colaboradores" not in html


def test_the_reference_code_sits_beside_the_title_with_a_copy_button(
    client, viewer, company
):
    """Not a stat card: it is what colaboradores type to activate, so the
    header hands it out, ready to copy."""
    viewer("Principal Exec")
    html = _get(client)
    header = html[html.index("<h1") : html.index("Cuentas activadas")]
    assert ">Código de empresa</p>" in header
    assert "data-copy-source" in header and company.reference_code in header
    assert f'data-copy="{company.reference_code}" hidden' in header
    assert "Tus colaboradores lo escriben al activar su cuenta." in header
    assert "js/copy.js" in html


def test_the_registered_stat_links_to_the_roster(client, viewer):
    viewer("Principal Exec")
    html = _get(client)
    roster = reverse("core:company_employee_list")
    card = html[html.index(f'href="{roster}"') :]
    assert "Cuentas activadas" in card[: card.index("</a>")]


def test_your_answer_shows_for_a_viewer_who_takes_surveys(
    client, viewer, active_assignment
):
    viewer("Principal Exec")
    html = _get(client)
    assert "Tus respuestas" in html
    assert "Responder" in html


def test_your_answer_is_absent_for_an_admin(
    client, make_user, bootstrap_groups, company, active_assignment
):
    admin = make_user(email="admin@x.mx")
    admin.groups.add(bootstrap_groups["Admins"])
    client.force_login(admin)
    html = client.get(
        reverse("core:company_dashboard_for", args=[company.reference_code])
    ).content.decode()
    assert "Tus respuestas" not in html


def test_the_threshold_tick_has_a_visible_caption(
    client, viewer, active_assignment, make_user_with_profile, company
):
    for i in range(3):
        make_user_with_profile(email=f"m{i}@acme.mx", company=company)
    viewer("Principal Exec")
    html = _get(client)
    assert "Mínimo representativo:" in html


def test_the_cochran_note_counts_every_member(client, viewer):
    """N is every member, activated or not: the formula reads member_count."""
    viewer("Principal Exec")
    html = _get(client)
    assert "es el total de colaboradores de la empresa" in html
    assert "Código de empresa" in html and "Cuentas activadas" in html
