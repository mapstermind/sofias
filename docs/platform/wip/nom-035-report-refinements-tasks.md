# NOM-035 Report Refinements

## What changes

**1. PDF page breaks.** The report PDF starts a new page:

- after the table of contents;
- after sections 4 (already), 5.4, 5.5, 5.6, 5.7, 5.8, 6, 7, 8 and 9 (already);
- inside 5.4, before every categoría after the first;
- inside 5.5, before every categoría group of dominios after the first;
- inside 5.6, before every dominio group of dimensiones after the first.

Breaks are print-only; the on-screen report scrolls as today. Which sections
break becomes a per-section flag in the registry, so the next reorder or new
section decides its own break in one place.

**2. A dominio-tier risk palette.** Every place a **dominio's** risk level is
drawn uses a deeper variant of the five-level palette, so a reader learns that
the deeper family means "dominio". Categorías and the final score keep the
current palette.

| Level | Categoría / final (unchanged) | Dominio |
|---|---|---|
| Nulo | `#D1D5DB` | `#9CA3AF` |
| Bajo | `#22C55E` | `#4A8039` |
| Medio | `#F59E0B` | `#CA9429` |
| Alto | `#F97316` | `#B5531F` |
| Muy alto | `#EF4444` | `#7A1010` |

Validated (OKLab ΔE ×100): worst adjacent dominio pair 16.5 normal / 11.4
under protan/deutan simulation; every mark ≥ 2.5:1 on white. Known weak spot:
Medio dominio vs Medio categoría is ΔE 7.8 — legends and solid badges carry the
distinction there.

Applies to, on the results dashboard and the report alike: dominio
`level_columns`, dominio statistics-strip bands, dominio badges (solid fill —
white text on Bajo/Alto/Muy alto, `#111827` text on Nulo/Medio — against the
tinted categoría badges), the dominio threshold-table header bars in the
report annex, and the dominio badges on the employee valuation card. Every
block that draws dominio marks shows a dominio legend.

**Why.** Requested by the product owner: page breaks make each categoría and
dominio group easy to find in the printed report; the second palette teaches
the reader which charts are categoría-level and which dominio-level.

**Live docs this makes wrong** (rewritten in the last task):
`docs/platform/nom-035-report.md` (PDF section's break list; Visual design
color rule and chart table), `docs/platform/nom-035-results-dashboard.md` (the
five-level palette and legends), `docs/platform/nom-035-analytics.md`
(employee card badges), `apps/core/CLAUDE.md` (Charts / valuation_extras
palette), `apps/reports/CLAUDE.md` (registry flags).

**ADRs:** none touched.

---

# Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Print-only page breaks at the listed points, and a dominio-tier
variant of the risk palette everywhere a dominio's level is drawn.

**Architecture:** Breaks: a `break_before` flag on registry `Section`s plus a
`report-group` class on repeated groups, turned into page breaks by
`report-print.css` (PDF only). Palette: the data layer already emits color
*keys* (`ndr-<level>`); dominio rows emit `dom-<level>` instead, and every
palette table (`valuation_extras`, `charts._COLORS/_HEX`, `report.css`) gains
the `dom-` entries — so templates change only where they pick a badge or
legend.

**Tech Stack:** Django templates, plain CSS (report), Tailwind v4 arbitrary
values (screen), WeasyPrint 70.

**Spec:** [`docs/platform/nom-035-report.md`](../nom-035-report.md),
[`docs/platform/nom-035-results-dashboard.md`](../nom-035-results-dashboard.md)

## Global Constraints

