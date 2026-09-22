# Employee roster

## Status

Current — implemented in `apps/core` and `apps/accounts`

## What this does

The roster lists every person linked to a company on one page, with the survey
progress of each. It is the surface an administrator or a company executive uses
to answer "who is on this list, and where are they up to".

The list is flat — one card per person, ordered by apellido paterno — and is
narrowed from a bar holding a search box, a *Filtros* button and a sort control:

- **Buscar** — free text matched against nombre, both apellidos and correo.
- **Ordenar por** — nombre, progreso, or estado de activación.
- **Filtros** — opens a modal holding four filter dimensions:
  - **Sexo** — masculino or femenino, one at a time.
  - **Rol** — the authorization group the person belongs to, shown in Spanish.
  - **Área** — one or more of the company's own áreas.
  - **Localidad** — one or more of the company's own localidades.

Rol, área and localidad each accept several values at once. Within a dimension
the chosen values are OR-ed and across dimensions they are AND-ed, so *Producción
o Logística, and only empleados* is one reading of the roster rather than three.

Each card carries a circular avatar of the person's initials, their name and
correo, a single metadata line reading *Rol · Cargo · Área · Localidad*, and a
progress bar per assigned survey.

The same Rol appears in the Django admin, as a column and a filter on the
Usuarios changelist.

## Why we're building it

A company with a few hundred people on one flat page cannot be read. The
operator's real questions are narrow — *where is Ana*, *who in Producción or
Logística has not started*, *who are the ejecutivos*, *who is still not
activated* — and each of them is a search, a filter or a sort away, provided the
roster offers all three.

Rol carries its own weight in that list: the authorization group decides what a
person can do in SOFIA-S, and the roster is where an operator reads it without
opening the Django admin.

The questions an operator asks rarely land on exactly one área or exactly one
role, so a dimension that accepted one value at a time answered half of them and
sent the operator back for a second look at the other half.

## Scope

**In scope:**

- The roster page (`CompanyEmployeeListView`) for both audiences it serves: a
  company executive viewing their own company, and an administrator viewing any
  company by `reference_code`.
- A search box, three sorts (nombre, progreso, activación) and four filter
  dimensions (sexo, rol, área, localidad), all as optional GET parameters on
  that page; rol, área and localidad repeatable.
- The filter modal: a native `<dialog>` of toggleable pills, and
  `static/ts/roster_filters.ts`, the small script that opens and closes it.
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
  demographics. NOM-035 results by age band and sex are read on the results
  page ([`nom-035-results-dashboard.md`](./nom-035-results-dashboard.md)), which
  applies a minimum group size; a roster filter needs none because the roster
  already names each person.
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

| Parameter | Repeatable | Values |
|---|---|---|
| `q` | no | Free text, split on whitespace, first five terms honoured; every term must match nombre, apellido paterno, apellido materno or correo, case- and accent-insensitively |
| `sexo` | no | `masculino`, `femenino` |
| `rol` | yes | `administrador`, `ejecutivo-principal`, `ejecutivo-secundario`, `empleado` |
| `area` | yes | The pk of a `CompanyArea` belonging to the company being viewed |
| `localidad` | yes | The pk of a `CompanyLocation` belonging to the company being viewed |
| `orden` | no | `nombre` (default), `progreso`, `activacion` |

`q` is split so that *ana ruiz* finds Ana Ruiz, whose nombre and apellido live
in different columns; each term may match a different one. Accents are folded
the way the área and localidad catalogs already fold them, so *ruiz* finds
*Ruíz*. A search is a convenience rather than a query language, so only the
first five terms are honoured — each one costs four comparisons.

Every parameter a human reads carries a Spanish value. `area` and `localidad`
are numeric pks because they identify a row rather than name a concept.

`?area=3&area=7&rol=empleado` keeps the empleados of área 3 and of área 7:
within a dimension the values are OR-ed, and the dimensions are AND-ed with each
other and with the search. A repeated `rol` is read back in the roles' declared
order rather than in URL order, so the same selection reads the same however it
was clicked, and repeated pks are deduplicated.

