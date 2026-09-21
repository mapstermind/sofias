# Employee roster

## Status

Current — implemented in `apps/core` and `apps/accounts`

## What this does

The roster lists every person linked to a company on one page, with the survey
progress of each. It is the surface an administrator or a company executive uses
to answer "who is on this list, and where are they up to".

The list is flat — one card per person, ordered by apellido paterno — and is
narrowed with a toolbar holding a search box, four filters and one sort control:

- **Buscar** — free text matched against nombre, both apellidos and correo.
- **Sexo** — masculino or femenino.
- **Localidad** — one of the company's own localidades.
- **Área** — one of the company's own áreas.
- **Rol** — the authorization group the person belongs to, shown in Spanish.
- **Ordenar por** — nombre, progreso, or estado de activación.

Each card carries an avatar of the person's initials, their name and correo, a
single metadata line reading *Rol · Cargo · Área · Localidad*, and a progress bar
per assigned survey.

The same Rol appears in the Django admin, as a column and a filter on the
Usuarios changelist.

## Why we're building it

A company with a few hundred people on one flat page cannot be read. The
operator's real questions are narrow — *where is Ana*, *who in Producción has
not started*, *who are the ejecutivos*, *who is still not activated* — and each
of them is a search, a filter or a sort away, provided the roster offers all
three.

Rol carries its own weight in that list: the authorization group decides what a
person can do in SOFIA-S, and the roster is where an operator reads it without
opening the Django admin.

## Scope

**In scope:**

- The roster page (`CompanyEmployeeListView`) for both audiences it serves: a
  company executive viewing their own company, and an administrator viewing any
  company by `reference_code`.
- A search box, four filters (sexo, localidad, área, rol) and three sorts
  (nombre, progreso, activación), as optional GET parameters on that page.
- `apps/accounts/roles.py` — the canonical four group names, their Spanish
  labels, their URL slugs and their display order, imported by everything that
  needs any of the four.
- A Rol column and a Rol filter on the Django admin Usuarios changelist.
- The roster card layout: an initials avatar, one metadata line, and progress.
- The card's accessibility: a named link per person rather than a card-sized
  one, and progress bars that report their value.
- The terminology sweep: *colaborador* for a person, *empleado* reserved for the
  `Employees` role, including the `/colaboradores/` URLs.

**Out of scope:**

- Grouping the roster into sections. It stays one flat list; the sort control is
  what recovers a role-ordered or progress-ordered reading.
- Renaming `auth.Group.name`. The four English names stay the lookup keys and
  the CSV importer's accepted values — only their presentation is Spanish.
  The rename remains open finding #1.
- Filtering by cargo. It is free text typed per person, not a catalog, so it
  offers no stable set of options; the search box reaches it instead.
- Filtering by edad or by date ranges, and any segmented *aggregate* of the
  demographics. Reading NOM-035 results by age band and sex is open finding #4
  and needs its own doc — the minimum segment size that avoids re-identifying a
  person in a small company is a decision for the domain expert, and a roster
  filter does not raise it because the roster already names each person.
- A count of matching people beside each filter option, which would cost a query
  per dimension to render a number the result already states.
- Saved or shared filter presets, pagination, and CSV export of a filtered view.

## Public behavior

### Routes

| URL | Audience |
|---|---|
| `/tablero-empresa/colaboradores/` | A user with `can_manage_employees`, showing their own company |
| `/empresas/<reference_code>/colaboradores/` | An administrator, showing any company |
| `/tablero-empresa/colaboradores/<employee_id>/` | The per-person detail page |
| `/empresas/<reference_code>/colaboradores/<employee_id>/` | The same, for an administrator |

Both roster URLs accept the same optional query parameters:

| Parameter | Values |
|---|---|
| `q` | Free text, split on whitespace, first five terms honoured; every term must match nombre, apellido paterno, apellido materno or correo, case- and accent-insensitively |
| `sexo` | `masculino`, `femenino` |
| `localidad` | The pk of a `CompanyLocation` belonging to the company being viewed |
| `area` | The pk of a `CompanyArea` belonging to the company being viewed |
| `rol` | `administrador`, `ejecutivo-principal`, `ejecutivo-secundario`, `empleado` |
| `orden` | `nombre` (default), `progreso`, `activacion` |

