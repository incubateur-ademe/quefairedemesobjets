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

# Local django operations
.PHONY: migrate
migrate:
	make -C webapp migrate

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
	make migrate
	make create-remote-db-server

.PHONY: db-restore-local-from-preprod
db-restore-local-from-preprod:
	make dump-preprod
	make drop-schema-public
	make create-schema-public
	make load-preprod-dump
	make migrate
	make create-remote-db-server

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
