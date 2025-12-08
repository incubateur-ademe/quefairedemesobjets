# Loading environment variables
ifneq (,$(wildcard ./.env))
	include .env
	export
endif

# Aliases
PYTHON := uv run python
DJANGO_ADMIN := $(PYTHON) manage.py
PYTEST := uv run pytest
HONCHO := uv run honcho
DB_URL := postgres://webapp:webapp@localhost:6543/webapp# pragma: allowlist secret
BASE_DOMAIN := quefairedemesdechets.ademe.local
FIXTURES_OPTIONS := --indent 4 --natural-foreign --natural-primary

# Makefile config
.PHONY: check
check:
	@source .venv/bin/activate; python --version; pip --version
	@npm --version
	@node --version

.PHONY: init-certs
init-certs:
	@which mkcert > /dev/null || { echo "mkcert is not installed. Please install it first: brew install mkcert (macOS) or visit https://github.com/FiloSottile/mkcert"; exit 1; }
	mkcert -install
	mkcert $(BASE_DOMAIN)
	mv *.pem ./nginx-local-only/certs/
	docker compose restart lvao-proxy

.PHONY: init-playwright
init-playwright:
	npx playwright install --with-deps

.PHONY: init-dev
init-dev:
	# python
	pip install uv
	uv install --with dev,airflow
	make init-certs
	# git
	git config blame.ignoreRevsFile .git-blame-ignore-revs
	pre-commit install
	# javascript
	npm ci
	make init-playwright
	# environment
	cp .env.template .env
	cp ./dags/.env.template ./dags/.env
	# prepare django
	make run-all
	make create-remote-db-server
	make migrate
	make createcachetable
	make createsuperuser
	make seed-database

.PHONY: check-format
check-format:
	uv run black --check --diff .

.PHONY: fix
fix:
	uv run ruff check . --fix
	uv run black --exclude=.venv .

# Run development servers
.PHONY: run-airflow
run-airflow:
	docker compose --profile airflow up -d

.PHONY: run-django
run-django:
	$(HONCHO) start -f Procfile.django.dev

run-all:
	$(HONCHO) start -f Procfile.all.dev

# Local django operations
.PHONY: migrate
migrate:
	$(DJANGO_ADMIN) migrate

.PHONY: collectstatic
collectstatic:
	$(DJANGO_ADMIN) collectstatic --noinput

.PHONY: shell
shell:
	$(DJANGO_ADMIN) shell

.PHONY: makemigrations
makemigrations:
	$(DJANGO_ADMIN) makemigrations

.PHONY: merge-migrations
merge-migrations:
	$(DJANGO_ADMIN) makemigrations --merge


.PHONY: createcachetable
createcachetable:
	$(DJANGO_ADMIN) createcachetable

.PHONY: clearsessions
clearsessions:
	$(DJANGO_ADMIN) clearsessions

.PHONY: create-remote-db-server
create-remote-db-server:
	$(DJANGO_ADMIN) create_remote_db_server

.PHONY: createsuperuser
createsuperuser:
	$(DJANGO_ADMIN) createsuperuser

.PHONY: seed-database
seed-database:
	$(DJANGO_ADMIN) loaddata_with_computed_fields categories labels sources actions produits acteur_services acteur_types objets synonymes suggestions carte_configs
	$(DJANGO_ADMIN) loaddata_with_computed_fields acteurs propositions_services

.PHONY: createsuperuser-example
createsuperuser-example:
	@echo "Creating Django superuser..."
	$(DJANGO_ADMIN) shell -c "from django.contrib.auth import get_user_model; User = get_user_model(); User.objects.create_superuser('admin', password='admin')"

.PHONY: generate-fixtures-acteurs
generate-fixtures-acteurs:
	$(DJANGO_ADMIN) dumpdata_acteurs

