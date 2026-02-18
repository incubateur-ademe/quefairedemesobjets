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
SAMPLE_DB_URL ?= $(if $(SAMPLE_DATABASE_URL),$(SAMPLE_DATABASE_URL),$(DB_URL))
SAMPLE_DUMP_FILE ?= tmpbackup-sample/sample.custom
BASE_DOMAIN := quefairedemesdechets.ademe.local
FIXTURES_OPTIONS := --indent 4 --natural-foreign --natural-primary
HONCHO := uv run honcho

.PHONY: init-playwright
init-playwright:
	npx playwright install --with-deps

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

.PHONY: rebuild-search-index
rebuild-search-index:
	$(DJANGO_ADMIN) rebuild_modelsearch_index


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
	$(DJANGO_ADMIN) loaddata_with_computed_fields categories labels sources actions produits acteur_services acteur_types objets synonymes carte_configs
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
