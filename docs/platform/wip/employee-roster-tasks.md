# Roster UI Revision — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development or superpowers:executing-plans. Steps use checkbox (`- [ ]`) syntax.

## What changes

Three revisions to the colaborador roster, on top of what PR #8 already carries:

1. **Cards, not a divided panel.** Each person returns to a discrete card. The
   panel-with-hairline-dividers form goes away.
2. **The initials avatar becomes a true circle**, optically centred, and renders
   identically on the roster and the detail page.
3. **The filter bar becomes a search bar plus a Filter button.** Only the search
   box stays visible. Sexo, rol, área and localidad move into a modal whose
   options are toggleable pills rather than dropdowns, so **rol, área and
   localidad accept more than one value at once**. The modal carries *Aplicar
   filtros* and *Limpiar filtros*; a second *Limpiar filtros* appears beside the
   Filter button whenever filters are active.

**Why this makes the live feature doc wrong.** `docs/platform/employee-roster.md`
states one value per dimension, describes a toolbar of selects, and describes the
card. Its parameter table, its "The toolbar" and "The card" sections, and the key
decision recording single-value filters all change. The doc is rewritten in the
last task, as the process requires.

**No ADR is touched.** ADR-0004 (per-company catalogs) and ADR-0005 (names and
demographics) are relied on and unaffected: multi-select changes how many pks a
filter accepts, not what the catalogs are.

**Decisions taken with the user before planning:**

- The modal is a native `<dialog>` driven by a small TypeScript file. The browser
  supplies focus trapping, Esc-to-close and the backdrop; hand-rolling those is
  where accessibility breaks. Filter *state* stays server-side, so the tested
  contract is unchanged and only open/close is unverified by the suite.
- **Rol, área and localidad** accept multiple values. **Sexo does not** — it has
  two values, so selecting both is identical to selecting neither; its pills are
  single-choice, and re-picking the selected one clears it.
- Within a dimension the values are OR-ed; across dimensions they are AND-ed.

**Controller decision, open to being waved off:** *Ordenar por* stays visible in
the bar as a three-way segmented control rather than moving into the modal.
Sorting is not filtering — the doc already separates them, and `Limpiar filtros`
deliberately does not reset the order. Changing the reading order is a cheap,
frequent act; burying it behind two clicks would make it expensive.

## Global Constraints

- Python 3.13 / Django 6.0 / PostgreSQL 17. Tests via `pytest`.
- **Spanish UI, English code.** Identifiers, comments and docstrings English; every string a user reads Spanish.
- **Parameter values a human reads are Spanish**; `area` and `localidad` are numeric pks.
- **An unrecognized parameter value is ignored**, never raised on. This now applies per value: `?area=3&area=nonsense&area=999` keeps 3 and drops the rest.
- **No migration.**
- **Preserve the N+1 pattern.** The four company-wide sweeps stay; narrowing happens before the per-member loop; the invariance test (same query count at 3 and 30 colaboradores) must still pass.
- Touched `templates/` or `static/` → `npm run build:css`; touched `static/ts/` → `npm run build:js`. Commit the regenerated output.
- `ruff format .` and `ruff check .` before each commit.

---

### Task 1: Multi-value filters in the query contract

**Files:**
- Modify: `apps/core/roster.py`
- Test: `apps/core/tests/test_roster.py`

**Interfaces produced:** `RosterQuery` with `area_ids: tuple[int, ...]`, `location_ids: tuple[int, ...]`, `role_names: tuple[str, ...]`, `role_slugs: tuple[str, ...]` replacing the four scalar fields. `sex`/`sex_slug` stay scalar. `parse_roster_query` keeps its signature.

**THE CORRECTNESS POINT.** With a single-value `rol` filter, `filter(user__groups__name=...)` cannot duplicate a row, and a test asserts that. With `__in` over several roles, a person in two selected groups matches **twice** and would appear twice on the roster. The role filter therefore needs `.distinct()`, and a test must add a second group and select both.

- [ ] **Step 1: Write the failing tests**

Add to `apps/core/tests/test_roster.py`. Keep the existing pure/DB split — parsing tests stay DB-free.

