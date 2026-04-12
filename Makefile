.PHONY: install lock serve makemigrations migrate bootstrap-groups clean-pycache test test-fast test-accounts test-core test-surveys test-responses \
        survey question-templates question choices sections lint fmt

lint:
	poetry run ruff check --fix .

fmt:
	poetry run ruff format .

install:
	poetry install

lock:
	poetry lock

serve:
	poetry run python manage.py runserver

makemigrations:
	poetry run python manage.py makemigrations

migrate:
	poetry run python manage.py migrate

bootstrap-groups:
	poetry run python manage.py bootstrap_groups

clean-pycache:
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -name "*.pyc" -delete

test:
	poetry run pytest

test-fast:
	poetry run pytest --reuse-db

test-accounts:
	poetry run pytest apps/accounts/tests/

test-core:
	poetry run pytest apps/core/tests/

test-surveys:
	poetry run pytest apps/surveys/tests/

test-responses:
	poetry run pytest apps/responses/tests/

# ── Survey builder ─────────────────────────────────────────────────────────────
#
# Recommended order for building a survey from scratch:
#
#   0. make question-templates — build the reusable question/choice library
#                                (company-agnostic; do this once, reuse across surveys)
#
#   1. make survey             — create a Survey + SurveyVersion v1
#                                (offers to launch `question` automatically when done)
#
#   2. make question           — add questions to an existing survey
#                                (stamp from library template, or create manually)
#
#   3. make choices            — add, edit, or delete choices on a question
#                                (only applies to single_choice and multiple_choice questions;
#                                 skippable when stamping from a template with choices)
#
#   4. make sections           — create sections and organise questions into them
#                                (optional; run after questions exist)
#
# Each command can also be run standalone at any time.
# Press Ctrl-C at any prompt to exit cleanly — no partial writes are left behind.

question-templates:
	poetry run python manage.py manage_question_templates

survey:
	poetry run python manage.py create_survey

question:
	poetry run python manage.py create_question

choices:
	poetry run python manage.py manage_choices

sections:
	poetry run python manage.py manage_sections
