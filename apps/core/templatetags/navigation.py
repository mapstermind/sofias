"""`{% company_nav %}`: the company sections a viewer may open, as a switcher and as tabs.

One list serves both renderings, so the phone and the desktop cannot disagree.
Each section is offered only when the viewer holds the permissions its view
checks, so a link never leads to a refusal. See docs/platform/design-system.md
(Navigation).
"""

from dataclasses import dataclass

from django import template
from django.urls import reverse

from apps.accounts.roles import labels_for_names

register = template.Library()


@dataclass(frozen=True)
class Section:
    label: str
    admin_url: str  # an Administrador viewing any company (`is_admin_view`)
    own_url: str | None  # an executive viewing their own company; None: admin only
    admin_perms: tuple[str, ...]
    own_perms: tuple[str, ...]
    lit_by: tuple[str, ...]  # view names, child pages included, that light it


SECTIONS = (
    Section(
        "Tablero",
        "core:company_dashboard_for",
        "core:company_dashboard",
        ("can_view_dashboard", "can_manage_surveys"),
        ("can_view_dashboard",),
        ("core:company_dashboard_for", "core:company_dashboard"),
    ),
    Section(
        "Colaboradores",
        "core:company_employee_list_for",
        "core:company_employee_list",
        ("can_manage_employees", "can_manage_surveys"),
        ("can_manage_employees",),
        (
            "core:company_employee_list_for",
            "core:company_employee_list",
            "core:company_employee_detail_for",
            "core:company_employee_detail",
        ),
    ),
    Section(
        "Resultados",
        "core:company_results_for",
        "core:company_results",
        ("can_view_insights",),
        ("can_view_insights",),
        (
            "core:company_results_for",
            "core:company_results",
            "core:company_results_fragment_for",
            "core:company_results_fragment",
        ),
    ),
    Section(
        "Reportes",
        "reports:admin_list",
        None,
        ("can_edit_report",),
        (),
        (
            "reports:admin_list",
            "reports:admin_detail",
            "reports:admin_edit",
        ),
    ),
)


def sections(request, company, is_admin_view) -> list[dict]:
    """The sections `request.user` may open for `company`, in order, one marked active."""
    if company is None or request is None:
        return []
    user = request.user
    match = getattr(request, "resolver_match", None)
    current = match.view_name if match else ""
    items = []
    for section in SECTIONS:
        if section.own_url is None and not is_admin_view:
            continue
        perms = section.admin_perms if is_admin_view else section.own_perms
        if not all(user.has_perm(f"accounts.{p}") for p in perms):
            continue
        url = (
            reverse(section.admin_url, args=[company.reference_code])
            if is_admin_view
            else reverse(section.own_url)
        )
        items.append(
            {"label": section.label, "url": url, "active": current in section.lit_by}
        )
    return items


@register.inclusion_tag("_company_nav.html", takes_context=True)
def company_nav(context):
    items = sections(
        context.get("request"), context.get("company"), context.get("is_admin_view")
    )
    if len(items) < 2:
        items = []
    active = next((i for i in items if i["active"]), None)
    return {"items": items, "active": active}


@register.filter
def role_label(user):
    """The viewer's role, as the Spanish label a user reads."""
    return ", ".join(labels_for_names(user.groups.values_list("name", flat=True)))