- Dominio hexes exactly: nulo `#9CA3AF`, bajo `#4A8039`, medio `#CA9429`, alto `#B5531F`, muy_alto `#7A1010`. Categoría/final hexes unchanged.
- Dominio badge text: `#FFFFFF` on bajo/alto/muy_alto, `#111827` on nulo/medio.
- Color keys: categoría/final `ndr-<level>`, dominio `dom-<level>`; `_COLORS` and `_HEX` keep identical key sets.
- Page breaks are print-only (report-print.css); the screen report is unchanged.
- WeasyPrint 70 honours no width media query; anything the PDF needs goes in report-print.css or report-wide.css.
- Everything a user sees is Spanish; mobile-first; no horizontal scroll at 360 px.
- Never commit without asking (CLAUDE.md gate 4): each task ends at a green suite with an uncommitted diff, the touched files and a proposed commit message.
- Any template/static change ends with `npm run build:css`.

## Review Focus

1. **A dominio whose whole block was skipped** (no GroupScore rows) — its row still renders with the dominio palette and no crash. Pinned in Task 2 (`test_empty_dominio_row_keeps_the_dominio_palette`).
2. **A published snapshot from before this change** — has no `palette` field; `load` must default it to `"ndr"`, not KeyError. Pinned in Task 2 (`test_load_defaults_missing_palette`).
3. **Guía II report** (fewer dominios, no Entorno) — group breaks and dominio legends still render. Pinned in Task 1 and Task 4.
4. **5.4 with a single categoría / 5.6 with a single dominio group** — no blank page: only groups *after the first* break. Pinned in Task 1 (`test_first_group_does_not_break`).
5. **Dashboard dominio disclosure** — dominio columns use the dominio palette, categoría rows don't. Pinned in Task 3.

---

### Task 1: Print page breaks

**Files:**
- Modify: `apps/reports/sections.py` (`Section`, `RenderedSection`, `_walk`, `REGISTRY`, `RESULTS_CHILDREN`)
- Modify: `templates/reports/_document.html`
- Modify: `templates/reports/sections/results/_categoria.html`, `_dominio.html`, `_dimension.html`
- Modify: `static/css/report-print.css`
- Test: `apps/reports/tests/test_page_breaks.py`

**Interfaces:**
- Produces: `Section.break_before: bool = False`, `RenderedSection.break_before: bool`; CSS classes `report-break-before`, `report-break-after`, `report-group`.

- [ ] **Step 1: Failing tests** — `apps/reports/tests/test_page_breaks.py`:

```python
import re
from pathlib import Path

import pytest
from django.template.loader import render_to_string

from apps.reports.models import Report
from apps.reports.sections import REGISTRY, context_for, render_sections

pytestmark = pytest.mark.django_db
PRINT_CSS = Path(__file__).resolve().parents[3] / "static/css/report-print.css"

BREAK_BEFORE = {
    "resultados", "resultados.dominio", "resultados.dimension",
    "resultados.area", "resultados.guia1", "criterios", "recomendaciones",
    "conclusiones", "responsables", "anexo",
}


def _flat(sections):
    for s in sections:
        yield s
        yield from _flat(s.children)


def _html(report):
    ctx = context_for(report)
    return render_to_string(
        "reports/_document.html", {"sections": render_sections(ctx), "ctx": ctx}
    )


def test_registry_flags_the_requested_breaks():
    flagged = {s.key for s in _flat(REGISTRY) if s.break_before}
    assert flagged == BREAK_BEFORE


def test_flagged_sections_carry_the_break_class(scored_assignment):
    html = _html(Report(assignment=scored_assignment))
    for key in BREAK_BEFORE:
        slug = key.replace(".", "")
        tag = re.search(rf'<section id="sec-{slug}"[^>]*>', html).group(0)
        assert "report-break-before" in tag, key
    assert re.search(r'class="[^"]*report-toc[^"]*report-break-after', html) or \
        re.search(r'class="[^"]*report-break-after[^"]*report-toc', html)


def test_groups_are_marked_for_breaking(scored_assignment):
    html = _html(Report(assignment=scored_assignment))
    for slug in ("resultadoscategoria", "resultadosdominio", "resultadosdimension"):
        part = html.split(f'id="sec-{slug}"')[1].split("</section>")[0]
        assert "report-group" in part, slug


def test_print_css_turns_flags_into_page_breaks():
    css = PRINT_CSS.read_text()
    assert re.search(r"\.report-break-before\s*\{[^}]*break-before:\s*page", css)
    assert re.search(r"\.report-break-after\s*\{[^}]*break-after:\s*page", css)
    assert re.search(r"\.report-group\s*\+\s*\.report-group\s*\{[^}]*break-before:\s*page", css)


def test_first_group_does_not_break():
    css = PRINT_CSS.read_text()
    # Only a group that follows another group breaks.
    assert not re.search(r"(^|[\s,}])\.report-group\s*\{[^}]*break-before", css)
```