`q` is split so that *ana ruiz* finds Ana Ruiz, whose nombre and apellido live
in different columns; each term may match a different one. Accents are folded
the way the área and localidad catalogs already fold them, so *ruiz* finds
*Ruíz*. A search is a convenience rather than a query language, so only the
first five terms are honoured — each one costs four comparisons.

Every parameter a human reads carries a Spanish value. `area` and `localidad`
are numeric pks because they identify a row rather than name a concept.

Parameters combine with AND: a search plus three filters shows the people who
match all of them. A parameter that is absent, empty, unrecognized, or names a
catalog entry from another company is ignored, and the roster renders as though
it had not been given. A filtered roster never raises.

### The toolbar

Above the list: the search box, the four selects, the sort select, an *Aplicar*
button and a *Limpiar filtros* link, followed by
`Mostrando X de Y colaboradores`. Every control shows its current value, so the
toolbar reflects the URL after a reload or a back button. The toolbar sticks to
the top of the viewport once the page header has scrolled past it, so the roster
scrolls beneath it and the controls stay reachable.

The localidad select renders only when the company has more than one localidad —
the same rule the activation form already applies to its own localidad picker.

The área and localidad selects offer the entries an operator may still assign,
while the parameters accept any entry the company owns: a retired área keeps the
colaboradores already assigned to it, so a URL naming one goes on working after
it stops being offered.
The rol select lists all four roles in their declared order regardless of who is
present, so an empty result is a readable answer rather than a missing option.

An empty list is replaced by one of two empty states, because *nobody matches
this search* and *this company has nobody* are different answers: a narrowed
roster with no match reads *Ningún colaborador coincide con la búsqueda* and
offers *Limpiar filtros*, while an unnarrowed one reads *Aún no hay
colaboradores vinculados a* the company and offers nothing to clear.

### Sorting

- **nombre** — apellido paterno, apellido materno, nombre. The default, and the
  tie-breaker for both other sorts.
- **progreso** — ascending by the percent answered of the assignment shown first
  on the card, which is the company's most recently created one, so the people
  who have not started come first. A person with no assignment sorts last.
- **activacion** — people who have not activated first.

Under every sort the viewer's own card stays at the top of the list — unless the
search or filters exclude them, in which case it is absent like any other
non-matching card.

### The card

One card per person:

- An avatar of the person's initials, the same one the detail page renders,
  falling back to the first letters of the correo for someone who has not yet
  recorded a name.
- Name, with a *Tú* badge on the viewer's own card, and the correo below it.
  Someone with no name recorded is listed by correo alone, which is then not
  repeated underneath.
- One metadata line: *Rol · Cargo · Área · Localidad*, with separators between
  whichever of the four are recorded. A value that is absent is omitted rather
  than printed as *Sin cargo*.
- A progress bar per assignment, labelled with the survey title, its variante,
  the percent, and the answered-over-total count.

A person who has not activated gets a muted card and a single *Sin activar*
badge. Activation is the normal state and carries no badge and no colour of its
own.

A company with no survey assigned is said once above the list — *No hay
encuestas asignadas a esta empresa* — rather than repeated as an empty progress
area on every card.

Opening a person and returning through the detail page's *Colaboradores* link
lands back on the same search, filters and sort, because that link carries the
roster's query string.

### Rol on a card

A person in exactly one group shows that group's label — which is what the CSV
importer produces, since it assigns exactly one group per row. A person given
more than one group in the admin shows all of them, in the declared order,
joined by commas; the rol filter matches a person who is in the selected group,
whatever else they are in. A person in no group shows *Sin rol* and is matched
by no rol filter.

### Accessibility

The card is a container, not a link. The person's name is the link, and it names
the destination on its own, so assistive technology announces "Ana Ruiz
Álvarez" rather than reading a card-sized link name that includes the correo and
every progress figure. Each progress bar reports itself as a progress bar with
its current value and the survey it belongs to, so the percentage is available
without relying on the bar's width.

### The admin

The Usuarios changelist carries a *Rol* column showing the same Spanish labels,
and a filter by group. The Grupos page shows the English names, because those
are the stored values.

## Terminology

A person on this roster is a **colaborador**, whatever their role — the list
holds administradores and ejecutivos alongside empleados. **Empleado** names one
of the four roles and nothing else.

