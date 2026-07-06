from django.apps import AppConfig


class Nom035Config(AppConfig):
    name = "apps.nom035"
    label = "nom035"
    default_auto_field = "django.db.models.BigAutoField"

    def ready(self):
        from apps.nom035 import signals  # noqa: F401
