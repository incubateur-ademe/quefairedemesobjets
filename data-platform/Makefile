BLACK := uv run black
PYTEST := uv run pytest
RUFF := uv run ruff
SQLFLUFF := uv run sqlfluff

.PHONY: check-format
check-format:
	$(RUFF) check dags
	$(BLACK) --check --diff dags
	$(SQLFLUFF) lint dbt/models dbt/macros

.PHONY: dags-test
dags-test:
	$(PYTEST) ./dags/tests

.PHONY: format
format:
	$(RUFF) check dags --fix
	$(BLACK) dags
	$(SQLFLUFF) fix dbt/models dbt/macros