`docs/platform/localization.md` owns the vocabulary and carries this rule in its
glossary. The word is used consistently across the surfaces that name this
population — `company_dashboard.html`, `company_list.html`,
`employee_detail.html`, `about.html` and the `/colaboradores/` URLs — because a
vocabulary applied to one page while its neighbours use the other word is the
two-words-for-one-population problem the glossary exists to prevent.

English identifiers are unaffected: `CompanyEmployeeListView`,
`can_manage_employees` and `employee_id` keep their names.

## Data model impact

None. No migration. Every filter reads a column that already exists —
`UserProfile.sex`, `UserProfile.area`, `UserProfile.location` — or the existing
`auth_user_groups` relation.

## Permissions and authorization

The roster is gated on `can_manage_employees`, and an administrator reaching
another company by `reference_code` additionally needs `can_manage_surveys`.
Search and filters narrow what is displayed and never widen who may display it.

## Key decisions

- Decision: Spanish role labels are presentation only; `auth.Group.name` keeps
  its English value.
  Reason: the name is looked up by string in four places and is an accepted
  value of the CSV importer's `group` column, so renaming it is a behavior
  change with an input-format consequence — open finding #1, deliberately not
  bundled into a display change.

- Decision: the four names, labels, slugs and order live in
  `apps/accounts/roles.py`, and `bootstrap_groups` imports its group names from
  there.
  Reason: the canonical list exists once instead of being retyped at each call
  site, which is what makes the eventual rename a small change.

- Decision: `Employees` is labelled *Empleado*, and *colaborador* is the word
  for a person on the roster.
  Reason: the roster lists administradores and ejecutivos too, so it needs a
  word for "a person on this list" that is not also the name of one of the four
  roles.

- Decision: filtering is server-side, through GET parameters.
  Reason: there is no JavaScript test runner in this project and none is
  planned, so a client-side filter would carry no automated coverage at all.
  GET parameters also survive a reload and can be pasted to a colleague.

- Decision: every parameter value a human reads is Spanish; `area` and
  `localidad` stay numeric pks.
  Reason: a Spanish URL that reads `?rol=Principal%20Exec&sexo=male` leaks
  English lookup keys onto a Spanish surface. Área and localidad are exempt
  because their names are per-company free text — slugs would have to be
  generated and could collide between companies, where a pk cannot.

- Decision: the search folds accents with `FoldCatalogName`, the expression the
  catalogs already use, rather than Postgres' `unaccent()`.
  Reason: it is the same folding rule the área and localidad catalogs are held
  to, so one concept has one definition; `unaccent()` is only STABLE and brings
  an extension for a rule this project has already written.

- Decision: an unrecognized parameter value is ignored rather than rejected.
  Reason: a hand-edited or stale URL should render the roster, not an error
  page; there is no input here a user typed into a field and could correct.

- Decision: the roster stays one flat list.
  Reason: sections fragment the count an operator is reading and duplicate what
  the sort control already does.

- Decision: the viewer's own card keeps its place at the top under every sort.
  Reason: it is existing behavior and an operator looking for themselves is the
  one lookup that never needs a filter; a sort is for reading the other people.

- Decision: the only badges on the page are *Tú* and *Sin activar*.
  Reason: a badge on every card for a state nearly every card shares carries no
  information, and four of them per card left nothing for the exception to stand
  out against.

- Decision: the card stops being a single link and the name becomes the link.
  Reason: a link wrapping the name, the correo and every progress figure
  announces all of it as one link name, which makes the list unusable by
  anything that reads links aloud or lists them.

- Decision: search and filtering narrow the roster queryset before the
  per-member progress loop, and the company-wide answer and module prefetches
  are left as they are.
  Reason: those sweeps are what keep this page free of N+1 queries; narrowing
  them per filter would trade a documented pattern for no measurable gain.

## Open questions

None.

## Linked ADRs

- [ADR-0004 — per-company área/localidad catalogs](../adr/adr-0004-per-company-area-and-locality-catalogs.md)
  — why área and localidad are curated per-company catalogs, which is what lets
  them be offered as a closed set of filter options validated against the
  company being viewed, and why they are filtered by pk rather than by name.
- [ADR-0005 — two-surname names and profile demographics](../adr/adr-0005-two-surname-names-and-profile-demographics.md)
  — why the default ordering is apellido paterno, why a search has three name
  fields to match, and where `sex` lives.
