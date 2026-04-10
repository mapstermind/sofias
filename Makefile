.PHONY: install lock serve makemigrations migrate clean-pycache

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
