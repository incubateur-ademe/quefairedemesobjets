SHELL := /bin/bash

# Loading environment variables
ifneq (,$(wildcard ./.env))
	include .env
	export
endif

# Aliases
PYTHON := uv run python
DJANGO_ADMIN := $(PYTHON) manage.py
PYTEST := uv run pytest
DB_URL := postgres://webapp:***@localhost:6543/webapp# pragma: allowlist secret
BASE_DOMAIN := quefairedemesdechets.ademe.local
FIXTURES_OPTIONS := --indent 4 --natural-foreign --natural-primary

.PHONY: sync
sync:
	uv sync

.PHONY: check-format
check-format:
	uv run black --check --diff .
	uv run ruff check .

.PHONY: format
format:
	uv run ruff check . --fix
	uv run black --exclude=.venv .

.PHONY: init-playwright
init-playwright:
	npx playwright install --with-deps

# Local django operations
.PHONY: runserver
# Run the django-tasks worker alongside runserver so background tasks (enqueued
# admin actions) are processed locally. The worker runs in the background (&) and
# `trap 'kill %1' EXIT` kills it when runserver stops, so we don't orphan it.
# Must stay on one line: each Make recipe line is its own shell.
runserver:
	$(DJANGO_ADMIN) db_worker & trap 'kill %1' EXIT; $(DJANGO_ADMIN) runserver

.PHONY: runserver-e2e
runserver-e2e:
	make DATABASE_URL=$(DB_WEBAPP_SAMPLE) runserver

.PHONY: migrate
migrate:
	$(DJANGO_ADMIN) migrate

.PHONY: collectstatic
collectstatic:
	$(DJANGO_ADMIN) collectstatic --noinput

.PHONY: shell
shell:
	$(DJANGO_ADMIN) shell

.PHONY: dbshell
dbshell:
	$(DJANGO_ADMIN) dbshell

.PHONY: makemigrations
makemigrations:
	$(DJANGO_ADMIN) makemigrations

.PHONY: merge-migrations
merge-migrations:
	$(DJANGO_ADMIN) makemigrations --merge

.PHONY: rebuild-search-index
rebuild-search-index:
	$(DJANGO_ADMIN) rebuild_modelsearch_index
	# rebuild never removes orphan base entries (django-modelsearch #58)
	$(DJANGO_ADMIN) purge_orphan_searchterm_index


.PHONY: createcachetable
createcachetable:
	$(DJANGO_ADMIN) createcachetable

.PHONY: clearsessions
clearsessions:
	$(DJANGO_ADMIN) clearsessions

.PHONY: compilemessages
compilemessages:
	$(DJANGO_ADMIN) compilemessages -l fr

.PHONY: create-remote-db-server
create-remote-db-server:
	$(DJANGO_ADMIN) create_remote_db_server

.PHONY: createsuperuser
createsuperuser:
	$(DJANGO_ADMIN) createsuperuser

.PHONY: seed-database
seed-database:
	$(DJANGO_ADMIN) loaddata_with_computed_fields categories labels sources actions produits acteur_services acteur_types objets synonymes carte_configs
	$(DJANGO_ADMIN) loaddata_with_computed_fields acteurs propositions_services

.PHONY: createsuperuser-example
createsuperuser-example:
	$(DJANGO_ADMIN) createsuperuser_example

.PHONY: create-db-sample
create-db-sample:
	$(DJANGO_ADMIN) create_webapp_sample_db

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
	$(DJANGO_ADMIN) dumpdata search.searchterm qfdmd.synonyme $(FIXTURES_OPTIONS) -o qfdmd/fixtures/synonymes.json
	$(DJANGO_ADMIN) dumpdata qfdmd.produit $(FIXTURES_OPTIONS) -o qfdmd/fixtures/produits.json

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

.PHONY: prepare-e2e-test
prepare-e2e-test:
	make migrate
	make createcachetable
	# Mirror CI: ensure unaccent / pg_trgm extensions and the f_unaccent()
	# wrapper exist before rebuilding the search index. Without these, the
	# autocomplete fuzzy search raises ProgrammingError at runtime.
	$(DJANGO_ADMIN) enable_unaccent
	$(DJANGO_ADMIN) enable_trigram
	make rebuild-search-index
	make createsuperuser-example
	BASE_URL=http://localhost:8888 npm run build

.PHONY: prepare-e2e-test-local
prepare-e2e-test-local:
	make create-db-sample
	make -C .. DB_WEBAPP_SAMPLE=$(DB_WEBAPP_SAMPLE) load-sample-dump
	make DATABASE_URL=$(DB_WEBAPP_SAMPLE) prepare-e2e-test

.PHONY: e2e-test
e2e-test:
	npx playwright test --update-snapshots all

.PHONY: e2e-test-ui
e2e-test-ui:
	npx playwright test --update-snapshots all --ui --workers=4

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

.PHONY: test
test:
	@make unit-test
	@make e2e-test
	@make integration-test

# DSFR
.PHONY: extract-dsfr
extract-dsfr:
	$(PYTHON) ./dsfr_hacks/extract_dsfr_colors.py
	$(PYTHON) ./dsfr_hacks/extract_used_colors.py
	$(PYTHON) ./dsfr_hacks/extract_used_icons.py
