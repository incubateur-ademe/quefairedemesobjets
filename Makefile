# Aliases
PYTHON := uv run python
DB_URL := postgres://webapp:webapp@localhost:6543/webapp# pragma: allowlist secret
SAMPLE_DB_URL ?= $(if $(SAMPLE_DATABASE_URL),$(SAMPLE_DATABASE_URL),$(DB_URL))
SAMPLE_DUMP_FILE ?= tmpbackup-sample/sample.custom
BASE_DOMAIN := quefairedemesdechets.ademe.local

# Loading environment variables
ifneq (,$(wildcard ./.env))
    include .env
    export
endif

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

# FIXME : Reactive it !

# .PHONY: init-dev
# init-dev:
# 	# python
# 	pip install uv
# 	uv install --with dev,airflow
# 	make init-certs
# 	# git
# 	git config blame.ignoreRevsFile .git-blame-ignore-revs
# 	pre-commit install
# 	# javascript
# 	npm ci
# 	make init-playwright
# 	# environment
# 	cp .env.template .env
# 	cp ./dags/.env.template ./dags/.env
# 	# prepare django
# 	make run-all
# 	make create-remote-db-server
# 	make migrate
# 	make createcachetable
# 	make createsuperuser
# 	make seed-database

.PHONY: sync
sync:
	uv sync --all-packages

.PHONY: check-format
check-format:
	uv run black --check --diff .

.PHONY: format
format:
	uv run ruff check . --fix
	uv run black --exclude=.venv .

# Run development servers
.PHONY: run-airflow
run-airflow:
	docker compose --profile airflow up -d

# Local django operations (delegated to webapp/Makefile)
.PHONY: webapp-migrate
webapp-migrate:
	$(MAKE) -C webapp migrate

.PHONY: webapp-collectstatic
webapp-collectstatic:
	$(MAKE) -C webapp collectstatic

.PHONY: webapp-shell
webapp-shell:
	$(MAKE) -C webapp shell

.PHONY: webapp-dbshell
webapp-dbshell:
	$(MAKE) -C webapp dbshell

.PHONY: webapp-makemigrations
webapp-makemigrations:
	$(MAKE) -C webapp makemigrations

.PHONY: webapp-merge-migrations
webapp-merge-migrations:
	$(MAKE) -C webapp merge-migrations

.PHONY: webapp-rebuild-search-index
webapp-rebuild-search-index:
	$(MAKE) -C webapp rebuild-search-index

.PHONY: webapp-createcachetable
webapp-createcachetable:
	$(MAKE) -C webapp createcachetable

.PHONY: webapp-clearsessions
webapp-clearsessions:
	$(MAKE) -C webapp clearsessions

.PHONY: webapp-create-remote-db-server
webapp-create-remote-db-server:
	$(MAKE) -C webapp create-remote-db-server

.PHONY: webapp-createsuperuser
webapp-createsuperuser:
	$(MAKE) -C webapp createsuperuser

.PHONY: webapp-seed-database
webapp-seed-database:
	$(MAKE) -C webapp seed-database

.PHONY: webapp-createsuperuser-example
webapp-createsuperuser-example:
	$(MAKE) -C webapp createsuperuser-example

.PHONY: webapp-generate-fixtures-acteurs
webapp-generate-fixtures-acteurs:
	$(MAKE) -C webapp generate-fixtures-acteurs

.PHONY: webapp-generate-fixtures
webapp-generate-fixtures:
	$(MAKE) -C webapp generate-fixtures

.PHONY: webapp-clear-cache
webapp-clear-cache:
	$(MAKE) -C webapp clear-cache

.PHONY: webapp-npm-upgrade
webapp-npm-upgrade:
	$(MAKE) -C webapp npm-upgrade

# Happy testing
.PHONY: webapp-unit-test
webapp-unit-test:
	$(MAKE) -C webapp unit-test

.PHONY: webapp-integration-test
webapp-integration-test:
	$(MAKE) -C webapp integration-test

.PHONY: webapp-dags-test
webapp-dags-test:
	$(MAKE) -C webapp dags-test

.PHONY: webapp-e2e-test
webapp-e2e-test:
	$(MAKE) -C webapp e2e-test

.PHONY: webapp-e2e-test-ui
webapp-e2e-test-ui:
	$(MAKE) -C webapp e2e-test-ui

.PHONY: webapp-a11y
webapp-a11y:
	$(MAKE) -C webapp a11y

.PHONY: webapp-js-test
webapp-js-test:
	$(MAKE) -C webapp js-test

.PHONY: webapp-backend-test
webapp-backend-test:
	$(MAKE) -C webapp backend-test

.PHONY: webapp-test
webapp-test:
	$(MAKE) -C webapp test

