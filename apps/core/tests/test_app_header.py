"""The application header, which every signed-in page renders.

The header holds the only logout control in the product, so these assert that
it survives — a header regression is otherwise invisible to a suite with no
browser.
"""

import pytest

pytestmark = pytest.mark.django_db

DASHBOARD_URL = "/tablero-empresa/"


def _header(html):
    """Just the <header> element.

    Not "everything before <main>": that sweeps in <head>, where <title>
    names the page and the company on purpose.
    """
    start = html.index("<header")
    return html[start : html.index("</header>", start)]


@pytest.fixture
def dashboard(client, make_company, make_user_with_profile, bootstrap_groups):
    """The company dashboard as its principal executive sees it."""
    company = make_company(name="Acme México")
    viewer = make_user_with_profile(
        email="exec@acme.mx",
        company=company,
        first_name="Laura",
        paternal_last_name="Torres",
    )
    viewer.groups.add(bootstrap_groups["Principal Exec"])
    client.force_login(viewer)

    response = client.get(DASHBOARD_URL)
    assert response.status_code == 200, f"got {response.status_code}"
    return response.content.decode()


def test_the_header_renders_the_viewers_initials(dashboard):
    """The avatar circle carries the viewer's initials."""
    header = _header(dashboard)

    assert "data-avatar" in header
    assert ">LT<" in header.replace(" ", "").replace("\n", "")


def test_the_header_always_offers_a_way_to_sign_out(dashboard):
    """The avatar opens a menu whose one action is a named logout button.

    The words are in the markup at every width, so no phone visitor is logged
    out by a curious tap on a bare circle.
    """
    header = _header(dashboard)

    assert header.count("Cerrar sesión") == 1
    assert 'action="/cuentas/cerrar-sesion/"' in header
    assert "data-disclosure" in header


def test_the_company_name_is_the_page_title_not_a_header_crumb(dashboard):
    """The company is named by the page's <h1>, not by the header."""
    header = _header(dashboard)
    content = dashboard[dashboard.index("<main") :]

    assert "Acme México" not in header
    assert "<h1" in content
    assert "Acme México" in content
