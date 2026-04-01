PYTEST := uv run pytest

.PHONY: dags-test
dags-test:
	$(PYTEST) ./dags/tests

.PHONY: check-format
check-format:
	uv run black --check --diff dags
	uv run ruff check dags

.PHONY: format
format:
	uv run ruff check dags --fix
	uv run black dags
