"""The DOM contract static/ts/survey_progress.ts depends on.

There is no JavaScript test runner, so nothing else in the suite notices when a
layout change renames an id or drops a data attribute. Autosave, the progress
bar, conditional visibility and the pendientes panel all go silently dead. This
module is the only thing standing between a CSS refactor and that outcome; the
lists below are transcribed from survey_progress.ts and must be kept in step
with it.
"""

from collections import Counter
from html.parser import HTMLParser

import pytest

pytestmark = pytest.mark.django_db


def _survey_url(assignment_id):
    return f"/encuestas/asignados/{assignment_id}/"


class _IdCounter(HTMLParser):
    """Counts `id` attributes on real elements.

    Counting substrings instead would also count an HTML comment that quotes an
    id — and `<!-- -->` is not a Django comment, so developer notes in a
    template are served to the browser and land in the response body.
    """

    def __init__(self):
        super().__init__()
        self.ids = Counter()

    def handle_starttag(self, tag, attrs):
        element_id = dict(attrs).get("id")
        if element_id:
            self.ids[element_id] += 1


def _rendered_ids(html):
    counter = _IdCounter()
    counter.feed(html)
    return counter.ids


# Every element survey_progress.ts resolves by id.
REQUIRED_IDS = [
    "survey-form",
    "progress-total",
    "progress-count",
    "progress-bar",
    "pending-panel",
    "pending-count",
    "pending-list",
    "pending-more",
    "pending-next",
    "session-expired-modal",
]

# Every attribute it reads off a card, and the hooks it selects them by.
REQUIRED_HOOKS = [
    'class="question-card',
    'class="module-card',
    "question-label",
    "data-question-code=",
    "data-question-name=",
    "data-module-key=",
    "data-visible-when=",
    "data-total=",
    "data-autosave-url=",
]


@pytest.fixture
def survey_page(
    client,
    company,
    survey_with_questions,
    active_assignment,
    make_user_with_profile,
    bootstrap_groups,
):
    """The survey page as a respondent of the assigned company sees it.

    The group membership is not decoration: `survey_detail` requires
    `can_take_assigned_surveys` and scopes the assignment to the caller's own
    company, so a user missing either lands on a redirect and every assertion
    below passes vacuously against an empty page.
    """
    user = make_user_with_profile(email="respondent@example.com", company=company)
    user.groups.add(bootstrap_groups["Employees"])
    client.force_login(user)

    response = client.get(_survey_url(active_assignment.pk))
    assert response.status_code == 200, (
        f"expected the survey page, got {response.status_code} — "
        "the respondent is probably missing its group or company"
    )
    return response.content.decode()


def test_every_id_the_progress_script_resolves_is_rendered(survey_page):
    rendered = _rendered_ids(survey_page)
    missing = [i for i in REQUIRED_IDS if i not in rendered]
    assert missing == [], (
        "survey_progress.ts resolves these by id and would fail silently: "
        + ", ".join(missing)
    )


def test_every_hook_the_progress_script_selects_by_is_rendered(survey_page):
    missing = [h for h in REQUIRED_HOOKS if h not in survey_page]
    assert missing == [], (
        "survey_progress.ts selects on these and would fail silently: "
        + ", ".join(missing)
    )


def test_progress_and_save_share_one_node_so_ids_stay_unique(survey_page):
    """The bottom bar is the sidebar block repositioned, never a second copy.

    Two copies would render `id="progress-bar"` twice; `getElementById` returns
    the first, so the visible one would freeze while the hidden one updated.
    """
    rendered = _rendered_ids(survey_page)
    duplicated = {i: rendered[i] for i in REQUIRED_IDS if rendered[i] > 1}
    assert duplicated == {}, f"rendered more than once: {duplicated}"