(The section-id split assumes each group lives inside its section; adjust the
slicing to the real markup if a nested `</section>` ends the slice early.)

- [ ] **Step 2: Run** `pytest apps/reports/tests/test_page_breaks.py -v` — expect FAIL (`Section` has no `break_before`).
- [ ] **Step 3: Registry.** Add `break_before: bool = False` to `Section` and `RenderedSection`; `_walk` copies it. Set `break_before=True` on exactly the keys in `BREAK_BEFORE` (keep keyword arguments readable). Replace the existing hard-coded `.report-section--resultados` / `--anexo` break rules in `report-print.css` with the flag.
- [ ] **Step 4: Markup.** `_document.html`: add `report-break-before` to a section's/subsection's class list when `s.break_before`; give the TOC wrapper `report-break-after`. In `_categoria.html`, `_dominio.html`, `_dimension.html` wrap each categoría / categoría group / dominio group in an element with class `report-group` (siblings of one another, so the adjacent-sibling rule applies). Keep the legend and n-line after the last group, outside the groups.
- [ ] **Step 5: CSS** (`static/css/report-print.css`):

```css
/* Page breaks — declared per section in apps/reports/sections.py (break_before). */
.report-break-before { break-before: page; }
.report-break-after { break-after: page; }
/* Repeated groups (5.4 categorías, 5.5 categoría groups, 5.6 dominio groups):
   every group after the first starts a new page. */
.report-group + .report-group { break-before: page; }
```

Keep the portada's existing `break-after: page`.
- [ ] **Step 6: Run** the new tests, then `pytest apps/reports -q` — PASS.
- [ ] **Step 7: Look at it.** Render a published PDF for a Guía III fixture-like company in the scratchpad, `pdftoppm -r 50 -png`, read the pages: TOC alone; section 1 on a new page; 5.4 categorías one per page after the first; 5.5 groups; 5.6 groups; breaks after 5.6–5.8, 6, 7, 8; no blank pages. Repeat once for Guía II.
- [ ] **Step 8:** `pytest -q && ruff check . && ruff format . && npm run build:css`. Stop; list files; propose `feat(reports): print page breaks per section and group`.

---

### Task 2: Dominio color keys in the data layer

**Files:**
- Modify: `apps/nom035/results.py` (`_ndr_slices`, `DistributionRow`, `_distribution`, `_stats`, `_valuation`, `_areas`)
- Modify: `apps/reports/snapshot.py` (`_distribution` loader)
- Test: `apps/nom035/tests/test_results.py`, `apps/reports/tests/test_snapshot.py`

**Interfaces:**
- Produces: `PALETTE_NDR = "ndr"`, `PALETTE_DOMINIO = "dom"` in `apps/nom035/results.py`; `DistributionRow.palette: str = PALETTE_NDR`; slices colored `f"{row.palette}-{level}"`; dominio `StatsRow.strip_bands` colored `dom-<level>`.

- [ ] **Step 1: Failing tests.** Add to `apps/nom035/tests/test_results.py` (uses the existing `scored_large` fixture):

