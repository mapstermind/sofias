# Branding and UI/UX plan — pending work

Phases 0–4 shipped (PRs #14–#19). What they built is described in
`docs/platform/design-system.md` (tokens, components, page rules, *Voz*) and
`docs/platform/localization.md` (glossary). The palette exploration that led to
the two finalists is recorded in `docs/adr/adr-0006-brand-palette.md`
(Proposed). This file keeps only what is still open.

Audience: executives and administrators first (dashboards, the report);
employees answer the survey once. Tone: calm and professional, with warmth.

---

## 1. Palette decision (with the client)

Two finalists ship behind a switch: **Petróleo** (blue-teal + periwinkle, cool
neutrals) and **Pizarra** (ink slate + peach, warm stone). The client compares
them on the real screens — `docs/branding/palette-preview.html` shows the main
screens in both palettes, phone and desktop, side by side. Two pages under
`/propuestas/` show the same comparison in the app itself, and a third palette,
**Azul marino**, appears there only so the client can see it was evaluated and
discarded (see §5).

After she picks:
- Accept ADR-0006 with the winner and the reason.
- Delete the losing palette and the switch (steps in
  `docs/internal/user-guides/rebranding.md`).
- Update the palette table in `design-system.md`.
- Remove the `/propuestas/` pages, navy included (§5).

## 2. Results dashboard redesign (with the client)

The results page (`/tablero-empresa/resultados/`) gets a new layout as part of
this branding work: it is the screen executives spend the most time on. The
proposal is drawn with sample data at `/propuestas/resultados/` (commit
`674f347`, Proposal A). Its last section, *Decisiones por revisar*, lists eight
decisions, each with today's behavior, the proposal, the cost and the question
for the client. A design canvas with Proposal A and an alternative, Proposal B
(center-split bars per categoría), is at
https://claude.ai/artifact/XmG48dJDWeGAqnCV1iMGoy (private; share it from its
page before sending it on).

What the proposal covers, in short:
- A main box for the final score: one stem per risk level on a variable
  scale, the selected level's share as the big figure, and a
  *Distribución* / *Estadísticas* switch.
- A right-hand column of categorías that open to their dominios, each row
  with the share in alto or muy alto.
- A second row of three boxes: participation, Guía I, and who answered.
- *Por área* rows with a button that adds the área to the filters.
- A **Ver** selector, separate from Filtros, that switches the page between
  the final score and one categoría. With a categoría chosen, the main box shows
  it and the right column shows its dominios, each with its statistics.
- Screen only: the report and its PDF keep today's chart components.

Order of work:
1. **After the palette decision (§1).** Decisions 4 (two color tiers) and 7
   (bigger type, borderless cards) are judged in the winning palette.
2. **Settle the eight decisions with the client** on `/propuestas/resultados/`,
   next to the real page. Note which parts of Proposal B, if any, are wanted.
3. **Route it** per `CLAUDE.md`. Expect *Doc: extend*
   `docs/platform/nom-035-results-dashboard.md`, with the client's answers in
   the change brief (`docs/platform/wip/nom-035-results-dashboard-tasks.md`), and
   *Path: branch → PR*. Things to raise in the brief:
   - Decision 1 (share in alto or muy alto) against the doc's out-of-scope rule
     that the page gives no company- or área-level verdict.
   - Decision 7: if the style is platform-wide, it also changes
     `docs/platform/design-system.md` and `/estilos/`.
   - Decision 6: Ver is a new query parameter in `results_query.py` and in
     `static/ts/results_dashboard.ts`, which no Python test covers.
4. **Build from the proposal templates, don't promote them.** The partials in
   `templates/core/proposal/` draw fixed states from invented data. The real
   page needs these working: selecting a level, the
   *Distribución* / *Estadísticas* switch, Ver, the área button, and the
   small-group rule in the right column.
