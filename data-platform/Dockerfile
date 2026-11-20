# The three Airflow images, one target each: webserver, scheduler, dag-processor
#   docker build -f data-platform/Dockerfile --target scheduler .
#
# The Airflow version comes from data-platform/pyproject.toml: `make -s airflow-version`
# Python and uv come from .tool-versions, through make (versions.mk)
ARG AIRFLOW_VERSION
ARG PYTHON_VERSION
ARG UV_VERSION
FROM ghcr.io/astral-sh/uv:${UV_VERSION:?build_through_make_which_reads_.tool-versions} AS uv

# Python dependencies
# --- --- --- ---
FROM apache/airflow:slim-${AIRFLOW_VERSION:?pass_--build-arg_AIRFLOW_VERSION}-python${PYTHON_VERSION:?build_through_make_which_reads_.tool-versions} AS python-builder

USER root

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    libpq-dev python3-dev g++ git

USER ${AIRFLOW_UID:-50000}:0

COPY --from=uv /uv /uvx /bin/
WORKDIR /opt/airflow/

# Workspace structure, for uv resolution
COPY data-platform/pyproject.toml data-platform/pyproject.toml
COPY pyproject.toml pyproject.toml
COPY uv.lock uv.lock
COPY webapp/pyproject.toml webapp/pyproject.toml

# Venv at /opt/airflow/.venv so shebangs match runtime (not data-platform/.venv)
ENV UV_PROJECT_ENVIRONMENT=/opt/airflow/.venv
RUN uv sync --project data-platform --frozen --no-editable --no-install-workspace

# Code, laid out as under /opt/airflow
# --- --- --- ---
# Kept out of the venv, so a code change does not push all the dependencies again
FROM scratch AS code
COPY webapp/core/ /webapp/core/
COPY webapp/data/ /webapp/data/
COPY webapp/dsfr_hacks/ /webapp/dsfr_hacks/
COPY webapp/infotri/ /webapp/infotri/
COPY webapp/qfdmd/ /webapp/qfdmd/
COPY webapp/qfdmo/ /webapp/qfdmo/
COPY webapp/search/ /webapp/search/
COPY webapp/settings/ /webapp/settings/
COPY webapp/stats/ /webapp/stats/
COPY webapp/assistant/ /webapp/assistant/
COPY data-platform/dags/ /dags/
COPY docs/reference/data-platform/ /docs/reference/data-platform/

# What the scheduler and the dag-processor need on top
FROM code AS pipeline-code
COPY data-platform/dbt/ /dbt/
COPY data-platform/config/ /config/
COPY data-platform/plugins/ /plugins/

# Common runtime
# --- --- --- ---
FROM apache/airflow:slim-${AIRFLOW_VERSION}-python${PYTHON_VERSION} AS base

USER root

# The base image ships outdated Debian packages and docker CLI (Trivy)
RUN apt-get update \
    && apt-get upgrade -y \
    && rm -rf /var/lib/apt/lists/*

# The base image installs its own Airflow in a venv at /home/airflow/.local.
# We never run it: our venv (/opt/airflow/.venv) comes first on PATH and holds
# Airflow and every dependency we use. Its outdated packages (PyJWT, certifi,
# urllib3, uv…) only fail the Trivy scan, so we drop it. The base /entrypoint
# only references it when the container runs as root, to extend PYTHONPATH.
RUN rm -rf /home/airflow/.local

USER ${AIRFLOW_UID:-50000}:0
WORKDIR /opt/airflow
ENV VIRTUAL_ENV=/opt/airflow/.venv \
    PYTHONPATH="/opt/airflow/dags:/opt/airflow/webapp" \
    PATH="/opt/airflow/.venv/bin:$PATH"

COPY --from=python-builder ${VIRTUAL_ENV} ${VIRTUAL_ENV}

# Webserver
# --- --- --- ---
FROM base AS webserver

ENV PORT="8080"

COPY --from=code --chown=${AIRFLOW_UID:-50000}:0 / /opt/airflow/
COPY --chmod=755 data-platform/airflow-webserver-start.sh /opt/airflow/airflow-webserver-start.sh

EXPOSE 8080

ENTRYPOINT ["/opt/airflow/airflow-webserver-start.sh"]

# Common to the scheduler and the dag-processor
# --- --- --- ---
FROM base AS pipeline

USER root

# unzip for Airflow DAG
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
    curl gdal-bin jq unzip \
    && rm -rf /var/lib/apt/lists/*

USER ${AIRFLOW_UID:-50000}:0
ENV LD_LIBRARY_PATH=/usr/lib
RUN mkdir -p /opt/airflow/tmp

# Scheduler
# --- --- --- ---
FROM pipeline AS scheduler

USER root

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

COPY --from=pipeline-code --chown=${AIRFLOW_UID:-50000}:0 / /opt/airflow/
COPY ./data-platform/scripts/ /opt/airflow/scripts/

CMD ["scheduler"]

# Dag-processor
# --- --- --- ---
FROM pipeline AS dag-processor

USER root

# nginx answers the platform health check on port 80
RUN apt-get update \
    && apt-get install -y --no-install-recommends nginx \
    && rm -rf /var/lib/apt/lists/* \
    && echo 'worker_processes 1; \
    events { worker_connections 1024; } \
    http { \
    server { \
    listen 80 default_server; \
    location / { return 200 "Hello"; } \
    } \
    }' > /etc/nginx/nginx.conf \
    && touch /run/nginx.pid \
    && chown -R ${AIRFLOW_UID:-50000}:0 /var/lib/nginx /var/log/nginx /run/nginx.pid

USER ${AIRFLOW_UID:-50000}:0

COPY --from=pipeline-code --chown=${AIRFLOW_UID:-50000}:0 / /opt/airflow/
COPY ./scripts/ /opt/airflow/scripts/
COPY --chmod=755 data-platform/airflow-dag-processor-start.sh /opt/airflow/airflow-dag-processor-start.sh

EXPOSE 80

ENTRYPOINT ["/opt/airflow/airflow-dag-processor-start.sh"]
CMD [""]
