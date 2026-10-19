# ADR-0006: The brand palette

Date: 2026-10-12
Status: Accepted

## Context

SOFIA-S needs a brand palette before the client confirms a name or a logo. The
product's heaviest screens are executive dashboards and the results report,
which already carry a fixed five-step color ramp for the NOM-035 Niveles de
Riesgo: gray for *Nulo*, green for *Bajo*, amber for *Medio*, orange for *Alto*
and red for *Muy alto*. A brand color in any of those hue bands would be read
as a risk level: a green primary button says *Bajo*, an orange accent says
*Alto*. Employees meet the brand only on the survey, where it has to stay calm
and out of the way of 61 to 87 answers.

The client supplied three reference images (A, B, C). The options drawn from
them, and a baseline teal-and-terracotta, were compared on screens of the real
application, including the results charts next to the risk ramp.

## Decision

Two finalists ship side by side behind one attribute (`data-palette`), so the
client can compare them on the real application:

- **Petróleo** — blue-teal primary (`#1F5D71`) with a periwinkle accent
  (`#B3C0FB`) on cool neutrals. Derived from reference A's teal and periwinkle,
  with the teal pushed toward blue and away from *Bajo*'s green.
- **Pizarra** — ink-slate primary (`#47546C`) with a peach accent (`#E5D09A`)
  on warm stone neutrals. Reference C's slate and peach (option C1), with the
  slate darkened to carry text and buttons.

The client chose **Pizarra** (2026-10-18). Its warm stone and peach suit the
calm, muted direction. Primary buttons use slate-500 (`#5D6C87`) rather than
600, to soften the classic-navy weight, with 600 as hover. Petróleo and the
switch are removed.

## Consequences

**Positive:**

- Neither finalist can be mistaken for a risk level: both live in the blue and
  slate family, away from the green, amber, orange and red bands.
- The comparison happens on real screens, and retiring the loser is one CSS
  block and the switch, not a branch to reconcile.

**Negative:**

- Pizarra's peach shares the amber *Medio* band, so it is confined to surfaces
  and never carries a chart series or a small mark; its second chart series is a
  lighter slate instead of a new hue.

## Alternatives considered

- **Option 0, teal + terracotta (baseline):** a teal primary with a terracotta
  accent on warm stone.
  - Why it was rejected: terracotta sits in the orange band and reads as *Alto*;
    the teal sat close to *Bajo*'s green.
- **A1, deep teal + lime + cream:**
  - Why it was rejected: lime is a green that reads as *Bajo*, is unreadable as
    text (2.05:1), and dominates next to teal.
- **A3, midnight navy + periwinkle** (with B2, deep blue + sky): the third
  direction previewed.
  - Why it was rejected: `#01012C` reads as black text rather than a brand
    color, and the saturated blue is heavy on large buttons and reads
    institutional; Petróleo keeps the periwinkle with a calmer primary.
- **B1, forest green + mint; B4, forest + mint + tangerine:**
  - Why they were rejected: a green primary reads as *Bajo*, and tangerine
    collides with *Alto* and the warning/danger colors.
- **B3, berry + lavender:**
  - Why it was rejected: distinctive, but berry sits next to the danger red,
    and the tone read as beauty or wellness rather than workplace risk.
- **C2, vista blue + peach; C3, whispering gray + peach:**
  - Why they were rejected: vista blue needs a derived shade for nearly every
    use and duplicates C1's role; whispering gray is a gray-green that reads as
    success and washes out hierarchy.
- **Combinations ruled out in every option:** lime with tangerine; berry or
  forest against tangerine (below 3:1); slate and vista blue as two brand
  colors (too similar to carry different roles); peach, mint, lime, sky or
  lavender as text on white (all below 2:1).

## Links

- Docs: `docs/platform/design-system.md` (palettes, fixed colors, the hue-band
  decision)
- User guides: `docs/internal/user-guides/rebranding.md`