A parameter that is absent or empty is ignored, and so is a single value that is
unrecognized or names a catalog entry from another company — **per value**, not
per parameter: `?area=3&area=nonsense&area=999` filters by área 3. A stale
bookmark naming four áreas, one of them since deleted, still narrows by the
other three. `sexo` takes the first value it recognizes, so a bad one does not
shadow a good one that follows it. A filtered roster never raises.

### The bar

Above the list, on an opaque strip the width of the page shell: the search box,
the *Filtros* button, a *Limpiar filtros* link when anything is being hidden,
and the *Ordenar por* control on a second row, followed by
`Mostrando X de Y colaboradores`. The bar starts below the page header and
sticks to the top of the viewport once that header has scrolled past, so the
roster scrolls beneath it and the controls stay reachable.

The *Filtros* button carries a count of the dimensions in use, not of the values
chosen: three áreas and one rol read as `2`. That is the number that answers
"how much of this roster is hidden from me".

The bar, the sort buttons and the modal are one GET form, so *Aplicar filtros*
is an ordinary submit and the whole narrowing lives in the URL. Every submit in
it names the sort it submits under, so searching or applying filters while
reading by progreso does not quietly reorder the list back to nombre.

An empty list is replaced by one of two empty states, because *nobody matches
this search* and *this company has nobody* are different answers: a narrowed
roster with no match reads *Ningún colaborador coincide con la búsqueda* and
offers *Limpiar filtros*, while an unnarrowed one reads *Aún no hay
colaboradores vinculados a* the company and offers nothing to clear.

### The filter modal

*Filtros* opens a native `<dialog>`, which brings its own backdrop, focus
trapping and Esc-to-close. It holds one row of pills per dimension — Sexo, Rol,
Área and, when the company has more than one, Localidad — over *Limpiar filtros*
and *Aplicar filtros*.

Each pill is a real checkbox, or a radio for sexo, hidden with `sr-only` behind
a styled label, so toggling one is markup rather than script and every pill
shows whether it is chosen. A dialog the browser is not showing still submits
the fields inside it, which is what makes a reload or a back button come back
with the same pills lit.

Sexo is single-choice: it has two values, so selecting both is identical to
selecting neither. Picking the option already chosen clears it, which is how a
roster returns to "either" without a third pill that says so.

The área and localidad pills offer the entries an operator may still assign,
while the parameters accept every entry the company owns: a retired área keeps
the colaboradores already assigned to it, so a URL naming one goes on working
after it stops being offered. The rol pills list all four roles in their
declared order regardless of who is present, so an empty result is a readable
answer rather than a missing option.

The localidad dimension is left out altogether when the company has one
localidad — the same rule the activation form applies to its own localidad
picker. One pill that changes nothing is a control that has to be read before it
can be dismissed.

*Limpiar filtros* — the one in the modal and the one beside the *Filtros*
button — points at the roster with nothing narrowing it, and keeps the sort.

### Without JavaScript

`static/ts/roster_filters.ts` does four things and holds no filter state: it
shows the dialog, closes it from the ✕ or the backdrop, lets a chosen sexo be
un-chosen, and puts the pills back as they were when the dialog is dismissed
without applying, so an abandoned edit does not ride along on the next search.

Everything else is server-rendered. Without the script the search box, the sort
buttons and every filter already in the URL go on working; only the modal is out
of reach, because a `<dialog>` the browser was never asked to open stays closed.

### Sorting

- **nombre** — apellido paterno, apellido materno, nombre. The default, and the
  tie-breaker for both other sorts.
- **progreso** — ascending by the percent answered of the assignment shown first
  on the card, which is the company's most recently created one, so the people
  who have not started come first. A person with no assignment sorts last.
- **activacion** — people who have not activated first.

The three sit in the bar as a segmented group of submit buttons, each reporting
whether it is the sort in force. Ordering is not narrowing: it survives
*Limpiar filtros*, and a roster in its default sequence says nothing about
`orden` in the URL.

Under every sort the viewer's own card stays at the top of the list — unless the
search or filters exclude them, in which case it is absent like any other
non-matching card.

### The card

One card per person:

- A circular avatar of the person's initials, rendered from the partial the
  detail page also includes so neither can drift away from the other, falling
  back to the first letters of the correo for someone who has not yet recorded a
  name.
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
joined by commas; the rol filter matches a person who is in any of the selected
groups, whatever else they are in, and lists them once however many of those
groups they hold. A person in no group shows *Sin rol* and is matched by no rol
filter.

### Accessibility

The card is a container, not a link. The person's name is the link, and it names
the destination on its own, so assistive technology announces "Ana Ruiz
Álvarez" rather than reading a card-sized link name that includes the correo and
every progress figure. The initials avatar repeats the name printed beside it,
so it is hidden from assistive technology as decoration. Each progress bar
reports itself as a progress bar with its current value and the survey it
belongs to, so the percentage is available without relying on the bar's width.

The pills are checkboxes and radios, so they are focusable, toggle with the
keyboard, and report their checked state without an ARIA attribute standing in
for one; each dimension is a `fieldset` whose `legend` names it, so a pill is
announced with the dimension it belongs to. The sort buttons are a labelled
group, each reporting through `aria-pressed` whether it is the sort in force.

The modal is a native `<dialog>` opened with `showModal()`, which is what makes
the browser trap focus inside it, treat the rest of the page as inert and close
it on Esc. The *Filtros* button declares what it opens, and the dialog is
labelled by its own heading.

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

- Decision: rol, área and localidad accept several values, OR-ed within the
  dimension and AND-ed across dimensions.
  Reason: that is the shape of the questions the roster is asked — *Producción
  or Logística*, *the ejecutivos of either kind* — and it is the only reading
  that keeps AND meaningful: OR-ing across dimensions would make each added
  filter widen the list, which is the opposite of what a filter is for.

- Decision: sexo stays single-choice, and re-picking the chosen option clears
  it.
  Reason: the dimension has two values, so selecting both is identical to
  selecting neither and the multi-select would offer one state that already has
  a name — no filter at all. A radio group has no way back to "either", which is
  why un-picking is the one filter behavior the script provides.

- Decision: the rol filter carries `.distinct()`.
  Reason: it matches across the groups many-to-many with `__in`, which returns
  one row per matching group, so a colaborador holding two of the selected roles
  would be listed twice on a page whose whole job is to name each person once.

- Decision: the pills are real checkboxes and radios, styled through their
  labels, rather than buttons driven by JavaScript.
  Reason: the chosen state then lives in the form and travels in the URL, so it
  is the server-rendered contract the test suite can actually assert; keyboard
  access, focus and the checked state come from the browser rather than from
  ARIA attributes that have to be kept honest by hand.

- Decision: the modal is a native `<dialog>` opened with `showModal()`.
  Reason: focus trapping, inertness and Esc-to-close are exactly what a
  hand-rolled modal gets wrong, and the browser gives all three for the one call
  that markup cannot make on its own.

- Decision: *Ordenar por* stays visible in the bar and *Limpiar filtros*
  preserves it.
  Reason: sorting is not narrowing — it hides nothing, so there is nothing for a
  clear to restore, and an operator reading by progreso who clears a filter
  wants the same reading of a wider list. Changing the reading order is a cheap,
  frequent act; behind two clicks it would be an expensive one.

- Decision: the *Filtros* button counts dimensions in use, not values chosen.
  Reason: the number answers "how much is hidden from me", and three áreas is
  one answer to one question; counting values would make a broad filter look
  like a narrow one.

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

- Decision: an unrecognized value is ignored rather than rejected, and it is
  dropped on its own rather than discarding the parameter.
  Reason: a hand-edited or stale URL should render the roster, not an error
  page; there is no input here a user typed into a field and could correct. Once
  a parameter may be repeated, discarding the whole of it would let one dead
  área silently widen the roster back to everybody.

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

- Decision: the query that lists a company's área and localidad pks for
  validation runs only when the request names the corresponding parameter.
  Reason: an unchecked pill submits nothing, so those parameters arrive only
  once one of theirs has been chosen, and the unnarrowed roster — the common
  reading — pays for neither.

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
