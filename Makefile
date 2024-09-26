# Loading environment variables
ifneq (,$(wildcard ./.env))
	include .env
	export
endif

DJANGO_ADMIN := .venv/bin/python manage.py
PYTEST := .venv/bin/python -m pytest

# Setup development environment
.PHONY: init-dev
init-dev:
	python -m venv .venv --prompt $(basename $(CURDIR)) --clear
	source .venv/bin/activate; pip install --no-deps -r requirements.txt -r dev-requirements.txt
	npm install
	cp .env.template .env
	cp ./dags/.env.template ./dags/.env
	make migrate
	make createsuperuser

# Run development servers
.PHONY: run-airflow
run-airflow:
		docker compose --profile airflow up -d

.PHONY: run-django
run-django:
		honcho start -f Procfile.dev

# Local django operations
.PHONY: migrate
migrate:
	$(DJANGO_ADMIN) migrate

.PHONY: createsuperuser
createsuperuser:
	$(DJANGO_ADMIN) createsuperuse

.PHONY: seed-database
seed-database:
	$(DJANGO_ADMIN) loaddata categories actions acteur_services acteur_types


# Happy testing
.PHONY: unit-test
unit-test:
	$(PYTEST) ./unit_tests

.PHONY: e2e-test
e2e-test:
	$(PYTEST) ./integration_tests

.PHONY: test
test:
	@make unit-test
	@make e2e-test

.PHONY: check
check:
	@source .venv/bin/activate; python --version; pip --version
	@npm --version
	@node --version
