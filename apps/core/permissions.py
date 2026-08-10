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

from django.contrib.auth import get_permission_codename

PROJECT_APP_LABELS = frozenset({"accounts", "surveys", "responses", "nom035"})

ACTION_VERBS = {
    "add": "Puede agregar",
    "change": "Puede modificar",
    "delete": "Puede eliminar",
    "view": "Puede consultar",
}


def _spanish_names(app_config):
    """{codename: Spanish name} for every permission the app declares."""
    names = {}
    for model in app_config.get_models():
        opts = model._meta
        for action in opts.default_permissions:
            verb = ACTION_VERBS.get(action)
            if verb is None:
                continue
            names[get_permission_codename(action, opts)] = (
                f"{verb} {opts.verbose_name_raw}"
            )
        names.update(dict(opts.permissions))
    return names


def rename_permissions_to_spanish(sender, apps=None, using=None, **kwargs):
    """`post_migrate` receiver. Display-only: codenames are never touched."""
    if sender.label not in PROJECT_APP_LABELS:
        return

    Permission = apps.get_model("auth", "Permission")
    names = _spanish_names(sender)
    queryset = Permission.objects.using(using).filter(
        content_type__app_label=sender.label, codename__in=names
    )
    stale = [p for p in queryset if p.name != names[p.codename]]
    for permission in stale:
        permission.name = names[permission.codename]
    Permission.objects.using(using).bulk_update(stale, ["name"])
