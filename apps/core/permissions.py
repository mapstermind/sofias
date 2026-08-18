"""Rewrite auto-generated permission names into Spanish.

Django builds the four built-in permission names from a hardcoded, untranslated
`"Can %s %s"` template, so a Spanish `Meta.verbose_name` alone produces
"Can add empresa" in the Groups permission picker. `create_permissions` only
ever *creates* missing rows and never renames one whose label changed, so the
correction has to be applied here rather than left to it.

Declaring the names instead — `Meta.default_permissions = ()` plus all four
actions in `Meta.permissions` — also works, but a model with an incomplete
block then gets no permissions at all. See `docs/platform/localization.md`.
"""

from django.apps import apps as global_apps
from django.conf import settings
from django.contrib.auth import get_permission_codename
from django.db import DEFAULT_DB_ALIAS
from django.utils import translation

ACTION_VERBS = {
    "add": "Puede agregar",
    "change": "Puede modificar",
    "delete": "Puede eliminar",
    "view": "Puede ver",
}


def project_app_labels():
    """Labels of the project's own apps that own models.

    Derived rather than listed so a newly registered app is covered by the
    receiver and by the `assert_explicit_labels` guard without anyone having to
    remember to add it in two places.
    """
    return frozenset(
        app_config.label
        for app_config in global_apps.get_app_configs()
        if app_config.name.startswith("apps.") and app_config.models_module is not None
    )


def _spanish_names(app_config):
    """{codename: Spanish name} for every permission the app declares."""
    names = {}
    # `verbose_name_raw` deliberately renders the *untranslated* name, which is
    # right for Django (it stores an English msgid) and wrong here: `User`
    # inherits `AbstractUser`'s lazy `_("user")` and would yield "Puede agregar
    # user". Pin the language so the result cannot depend on whatever was active
    # when `migrate` happened to run.
    with translation.override(settings.LANGUAGE_CODE):
        for model in app_config.get_models():
            opts = model._meta
            verbose_name = str(opts.verbose_name)
            for action in opts.default_permissions:
                verb = ACTION_VERBS.get(action)
                if verb is None:
                    continue
                names[get_permission_codename(action, opts)] = f"{verb} {verbose_name}"
            names.update(dict(opts.permissions))
    return names


def rename_permissions_to_spanish(
    sender, apps=global_apps, using=DEFAULT_DB_ALIAS, **kwargs
):
    """`post_migrate` receiver. Display-only: codenames are never touched.

    `apps` and `using` carry defaults because `post_migrate` is not only sent by
    `migrate`: `manage.py flush` — and so the teardown of every
    `transaction=True` test — emits it without an `apps` kwarg.
    """
    if sender.label not in project_app_labels():
        return

    names = _spanish_names(sender)
    if not names:
        return

    Permission = apps.get_model("auth", "Permission")
    queryset = Permission.objects.using(using).filter(
        content_type__app_label=sender.label, codename__in=names
    )
    stale = [p for p in queryset if p.name != names[p.codename]]
    for permission in stale:
        permission.name = names[permission.codename]
    Permission.objects.using(using).bulk_update(stale, ["name"])
