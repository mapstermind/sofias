import pytest

from apps.nom035 import _nom035_scoring as cfg
from apps.nom035 import constants as c
from apps.nom035.tests.factories import make_assignment, make_score
from apps.surveys.models import SurveyAssignment


@pytest.fixture
def scored_assignment(company, make_user_with_profile, make_area, nom035_survey):
    """A closed Guía III assignment: 6 in Operaciones, 5 in Ventas, 1 with no área."""
    company.industry = "Manufactura"
    company.work_center = "Planta Norte"
    company.save()
    assignment = make_assignment(company, nom035_survey, variant="large")
    specs = [("Operaciones", 6, c.NDR_ALTO), ("Ventas", 5, c.NDR_BAJO)]
    for name, count, ndr in specs:
        area = make_area(company, name=name)
        for i in range(count):
            user = make_user_with_profile(
                email=f"{name[:3].lower()}{i}@x.mx", company=company, area=area
            )
            make_score(
                assignment,
                user,
                final_score=90,
                final_ndr=ndr,
                groups=[
                    (c.LEVEL_CATEGORIA, cfg.CAT_AMBIENTE, 12, ndr),
                    (c.LEVEL_DOMINIO, cfg.DOM_CONDICIONES, 12, ndr),
                    (c.LEVEL_DOMINIO, cfg.DOM_LIDERAZGO, 18, c.NDR_MUY_ALTO),
                ],
            )
    make_score(
        assignment,
        make_user_with_profile(email="solo@x.mx", company=company),
        final_ndr=c.NDR_NULO,
    )
    assignment.status = SurveyAssignment.Status.CLOSED
    assignment.save()
    return assignment
