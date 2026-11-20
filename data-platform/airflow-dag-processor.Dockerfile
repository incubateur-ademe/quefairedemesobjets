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
FROM apache/airflow:slim-${AIRFLOW_VERSION}-python3.12 AS dag-processor

USER root

# unzip for Airflow DAG
# upgrade: the base image ships outdated Debian packages and docker CLI (Trivy)
RUN apt-get update \
    && apt-get upgrade -y \
    && apt-get install -y --no-install-recommends \
    curl gdal-bin jq nginx unzip \
    && rm -rf /var/lib/apt/lists/*

# The base image installs its own Airflow in a venv at /home/airflow/.local.
# We never run it: our venv (/opt/airflow/.venv) comes first on PATH and holds
# Airflow and every dependency we use. Its outdated packages (PyJWT, certifi,
# urllib3, uv…) only fail the Trivy scan, so we drop it. The base /entrypoint
# only references it when the container runs as root, to extend PYTHONPATH.
RUN rm -rf /home/airflow/.local

# Installation du client Scaleway CLI
# RUN curl -s https://raw.githubusercontent.com/scaleway/scaleway-cli/master/scripts/get.sh | sh

# Nginx
RUN echo 'worker_processes 1; \
    events { worker_connections 1024; } \
    http { \
    server { \
    listen 80 default_server; \
    location / { return 200 "Hello"; } \
    } \
    }' > /etc/nginx/nginx.conf


USER ${AIRFLOW_UID:-50000}:0
WORKDIR /opt/airflow
ENV VIRTUAL_ENV=/opt/airflow/.venv \
    LD_LIBRARY_PATH=/usr/lib \
    PYTHONPATH="/opt/airflow/dags:/opt/airflow/webapp" \
    PATH="/opt/airflow/.venv/bin:$PATH"

COPY --from=python-builder ${VIRTUAL_ENV} ${VIRTUAL_ENV}

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
COPY ./scripts/ /opt/airflow/scripts/

# Classique Airflow
COPY ./data-platform/dags/ /opt/airflow/dags/
COPY ./data-platform/config/ /opt/airflow/config/
COPY ./data-platform/plugins/ /opt/airflow/plugins/

COPY ./data-platform/airflow-dag-processor-start.sh /opt/airflow/airflow-dag-processor-start.sh

# Copy data-platform docs
COPY ./docs/reference/data-platform/ /opt/airflow/docs/reference/data-platform/

RUN mkdir -p /opt/airflow/tmp
RUN chown -R ${AIRFLOW_UID:-50000}:0 /opt/airflow/tmp

WORKDIR /opt/airflow
USER 0
RUN touch /run/nginx.pid
RUN chown -R ${AIRFLOW_UID:-50000}:0 /var/lib/nginx /var/log/nginx /run/nginx.pid
RUN chmod +x /opt/airflow/airflow-dag-processor-start.sh
USER ${AIRFLOW_UID:-50000}:0

EXPOSE 80

ENTRYPOINT ["/opt/airflow/airflow-dag-processor-start.sh"]
CMD [""]
