# ADR-0004: Per-company área/localidad catalogs instead of free-text department

Date: 2026-08-04
Status: Accepted

## Context

`docs/platform/nom-035-analytics.md` records an earlier decision to keep the employee's
área as a **free-text `UserProfile.department`** field — "area names vary between
companies and the admin uploads already-cleaned data; a managed Department model would
add an unneeded management surface for no aggregation benefit today."

Two requirements from the Aug 3 2026 session with the domain expert
(`docs/internal/meetings/20260803.md:9-23`) invalidate that premise:

1. When preloading a company, the admin must also load its **áreas** and
   **localidades**.
2. After activating with the company reference code, the employee must **select** their
   área — and their localidad when the company has more than one — *"del listado
   precargado"*.

Free text cannot back a picker: there is no list to populate the dropdown from. It also
carries failure modes that only matter once the data drives reporting. `_area_breakdown`
bucketed by `department.casefold()`, so "Ventas" and "ventas " merged by luck of
normalization rather than by identity; renaming an área left every profile pointing at
the old string; and two different companies with an "Operaciones" área were
indistinguishable at the string level. Área-level valuation is an open item with the
expert (`20260803.md:25`, and the unresolved rollup criterion in
`docs/platform/nom-035-valoracion-supuestos.md:42-56`), so those buckets need stable
identity before that work lands.

## Decision

Two **company-scoped catalog models**, `CompanyArea` and `CompanyLocation`, sharing an
abstract `CompanyCatalogEntry` base (`name`, `is_active`), each with a
`UniqueConstraint(company, Lower("name"))`. They are curated by an admin as
`TabularInline`s on the Company change page and are deliberately **not** registered as
standalone `ModelAdmin`s, so the inline is the only write surface.

`UserProfile.department` is **replaced** by `UserProfile.area`, and a new
`UserProfile.location` is added; both are `SET_NULL` FKs. The activation form
(`ProfileActivationForm`) gains company-scoped `ModelChoiceField` pickers, and
`apps/nom035`'s per-área breakdown groups by área **pk** rather than by casefolded name.

This **supersedes** the "Free-text `UserProfile.department`, not a model/enum" key
decision in `docs/platform/nom-035-analytics.md`.

## Consequences

**Positive:**

- The activation picker has a real source of options, scoped per company.
- Case-insensitive per-company uniqueness makes duplicate áreas structurally
  impossible, replacing normalization-by-luck with identity.
- Renaming an área propagates to every member; identically named áreas in different
  companies can no longer merge into one dashboard bucket.
- Grouping is by pk, which is the stable key the pending área-level valuation work
  needs.
- The catalogs are ordinary child models, so a future operator-facing UI outside Django
  admin gets `inlineformset_factory` rather than needing a bespoke JSON list widget.

**Negative:**

- A management surface the previous decision deliberately avoided: someone must load
  áreas/localidades before employees can activate.
- **A company with zero active áreas blocks activation** for its employees. This is a
  deliberate loud failure — letting people through would rebuild the "Sin área" pile
  that cannot be fixed later without re-interviewing them — but it is a new way for
  onboarding to stall on an admin task. The Company changelist shows área/localidad
  counts to surface it before an employee hits it.
- `accounts.0002` drops the free-text column outright rather than backfilling catalog
  rows from it. The platform is pre-production and the handful of existing values were
  not worth a data migration; every profile starts with no área and picks one at
  activation.
- `SET_NULL` means deleting an área silently orphans members at the ORM level; the
  admin inline formset guards the only deletion path, but code paths outside it (shell,
  future APIs) are unguarded.
- The CSV importer resolves área **by name, lookup-only**, so a typo imports the
  user with no área plus a report warning rather than failing.

## Alternatives considered

- **`JSONField` lists on `Company`.** Fewest tables. Rejected: Django renders a
  `JSONField` as raw JSON in the admin, so a non-technical operator would need a custom
  one-per-line widget anyway — it saves a model and costs a widget. More importantly it
  gives up integrity: renaming an entry orphans every profile that stored the old
  string, and nothing prevents deleting an entry that people belong to.
- **`PROTECT` instead of `SET_NULL` on `UserProfile.area`.** Rejected: `Company →
  CompanyArea` is CASCADE, so a protected reference would abort deleting the Company
  outright, and the admin renders that as an unactionable wall. It would also invert the
  existing intent of `UserProfile.company = SET_NULL` ("profiles outlive their
  company"). The inline formset guard covers the realistic deletion path instead.
- **A global área enum shared across companies.** Rejected: the expert confirmed the
  lists are unique per company.
- **Keeping `department` as a denormalized label alongside the FK.** Rejected: two
  sources of truth that drift, for no read benefit that `select_related` doesn't give.

## Links

- Requirement: `docs/internal/meetings/20260803.md`
- Supersedes the free-text key decision in: `docs/platform/nom-035-analytics.md`
- Spec: `docs/platform/auth-and-onboarding.md`, `docs/platform/database.md`
- Open question this unblocks: `docs/platform/nom-035-valoracion-supuestos.md` §3
- App docs: `apps/accounts/CLAUDE.md`, `apps/nom035/CLAUDE.md`
