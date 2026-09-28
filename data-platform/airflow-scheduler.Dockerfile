# Builder python
# --- --- --- ---
FROM apache/airflow:slim-3.3.1-python3.12 AS python-builder

# system dependencies
USER root

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    libpq-dev python3-dev g++ git

# python dependencies
USER ${AIRFLOW_UID:-50000}:0

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/
WORKDIR /opt/airflow/

# Copy data-platform uv project structure
COPY data-platform/pyproject.toml data-platform/pyproject.toml
COPY pyproject.toml pyproject.toml
COPY uv.lock uv.lock

# Copy webapp source (needed for package install)
COPY webapp/pyproject.toml webapp/pyproject.toml
COPY webapp/core/ webapp/core/
COPY webapp/data/ webapp/data/
COPY webapp/dsfr_hacks/ webapp/dsfr_hacks/
COPY webapp/infotri/ webapp/infotri/
COPY webapp/qfdmd/ webapp/qfdmd/
COPY webapp/qfdmo/ webapp/qfdmo/
COPY webapp/search/ webapp/search/
COPY webapp/settings/ webapp/settings/
COPY webapp/stats/ webapp/stats/

# Venv at /opt/airflow/.venv so shebangs match runtime (not data-platform/.venv)
ENV UV_PROJECT_ENVIRONMENT=/opt/airflow/.venv
RUN uv sync --project data-platform --frozen --no-editable

# Runtime
# --- --- --- ---
FROM apache/airflow:slim-3.3.1-python3.12 AS scheduler

USER root

# unzip for Airflow DAG
RUN apt-get update
RUN apt-get install -y unzip curl

RUN apt-get install -y --no-install-recommends \
    gdal-bin libgdal-dev jq

# Installation du client Scaleway CLI
RUN curl -s https://raw.githubusercontent.com/scaleway/scaleway-cli/master/scripts/get.sh | sh

# Client Docker CLI (sans daemon) pour le mode local d'inférence ML:
# il permet d'exécuter `docker run` de l'image d'inférence en s'appuyant sur le
# socket Docker du host (monté en lecture seule via docker-compose). Nécessaire
# uniquement pour le mode `run_locally` du DAG ml_deduplication.
RUN DOCKER_ARCH="$(uname -m | sed 's/x86_64/x86_64/; s/aarch64/aarch64/; s/armv7l/armhf/')" \
    && curl -fsSL "https://download.docker.com/linux/static/stable/${DOCKER_ARCH}/docker-27.3.1.tgz" -o /tmp/docker.tgz \
    && tar -xzf /tmp/docker.tgz -C /tmp \
    && mv /tmp/docker/docker /usr/local/bin/docker \
    && rm -rf /tmp/docker /tmp/docker.tgz \
    && docker --version

USER ${AIRFLOW_UID:-50000}:0
WORKDIR /opt/airflow
ENV VIRTUAL_ENV=/opt/airflow/.venv \
    LD_LIBRARY_PATH=/usr/lib \
    PYTHONPATH="/opt/airflow/dags" \
    PATH="/opt/airflow/.venv/bin:$PATH"

COPY --from=python-builder ${VIRTUAL_ENV} ${VIRTUAL_ENV}

COPY ./data-platform/dbt/ /opt/airflow/dbt/
COPY ./data-platform/scripts/ /opt/airflow/scripts/

# Classique Airflow
COPY ./data-platform/dags/ /opt/airflow/dags/
COPY ./data-platform/config/ /opt/airflow/config/
COPY ./data-platform/plugins/ /opt/airflow/plugins/

# Copy data-platform docs
COPY ./docs/reference/data-platform/ /opt/airflow/docs/reference/data-platform/

RUN mkdir -p /opt/airflow/tmp
RUN chown -R ${AIRFLOW_UID:-50000}:0 /opt/airflow/tmp

WORKDIR /opt/airflow/dbt
USER 0
RUN chown -R ${AIRFLOW_UID:-50000}:0 /opt/airflow/dbt
USER ${AIRFLOW_UID:-50000}:0

ENV DBT_PROFILES_DIR=/opt/airflow/dbt
ENV DBT_PROJECT_DIR=/opt/airflow/dbt

RUN dbt deps

CMD ["scheduler"]
