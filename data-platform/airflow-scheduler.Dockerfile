# Builder python
# --- --- --- ---
# The version comes from data-platform/pyproject.toml: `make -s airflow-version`
ARG AIRFLOW_VERSION
FROM apache/airflow:slim-${AIRFLOW_VERSION:?pass_--build-arg_AIRFLOW_VERSION}-python3.12 AS python-builder

# system dependencies
USER root

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    libpq-dev python3-dev g++ git

# python dependencies
USER ${AIRFLOW_UID:-50000}:0

COPY --from=ghcr.io/astral-sh/uv:0.13.5 /uv /uvx /bin/
WORKDIR /opt/airflow/

# Copy data-platform uv project structure
COPY data-platform/pyproject.toml data-platform/pyproject.toml
COPY pyproject.toml pyproject.toml
COPY uv.lock uv.lock

COPY webapp/pyproject.toml webapp/pyproject.toml

# Venv at /opt/airflow/.venv so shebangs match runtime (not data-platform/.venv)
ENV UV_PROJECT_ENVIRONMENT=/opt/airflow/.venv
RUN uv sync --project data-platform --frozen --no-editable --no-install-workspace

# Runtime
# --- --- --- ---
ARG AIRFLOW_VERSION
FROM apache/airflow:slim-${AIRFLOW_VERSION}-python3.12 AS scheduler

USER root

# unzip and osm2pgsql for Airflow DAG
RUN apt-get update \
    && apt-get upgrade -y \
    && apt-get install -y --no-install-recommends \
    curl gdal-bin jq unzip osm2pgsql \
    && rm -rf /var/lib/apt/lists/*

# The base image installs its own Airflow in a venv at /home/airflow/.local.
# We never run it: our venv (/opt/airflow/.venv) comes first on PATH and holds
# Airflow and every dependency we use. Its outdated packages (PyJWT, certifi,
# urllib3, uv…) only fail the Trivy scan, so we drop it. The base /entrypoint
# only references it when the container runs as root, to extend PYTHONPATH.
RUN rm -rf /home/airflow/.local

# Scaleway CLI, download a pinned version
# rather than through the official get.sh installer, because it resolves the latest
# release through an unauthenticated GitHub API call and fails under rate
# limiting.
# It is used by a DAG (purge_log_db)
ARG SCW_CLI_VERSION=2.66.0
RUN ARCH="$(dpkg --print-architecture)" && \
    curl -fsSL -o /usr/local/bin/scw \
    "https://github.com/scaleway/scaleway-cli/releases/download/v${SCW_CLI_VERSION}/scaleway-cli_${SCW_CLI_VERSION}_linux_${ARCH}" && \
    chmod +x /usr/local/bin/scw

USER ${AIRFLOW_UID:-50000}:0
WORKDIR /opt/airflow
ENV VIRTUAL_ENV=/opt/airflow/.venv \
    LD_LIBRARY_PATH=/usr/lib \
    PYTHONPATH="/opt/airflow/dags:/opt/airflow/webapp" \
    PATH="/opt/airflow/.venv/bin:$PATH"

COPY --from=python-builder ${VIRTUAL_ENV} ${VIRTUAL_ENV}

# Before the code, so a code change does not download the dbt packages again
ENV DBT_PROFILES_DIR=/opt/airflow/dbt \
    DBT_PROJECT_DIR=/opt/airflow/dbt
COPY --chown=${AIRFLOW_UID:-50000}:0 \
    data-platform/dbt/dbt_project.yml \
    data-platform/dbt/package-lock.yml \
    data-platform/dbt/packages.yml \
    /opt/airflow/dbt/
WORKDIR /opt/airflow/dbt
RUN dbt deps

# Kept out of the venv, so a code change does not push all the dependencies again
COPY --chown=${AIRFLOW_UID:-50000}:0 webapp/core/ /opt/airflow/webapp/core/
COPY --chown=${AIRFLOW_UID:-50000}:0 webapp/data/ /opt/airflow/webapp/data/
COPY --chown=${AIRFLOW_UID:-50000}:0 webapp/dsfr_hacks/ /opt/airflow/webapp/dsfr_hacks/
COPY --chown=${AIRFLOW_UID:-50000}:0 webapp/infotri/ /opt/airflow/webapp/infotri/
COPY --chown=${AIRFLOW_UID:-50000}:0 webapp/qfdmd/ /opt/airflow/webapp/qfdmd/
COPY --chown=${AIRFLOW_UID:-50000}:0 webapp/qfdmo/ /opt/airflow/webapp/qfdmo/
COPY --chown=${AIRFLOW_UID:-50000}:0 webapp/search/ /opt/airflow/webapp/search/
COPY --chown=${AIRFLOW_UID:-50000}:0 webapp/settings/ /opt/airflow/webapp/settings/
COPY --chown=${AIRFLOW_UID:-50000}:0 webapp/stats/ /opt/airflow/webapp/stats/
COPY --chown=${AIRFLOW_UID:-50000}:0 webapp/assistant/ /opt/airflow/webapp/assistant/

COPY --chown=${AIRFLOW_UID:-50000}:0 ./data-platform/dbt/ /opt/airflow/dbt/
COPY ./data-platform/scripts/ /opt/airflow/scripts/

# Classique Airflow
COPY ./data-platform/dags/ /opt/airflow/dags/
COPY ./data-platform/config/ /opt/airflow/config/
COPY ./data-platform/plugins/ /opt/airflow/plugins/

# Copy data-platform docs
COPY ./docs/reference/data-platform/ /opt/airflow/docs/reference/data-platform/

RUN mkdir -p /opt/airflow/tmp
RUN chown -R ${AIRFLOW_UID:-50000}:0 /opt/airflow/tmp

CMD ["scheduler"]
