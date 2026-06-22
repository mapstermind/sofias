from django.apps import apps


def test_nom035_app_is_registered():
    assert apps.is_installed("apps.nom035")
    config = apps.get_app_config("nom035")
    assert config.name == "apps.nom035"
