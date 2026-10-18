# Resolve the open points of the NOM-035 supuestos

## What changes

Nine points in `docs/platform/nom-035-valoracion-supuestos.md` were walked through with
the domain owner. Answered points leave the file; three change behavior.

- **#6 Final-score sentence.** The report states three shares: Nulo o Bajo; Medio;
  Alto o Muy alto. Makes `nom-035-report.md` (final-score section) wrong.
- **#4 Report for Administración only.** New permission `can_edit_report`, held only by
  Administrador, gates every report view. The report is no longer suppressed by
  small-group rules. The Ejecutivo principal's report pages (`tablero-empresa/reportes/…`)
  are removed. Makes `nom-035-report.md` (routes, decisions, scope), `apps/reports/CLAUDE.md`,
  `apps/accounts/CLAUDE.md` and the root `CLAUDE.md` wrong. No ADR records the Ejecutivo
  reading decision (checked `docs/adr/`), so no new ADR.
- **#9 Puesto removed.** `UserProfile.position` is dropped (migration) and disappears from
  activation, admin, roster list/detail and docs. The report signatory `title` is unrelated.

Doc-only: #1 and #3 confirmed (entries removed; rule stated in `nom-035-analytics.md`);
#5 and #8 narrowed; #2 and #7 unchanged.

## Tasks

- [x] 1. #6: `final_sentence` test then implementation (three shares)
- [x] 2. #9: remove `position` (tests, form, view, admin, templates, model, migration)
- [x] 3. #4: `can_edit_report` permission, group grant, tests
- [x] 4. #4: gate report views on it; remove Executive views/routes/templates/tests; nav
- [x] 5. #4: report results unsuppressed; update tests; drop `suppressed` from report templates/snapshot if unused
- [x] 6. Full suite, ruff, `makemigrations --check`
- [x] 7. Documentation: supuestos file, report, analytics, dashboard, auth-and-onboarding, csv-user-import, roster, localization, CLAUDE.md files, user guides
