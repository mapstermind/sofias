# responses

Storage for survey submissions and answers. Thin data layer — collection logic (the form handling) lives in `apps/surveys/views.py`; reporting/aggregation reads from here. No URLs or views of its own.

## Models (`models.py`)

- `SurveySubmission` — one respondent's attempt at a `surveys.SurveyAssignment`.
  - `status`: `in_progress` / `completed`.
  - `user` is nullable (`SET_NULL`) so a deleted employee's answers survive (they still count in the NOM-035 aggregates) — **not** to allow anonymous submissions: every submission is created by a logged-in user (`apps/surveys/views.py` is `@login_required`), so `user` is null only for users deleted after the fact. A **partial unique constraint** enforces one submission per (user, assignment) only when `user` is set.
  - `completed_at` is set when all questions are answered (by the survey view).
- `Answer` — one answer within a submission.
  - FK to `surveys.Question`; `unique(submission, question)`.
  - `value` is a **JSONField whose shape depends on `question.question_type`** (string, int, float, bool, or list for multiple-choice). There is no per-type column — consumers must interpret `value` using the question type.

## Conventions & gotchas

- Writing answers is done exclusively by `apps/surveys/views.py` (`survey_detail`, `autosave_survey`), which `update_or_create`s `Answer` rows and deletes rows whose value becomes empty/None. Reading/rendering answers is done in `apps/core` (`EmployeeDetailView`) and the admin.
- When adding a `Question.QuestionType`, ensure the JSON `value` shape it produces is handled everywhere answers are parsed (surveys views) and rendered (core views, templates, admin).
- `admin.py` registers `SurveySubmission` (with inline `Answer`s) and `Answer`, filterable by company/survey.
- Tests: `tests/test_models.py`.
