# docs/

Documentation for the SOFIA-S platform. These files describe what the system does, why architectural decisions were made, and how operators should work with it.

Read the relevant docs in `docs/platform/` and `docs/adr/` before starting any feature — they are the source of truth for implementation.

---

## Directory structure

```
docs/
├── README.md                        # This file
├── adr/                             # Architectural decision records
│   ├── adr-0000-template.md         # Copy this when writing a new ADR
│   └── adr-NNNN-[decision].md
├── platform/                        # Feature and system documentation
│   ├── [new-feature]-template.md    # Copy this when drafting a new feature
│   ├── overview.md                  # Start here — how the apps fit together
│   ├── auth-and-onboarding.md
│   ├── csv-user-import.md
│   ├── database.md
│   ├── nom-035-analytics.md
│   ├── nom-035-valoracion-supuestos.md
│   ├── setup-access-codes.md
│   └── survey-model.md
├── internal/                        # Human-only reference — not referenced by the agent
│   ├── prompting-workflow.md        # End-to-end guide for developing a feature
│   ├── keep-in-mind.md
│   ├── HARNESS-ENGINEERING.md
│   ├── characterization-testing.md
│   ├── Guias de Referencia.md       # NOM-035 scoring source of truth
│   ├── meetings/
│   └── user-guides/
└── archive/                         # Retired docs — moved here with a note of when/why
    └── internal/
        └── interactive-workflows.md # Retired authoring CLI (removed in ADR-0002)
```

---

## What goes where

### `docs/adr/` — Architectural Decision Records

Write an ADR when a decision:
- Affects more than just the current feature
- Would not be obvious from the code alone
- Overrides or extends an existing ADR

Number them sequentially (`adr-0001-...`, `adr-0002-...`). Copy `adr-0000-template.md` to get started. Link the ADR from the relevant feature doc.

Skip the ADR if the decision is an implementation detail scoped entirely to one feature.

### `docs/platform/` — Feature and system docs

One file per feature or system concern. These describe what the system does and how it works — not implementation notes, not planning artifacts, not specs.

- Write in present tense as if the feature already exists and is shipped.
- Keep the doc current after implementation: trim open questions, update anything that changed.
- When a feature is retired, move its doc to `docs/archive/` with a note of when and why.

Copy `[new-feature]-template.md` when starting a new feature doc.

### `docs/internal/` — Human-only reference

Guides, meeting notes, roadmap context, and workflows for the team. These are not referenced by the agent in normal sessions.

- `prompting-workflow.md` is the master guide for how to develop a feature end-to-end.
- `user-guides/` contains operator procedures (CSV import, user onboarding).
- `meetings/` contains background context. `Guias de Referencia.md` is the single
  source of truth for NOM-035 scoring data (see `.claude/CLAUDE.md`).

### `docs/archive/` — Retired docs

Docs moved here when the feature they describe is retired or superseded. Include a short note at the top of each archived file with the date and reason.

---

## Key documents

| Document | What it covers |
|----------|---------------|
| `platform/overview.md` | **Start here** — system map: the apps, the shared-base + per-instrument-engine shape, and end-to-end data flow |
| `internal/prompting-workflow.md` | End-to-end feature development workflow |
| `platform/survey-model.md` | The survey authoring base (Survey→Module→Question), variants, `visible_when` branching |
| `platform/database.md` | Full database schema reference |
| `platform/nom-035-analytics.md` | NOM-035 valuation engine (scores → NDR) + Insights panels |
| `platform/nom-035-valoracion-supuestos.md` | (Spanish) NOM-035 scoring assumptions tracked for the domain expert |
| `platform/auth-and-onboarding.md` | Login flows, OTP, setup codes, profile activation |
| `platform/csv-user-import.md` | Bulk user creation via Django Admin |
| `platform/setup-access-codes.md` | First-login fallback for blocked-email users |
| `adr/adr-0001-setup-access-codes-for-blocked-email-login.md` | Why setup codes exist instead of temporary passwords |
| `adr/adr-0002-flatten-survey-authoring-model.md` | Why the survey model is a flat Survey→Module→Question tree (no library/versions) |
| `adr/adr-0003-per-instrument-survey-processing-apps.md` | Why each instrument gets its own engine app instead of a generic engine |
| `internal/Guias de Referencia.md` | Single source of truth for NOM-035 scoring data |