```python
def test_dominio_rows_use_the_dominio_palette(scored_large):
    results = results_for(scored_large, ResultsQuery(), suppress_small_groups=True)
    cat = results.categoria_distribution[0]
    assert {s.color.split("-")[0] for s in cat.slices} == {"ndr"}
    assert {s.color.split("-")[0] for s in cat.children[0].slices} == {"dom"}
    assert all(b[1].startswith("ndr-") for b in results.categoria_stats[0].strip_bands)
    assert all(b[1].startswith("dom-") for b in results.categoria_stats[0].children[0].strip_bands)
    assert all(s.color.startswith("ndr-") for s in results.final_distribution.slices)


def test_empty_dominio_row_keeps_the_dominio_palette(scored_large):
    results = results_for(scored_large, ResultsQuery(), suppress_small_groups=True)
    empty = [d for c in results.categoria_distribution for d in c.children if d.n == 0]
    assert empty and all(s.color.startswith("dom-") for s in empty[0].slices)
```

Add to `apps/reports/tests/test_snapshot.py`:

```python
def test_load_defaults_missing_palette(scored_assignment):
    raw = json.loads(json.dumps(dump(build_report_data(scored_assignment))))
    for cat in raw["categoria_distribution"]:
        cat.pop("palette", None)
        for dom in cat["children"]:
            dom.pop("palette", None)
    data = load(raw)
    assert data.categoria_distribution[0].palette == "ndr"
```

- [ ] **Step 2: Run** — FAIL.
- [ ] **Step 3: Implement.**

```python
PALETTE_NDR = "ndr"
PALETTE_DOMINIO = "dom"


def _ndr_slices(counts, palette=PALETTE_NDR) -> tuple[Slice, ...]:
    return tuple(
        Slice(level, c.NDR_LABELS[level], count, f"{palette}-{level}")
        for level, count in counts
    )
```

`DistributionRow` gains `palette: str = PALETTE_NDR` (after `counts`, before `children`); its `slices` passes `self.palette`. `ParticipationRow.slices` stays categoría (final score). `_distribution(key, label, ndrs, children=(), palette=PALETTE_NDR)`. In `_valuation`, dominio children get `palette=PALETTE_DOMINIO`. `_stats` builds band keys with `PALETTE_DOMINIO if level == c.LEVEL_DOMINIO else PALETTE_NDR`. Per-área categoría rows stay `ndr`.
- [ ] **Step 4: Snapshot loader.** In `apps/reports/snapshot.py` `_distribution`, pass `palette=raw.get("palette", "ndr")`. `dump` needs nothing (`asdict` includes it).
- [ ] **Step 5:** `pytest apps/nom035 apps/reports -q` — PASS (round-trip test still green).
- [ ] **Step 6:** full `pytest -q && ruff check . && ruff format .`. Stop; propose `feat(nom035): dominio rows carry the dominio color key`.

---

### Task 3: Dominio palette in the shared components (dashboard + employee card)

**Files:**
- Modify: `apps/core/templatetags/valuation_extras.py`
- Modify: `apps/core/templatetags/charts.py` (`_COLORS`, `_HEX`)
- Modify: `templates/core/employee_detail.html` (dominio badges)
- Modify: `templates/core/results/_ndr_legend.html` and the dashboard partials that show dominio marks (`_categoria_distribution.html`, `_categoria_stats.html`, `_dominios_summary.html` — check each for dominio rows)
- Test: `apps/core/tests/test_valuation_extras.py`, `apps/core/tests/test_chart_components.py`, `apps/core/tests/test_results_views.py`, `apps/core/tests/test_employee_valuation_panel.py`

**Interfaces:**
- Produces: filters `ndr_badge`, `ndr_bar`, `ndr_fill` accept an optional tier argument (`"dominio"`): `{{ dom.ndr|ndr_badge:"dominio" }}`; chart keys `dom-<level>` in both `_COLORS` and `_HEX`.

- [ ] **Step 1: Failing tests.**

