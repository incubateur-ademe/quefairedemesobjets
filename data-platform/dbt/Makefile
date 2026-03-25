.PHONY: generate-docs
generate-docs:
	uv run dbt docs generate

.PHONY: serve-docs
serve-docs:
	uv run dbt docs serve --port 8085

.PHONY: clean-docs
clean-docs:
	rm -rf target