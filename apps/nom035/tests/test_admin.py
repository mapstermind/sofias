import pytest

pytestmark = pytest.mark.django_db


def test_no_nom035_model_shows_an_auto_derived_label(assert_explicit_labels):
    assert_explicit_labels("nom035")
