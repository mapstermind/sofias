import re
from html.parser import HTMLParser

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

MESSAGE = "Grupo muy pequeño: ocultamos sus resultados para no identificar a nadie (mínimo 5 personas)."


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
    assert "Por área" in body
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
    assert "Categorías" not in locked

    client.force_login(setup["admin"])
    url = reverse(
        "core:company_results_fragment_for", args=[setup["company"].reference_code]
    )
    free = client.get(url, params).content.decode()
    assert MESSAGE not in free
    assert "Categorías" in free


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


class _SummaryContents(HTMLParser):
    """Tags opened inside each <summary>, and every tabindex that puts an element
    in the tab order (`-1`, focusable only by script, does not)."""

    def __init__(self):
        super().__init__()
        self.depth = 0
        self.nested = []
        self.tabindexes = 0

    def handle_starttag(self, tag, attrs):
        if any(name == "tabindex" and value != "-1" for name, value in attrs):
            self.tabindexes += 1
        if tag == "summary":
            self.depth += 1
        elif self.depth:
            self.nested.append(tag)

    def handle_endtag(self, tag):
        if tag == "summary":
            self.depth -= 1


def test_summaries_hold_no_interactive_content(client, setup, make_user_with_profile):
    add_respondents(setup, make_user_with_profile, 6)
    client.force_login(setup["exec"])
    body = client.get(reverse("core:company_results_fragment")).content.decode()
    parser = _SummaryContents()
    parser.feed(body)
    assert "Dominios (" in body
    assert not {"a", "button", "input", "select", "textarea"} & set(parser.nested)
    assert parser.tabindexes == 0
    assert "data-tooltip" not in body


def test_dominio_rows_draw_in_the_dominio_tier(client, setup, make_user_with_profile):
    from apps.nom035 import _nom035_scoring as cfg
    from apps.nom035.models import GroupScore

    for i in range(6):
        user = make_user_with_profile(email=f"d{i}@x.mx", company=setup["company"])
        sub = SurveySubmission.objects.create(
            assignment=setup["assignment"],
            user=user,
            status=SurveySubmission.Status.IN_PROGRESS,
        )
        score = SubmissionScore.objects.create(
            submission=sub, final_score=60, final_ndr=c.NDR_BAJO
        )
        GroupScore.objects.create(
            submission_score=score,
            level=c.LEVEL_CATEGORIA,
            key=cfg.CAT_AMBIENTE,
            score=6,
            ndr=c.NDR_BAJO,
        )
        GroupScore.objects.create(
            submission_score=score,
            level=c.LEVEL_DOMINIO,
            key=cfg.DOM_CONDICIONES,
            score=12,
            ndr=c.NDR_MUY_ALTO,
        )
    client.force_login(setup["exec"])
    body = client.get(reverse("core:company_results")).content.decode()
    assert "bg-[#7A1010]" in body  # dominio Muy alto segment
    assert (
        "bg-green-500" in body or "bg-success" in body or "bg-[#22C55E]" in body
    )  # categoría Bajo, base tier
    chosen = client.get(
        reverse("core:company_results"), {"ver": cfg.CAT_AMBIENTE}
    ).content.decode()
    assert "Dominios:" in chosen  # the dominio legend heads the dominio column


def _results_page(client, setup, make_user_with_profile):
    add_respondents(setup, make_user_with_profile, 6, area=setup["area"])
    client.force_login(setup["exec"])
    html = client.get(reverse("core:company_results")).content.decode()
    return html[html.index("<main") :]


def test_the_page_sections_are_headings_in_sentence_case(
    client, setup, make_user_with_profile
):
    html = _results_page(client, setup, make_user_with_profile)
    assert "uppercase" not in html
    assert ">Calificación final</h2>" in html
    assert ">Categorías</h2>" in html
    assert ">Participación</h2>" in html
    assert ">Por área</h2>" in html
    assert "Guía I: acontecimientos traumáticos severos" in html
    assert ">Quienes respondieron</h2>" in html


def test_the_filters_are_the_rosters_dialog_of_chips(
    client, setup, make_user_with_profile
):
    html = _results_page(client, setup, make_user_with_profile)
    form = html[html.index('id="results-filters"') : html.index("</dialog>")]
    assert 'data-dialog-open="results-filter-modal"' in form
    assert '<dialog id="results-filter-modal"' in form
    inputs = form.count('type="radio"') + form.count('type="checkbox"')
    assert inputs and form.count('class="chip"') == inputs
    # Sexo returns to "either" by un-choosing, as on the roster: no Todos chip.
    assert "Todos" not in form
    assert "<details" not in form


