# Loading environment variables
ifneq (,$(wildcard ./.env))
	include .env
	export
endif

# Aliases
PYTHON := .venv/bin/python
DJANGO_ADMIN := $(PYTHON) manage.py
PYTEST := $(PYTHON) -m pytest

# Makefile config
.PHONY: check
check:
	@source .venv/bin/activate; python --version; pip --version
	@npm --version
	@node --version

# Setup development environment
.PHONY: init-dev
init-dev:
	# git
	git config blame.ignoreRevsFile .git-blame-ignore-revs
	pre-commit install
	# python
	python -m venv .venv --prompt $(basename $(CURDIR)) --clear
	$(PYTHON) -m pip install --no-deps -r requirements.txt -r dev-requirements.txt
	$(PYTON) -m pip install pip-tools
	# javascript
	npm install
	npx playwright install --with-deps
	# environment
	cp .env.template .env
	cp ./dags/.env.template ./dags/.env
	# prepare django
	make migrate
	make createsuperuser

# Run development servers
.PHONY: run-airflow
run-airflow:
	docker compose --profile airflow up -d

.PHONY: run-django
run-django:
	docker compose --profile lvao up -d
	rm -rf .parcel-cache
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

# Dependencies management
.PHONY: pip-update
pip-update:
	$(PYTHON) -m pip-compile dev-requirements.in --generate-hashes
	$(PYTHON) -m pip-compile requirements.in --generate-hashes

.PHONY: npm-upgrade
npm-upgrade:
	npx npm-upgrade

# Happy testing
.PHONY: unit-test
unit-test:
	$(PYTEST) ./unit_tests

.PHONY: e2e-test
e2e-test:
	npx playwright test
	$(PYTEST) ./integration_tests

.PHONY: js-test
js-test:
	npm run test

.PHONY: test
test:
	@make unit-test
	@make e2e-test
