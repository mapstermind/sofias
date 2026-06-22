# ADR-0003: Per-instrument survey-processing apps instead of a generic valuation engine

Date: 2026-06-21
Status: Accepted

## Context

The product roadmap (`docs/internal/roadmap_context/hoja-de-ruta-nom035.md`,
Iniciativa 1) proposes a **generic, configurable valuation engine**: per-answer
values, inverted-item flags, the Categoría→Dominio→Dimensión taxonomy, and the NDR
threshold tables would all be stored as **data** (not code) so that future
instruments — clima laboral, validated in-house surveys — could be scored without
writing new engine code. NOM-035 would simply be its first loaded configuration,
and a single `apps/analytics` app (today an empty, unregistered stub) would host
the aggregation. SOFIA-S, however, processes a **small number of fixed
instruments** (NOM-035 today, an unrelated second survey later), seeded once and
rarely changed — the same premise that drove ADR-0002 to flatten the survey
authoring model. A generic engine, plus the config tables and authoring UI needed
to make it genuinely instrument-agnostic, is standing complexity built for a
reuse case that does not yet exist, while NOM-035 itself needs scoring now.

## Decision

Each survey instrument's valuation/processing lives in its **own dedicated Django
app**, NOM-035-specific by construction. The empty `apps/analytics` stub is
**renamed to `apps/nom035`** and registered; its scoring configuration (inverted
items, taxonomy, threshold tables, action text) is held as **instrument-specific
Python constants**, not generic database configuration, and is keyed by the stable
`surveys.Question.code`. A future second instrument gets its **own app** (e.g.
`apps/<instrument>`) rather than a generalization of this one. Full design:
`docs/platform/nom-035-analytics.md`.

## Consequences

**Positive:**

- No generic-engine framework, config schema, or authoring UI to build or maintain
  before a second instrument actually exists — the engine is as simple as the
  single instrument it serves.
- Strong isolation: each instrument's scoring rules, models, and tests are
  self-contained in one app and can be reasoned about and changed without touching
  others.
- The MVP can ship scoring with documented assumptions and iterate quickly, since
  configuration is plain code edited and re-run via `recompute_nom035_scores`
  rather than data migrated through a config model.
- Preserves the `apps/surveys` → no-scoring boundary from ADR-0002: scoring depends
  on `surveys`/`responses` via `Question.code`, never the reverse.

**Negative:**

- A second instrument duplicates engine *structure* (scoring service, result
  models, materialization signal) rather than reusing a shared framework; common
  patterns may later warrant extraction into a shared library/app.
- Diverges from the roadmap's stated generic-engine intent, so that document is no
  longer the source of truth for engine architecture (the roadmap is a
  non-living starting point; this ADR and the feature doc supersede it here).
- The `apps/analytics` name disappears; references in `INSTALLED_APPS`,
  `.claude/CLAUDE.md`, and `apps/reports/CLAUDE.md` must be updated to `apps/nom035`.
- Cross-instrument aggregation (if ever needed) has no natural home and would
  require a later decision.

## Alternatives considered

- **Generic configurable engine (roadmap proposal).** Scoring rules modeled as data
  in a shared `analytics` app, reusable across instruments. Rejected: it builds a
  reuse framework — and the config schema/UI to populate it — for a second
  instrument that does not exist yet, paying complexity now against an uncertain
  future, contrary to the fixed-instrument premise of ADR-0002.
- **One shared `analytics` app hosting multiple instrument-specific engines.**
  Keeps a single app but with per-instrument modules inside. Rejected: weaker
  isolation than separate apps and an ambiguous generic name for code that is, in
  fact, instrument-specific; separate apps make ownership and boundaries explicit.
- **Scoring config in database tables (but still NOM-035-only).** Instrument-
  specific yet data-driven. Rejected: with a single fixed instrument, Python
  constants are a simpler source of truth and need no migration/seed to evolve
  during the assumption-refinement phase.

## Links

- Spec: `docs/platform/nom-035-analytics.md`,
  `docs/platform/nom-035-valoracion-supuestos.md`
- Related: `docs/adr/adr-0002-flatten-survey-authoring-model.md`,
  `docs/platform/survey-model.md`
- Context: `docs/internal/roadmap_context/hoja-de-ruta-nom035.md`
- App docs: `apps/nom035/CLAUDE.md` (replaces `apps/analytics/CLAUDE.md`)
