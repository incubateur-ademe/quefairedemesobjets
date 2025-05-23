# Loading environment variables
ifneq (,$(wildcard ./.env))
	include .env
	export
endif

# Aliases
PYTHON := poetry run python
DJANGO_ADMIN := $(PYTHON) manage.py
PYTEST := poetry run pytest
DB_URL := postgres://qfdmo:qfdmo@localhost:6543/qfdmo# pragma: allowlist secret
ASSISTANT_URL := quefairedemesdechets.ademe.local
LVAO_URL := lvao.ademe.local

# Makefile config
.PHONY: check
check:
	@source .venv/bin/activate; python --version; pip --version
	@npm --version
	@node --version

.PHONY: init-certs
init-certs:
	docker run -ti -v ./nginx-local-only/certs:/app/certs -w /app/certs --rm alpine/mkcert $(LVAO_URL) $(ASSISTANT_URL)


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
	poetry run ruff check . --fix
	poetry run black --exclude=.venv .


# Run development servers
.PHONY: run-airflow
run-airflow:
	docker compose --profile airflow up -d

.PHONY: run-django
run-django:
	honcho start -f Procfile.django.dev

run-all:
	honcho start -f Procfile.all.dev

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

.PHONY: e2e-test
e2e-test:
	npx playwright test --update-snapshots --ui
	$(PYTEST) ./integration_tests

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

# DSFR
.PHONY: extract-dsfr
extract-dsfr:
	$(PYTHON) ./dsfr_hacks/extract_dsfr_colors.py
	$(PYTHON) ./dsfr_hacks/extract_used_colors.py
	$(PYTHON) ./dsfr_hacks/extract_used_icons.py

.PHONY: drop-schema-public
drop-schema-public:
	docker compose exec warehouse-db psql -U qfdmo -d qfdmo -c "DROP SCHEMA IF EXISTS public CASCADE;"

.PHONY: create-schema-public
create-schema-public:
	docker compose exec warehouse-db psql -U qfdmo -d qfdmo -c "CREATE SCHEMA IF NOT EXISTS public;"

.PHONY: dump-production
dump-production:
	mkdir -p tmpbackup
	scalingo --app quefairedemesobjets --addon postgresql backups-download --output tmpbackup/backup.tar.gz
	tar xfz tmpbackup/backup.tar.gz --directory tmpbackup

# We need to create extensions because they are not restored by pg_restore
.PHONY: load-production-dump
load-production-dump:
	@DUMP_FILE=$$(find tmpbackup -type f -name "*.pgsql" -print -quit); \
	psql -d "$(DB_URL)" -f scripts/sql/create_extensions.sql && \
	pg_restore -d "$(DB_URL)" --schema=public --clean --no-acl --no-owner --no-privileges "$$DUMP_FILE" || true
	rm -rf tmpbackup

.PHONY: db-restore
db-restore:
	make drop-schema-public
	make create-schema-public
	make dump-production
	make load-production-dump
	make migrate

# Docs
.PHONY: build-docs
build-docs:
		poetry run sphinx-build -b html -c docs docs _build
