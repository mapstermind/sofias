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

## 2. Results dashboard redesign

The results page (`/tablero-empresa/resultados/`) has the redesigned layout,
described in `docs/platform/nom-035-results-dashboard.md`. Left for the Phase 5
walkthrough *dashboard → results → report* (§3): judge the two risk ramps
(decision 4) and the page's larger type and borderless cards (decision 7) in the
winning palette. If the style is to be platform-wide, it also changes
`docs/platform/design-system.md` and `/estilos/`.

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
left behind.

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

**Shared** — delete the whole `templates/core/proposal/` directory
(`_palette_specimen` and `_level_bar`). Before deleting `_level_bar.html`,
`grep -rn "proposal/" templates apps` to confirm no real page has started
including it.

**Then:**
1. Delete the `PaletteProposalView` paragraph in `apps/core/CLAUDE.md` (under
   *Components*). Leave nothing that says the pages ever existed.
2. Run `npm run build:css` and commit `static/css/output.css`; the classes only
   those templates used drop out of the build.
3. Check that nothing is left:
   `grep -rIn "propuestas\|palette_proposal\|PaletteProposal\|proposal-navy\|head_extra\|core/proposal" . --exclude-dir=node_modules --exclude-dir=.venv --exclude-dir=.git`
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