```python
class TestMultiValueParsing:
    def test_repeated_area_collects_every_valid_pk(self):
        params = QueryDict("area=3&area=7")
        query = roster.parse_roster_query(
            params, area_ids={3, 7}, location_ids=set()
        )
        assert query.area_ids == (3, 7)

    def test_invalid_values_are_dropped_individually(self):
        """One bad value must not discard its good neighbours."""
        params = QueryDict("area=3&area=nonsense&area=999")
        query = roster.parse_roster_query(
            params, area_ids={3, 7}, location_ids=set()
        )
        assert query.area_ids == (3,)

    def test_duplicate_values_collapse(self):
        params = QueryDict("area=3&area=3")
        query = roster.parse_roster_query(
            params, area_ids={3}, location_ids=set()
        )
        assert query.area_ids == (3,)

    def test_repeated_rol_collects_group_names(self):
        params = QueryDict("rol=empleado&rol=administrador")
        query = roster.parse_roster_query(params, area_ids=set(), location_ids=set())
        assert query.role_names == ("Admins", "Employees")
        assert query.role_slugs == ("administrador", "empleado")

    def test_role_order_is_declared_order_not_url_order(self):
        """The modal lists roles in declared order; echoing URL order would make
        the same selection read differently depending on click sequence."""
        params = QueryDict("rol=empleado&rol=administrador")
        query = roster.parse_roster_query(params, area_ids=set(), location_ids=set())
        assert query.role_names == ("Admins", "Employees")

    def test_sexo_stays_single_valued(self):
        """Two values means selecting both equals selecting neither, so sexo is
        single-choice; a repeated parameter keeps the first recognized value."""
        params = QueryDict("sexo=femenino&sexo=masculino")
        query = roster.parse_roster_query(params, area_ids=set(), location_ids=set())
        assert query.sex == "female"

    def test_a_plain_dict_still_works(self):
        """The view passes a QueryDict; unit tests pass dicts. Both must parse."""
        query = roster.parse_roster_query(
            {"area": "3"}, area_ids={3}, location_ids=set()
        )
        assert query.area_ids == (3,)

    def test_no_filters_means_empty_tuples_not_none(self):
        query = roster.parse_roster_query({}, area_ids=set(), location_ids=set())
        assert query.area_ids == ()
        assert query.role_names == ()
        assert query.is_narrowed is False
```

And the DB-backed tests, in the existing `TestNarrowProfiles` (which has the `roster_company` fixture):

```python
    def test_two_areas_are_or_ed_within_the_dimension(self, roster_company):
        ...assert both Ana (Producción) and Beto (Sistemas) come back...

    def test_dimensions_are_and_ed(self, roster_company):
        """área in (Producción, Sistemas) AND rol=empleado narrows to Ana."""

    def test_a_person_in_two_selected_roles_appears_once(
        self, roster_company, bootstrap_groups
    ):
        """__in over an M2M duplicates rows without .distinct(); a colaborador
        must never appear twice on a roster."""
        roster_company["ana"].groups.add(bootstrap_groups["Admins"])
        emails = self._emails(roster_company, rol=["empleado", "administrador"])
        assert emails == ["ana@example.com"]
        assert len(emails) == len(set(emails))
```

`_emails`/`_emails_in_order` currently build params as a plain dict. Extend the helper so a list value becomes a repeated parameter (build a `QueryDict` via `QueryDict(urlencode(params, doseq=True))`), and keep existing call sites working.

- [ ] **Step 2: Run the tests to verify they fail**

Run: `pytest apps/core/tests/test_roster.py -v`
Expected: FAIL — `RosterQuery` has no `area_ids`.

- [ ] **Step 3: Implement**

In `apps/core/roster.py`:

```python
def _values(params, key) -> list[str]:
    """Every value given for `key`, whether params is a QueryDict or a dict.

    The view hands us `request.GET`, which may repeat a parameter; unit tests
    hand us a plain dict. `getlist` exists only on the former.
    """
    getlist = getattr(params, "getlist", None)
    if getlist is not None:
        return getlist(key)
    value = params.get(key)
    if value is None:
        return []
    return list(value) if isinstance(value, (list, tuple)) else [value]


def _valid_pks(raw_values, valid_ids: set[int]) -> tuple[int, ...]:
    """Every value that names an entry the company owns, deduplicated.

    A bad value is dropped on its own rather than discarding its neighbours:
    a stale bookmark listing four áreas, one of them since deleted, should
    still filter by the other three.
    """
    seen = []
    for raw in raw_values:
        pk = _valid_pk(raw, valid_ids)
        if pk is not None and pk not in seen:
            seen.append(pk)
    return tuple(seen)
```

`RosterQuery` gains `area_ids`, `location_ids`, `role_names`, `role_slugs` (all `tuple`, default `()`), losing `area_id`, `location_id`, `role_name`, `role_slug`. `is_narrowed` becomes:

```python
        return bool(
            self.terms or self.sex or self.area_ids
            or self.location_ids or self.role_names
        )
```

