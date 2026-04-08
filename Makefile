.PHONY: install lock serve makemigrations migrate

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
