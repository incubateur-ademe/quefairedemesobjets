############################################
# Runtime stage: Python 3.13 inference image
############################################
FROM python:3.13-slim-bookworm

# Path (relative to the build context) of the directory containing the trained
# model artifacts (model.json, calibrator.pkl, training_results.json). These are
# baked into the image at /model.
ARG MODEL_DIR=models/xgboost

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UV_LINK_MODE=copy \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# System deps: git for uv, libpq for psycopg2, build tools for wheels
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
      ca-certificates \
      curl \
      git \
      libpq-dev \
      build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install uv (official installer)
RUN curl -LsSf https://astral.sh/uv/install.sh | sh -s -- --no-modify-path

# Copy app code (package source lives in ./ml_deduplication/). Required before
# `uv sync` because the build backend (module-root = "") imports the package.
COPY ml_deduplication ./ml_deduplication

# Install python deps (cached as long as lockfiles unchanged)
COPY pyproject.toml README.md uv.lock ./
RUN /root/.local/bin/uv sync --frozen --no-dev

# Use the venv for subsequent RUN/CMD
ENV VIRTUAL_ENV="/app/.venv" \
    PATH="/app/.venv/bin:${PATH}"

# Bake the trained model artifacts into the image at /model.
COPY ${MODEL_DIR} /model

# Run as a non-root user. /app and /model are only read at runtime, so their
# root ownership + world-read permissions are enough; we avoid `chown -R`ing
# them because that would duplicate the whole venv into a new layer (+5.9GB).
RUN useradd --create-home --uid 1000 dedup
USER dedup

# Inputs are mounted at runtime; the model is baked in at /model.
CMD ["python", "-m", "ml_deduplication.inference.xgboost.run_inference", "--model-path", "/model"]