.PHONY: generate-fixtures
generate-fixtures:
	$(DJANGO_ADMIN) dumpdata qfdmo.objet $(FIXTURES_OPTIONS) -o qfdmo/fixtures/objets.json
	$(DJANGO_ADMIN) dumpdata qfdmo.categorieobjet qfdmo.souscategorieobjet $(FIXTURES_OPTIONS) -o qfdmo/fixtures/categories.json
	$(DJANGO_ADMIN) dumpdata qfdmo.actiondirection qfdmo.groupeaction qfdmo.action $(FIXTURES_OPTIONS) -o qfdmo/fixtures/actions.json
	$(DJANGO_ADMIN) dumpdata qfdmo.acteurtype $(FIXTURES_OPTIONS) -o qfdmo/fixtures/acteur_types.json
	$(DJANGO_ADMIN) dumpdata qfdmo.acteurservice $(FIXTURES_OPTIONS) -o qfdmo/fixtures/acteur_services.json
	$(DJANGO_ADMIN) dumpdata qfdmo.labelqualite $(FIXTURES_OPTIONS) -o qfdmo/fixtures/labels.json
	$(DJANGO_ADMIN) dumpdata qfdmo.source $(FIXTURES_OPTIONS) -o qfdmo/fixtures/sources.json
	$(DJANGO_ADMIN) dumpdata qfdmo.carteconfig qfdmo.groupeactionconfig $(FIXTURES_OPTIONS) -o qfdmo/fixtures/carte_configs.json
	$(DJANGO_ADMIN) dumpdata qfdmd.synonyme $(FIXTURES_OPTIONS) -o qfdmd/fixtures/synonymes.json
	$(DJANGO_ADMIN) dumpdata qfdmd.produit $(FIXTURES_OPTIONS) -o qfdmd/fixtures/produits.json
	$(DJANGO_ADMIN) dumpdata qfdmd.suggestion $(FIXTURES_OPTIONS) -o qfdmd/fixtures/suggestions.json

.PHONY: clear-cache
clear-cache:
	$(DJANGO_ADMIN) clear_cache --all

.PHONY: npm-upgrade
npm-upgrade:
	npx npm-upgrade

# Happy testing
.PHONY: unit-test
unit-test:
	$(PYTEST) ./unit_tests

.PHONY: integration-test
integration-test:
	$(PYTEST) ./integration_tests


.PHONY: dags-test
dags-test:
	$(PYTEST) ./dags/tests

.PHONY: e2e-test
e2e-test:
	npx playwright test --update-snapshots all

.PHONY: e2e-test-ui
e2e-test-ui:
	npx playwright test --update-snapshots all --ui

.PHONY: a11y
a11y:
	npx playwright test --reporter=list ./e2e_tests/accessibility.spec.ts

.PHONY: js-test
js-test:
	npm run test

.PHONY: backend-test
backend-test:
	@make unit-test
	@make integration-test
	@make dags-test

.PHONY: test
test:
	@make unit-test
	@make e2e-test
	@make integration-test
	@make dags-test

# DSFR
.PHONY: extract-dsfr
extract-dsfr:
	$(PYTHON) ./dsfr_hacks/extract_dsfr_colors.py
	$(PYTHON) ./dsfr_hacks/extract_used_colors.py
	$(PYTHON) ./dsfr_hacks/extract_used_icons.py

.SILENT:
.PHONY: drop-all-tables
drop-all-tables:
	@echo "Removing all tables, views, functions, etc. from the public schema..."
	psql -d '$(DB_URL)' -f scripts/sql/drop_all_tables.sql

.SILENT:
.PHONY: drop-schema-public
drop-schema-public:
	psql -d '$(DB_URL)' -c "DROP SCHEMA IF EXISTS public CASCADE;"

.SILENT:
.PHONY: create-schema-public
create-schema-public:
	psql -d '$(DB_URL)' -c "CREATE SCHEMA IF NOT EXISTS public;"

.PHONY: psql
psql:
	docker compose exec lvao-db psql -U qfdmo -d qfdmo

.PHONY: dump-production
dump-production:
	sh scripts/infrastructure/backup-db.sh

.PHONY: dump-production-quiet
dump-production-quiet:
	sh scripts/infrastructure/backup-db.sh --quiet

# We need to create extensions because they are not restored by pg_restore
.PHONY: create-sql-extensions
create_sql_extensions:

.SILENT:
.PHONY: load-production-dump
load-production-dump:
	@DUMP_FILE=$$(find tmpbackup -type f -name "*.custom" -print -quit); \
	psql -d '$(DB_URL)' -f scripts/sql/create_extensions.sql && \
	pg_restore -d '$(DB_URL)' --schema=public --clean --no-acl --no-owner --no-privileges "$$DUMP_FILE" || true

.PHONY: db-restore
db-restore:
	make dump-production
	make drop-schema-public
	make create-schema-public
	make load-production-dump
	make migrate
	make create-remote-db-server

.PHONY: db-restore-preprod
db-restore-preprod:
	make dump-production-quiet
	make drop-all-tables
	make load-production-dump

.PHONY: db-restore-for-tests
db-restore-for-tests:
	make drop-schema-public
	make create-schema-public
	make migrate
	make seed-database

# Docs
.PHONY: build-docs
build-docs:
	uv run sphinx-build -b html -c docs docs _build

.PHONY: fmt-infra
fmt-infra:
	tofu fmt -recursive infrastructure
	terragrunt hcl fmt infrastructure
