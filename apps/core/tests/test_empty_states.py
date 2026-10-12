"""Empty states draw through one partial: see docs/platform/design-system.md (Empty states)."""

from pathlib import Path

import pytest
from django.template.loader import render_to_string

ROOT = Path(__file__).resolve().parents[3]


def empty(**context):
    return render_to_string("components/_empty.html", context)


def test_it_draws_the_icon_title_body_and_action():
    html = empty(
        icon="users",
        title="Ningún colaborador coincide",
        body="Prueba con otra búsqueda.",
        action_url="/tablero-empresa/colaboradores/",
        action_label="Limpiar filtros",
    )
    assert "<svg" in html and "bg-neutral-100" in html
    assert html.index("Ningún colaborador") < html.index("Prueba con otra")
    assert 'href="/tablero-empresa/colaboradores/"' in html and "btn-secondary" in html
    assert "border-dashed" in html


def test_it_needs_only_a_body():
    html = empty(body="No hay empresas creadas aún.")
    assert "No hay empresas creadas aún." in html
    assert "<svg" not in html and "<a " not in html


def test_compact_uses_less_room():
    assert "py-8" in empty(body="x", compact=True)
    assert "py-12" in empty(body="x")


def test_no_template_hand_rolls_an_empty_state():
    allowed = {"components/_empty.html"}
    hits = [
        str(p.relative_to(ROOT / "templates"))
        for p in (ROOT / "templates").rglob("*.html")
        if "border-dashed" in p.read_text()
        and str(p.relative_to(ROOT / "templates")) not in allowed
    ]
    assert not hits, "use components/_empty.html:\n" + "\n".join(hits)


@pytest.mark.django_db
def test_the_empty_roster_offers_to_clear_its_filters(
    client, make_user_with_profile, company, bootstrap_groups
):
    viewer = make_user_with_profile(email="exec@example.com", company=company)
    viewer.groups.add(bootstrap_groups["Principal Exec"])
    client.force_login(viewer)
    html = client.get("/tablero-empresa/colaboradores/?q=zzzz-nadie").content.decode()
    assert "Ningún colaborador coincide con la búsqueda o los filtros." in html
    assert "Limpiar filtros" in html and "border-dashed" in html
