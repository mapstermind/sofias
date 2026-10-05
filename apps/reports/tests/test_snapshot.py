import json

import pytest

from apps.nom035 import constants as c
from apps.reports.models import Report
from apps.reports.snapshot import build_report_data, data_for, dump, load

pytestmark = pytest.mark.django_db


def test_build_report_data_facts(scored_assignment):
    data = build_report_data(scored_assignment)
    assert data.company.name == scored_assignment.company.name
    assert data.company.industry == "Manufactura"
    assert data.company.work_center == "Planta Norte"
    assert data.variant == "large"
    assert data.variant_label == "Guía III"
    assert data.responded == 12
    assert data.registered == 12
    assert data.participation_percent == 100
    assert data.final_distribution.n == 12


def test_round_trip_is_lossless(scored_assignment):
    data = build_report_data(scored_assignment)
    raw = json.loads(json.dumps(dump(data)))  # what a JSONField stores
    assert load(raw) == data


def test_infinite_band_is_clamped_for_json(scored_assignment):
    raw = dump(build_report_data(scored_assignment))
    text = json.dumps(raw, allow_nan=False)  # raises on inf
    assert "Infinity" not in text


def test_empty_assignment(company, nom035_survey):
    from apps.nom035.tests.factories import make_assignment

    data = build_report_data(make_assignment(company, nom035_survey))
    assert data.responded == 0
    assert data.final_distribution is None
    assert data.participation_percent is None or data.participation_percent == 0
    assert load(json.loads(json.dumps(dump(data)))) == data


def test_data_for_reads_snapshot_when_published(scored_assignment):
    report = Report.objects.create(assignment=scored_assignment)
    live = data_for(report)
    report.snapshot = dump(live)
    report.status = Report.Status.PUBLISHED
    report.save()
    from apps.nom035.models import SubmissionScore

    SubmissionScore.objects.update(final_ndr=c.NDR_MUY_ALTO)
    assert data_for(report) == live
    report.status = Report.Status.DRAFT
    assert data_for(report) != live


def test_load_defaults_missing_palette(scored_assignment):
    raw = json.loads(json.dumps(dump(build_report_data(scored_assignment))))
    for cat in raw["categoria_distribution"]:
        cat.pop("palette", None)
        for dom in cat["children"]:
            dom.pop("palette", None)
    data = load(raw)
    assert data.categoria_distribution[0].palette == "ndr"
    assert data.categoria_distribution[0].children[0].palette == "dom"
