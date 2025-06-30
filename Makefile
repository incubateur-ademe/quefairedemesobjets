# Loading environment variables
ifneq (,$(wildcard ./.env))
	include .env
	export
endif

# Aliases
PYTHON := poetry run python
DJANGO_ADMIN := $(PYTHON) manage.py
PYTEST := poetry run pytest
HONCHO := poetry run honcho
DB_URL := postgres://qfdmo:qfdmo@localhost:6543/qfdmo# pragma: allowlist secret
ASSISTANT_URL := quefairedemesdechets.ademe.local
LVAO_URL := lvao.ademe.local
FIXTURES_OPTIONS := --indent 4 --natural-foreign --natural-primary

# Makefile config
.PHONY: check
check:
	@source .venv/bin/activate; python --version; pip --version
	@npm --version
	@node --version

.PHONY: init-certs
init-certs:
	docker run -ti -v ./nginx-local-only/certs:/app/certs -w /app/certs --rm alpine/mkcert $(LVAO_URL) $(ASSISTANT_URL)

.PHONY: init-playwright
init-playwright:
	npx playwright install --with-deps

.PHONY: init-dev
init-dev:
	# git
	git config blame.ignoreRevsFile .git-blame-ignore-revs
	pre-commit install
	# python
	curl -sSL https://install.python-poetry.org | python3 -
	poetry install --with dev,airflow
	make init-certs
	# javascript
	npm install
	make init-playwright
	# environment
	cp .env.template .env
	cp ./dags/.env.template ./dags/.env
	# prepare django
	psql -d "$(DB_URL)" -f scripts/sql/create_databases.sql
	psql -d "$(DB_URL)" -f scripts/sql/create_extensions.sql
	make migrate
	make createcachetable
	make createsuperuser
	make seed-database

.PHONY: check-format
check-format:
	poetry run black --check --diff .

.PHONY: fix
fix:
	poetry run ruff check . --fix
	poetry run black --exclude=.venv .

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

.PHONY: createsuperuser
createsuperuser:
	$(DJANGO_ADMIN) createsuperuser

.PHONY: seed-database
seed-database:
	$(DJANGO_ADMIN) loaddata categories labels sources actions produits acteur_services acteur_types objets synonymes suggestions
	$(DJANGO_ADMIN) loaddata_with_computed_fields acteurs proposition_services

FIXTURES_ACTEURS_PKS = "communautelvao_LWTYYUPBDMWM","6554f1bb-82d2-567f-8453-eec5405e5b5d","65791ef2-bb37-4569-b011-8cece03dcdcf","antiquites_du_poulbenn_152575_reparation","refashion_TLC-REFASHION-PAV-3445001","communautelvao_VBOFDJDBOCTW","refashion_TLC-REFASHION-REP-603665791852778329","ocad3e_SGS-02069" # pragma: allowlist secret
.PHONY: generate-fixtures-acteurs
generate-fixtures-acteurs:
	$(DJANGO_ADMIN) dumpdata qfdmo.displayedacteur $(FIXTURES_OPTIONS) --pk $(FIXTURES_ACTEURS_PKS) -o qfdmo/fixtures/acteurs.json # pragma: allowlist secret
	@IDS=$$(poetry run python manage.py shell -c "from qfdmo.models import DisplayedActeur; pks = '$(FIXTURES_ACTEURS_PKS)'.split(','); print(','.join(map(str, DisplayedActeur.objects.filter(pk__in=pks).values_list('proposition_services__pk', flat=True))))"); \
	echo "Generate fixtures for Propositions services: IDS=$$IDS"; \
	$(DJANGO_ADMIN) dumpdata qfdmo.displayedpropositionservice $(FIXTURES_OPTIONS) --pk $$IDS -o qfdmo/fixtures/propositions_services.json

.PHONY: generate-fixtures
generate-fixtures:
	$(DJANGO_ADMIN) dumpdata qfdmo.objet $(FIXTURES_OPTIONS) -o qfdmo/fixtures/objets.json
	$(DJANGO_ADMIN) dumpdata qfdmo.categorieobjet qfdmo.souscategorieobjet $(FIXTURES_OPTIONS) -o qfdmo/fixtures/categories.json
	$(DJANGO_ADMIN) dumpdata qfdmo.actiondirection qfdmo.groupeaction qfdmo.action $(FIXTURES_OPTIONS) -o qfdmo/fixtures/actions.json
	$(DJANGO_ADMIN) dumpdata qfdmo.acteurtype $(FIXTURES_OPTIONS) -o qfdmo/fixtures/acteur_types.json
	$(DJANGO_ADMIN) dumpdata qfdmo.acteurservice $(FIXTURES_OPTIONS) -o qfdmo/fixtures/acteur_services.json
	$(DJANGO_ADMIN) dumpdata qfdmo.labelqualite $(FIXTURES_OPTIONS) -o qfdmo/fixtures/labels.json
	$(DJANGO_ADMIN) dumpdata qfdmo.source $(FIXTURES_OPTIONS) -o qfdmo/fixtures/sources.json
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


.PHONY: test-dags
test-dags:
	$(PYTEST) ./dags/tests

.PHONY: e2e-test
e2e-test:
	npx playwright test --update-snapshots

.PHONY: e2e-test-ui
e2e-test-ui:
	npx playwright test --update-snapshots --ui

.PHONY: a11y
a11y:
	npx playwright test --reporter=list ./e2e_tests/accessibility.spec.ts

.PHONY: js-test
js-test:
	npm run test

.PHONY: test
test:
	@make unit-test
	@make e2e-test
	@make integration-test
	@make test-dags

# DSFR
.PHONY: extract-dsfr
extract-dsfr:
	$(PYTHON) ./dsfr_hacks/extract_dsfr_colors.py
	$(PYTHON) ./dsfr_hacks/extract_used_colors.py
	$(PYTHON) ./dsfr_hacks/extract_used_icons.py

.PHONY: drop-schema-public
drop-schema-public:
	docker compose exec lvao-db psql -U qfdmo -d qfdmo -c "DROP SCHEMA IF EXISTS public CASCADE;"

.PHONY: create-schema-public
create-schema-public:
	docker compose exec lvao-db psql -U qfdmo -d qfdmo -c "CREATE SCHEMA IF NOT EXISTS public;"

.PHONY: dump-production
dump-production:
	sh scripts/infrastructure/backup-db.sh

# We need to create extensions because they are not restored by pg_restore
.PHONY: load-production-dump
load-production-dump:
	@DUMP_FILE=$$(find tmpbackup -type f -name "*.custom" -print -quit); \
	psql -d "$(DB_URL)" -f scripts/sql/create_extensions.sql && \
	pg_restore -d "$(DB_URL)" --schema=public --clean --no-acl --no-owner --no-privileges "$$DUMP_FILE" || true

.PHONY: db-restore
db-restore:
	make dump-production
	make drop-schema-public
	make create-schema-public
	make load-production-dump
	make migrate

.PHONY: db-restore-for-tests
db-restore-for-tests:
	make drop-schema-public
	make create-schema-public
	make migrate
	make seed-database

# Docs
.PHONY: build-docs
build-docs:
	poetry run sphinx-build -b html -c docs docs _build
