from django.apps import AppConfig
from django.db.models.signals import post_migrate


class CoreConfig(AppConfig):
    name = "apps.core"
    label = "core"
    default_auto_field = "django.db.models.BigAutoField"

    def ready(self):
        from apps.core.permissions import rename_permissions_to_spanish

        # Connected without a sender: the receiver filters to the project's apps
        # itself, and each app's permissions only exist once its own post_migrate
        # has fired. `django.contrib.auth` is earlier in INSTALLED_APPS, so its
        # create_permissions receiver always runs before this one.
        post_migrate.connect(rename_permissions_to_spanish)
