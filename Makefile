# Aliases
BASE_DOMAIN := quefairedemesdechets.localhost
WEBAPP_DB_PORT ?= 6543
DB_URL = postgres://webapp:webapp@localhost:$(WEBAPP_DB_PORT)/webapp# pragma: allowlist secret
PG_RESTORE_JOBS ?= 1
WAGTAIL_FRENCH_SQL := webapp/qfdmd/migrations/sql/create_wagtail_french_config.sql

include versions.mk

# apache/airflow:slim-<version>-python<version> — extracted from data-platform/pyproject.toml,
# the only place where the Airflow version is written. The CI reads it with
# `make -s airflow-version`.
AIRFLOW_VERSION ?= $(shell sed -n 's/.*"apache-airflow==\([^"]*\)".*/\1/p' data-platform/pyproject.toml)
export AIRFLOW_VERSION

.PHONY: airflow-version
airflow-version:
	@echo $(AIRFLOW_VERSION)

# KEY=value lines, appended to $GITHUB_ENV by the image build workflows
.PHONY: versions
versions:
	@echo NODE_VERSION=$(NODE_VERSION)
	@echo PYTHON_VERSION=$(PYTHON_VERSION)
	@echo UV_VERSION=$(UV_VERSION)
	@echo AIRFLOW_VERSION=$(AIRFLOW_VERSION)

# The containers run as the host user (docker-compose.yml)
export HOST_UID := $(shell id -u)
PSQL := docker compose exec -T lvao-webapp-db psql -U webapp -d webapp

# --- Local stack -----------------------------------------------------------
# Everything runs in Docker Compose: no Python, Node or Postgres on the host.

# First start: builds the images, starts the stack and creates the example
# superuser (admin / admin). Safe to run again. The data comes from a restore:
# make db-restore-local-from-prod
.PHONY: setup
setup: up
	$(MAKE) -C webapp createsuperuser-example
	@echo "✓ http://$(BASE_DOMAIN) (ou http://localhost:8000)"

# Rebuilds the images when a lockfile or a Dockerfile changed, then starts
.PHONY: up
up:
	docker compose up -d --build --wait

.PHONY: down
down:
	docker compose --profile airflow down

.PHONY: logs
logs:
	docker compose logs -f --tail 50

# make add pkg=requests [group=dev]
.PHONY: add
add:
	docker compose run --rm webapp uv add --project /app/webapp $(if $(group),--group $(group)) $(pkg)
	$(MAKE) up

# make add-js pkg=lodash
.PHONY: add-js
add-js:
	docker compose run --rm assets npm install -w webapp $(pkg)
	$(MAKE) up

.PHONY: check-format
check-format:
	make -C data-platform check-format
	make -C webapp check-format

.PHONY: format
format:
	make -C data-platform format
	make -C webapp format

# Run development servers
.PHONY: run-airflow
run-airflow:
	docker compose --profile airflow up -d

# Run development servers
.PHONY: build-airflow
build-airflow:
	docker compose --profile airflow build

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

.PHONY: webapp-compilemessages
webapp-compilemessages:
	$(MAKE) -C webapp compilemessages

.PHONY: webapp-create-remote-db-server
webapp-create-remote-db-server:
	$(MAKE) -C webapp create-remote-db-server

.PHONY: webapp-createsuperuser
webapp-createsuperuser:
	$(MAKE) -C webapp createsuperuser

.PHONY: webapp-createsuperuser-example
webapp-createsuperuser-example:
	$(MAKE) -C webapp createsuperuser-example

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

.PHONY: data-platform-dags-test
data-platform-dags-test:
	$(MAKE) -C data-platform dags-test

# --- E2E tests -------------------------------------------------------------
# `e2e-prepare` checks the prerequisites, builds the sample database through
# the `compute_sample_acteur` DAG and prepares the webapp; `e2e` then runs
# the Playwright suite. Both require a restored `webapp` database
# (make db-restore-local-from-prod).
.PHONY: e2e-prepare
e2e-prepare:
	./scripts/e2e_prepare.sh

