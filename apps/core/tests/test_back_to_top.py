"""The back-to-top button every signed-in page carries.

Its behaviour lives in static/ts/back_to_top.ts, which no test can run. These
pin the server-rendered half: that the button and its hooks are there, that it
starts hidden, that it follows the page's content width, and that the survey
form opts out.
"""

import pytest

from apps.accounts.roles import ROLES

pytestmark = pytest.mark.django_db

DASHBOARD_URL = "/tablero-empresa/"
RESULTS_URL = "/tablero-empresa/resultados/"


def _root(html):
    """The opening tag of the fixed wrapper, which carries the width and print rule."""
    start = html.index("data-back-to-top-root")
    return html[html.rindex("<div", 0, start) : html.index(">", start)]


def _button(html):
    start = html.index("<button", html.index("data-back-to-top-root"))
    return html[start : html.index("</button>", start)]


def _get(client, url):
    response = client.get(url)
    assert response.status_code == 200, f"got {response.status_code}"
    return response.content.decode()


@pytest.fixture
def exec_client(client, company, make_user_with_profile, bootstrap_groups):
    """A principal executive, who can open the dashboard and the results page."""
    viewer = make_user_with_profile(email="exec@acme.mx", company=company)
    viewer.groups.add(bootstrap_groups[ROLES[1].name])
    client.force_login(viewer)
    return client


def test_the_dashboard_offers_a_way_back_to_the_top(exec_client):
    html = _get(exec_client, DASHBOARD_URL)
    button = _button(html)

    assert 'aria-label="Volver arriba"' in button
    assert "data-back-to-top-ring" in button
    assert "js/back_to_top.js" in html


def test_the_button_starts_hidden(exec_client):
    """Only the script reveals it, so a page without JS never shows a dead button."""
    button = _button(_get(exec_client, DASHBOARD_URL))

    assert "invisible" in button
    assert "opacity-0" in button


def test_the_button_is_left_out_of_print(exec_client):
    assert "print:hidden" in _root(_get(exec_client, DASHBOARD_URL))


def test_main_can_receive_focus_after_the_jump(exec_client):
    html = _get(exec_client, DASHBOARD_URL)
    start = html.index("<main")
    main = html[start : html.index(">", start)]

    assert 'id="main"' in main
    assert 'tabindex="-1"' in main


def test_the_gutter_follows_the_pages_content_width(exec_client):
    """The default column is 5xl; the results page widens to 6xl."""
    assert "--container-5xl" in _root(_get(exec_client, DASHBOARD_URL))
    assert "--container-6xl" in _root(_get(exec_client, RESULTS_URL))


def test_the_survey_form_opts_out(
    client,
    company,
    survey_with_questions,
    active_assignment,
    make_user_with_profile,
    bootstrap_groups,
):
    """Its phone bottom bar owns the corner, and respondents move forward, not up."""
    user = make_user_with_profile(email="respondent@acme.mx", company=company)
    user.groups.add(bootstrap_groups[ROLES[3].name])
    client.force_login(user)

    html = _get(client, f"/encuestas/asignados/{active_assignment.pk}/")

    assert "data-back-to-top" not in html
    assert "back_to_top.js" not in html