def test_limpiar_filtros_is_in_the_bar_only_while_filtering(
    client, setup, make_user_with_profile
):
    """It is rendered `hidden` rather than left out, so the script can show it
    after an *Aplicar* that swaps the body without a reload."""
    add_respondents(setup, make_user_with_profile, 6, area=setup["area"])
    client.force_login(setup["exec"])
    url = reverse("core:company_results")
    pk = setup["assignment"].pk

    wide = client.get(url).content.decode()
    bar = wide[wide.index('id="results-filters"') : wide.index("<dialog")]
    assert re.search(r"<a [^>]*data-filter-clear hidden", bar)

    narrowed = client.get(
        url, {"area": setup["area"].pk, "sexo": "femenino", "edad": ["18-19", "20-24"]}
    ).content.decode()
    bar = narrowed[narrowed.index('id="results-filters"') : narrowed.index("<dialog")]
    link = re.search(r"<a [^>]*data-filter-clear[^>]*>", bar).group(0)
    assert " hidden" not in link
    assert f'href="{url}?encuesta={pk}"' in link
    # Three dimensions, four values: the count is of dimensions, as on the roster.
    assert re.search(r"data-filter-count[^>]*>3<", bar)


def test_one_localidad_offers_no_localidad_filter(
    client, setup, make_user_with_profile, make_location
):
    make_location(setup["company"], name="Matriz")
    html = _results_page(client, setup, make_user_with_profile)
    assert 'name="localidad"' not in html


def test_a_filtered_empty_group_offers_to_clear(client, setup, make_user_with_profile):
    add_respondents(setup, make_user_with_profile, 6)
    client.force_login(setup["exec"])
    body = client.get(
        reverse("core:company_results") + f"?area={setup['area'].pk}"
    ).content.decode()
    empty = body[body.index("Ningún cuestionario coincide") :]
    assert "Limpiar filtros" in empty[:600]


def test_the_sticky_strip_says_what_is_shown_and_for_whom(
    client, setup, make_user_with_profile
):
    from apps.nom035 import _nom035_scoring as cfg

    add_respondents(setup, make_user_with_profile, 6, area=setup["area"])
    client.force_login(setup["exec"])
    url = reverse("core:company_results")
    plain = client.get(url).content.decode()
    strip = plain[plain.index('id="results-strip"') : plain.index("<dialog")]
    assert "sticky top-0" in strip
    assert "Mostrando: Calificación final" in strip
    assert "Toda la empresa" in strip and "6</span> colaboradores" in strip
    assert "data-filter-count" in strip  # Filtros lives in the strip

    chosen = client.get(
        url, {"ver": cfg.CAT_AMBIENTE, "area": setup["area"].pk}
    ).content.decode()
    strip = chosen[chosen.index('id="results-strip"') : chosen.index("<dialog")]
    assert "Mostrando: Ambiente de trabajo" in strip
    assert "Volver a la calificación final" in strip
    assert setup["area"].name in strip and "Quitar filtro" in strip


def test_the_fragment_parks_the_summary_for_the_script_to_move(
    client, setup, make_user_with_profile
):
    add_respondents(setup, make_user_with_profile, 6)
    client.force_login(setup["exec"])
    body = client.get(reverse("core:company_results_fragment")).content.decode()
    assert body.lstrip().startswith("<div data-results-summary hidden>")
    assert body.index("data-group-line") < body.index("data-hero")


def test_a_filtered_group_is_marked_and_sized_against_the_whole(
    client, setup, make_user_with_profile
):
    add_respondents(setup, make_user_with_profile, 6, area=setup["area"], prefix="ops")
    add_respondents(setup, make_user_with_profile, 6, prefix="rest")
    client.force_login(setup["admin"])
    url = reverse("core:company_results")
    plain = client.get(url).content.decode()
    assert 'id="results-strip" data-filtered="false"' in plain
    assert "12</span> colaboradores" in plain

    filtered = client.get(url, {"area": setup["area"].pk}).content.decode()
    assert 'id="results-strip" data-filtered="true"' in filtered
    assert f"Área: {setup['area'].name}" in filtered
    assert "6</span> de 12 colaboradores" in filtered
    # The área's own row offers to remove the filter instead of adding it.
    assert f"Quitar el filtro de {setup['area'].name}" in filtered
    assert f"Filtrar por {setup['area'].name}" not in filtered


def test_choosing_a_categoria_marks_the_strip_without_turning_filtros_solid(
    client, setup, make_user_with_profile
):
    from apps.nom035 import _nom035_scoring as cfg

    add_respondents(setup, make_user_with_profile, 6)
    client.force_login(setup["exec"])
    url = reverse("core:company_results")
    plain = client.get(url).content.decode()
    assert 'data-filtered="false" data-active="false"' in plain
    chosen = client.get(url, {"ver": cfg.CAT_AMBIENTE}).content.decode()
    assert 'data-filtered="false" data-active="true"' in chosen