Roles are collected in **declared order** by filtering `ROLES`, not in URL order:

```python
    role_slugs = {slug for slug in _values(params, "rol")}
    selected_roles = [role for role in ROLES if role.slug in role_slugs]
```

In `narrow_profiles`:

```python
    if query.area_ids:
        queryset = queryset.filter(area_id__in=query.area_ids)
    if query.location_ids:
        queryset = queryset.filter(location_id__in=query.location_ids)
    if query.role_names:
        # `__in` across the groups M2M returns one row per matching group, so a
        # colaborador holding two of the selected roles would be listed twice.
        queryset = queryset.filter(
            user__groups__name__in=query.role_names
        ).distinct()
```

- [ ] **Step 4: Run tests until green, then the full suite**

Run: `pytest apps/core/tests/test_roster.py -v` then `pytest`
Expected: PASS. Tests elsewhere referencing `area_id`/`role_name` will fail — update them to the tuple fields; that is expected churn, not a regression.

- [ ] **Step 5: Prove the distinct() guard bites**

Temporarily delete `.distinct()`, run `test_a_person_in_two_selected_roles_appears_once`, confirm it FAILS, restore. Put the output in your report. Without this evidence the test is unproven.

- [ ] **Step 6: Commit**

```bash
ruff format . && ruff check .
git add apps/core/roster.py apps/core/tests/test_roster.py
git commit -m "feat(core): accept several roles, areas and localidades at once"
```

---

### Task 2: Filter state for the modal

**Files:**
- Modify: `apps/core/views.py` (`CompanyEmployeeListView`)
- Test: `apps/core/tests/test_views.py`

**Interfaces produced:** context keys `filter_groups` and `active_filter_count`, replacing `role_options`/`sex_options`/`area_options`/`location_options`.

`filter_groups` is a list the template walks blindly, so adding a dimension later is a view change rather than a template change:

```python
[
  {"key": "sexo",      "label": "Sexo",      "multiple": False, "options": [...]},
  {"key": "rol",       "label": "Rol",       "multiple": True,  "options": [...]},
  {"key": "area",      "label": "Área",      "multiple": True,  "options": [...]},
  {"key": "localidad", "label": "Localidad", "multiple": True,  "options": [...]},
]
```

Each option is `{"value": <str>, "label": <str>, "selected": <bool>}`. The localidad group is omitted entirely when the company has one localidad or none — the same rule the activation form applies.

`active_filter_count` counts **dimensions in use**, not values chosen: picking three áreas is one filter, and the button reads *Filtros (1)*. Search is not counted — it has its own visible box.

- [ ] **Step 1: Write the failing tests**

```python
    def test_filter_groups_expose_every_dimension(self, ...):
        """Sexo, rol and área always; localidad only when there are two."""

    def test_selected_options_are_marked(self, ...):
        """GET ?area=<pk> -> that option's selected is True, others False."""

    def test_active_filter_count_counts_dimensions_not_values(self, ...):
        """?area=1&area=2&rol=empleado -> 2, not 3."""

    def test_search_does_not_count_as_a_filter(self, ...):
        """?q=ana -> active_filter_count == 0; the search box is visible anyway."""

    def test_localidad_group_absent_with_one_localidad(self, ...):

    def test_roster_query_count_does_not_grow_with_the_roster(...)  # already exists
```

- [ ] **Step 2: Run to verify they fail**
- [ ] **Step 3: Implement**, replacing the four `*_options` keys. Keep `roster_query`, `roster_querystring`, `show_location_filter`, `shown_count`, `total_count`.
- [ ] **Step 4: Full suite green** — the existing template still references the old keys, so update the template minimally here or accept red until Task 3; prefer keeping the suite green by landing Task 2 and Task 3 in one commit if the template cannot survive the rename.
- [ ] **Step 5: Commit**

```bash
git commit -m "feat(core): hand the roster's filter state to the template as groups"
```

---

### Task 3: The cards, the avatar, and the filter modal

**Files:**
- Modify: `templates/core/employee_list.html`
- Create: `static/ts/roster_filters.ts`
- Modify: `static/js/roster_filters.js`, `static/css/output.css` (both generated)
- Test: `apps/core/tests/test_views.py`

Use the `frontend-design` skill. The constraints below come from the user and are not the skill's to revisit.

**The card.** One discrete card per person — not a panel with dividers. Keep everything the previous review verified: one `<article>`, the name as the only link carrying `?{{ roster_querystring }}`, one metadata line (`Rol · Cargo · Área · Localidad`, absent values omitted, `Sin rol` when in no group), at most two badges (`Tú`, `Sin activar`), and each progress bar `role="progressbar"` with `aria-valuenow`/`aria-valuemin`/`aria-valuemax` and an `aria-label` naming its own survey.

