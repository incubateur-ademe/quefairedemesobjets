# Loading environment variables
ifneq (,$(wildcard ./.env))
	include .env
	export
endif

# Aliases
PYTHON := .venv/bin/python
DJANGO_ADMIN := $(PYTHON) manage.py
PYTEST := $(PYTHON) -m pytest
DB_URL := postgres://qfdmo:qfdmo@localhost:6543/qfdmo# pragma: allowlist secret

# Makefile config
.PHONY: check
check:
	@source .venv/bin/activate; python --version; pip --version
	@npm --version
	@node --version

# Setup development environment
.PHONY: update-requirements
update-requirements:
	$(PYTHON) -m pip install --no-deps -r requirements.txt -r dev-requirements.txt


.PHONY: init-venv
init-venv:
	python -m venv .venv --prompt $(basename $(CURDIR)) --clear

.PHONY: init-dev
init-dev:
	# git
	git config blame.ignoreRevsFile .git-blame-ignore-revs
	pre-commit install
	# python
	make init-venv
	$(PYTHON) -m pip install pip-tools
	$(PYTHON) -m pip install --no-deps -r requirements.txt -r dev-requirements.txt
	# javascript
	npm install
	npx playwright install --with-deps
	# environment
	cp .env.template .env
	cp ./dags/.env.template ./dags/.env
	# prepare django
	make migrate
	make createcachetable
	make createsuperuser

.PHONY: fix
fix:
	$(PYTHON) -m ruff check . --fix
	$(PYTHON) -m black --exclude=.venv .


# Run development servers
.PHONY: run-airflow
run-airflow:
	docker compose --profile airflow up -d

.PHONY: run-django
run-django:
	rm -rf .parcel-cache
	honcho start -f Procfile.dev

run-all:
	docker compose --profile airflow up -d
	rm -rf .parcel-cache
	$(DJANGO_ADMIN) runserver 0.0.0.0:8000
	npm run watch

# Local django operations
.PHONY: migrate
migrate:
	$(DJANGO_ADMIN) migrate

.PHONY: makemigrations
makemigrations:
	$(DJANGO_ADMIN) makemigrations

.PHONY: merge-migrations
merge-migrations:
	$(DJANGO_ADMIN) makemigrations --merge


.PHONY: createcachetable
createcachetable:
	$(DJANGO_ADMIN) createcachetable

.PHONY: createsuperuser
createsuperuser:
	$(DJANGO_ADMIN) createsuperuser

.PHONY: seed-database
seed-database:
	$(DJANGO_ADMIN) loaddata categories actions acteur_services acteur_types acteurs objets

.PHONY: drop-db
drop-db:
	docker compose exec lvao-db dropdb -f -i -U qfdmo -e qfdmo

.PHONY: create-db
create-db:
	docker compose exec lvao-db createdb -U qfdmo -e qfdmo

.PHONY: restore-prod
restore-prod:
	./scripts/restore_prod_locally.sh

.PHONY: clear-cache
clear-cache:
	$(DJANGO_ADMIN) clear_cache --all

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

# DSFR
.PHONY: extract-dsfr
extract-dsfr:
	$(PYTHON) ./dsfr_hacks/extract_dsfr_colors.py
	$(PYTHON) ./dsfr_hacks/extract_used_colors.py
	$(PYTHON) ./dsfr_hacks/extract_used_icons.py

# RESTORE DB LOCALLY
.PHONY: db-restore
db-restore:
	mkdir -p tmpbackup
	scalingo --app quefairedemesobjets --addon postgresql backups-download --output tmpbackup/backup.tar.gz
	tar xfz tmpbackup/backup.tar.gz --directory tmpbackup
	@DUMP_FILE=$$(find tmpbackup -type f -name "*.pgsql" -print -quit); \
	for table in $$(psql "$(DB_URL)" -t -c "SELECT tablename FROM pg_tables WHERE schemaname='public'"); do \
	    psql "$(DB_URL)" -c "DROP TABLE IF EXISTS $$table CASCADE"; \
	done || true
	@DUMP_FILE=$$(find tmpbackup -type f -name "*.pgsql" -print -quit); \
	pg_restore -d "$(DB_URL)" --clean --no-acl --no-owner --no-privileges "$$DUMP_FILE" || true
	rm -rf tmpbackup
	$(DJANGO_ADMIN) migrate
