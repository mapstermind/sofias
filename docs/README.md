# Documentation

This repository separates user-facing documentation, durable internal specifications, and temporary workflow artifacts.

## Directories

- `docs/user/`: user-facing usage documentation.
- `docs/specs/`: durable functional specs describing current system behavior.
- `docs/adr/`: architecture decision records for meaningful technical decisions.
- `docs/workflow/`: temporary workflow templates, PRDs, test plans, refactor plans, and migration notes.

## Durable artifacts

Keep these current:

- Functional specs
- User docs
- Tests
- ADRs for meaningful architectural, dependency, data-model, or infrastructure decisions

## Temporary artifacts

These may be deleted after implementation:

- PRDs
- Test plans
- Refactor plans
- Implementation plans
- Migration notes

Before deleting temporary artifacts, transfer durable knowledge into specs, tests, user docs, or ADRs.

Do not preserve documents only for process reasons.

## Existing Documentation Notes

- `README.md` remains at the repository root as the project overview.
- `CLAUDE.md` remains at the repository root because Claude Code tooling may expect it there. TODO: reconcile it with `AGENTS.md` if Claude Code remains part of the workflow; it contains stale project wiring notes.
- Ignored personal notes in `client_meetings/` and `gerry_notas.md` were left in place. TODO: review them and promote any durable product intent into `docs/specs/`, `docs/user/`, or ADRs before deleting or archiving them.