```python
# test_valuation_extras.py
from apps.core.templatetags.valuation_extras import ndr_badge, ndr_bar, ndr_fill

DOMINIO_HEX = {"nulo": "#9CA3AF", "bajo": "#4A8039", "medio": "#CA9429",
               "alto": "#B5531F", "muy_alto": "#7A1010"}


def test_dominio_tier_classes():
    for level, hex_ in DOMINIO_HEX.items():
        assert f"[{hex_}]" in ndr_bar(level, "dominio")
        assert f"[{hex_}]" in ndr_fill(level, "dominio")
        assert f"bg-[{hex_}]" in ndr_badge(level, "dominio")
    assert "text-white" in ndr_badge("bajo", "dominio")
    assert "text-gray-900" in ndr_badge("medio", "dominio")
    assert ndr_badge("bajo") == ndr_badge("bajo", "")  # categoría unchanged


# test_chart_components.py
from apps.core.templatetags.charts import _COLORS, _HEX


def test_dominio_keys_have_classes_and_hexes():
    for level, hex_ in DOMINIO_HEX.items():  # same dict as above
        assert f"dom-{level}" in _COLORS
        assert _HEX[f"dom-{level}"] == hex_
```

Also: a results-view test asserting the dashboard body contains `fill="#4A8039"` (or another dominio hex) inside the dominio disclosure and the dominio legend text; an employee-panel test asserting a dominio badge carries `bg-[#...]` and a categoría badge does not.
- [ ] **Step 2: Run** — FAIL.
- [ ] **Step 3: Filters.** In `valuation_extras.py` add dominio tables with classes spelled out in full (Tailwind scans this file): bars `bg-[#9CA3AF]` …, fills `fill-[#9CA3AF]` …, badges `bg-[#4A8039] text-white ring-[#4A8039]/30` (nulo/medio: `text-gray-900`). Each filter takes `tier=""`; `"dominio"` selects the dominio table. Docstrings state the two tiers.
- [ ] **Step 4: Chart palette.** `_COLORS` adds `f"dom-{level}": (ndr_fill(level, "dominio"), ndr_bar(level, "dominio"))`; `_HEX` adds the five dominio hexes. The module docstring names both tiers.
- [ ] **Step 5: Templates.** `employee_detail.html`: dominio badges use `|ndr_badge:"dominio"` (categoría badges and the NDR scales stay). Dashboard: `_ndr_legend.html` accepts a `tier` and renders the dominio legend (heading *Dominios*) with `|ndr_bar:"dominio"`; include it, after the categoría legend, wherever dominio rows render (inside or after the *Dominios (n)* disclosure in both the distribution and statistics sections). Charts themselves need no template change — the slice keys carry the palette.
- [ ] **Step 6:** `pytest apps/core -q` — PASS; `npm run build:css` and confirm the arbitrary classes compiled (`grep -c "4A8039" static/css/output.css`).
- [ ] **Step 7:** full `pytest -q && ruff check . && ruff format .`. Stop; propose `feat(core): dominio-tier risk palette on the dashboard and employee card`.

---

### Task 4: Dominio palette in the report

**Files:**
- Modify: `static/css/report.css` (`report-badge--dom-*`, `report-level--dom-*`, legend swatches)
- Modify: `templates/reports/_badge.html`, `templates/reports/sections/_recomendaciones.html`, `templates/reports/sections/_threshold_table.html`, `templates/reports/sections/_anexo.html`, `templates/reports/sections/results/_legend.html`, `_dominio.html`
- Modify: `apps/reports/sections.py` (legend context for the dominio tier; method tables pass a tier per table)
- Test: `apps/reports/tests/test_results_sections.py`, `apps/reports/tests/test_sections.py`

**Interfaces:**
- Consumes: `dom-<level>` keys (Task 2), chart hex attributes (Task 3).
- Produces: `_badge.html` takes `tier` (`""` or `"dom"`); `_threshold_table.html` takes `tier`; `_legend.html` takes `tier` and a heading.

- [ ] **Step 1: Failing tests.**