# DSFR
.PHONY: webapp-extract-dsfr
webapp-extract-dsfr:
	$(MAKE) -C webapp extract-dsfr

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
.PHONY: drop-schema-public-sample
drop-schema-public-sample:
	psql -d '$(SAMPLE_DB_URL)' -c "DROP SCHEMA IF EXISTS public CASCADE;"

.SILENT:
.PHONY: create-schema-public
create-schema-public:
	psql -d '$(DB_URL)' -c "CREATE SCHEMA IF NOT EXISTS public;"

.SILENT:
.PHONY: create-schema-public-sample
create-schema-public-sample:
	psql -d '$(SAMPLE_DB_URL)' -c "CREATE SCHEMA IF NOT EXISTS public;"


.SILENT:
.PHONY: create-db-extensions
create-extensions:
	@echo "Creating required extensions"
	psql -d '$(DB_URL)' -f scripts/sql/create_extensions.sql

.PHONY: psql
psql:
	docker compose exec lvao-db psql -U qfdmo -d qfdmo

.PHONY: dump-prod
dump-prod:
	sh scripts/infrastructure/backup-db.sh --env prod

.PHONY: dump-preprod
dump-preprod:
	sh scripts/infrastructure/backup-db.sh --quiet --env preprod

.PHONY: dump-prod-quiet
dump-prod-quiet:
	sh scripts/infrastructure/backup-db.sh --quiet

.PHONY: dump-sample
dump-sample:
	@[ -n "$(REMOTE_SAMPLE_DATABASE_URL)" ] || { echo "REMOTE_SAMPLE_DATABASE_URL is not set"; exit 1; }
	mkdir -p $(dir $(SAMPLE_DUMP_FILE))
	pg_dump --format=custom --no-acl --no-owner --no-privileges "$(REMOTE_SAMPLE_DATABASE_URL)" --file="$(SAMPLE_DUMP_FILE)"


.SILENT:
.PHONY: load-prod-dump
load-prod-dump:
	@DUMP_FILE=$$(find tmpbackup-prod -type f -name "*.custom" -print -quit); \
	psql -d '$(DB_URL)' -f scripts/sql/create_extensions.sql && \
	pg_restore -d '$(DB_URL)' --schema=public --clean --no-acl --no-owner --no-privileges "$$DUMP_FILE" || true

.SILENT:
.PHONY: load-preprod-dump
load-preprod-dump:
	@DUMP_FILE=$$(find tmpbackup-preprod -type f -name "*.custom" -print -quit); \
	psql -d '$(DB_URL)' -f scripts/sql/create_extensions.sql && \
	pg_restore -d '$(DB_URL)' --schema=public --clean --no-acl --no-owner --no-privileges "$$DUMP_FILE" || true

.SILENT:
.PHONY: load-sample-dump
load-sample-dump:
	@DUMP_FILE=$(SAMPLE_DUMP_FILE); \
	[ -f "$$DUMP_FILE" ] || DUMP_FILE=$$(find tmpbackup-sample -type f -name "*.custom" -print -quit); \
	[ -n "$$DUMP_FILE" ] || { echo "No sample dump found"; exit 1; }; \
	psql -d '$(SAMPLE_DB_URL)' -f scripts/sql/create_extensions.sql && \
	pg_restore -d '$(SAMPLE_DB_URL)' --schema=public --clean --no-acl --no-owner --no-privileges "$$DUMP_FILE" || true

.PHONY: db-restore-local-from-prod
db-restore-local-from-prod:
	make dump-prod
	make drop-schema-public
	make create-schema-public
	make load-prod-dump
	make webapp-migrate
	make webapp-create-remote-db-server

.PHONY: db-restore-local-from-preprod
db-restore-local-from-preprod:
	make dump-preprod
	make drop-schema-public
	make create-schema-public
	make load-preprod-dump
	make webapp-migrate
	make webapp-create-remote-db-server

.PHONY: db-restore-preprod-from-prod
db-restore-preprod-from-prod:
	make dump-prod-quiet
	make drop-all-tables
	make load-prod-dump

.PHONY: db-restore-local-from-sample
db-restore-local-from-sample:
	make dump-sample
	make drop-schema-public-sample
	make create-schema-public-sample
	make load-sample-dump

.PHONY: db-restore-local-for-tests
db-restore-local-for-tests:
	make drop-schema-public
	make create-schema-public
	make webapp-migrate
	make webapp-seed-database

# Docs
.PHONY: build-docs
build-docs:
	make -C docs build-docs

.PHONY: fmt-infra
fmt-infra:
	tofu fmt -recursive infrastructure
	terragrunt hcl fmt infrastructure
