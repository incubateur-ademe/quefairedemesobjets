# Aliases
IMAGE ?= ml-deduplication-inference
TAG ?= latest

# Platform override: defaults to the host architecture (linux/arm64 on Apple
# Silicon, linux/amd64 on x86_64).
PLATFORM ?= $(shell uname -m | sed 's/arm64/linux\/arm64/; s/x86_64/linux\/amd64/; s/aarch64/linux\/arm64/')

# Model directory baked into the image at build time (see Dockerfile ARG MODEL_DIR).
MODEL_DIR ?= models/xgboost
# Paths used by the run target (adjust to your layout).
OUTPUT_DIR ?= outputs
# Source of acteurs: either a file (ACTEURS_FILE) or a DB table (ACTEURS_TABLE).
ACTEURS_FILE ?=
ACTEURS_TABLE ?=
# Mounted into the container as /data/acteurs.parquet when ACTEURS_FILE is used.
DATA_DIR ?= data
# Only required when reading acteurs from a database table.
# pragma: allowlist nextline secret
DATABASE_URI ?= postgresql://webapp:webapp@localhost:6543/webapp # pragma
# Base name of the DB table(s) to upload results to (requires DATABASE_URI).
# Clusters go to <OUTPUT_TABLE>_clusters, candidate pairs to <OUTPUT_TABLE>_predictions.
OUTPUT_TABLE ?=
# Column holding the dataset id (e.g. _dataset with A/B values) for entity
# linkage mode. When set, only cross-dataset pairs are considered at blocking.
LINKAGE_COLUMN ?=

.PHONY: help build run push buildx

help:
	@echo "ml_deduplication Docker inference targets:"
	@echo "  make build        Build the inference image with MODEL_DIR baked in (platform: $(PLATFORM))"
	@echo "  make run          Run inference, mounting acteurs file/table + outputs directory"
	@echo "  make buildx        Multi-arch build (linux/arm64 + linux/amd64) and push to a registry"
	@echo ""
	@echo "Variables: IMAGE, TAG, PLATFORM, DATA_DIR, OUTPUT_DIR,"
	@echo "           ACTEURS_FILE, ACTEURS_TABLE, DATABASE_URI, OUTPUT_TABLE,"
	@echo "           MODEL_THRESHOLD, SPLIT_BY_DEPARTEMENT, RUN_ID, GPU,"
	@echo "           LINKAGE_COLUMN"
	@echo ""
	@echo "Examples:"
	@echo "  make run ACTEURS_FILE=data/acteurs.parquet"
	@echo "  make run ACTEURS_TABLE=qfdmo_vueacteur DATABASE_URI=postgresql://..."
	@echo "  make run ACTEURS_FILE=data/acteurs.parquet MODEL_THRESHOLD=0.8 GPU=1"
	@echo "  make run ACTEURS_FILE=data/acteurs.parquet LINKAGE_COLUMN=_dataset"
	@echo "  make run ACTEURS_FILE=data/acteurs.parquet OUTPUT_TABLE=luis.inference_results DATABASE_URI=postgresql://..."

build:
	docker build --platform $(PLATFORM) --build-arg MODEL_DIR="$(MODEL_DIR)" -t $(IMAGE):$(TAG) .

run:
	@if [ -n "$(ACTEURS_TABLE)" ] && [ -n "$(ACTEURS_FILE)" ]; then \
		echo "Set exactly one of ACTEURS_TABLE or ACTEURS_FILE (not both)"; exit 1; fi
	@if [ -z "$(ACTEURS_TABLE)" ]; then \
		test -f "$(ACTEURS_FILE)" || { echo "Acteurs file not found: $(ACTEURS_FILE)"; exit 1; }; \
	fi
	mkdir -p $(OUTPUT_DIR)
	docker run --rm \
		$(if $(ACTEURS_TABLE),,-v "$$PWD/$(DATA_DIR)/$(notdir $(ACTEURS_FILE))":/data/acteurs.parquet:ro) \
		-v "$$PWD/$(OUTPUT_DIR)":/outputs \
		$(if $(DATABASE_URI),-e DATABASE_CONNECTION_URI="$(DATABASE_URI)") \
		$(if $(GPU),--gpus all,) \
		$(IMAGE):$(TAG) \
		python -m ml_deduplication.inference.xgboost.run_inference \
		--model-path /model \
		--output-dir /outputs \
		$(if $(MODEL_THRESHOLD),--model-threshold $(MODEL_THRESHOLD)) \
		$(if $(SPLIT_BY_DEPARTEMENT),--split-by-departement) \
		$(if $(LINKAGE_COLUMN),--linkage-column $(LINKAGE_COLUMN)) \
		$(if $(RUN_ID),--run-id $(RUN_ID)) \
		$(if $(OUTPUT_TABLE),--output-table $(OUTPUT_TABLE)) \
		$(if $(ACTEURS_TABLE),--acteurs-table $(ACTEURS_TABLE),/data/acteurs.parquet)

# Multi-arch build + push. Requires buildx and a registry (e.g. ghcr.io/org/ml-deduplication-inference).
buildx:
	docker buildx build --platform linux/arm64,linux/amd64 \
		-t $(IMAGE):$(TAG) \
		--push .
