import pytest
from django.urls import reverse

from apps.accounts.roles import ROLES
from apps.reports.models import Report, ReportSignatory

pytestmark = pytest.mark.django_db


@pytest.fixture
def admin_client(client, make_user, bootstrap_groups):
    user = make_user(email="op@x.mx")
    user.groups.add(bootstrap_groups[ROLES[0].name])
    client.force_login(user)
    return client


@pytest.fixture
def urls(scored_assignment):
    ref = scored_assignment.company.reference_code
    pk = scored_assignment.pk
    return {
        "list": reverse("reports:admin_list", args=[ref]),
        "detail": reverse("reports:admin_detail", args=[ref, pk]),
        "edit": reverse("reports:admin_edit", args=[ref, pk]),
        "publish": reverse("reports:admin_publish", args=[ref, pk]),
        "unpublish": reverse("reports:admin_unpublish", args=[ref, pk]),
    }


def _form_data(**overrides):
    data = {
        "issued_in": "CDMX",
        "activities_summary": "Compras",
        "headcount_in_person": "10",
        "headcount_home_office": "",
        "headcount_hybrid": "",
        "evaluator_name": "Sofía",
        "evaluator_license": "123",
        "additional_recommendations": "",
        "conclusions": "Ok",
        "signatories-TOTAL_FORMS": "1",
        "signatories-INITIAL_FORMS": "0",
        "signatories-MIN_NUM_FORMS": "0",
        "signatories-MAX_NUM_FORMS": "1000",
        "signatories-0-title": "Dirección de RH",
        "signatories-0-name": "Lic. Ana",
        "signatories-0-ORDER": "1",
    }
    return data | overrides


def test_list_shows_states(admin_client, urls):
    body = admin_client.get(urls["list"]).content.decode()
    assert "Sin iniciar" in body


def test_detail_previews_without_creating(admin_client, urls):
    resp = admin_client.get(urls["detail"])
    assert resp.status_code == 200
    assert "Datos del centro de trabajo" in resp.content.decode()
    assert Report.objects.count() == 0


def test_edit_creates_report_and_signatories(admin_client, urls):
    resp = admin_client.post(urls["edit"], _form_data())
    assert resp.status_code == 302
    report = Report.objects.get()
    assert report.signatories.get().name == "Lic. Ana"


def test_edit_prefills_from_previous_report(
    admin_client, urls, scored_assignment, nom035_survey
):
    from apps.nom035.tests.factories import make_assignment

    older = make_assignment(scored_assignment.company, nom035_survey)
    prev = Report.objects.create(
        assignment=older, evaluator_name="Sofía", evaluator_license="999"
    )
    ReportSignatory.objects.create(report=prev, title="RH", name="Ana", order=1)
    body = admin_client.get(urls["edit"]).content.decode()
    assert 'value="999"' in body and 'value="Ana"' in body


def test_publish_flow_and_edit_lock(admin_client, urls):
    admin_client.post(urls["edit"], _form_data())
    resp = admin_client.post(urls["publish"], follow=True)
    assert "Reporte publicado." in resp.content.decode()
    resp = admin_client.get(urls["edit"], follow=True)
    assert "Despublica el reporte para editarlo." in resp.content.decode()
    resp = admin_client.post(urls["unpublish"], follow=True)
    assert "Reporte despublicado." in resp.content.decode()


def test_publish_refusal_names_the_reasons(admin_client, urls, scored_assignment):
    scored_assignment.status = "active"
    scored_assignment.save()
    resp = admin_client.post(urls["publish"], follow=True)
    assert "La encuesta sigue activa" in resp.content.decode()


def test_publish_is_post_only(admin_client, urls):
    assert admin_client.get(urls["publish"]).status_code == 405


def test_executive_cannot_use_admin_routes(
    client, urls, make_user_with_profile, bootstrap_groups, scored_assignment
):
    user = make_user_with_profile(email="e@x.mx", company=scored_assignment.company)
    user.groups.add(bootstrap_groups[ROLES[1].name])
    client.force_login(user)
    assert client.get(urls["detail"]).status_code == 403


def test_foreign_or_non_nom035_assignment_is_404(
    admin_client, scored_assignment, make_company, survey
):
    from apps.surveys.models import SurveyAssignment

    other = make_company(name="Otra", legal_name="Otra SA")
    url = reverse(
        "reports:admin_detail", args=[other.reference_code, scored_assignment.pk]
    )
    assert admin_client.get(url).status_code == 404
    plain = SurveyAssignment.objects.create(
        company=scored_assignment.company, survey=survey, variant="large"
    )
    url = reverse(
        "reports:admin_detail",
        args=[scored_assignment.company.reference_code, plain.pk],
    )
    assert admin_client.get(url).status_code == 404


def test_signatories_keep_order_skip_blank_rows_and_honour_delete(admin_client, urls):
    data = _form_data(
        **{
            "signatories-TOTAL_FORMS": "3",
            "signatories-1-title": "Dirección general",
            "signatories-1-name": "Ing. Luis",
            "signatories-1-ORDER": "2",
            "signatories-2-title": "",
            "signatories-2-name": "",
            "signatories-2-ORDER": "3",
        }
    )
    assert admin_client.post(urls["edit"], data).status_code == 302
    report = Report.objects.get()
    assert [(s.name, s.order) for s in report.signatories.all()] == [
        ("Lic. Ana", 1),
        ("Ing. Luis", 2),
    ]
    ana, luis = report.signatories.all()
    data = _form_data(
        **{
            "signatories-TOTAL_FORMS": "3",
            "signatories-INITIAL_FORMS": "2",
            "signatories-0-id": str(luis.pk),
            "signatories-0-report": str(report.pk),
            "signatories-0-title": luis.title,
            "signatories-0-name": luis.name,
            "signatories-0-ORDER": "1",
            "signatories-1-id": str(ana.pk),
            "signatories-1-report": str(report.pk),
            "signatories-1-title": ana.title,
            "signatories-1-name": ana.name,
            "signatories-1-ORDER": "2",
            "signatories-1-DELETE": "on",
            "signatories-2-title": "Seguridad e higiene",
            "signatories-2-name": "Mtra. Eva",
            "signatories-2-ORDER": "3",
        }
    )
    assert admin_client.post(urls["edit"], data).status_code == 302
    assert [(s.name, s.order) for s in report.signatories.all()] == [
        ("Ing. Luis", 1),
        ("Mtra. Eva", 2),
    ]


def test_list_shows_draft_and_published(admin_client, urls, scored_assignment):
    report = Report.objects.create(assignment=scored_assignment)
    assert "Borrador" in admin_client.get(urls["list"]).content.decode()
    report.status = Report.Status.PUBLISHED
    report.save()
    assert "Publicado" in admin_client.get(urls["list"]).content.decode()


def test_invalid_edit_rerenders_without_saving(admin_client, urls):
    resp = admin_client.post(urls["edit"], _form_data(headcount_in_person="-1"))
    assert resp.status_code == 200
    assert Report.objects.count() == 0