# Same, without rebuilding the sample database.
.PHONY: e2e-prepare-fast
e2e-prepare-fast:
	./scripts/e2e_prepare.sh --skip-dag

.PHONY: e2e
e2e:
	$(MAKE) e2e-prepare
	$(MAKE) webapp-e2e-test

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
	$(PSQL) -c "DROP SCHEMA IF EXISTS public CASCADE;"

.SILENT:
.PHONY: create-schema-public
create-schema-public:
	$(PSQL) -c "CREATE SCHEMA IF NOT EXISTS public;"

.PHONY: psql
psql:
	docker compose exec lvao-webapp-db psql -U webapp -d webapp

.PHONY: dump-prod
dump-prod:
	bash scripts/infrastructure/backup-db.sh --env prod

.PHONY: dump-preprod
dump-preprod:
	bash scripts/infrastructure/backup-db.sh --quiet --env preprod

# USE_LATEST_BACKUP=true réutilise le dernier backup Scaleway prêt
# au lieu d'en créer un nouveau (évite la création + polling).
.PHONY: dump-prod-quiet
dump-prod-quiet:
	bash scripts/infrastructure/backup-db.sh --quiet $(if $(filter true,$(USE_LATEST_BACKUP)),--latest)

# Restore targets — all run psql/pg_restore inside Docker for version compatibility.
# The script handles extension creation before restore.
# drop-schema-public / create-schema-public are defined once above.
.SILENT:
.SILENT:
.PHONY: load-prod-dump
load-prod-dump:
	@DUMP_FILE=$$(find tmpbackup-prod -type f -name "*.custom" -print -quit); \
	psql -d '$(DB_URL)' -f scripts/sql/create_extensions.sql && \
	psql -d '$(DB_URL)' -f $(WAGTAIL_FRENCH_SQL) && \
	pg_restore -d '$(DB_URL)' --schema=public --clean --if-exists --no-acl --no-owner --no-privileges --jobs=4 "$$DUMP_FILE"

.SILENT:
.PHONY: load-dump-to-loc
load-dump-to-loc:
	./scripts/db_restore.sh $(ENV) $(TMPDIR) $(PG_RESTORE_JOBS)

.PHONY: db-restore-local-from
db-restore-local-from:
	@ENV=$(env) $(MAKE) dump-$(env)
	@$(MAKE) drop-schema-public
	@$(MAKE) create-schema-public
	@ENV=$(env) TMPDIR=tmpbackup-$(env) PG_RESTORE_JOBS=$(PG_RESTORE_JOBS) $(MAKE) load-dump-to-loc
	@$(MAKE) webapp-migrate
ifeq ($(env),prod)
	@$(MAKE) webapp-create-remote-db-server
endif

.PHONY: db-restore-local-from-prod
db-restore-local-from-prod:
	$(MAKE) db-restore-local-from env=prod PG_RESTORE_JOBS=$(PG_RESTORE_JOBS)

.PHONY: db-restore-local-from-preprod
db-restore-local-from-preprod:
	$(MAKE) db-restore-local-from env=preprod
	@echo "⚠️  Preprod restore done — no remote DB server created."

.PHONY: db-restore-preprod-from-prod
db-restore-preprod-from-prod:
	$(MAKE) dump-prod-quiet USE_LATEST_BACKUP=$(USE_LATEST_BACKUP)
	$(MAKE) drop-all-tables
	$(MAKE) load-prod-dump

# The sample database is built from the local `webapp` database by the
# `compute_sample_acteur` DAG.
.PHONY: db-restore-local-from-sample
db-restore-local-from-sample:
	./scripts/e2e_run_sample_dag.sh

# Docs
.PHONY: build-docs
build-docs:
	make -C docs build-docs

.PHONY: fmt-infra
fmt-infra:
	tofu fmt -recursive infrastructure
	terragrunt hcl fmt infrastructure

.PHONY: dbt-generate-docs
dbt-generate-docs:
	make -C data-platform/dbt generate-docs

.PHONY: dbt-serve-docs
dbt-serve-docs:
	make -C data-platform/dbt serve-docs

.PHONY: dbt-clean
dbt-clean-docs:
	make -C data-platform/dbt clean-docs
