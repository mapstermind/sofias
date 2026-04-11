.PHONY: install lock serve makemigrations migrate clean-pycache test test-fast test-accounts test-core test-surveys test-responses

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