```python
def test_recommendation_badges_use_the_dominio_tier(scored_assignment):
    html = _html(Report(assignment=scored_assignment))
    recs = html.split('id="sec-recomendaciones"')[1].split("</section>")[0]
    assert "report-badge--dom-" in recs


def test_criteria_badges_stay_categoria(scored_assignment):
    html = _html(Report(assignment=scored_assignment))
    crit = html.split('id="sec-criterios"')[1].split("</section>")[0]
    assert "report-badge--dom-" not in crit


def test_dominio_section_draws_dominio_marks_and_legend(scored_assignment):
    html = _html(Report(assignment=scored_assignment))
    dom = html.split('id="sec-resultadosdominio"')[1].split('id="sec-resultadosdimension"')[0]
    assert 'fill="#4A8039"' in dom or 'fill="#7A1010"' in dom or 'fill="#B5531F"' in dom
    assert "report-legend--dom" in dom


def test_annex_dominio_thresholds_use_the_dominio_tier(scored_assignment):
    html = _html(Report(assignment=scored_assignment))
    annex = html.split('id="sec-anexo"')[1]
    assert "report-level--dom-" in annex
    assert "report-level--muy_alto" in annex  # final/categoría tables unchanged
```

(`_html` as in the existing report tests.)
- [ ] **Step 2: Run** — FAIL.
- [ ] **Step 3: CSS.** In `report.css` add, next to the existing level/badge rules: `.report-badge--dom-<level>` solid (`background: <hex>; color: #FFFFFF` or `#111827`; `border: 1px solid <hex>`), `.report-level--dom-<level>` bars with the dominio hexes, and `.report-legend--dom` swatches (the legend swatch class names follow whatever `_legend.html` uses today, with the `dom-` level keys).
- [ ] **Step 4: Templates.** `_badge.html`: `report-badge--{% if tier %}{{ tier }}-{% endif %}{{ level }}`. `_recomendaciones.html` passes `tier="dom"`; `_criterios.html` passes nothing. `_threshold_table.html` takes `tier`; `_anexo.html` passes `tier="dom"` for the dominio table only. `_legend.html` takes `tier`/heading; `_dominio.html` renders the categoría legend and a *Dominios* legend in the dominio tier (its marks are dominio). The builder in `sections.py` supplies both legends.
- [ ] **Step 5:** `pytest apps/reports -q` — PASS; `npm run build:css`.
- [ ] **Step 6: Look at it.** Render screen (dev server, you or the user) and PDF (scratchpad → PNG): 5.5 dominio columns/strips deep; categoría rows unchanged; recommendation badges solid; annex dominio header bars deep; legends present. Check Medio dominio vs categoría is distinguishable side by side.
- [ ] **Step 7:** full `pytest -q && ruff check . && ruff format .`. Stop; propose `feat(reports): dominio-tier palette in the report`.

---

### Task 5: Documentation (always last)

**Files:**
- Modify: `docs/platform/nom-035-report.md` — PDF section: the page-break list (after the TOC; before 5.5–5.8, 6–9 and Resultados/Anexo; groups in 5.4–5.6 after the first) and the `break_before` registry flag; Visual design: two palette tiers with the table of hexes, the dominio badge treatment, legends; chart-placement table rows for 5.5 and Recomendaciones; a Key decision for the dominio tier (with the ΔE figures and the Medio caveat).
- Modify: `docs/platform/nom-035-results-dashboard.md` — the palette: dominio rows/strips in the dominio tier, the dominio legend.
- Modify: `docs/platform/nom-035-analytics.md` — the employee card's dominio badges.
- Modify: `apps/core/CLAUDE.md` — valuation_extras tiers (`|ndr_badge:"dominio"`), chart keys `ndr-`/`dom-`.
- Modify: `apps/reports/CLAUDE.md` — `break_before` and `report-group`.

- [ ] **Step 1:** Rewrite those passages in present tense, no migration commentary; read the code for exact names.
- [ ] **Step 2:** `pytest -q && ruff check .`. Stop; propose `docs: page breaks and the dominio palette`.
