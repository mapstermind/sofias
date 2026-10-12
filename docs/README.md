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
│   ├── feature-template.md          # Copy this to start a feature doc — never edit it
│   ├── overview.md                  # Start here — how the apps fit together
│   ├── auth-and-onboarding.md
│   ├── csv-user-import.md
│   ├── database.md
│   ├── design-system.md
│   ├── employee-roster.md
│   ├── localization.md
│   ├── nom-035-analytics.md
│   ├── nom-035-report.md
│   ├── nom-035-results-dashboard.md
│   ├── nom-035-valoracion-supuestos.md
│   ├── responsive-layout.md
│   ├── setup-access-codes.md
│   ├── survey-model.md
│   └── wip/                         # Disposable scaffolding — emptied when a branch merges
├── internal/                        # The human side of the process
│   ├── prompting-workflow.md        # End-to-end guide for developing a feature
│   ├── open-findings.md             # Issues found out of scope of the change that found them
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
- Describe only the present. There is no ledger here of how a feature used to behave; when that history is worth keeping, it goes in an ADR and the feature doc links to it.
- The doc is rewritten in the same branch as the code that changes it, so it never lags behind `main`.
- Use the `## Status` vocabulary from the template — `Draft`, `Current`, or `Archived` — and nothing else.
- When a feature is retired, move its doc to `docs/archive/` with a note of when and why.

Copy `feature-template.md` when starting a new feature doc. Never edit the template itself.

### `docs/platform/wip/` — Disposable scaffolding

One working artifact per branch: `<feature>-tasks.md`, holding the change brief under `## What changes` and the implementation plan below it. Nothing here is a source of truth, and the folder is emptied when the branch merges. On `main` it holds only its README.

### `docs/internal/` — The human side of the process

Guides, meeting notes, roadmap context, and workflows for the team. The agent does not read most of this in a normal session, but it is not off-limits: `CLAUDE.md` points here for the full development workflow, and `Guias de Referencia.md` is the authoritative NOM-035 scoring reference it must consult.

- `prompting-workflow.md` is the master guide: how a request is routed, and the eight steps from there to merged.
- `open-findings.md` tracks issues found during development that were out of scope for the change that found them.
- `user-guides/` contains operator procedures: platform setup, onboarding a client company, the CSV import reference, rebranding.
- `meetings/` contains background context. `Guias de Referencia.md` is the single
  source of truth for NOM-035 scoring data (see `.claude/CLAUDE.md`).

### `docs/archive/` — Retired docs

Docs moved here when the feature they describe is retired or superseded. Include a short note at the top of each archived file with the date and reason.

---

## Key documents

| Document | What it covers |
|----------|---------------|
| `platform/overview.md` | **Start here** — system map: the apps, the shared-base + per-instrument-engine shape, and end-to-end data flow |
| `internal/prompting-workflow.md` | End-to-end development workflow, starting with how a request is routed — which docs it needs, and whether it takes a branch or goes straight to `main` |
| `platform/survey-model.md` | The survey authoring base (Survey→Module→Question), variants, `visible_when` branching |
| `platform/database.md` | Full database schema reference |
| `platform/nom-035-analytics.md` | NOM-035 valuation engine (scores → NDR, Guía I flags) + the employee valuation card |
| `platform/nom-035-results-dashboard.md` | The company NOM-035 results page: filters, SVG charts, small-group rule |
| `platform/nom-035-valoracion-supuestos.md` | (Spanish) NOM-035 scoring assumptions tracked for the domain expert |
| `platform/auth-and-onboarding.md` | Login flows, OTP, setup codes, profile activation |
| `platform/csv-user-import.md` | Bulk user creation via Django Admin |
| `platform/localization.md` | Spanish-UI / English-code conventions, where each layer of copy comes from, and the glossary |
| `platform/design-system.md` | Brand config, palettes, type scale, components, page rules and the product's voice (*Voz*) |
| `platform/responsive-layout.md` | The 360px phone contract and the survey's tappable answer rows |
| `platform/employee-roster.md` | The colaborador roster: search, filters, sorting, the detail page |
| `platform/nom-035-report.md` | The formal NOM-035 results report: draft/publish, snapshot, PDF |
| `platform/setup-access-codes.md` | First-login fallback for blocked-email users |
| `adr/adr-0001-setup-access-codes-for-blocked-email-login.md` | Why setup codes exist instead of temporary passwords |
| `adr/adr-0002-flatten-survey-authoring-model.md` | Why the survey model is a flat Survey→Module→Question tree (no library/versions) |
| `adr/adr-0003-per-instrument-survey-processing-apps.md` | Why each instrument gets its own engine app instead of a generic engine |
| `adr/adr-0004-per-company-area-and-locality-catalogs.md` | Why área and localidad are per-company catalogs |
| `adr/adr-0005-two-surname-names-and-profile-demographics.md` | Why a name is three fields and demographics live on the profile |
| `adr/adr-0006-brand-palette.md` | (Proposed) The brand palette: why blue/slate, the alternatives weighed |
| `internal/user-guides/platform-setup.md` | Fresh machine → running platform with an operator account |
| `internal/user-guides/user-onboarding.md` | Onboarding a client: company, users, survey assignment, hand-off |
| `internal/user-guides/csv-user-import.md` | The CSV user import: columns, report, skipped rows |
| `internal/user-guides/rebranding.md` | (Draft) Replacing the product's name, logo and palette |
| `internal/Guias de Referencia.md` | Single source of truth for NOM-035 scoring data |