**The avatar.** A true circle — equal width and height, `rounded-full`, content optically centred both axes, identical on the roster and `employee_detail.html`. It currently renders inconsistently between the two. Fix both so they are the same component; if that means extracting `templates/core/_avatar.html`, do it.

**The bar.** Search box (`name="q"`), a *Filtros* button showing `active_filter_count` when non-zero, a *Limpiar filtros* link rendered **only when `roster_query.is_narrowed`**, and the three-way *Ordenar por* segmented control.

**The modal.** A native `<dialog id="roster-filter-modal">` inside the same `method="get"` form as the search box, so *Aplicar filtros* is a plain submit and the whole contract stays server-side.

- One dimension per row, walking `filter_groups`.
- Options are **pills, not dropdowns**: a real `<input type="checkbox">` (or `type="radio"` for `sexo`, which is single-choice) visually hidden with `sr-only` and a `<label>` styled as the pill, so toggling needs no JavaScript and the keyboard works by default. Style the checked state with `peer-checked:`.
- `sexo` is single-choice and re-picking the selected value clears it — that needs one line of TS, since a radio cannot be unchecked by clicking it.
- Footer: *Limpiar filtros* and *Aplicar filtros*.

**The TypeScript** (`static/ts/roster_filters.ts`) does four things and nothing else: open the dialog, close it, allow a checked `sexo` radio to be unchecked, and keep the pills' state if the dialog is dismissed without applying. Match the file-header comment style of `static/ts/survey_progress.ts`, which documents the element ids it binds to. Load it from the template with `{% static 'js/roster_filters.js' %}`.

**Without JavaScript** the page must still work: the dialog is not reachable, but the search box, the sort control and any filters already in the URL all function. Do not put filter state in JS.

- [ ] **Step 1: Write the failing tests** — the server-rendered contract only: the pill inputs exist with the right `name`/`value`/`checked` state, the modal element exists, `Filtros` shows the count, `Limpiar filtros` appears only when narrowed, the card is an `<article>`, the two empty states still branch, and the avatar markup is shared.
- [ ] **Step 2: Run to verify they fail**
- [ ] **Step 3: Build the template and the TS**
- [ ] **Step 4: Tests green, then the full suite**
- [ ] **Step 5: Build both assets**

```bash
npm run build:css && npm run build:js
```
Confirm a distinctive new class appears in `static/css/output.css` and that `static/js/roster_filters.js` exists. Commit both generated files.

- [ ] **Step 6: Commit**

```bash
git commit -m "feat(core): give the roster cards again and a filter modal"
```

---

### Task 4: Documentation

- [ ] **Step 1: Rewrite `docs/platform/employee-roster.md`** to describe the new behaviour in present tense, with no migration commentary — a reader must not be able to tell the single-value version existed. Specifically: the parameter table gains repeatability for `rol`/`area`/`localidad`; "The toolbar" becomes the search bar plus the modal; "The card" describes cards; the key decision about one value per dimension is replaced by the OR-within/AND-across rule and the `.distinct()` reason; the accessibility section gains the dialog and the pill inputs. Add a decision recording why sexo stays single-choice.
- [ ] **Step 2: Update `apps/core/CLAUDE.md`** — the six parameters, now some repeatable; `roster.py`'s `_values`/`_valid_pks`; and that the roster page carries a TS file, so `npm run build:js` matters when touching it.
- [ ] **Step 3: Check `.claude/CLAUDE.md`'s frontend-build section** still reads true now that a second page has TypeScript. Correct it only if it is wrong.
- [ ] **Step 4: Verify** — `grep -rniE "formerly|previously|no longer|used to|replaces the old|deprecated" docs/platform/employee-roster.md` returns nothing.
- [ ] **Step 5: Commit**

```bash
git commit -m "docs: describe the roster's multi-select filters and its cards"
```

---

### Task 5: Verify

- [ ] `pytest` — all green
- [ ] `python manage.py makemigrations --check --dry-run` — no changes
- [ ] `python manage.py check` — no issues
- [ ] `npm run build:css && npm run build:js` then `git diff --stat static/` — no diff
- [ ] Browser checklist for the user: modal opens/closes/Esc, pills toggle, multi-select actually narrows, Aplicar submits, both Limpiar buttons clear, sexo re-click clears, cards read well at 375px, avatar circular on both pages, focus visible throughout, and the page still usable with JS disabled.