5. **Check it at 360 px in a browser** (the stems' level labels, the *Por área*
   rows, the dominios' range charts) and list what to click in the PR.
6. **The redesign branch deletes `/propuestas/resultados/`** (the files under
   *`/propuestas/resultados/`* in §5) in its own diff, once the real page
   replaces it.

The Phase 5 walkthrough *dashboard → results → report* (§3) runs on the
redesigned page.

## 3. Phase 5: QA and handoff

- Cross-browser check (Chrome, Safari, Firefox) and responsive check at 375,
  768 and 1280, on the remaining palette.
- Final contrast run (`apps/core/tests/test_design_tokens.py`) and an
  accessibility pass: keyboard-only walkthrough of sign-in → survey → submit,
  and dashboard → results → report; a screen-reader spot check.
- Finish `docs/internal/user-guides/rebranding.md` (draft) once the name, logo
  and palette are known.

## 4. Pending on the client

- Final name and logo (placeholders today; `settings.BRAND`, `static/img/logo.svg`).
- The survey instructions' final text and video, the confidentiality wording
  and *quien te invitó* — `docs/platform/nom-035-valoracion-supuestos.md` §3.
- One report per company when it has several localidades — same doc, §4.

## 5. Remove the `/propuestas/` pages

Both pages are scaffolding for the client's decision, not product. They are
shown only to whoever may see `/estilos/` (`brand.can_switch_palette`), and
nothing outside them depends on what they add. Remove the palette page and the
shared pieces in one commit once the palette is chosen, so no dead code is
left behind. The results page is removed by the redesign branch (§2); if that
branch has not landed yet, keep its files and the partials it includes, and
expect step 3's grep below to list them.

**`/propuestas/resultados/`** — the proposed results dashboard (commit
`674f347`):
- `apps/core/results_proposal.py`
- `apps/core/tests/test_results_proposal.py`
- `templates/core/results_proposal.html`
- `ResultsProposalView` in `apps/core/views.py` and its `results_proposal`
  import; the `propuestas/resultados/` route in `apps/core/urls.py`.

**`/propuestas/paletas/`** — the palettes side by side, with navy:
- `apps/core/palette_proposal.py`
- `apps/core/tests/test_palette_proposal.py`
- `templates/core/palette_proposal.html`
- `static/css/proposal-navy.css` — the only definition of navy. It is not in
  `settings.BRAND_PALETTES`, `main.css` or the contrast test, so deleting the
  file removes the palette entirely.
- `PaletteProposalView` in `apps/core/views.py` and its `palette_proposal`
  import; the `propuestas/paletas/` route in `apps/core/urls.py`.
- The `{% block head_extra %}{% endblock %}` line in `templates/base.html`. It
  was added only so this page could load `proposal-navy.css`; remove it unless
  another page has started using it.

**Shared by both** — delete the whole `templates/core/proposal/` directory
(`_hero`, `_cards`, `_areas`, `_categorias`, `_dominios`, `_decisions`,
`_toolbar`, `_level_bar`, `_level_cells`, and `_palette_specimen`). Before
deleting `_level_bar.html` or `_level_cells.html`, `grep -rn "proposal/" templates apps`
to confirm no real page has started including them.

**Then:**
1. Delete the `PaletteProposalView` paragraph in `apps/core/CLAUDE.md` (under
   *Components*). Leave nothing that says the pages ever existed.
2. Run `npm run build:css` and commit `static/css/output.css`; the classes only
   those templates used drop out of the build.
3. Check that nothing is left:
   `grep -rIn "propuestas\|results_proposal\|palette_proposal\|PaletteProposal\|ResultsProposal\|proposal-navy\|head_extra\|core/proposal" . --exclude-dir=node_modules --exclude-dir=.venv --exclude-dir=.git`
   should print nothing, apart from this plan and the rest of `docs/branding/`.
4. Run `pytest` and `ruff check .`. `can_switch_palette` stays: the styleguide
   and the palette switch use it until the switch itself is deleted.

Delete `docs/branding/palette-preview.html` with the rest of `docs/branding/`
when this plan is closed.

## 6. Deferred decisions

Not part of this plan unless decided otherwise:
- Dark mode. The token layer makes it one more variable block.
- Animation beyond the basic transitions.
- Final typeface, pending the client (Figtree today).
