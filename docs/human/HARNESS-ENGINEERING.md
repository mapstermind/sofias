Every time something goes wrong or a pattern emerges, it goes into CLAUDE.md so it doesn't happen again.

My recommendation is to take notes about it and at the end ask claude to update the relevant files with your observations.

CLAUDE.md answers: how should the agent work?

Workflow rules (write tests before implementation)
Constraints (never modify these files directly)
Patterns specific to your codebase (how you structure API routes, naming conventions)
Stopping conditions (if touching more than 3 unplanned files, stop and report)

docs/specs/*.md answers: how does the system work?

What a module does and why
Its inputs, outputs, edge cases
Architectural decisions and their rationale

Don't put system behavior in CLAUDE.md and don't put agent rules in specs. When they drift together, context quality drops.
