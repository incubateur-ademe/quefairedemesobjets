# Builder python
# --- --- --- ---
# The version comes from data-platform/pyproject.toml: `make -s airflow-version`
# Python and uv come from .tool-versions, through make (versions.mk)
ARG AIRFLOW_VERSION
ARG PYTHON_VERSION
ARG UV_VERSION
FROM ghcr.io/astral-sh/uv:${UV_VERSION:?build_through_make_which_reads_.tool-versions} AS uv

FROM apache/airflow:slim-${AIRFLOW_VERSION:?pass_--build-arg_AIRFLOW_VERSION}-python${PYTHON_VERSION:?build_through_make_which_reads_.tool-versions} AS python-builder

# system dependencies
USER root

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    libpq-dev python3-dev g++ git

# python dependencies
USER ${AIRFLOW_UID:-50000}:0

COPY --from=uv /uv /uvx /bin/
WORKDIR /opt/airflow/

# Copy workspace structure for uv resolution
COPY data-platform/pyproject.toml data-platform/pyproject.toml
COPY pyproject.toml pyproject.toml
COPY uv.lock uv.lock

COPY webapp/pyproject.toml webapp/pyproject.toml

# Venv at /opt/airflow/.venv so shebangs match runtime (not data-platform/.venv)
ENV UV_PROJECT_ENVIRONMENT=/opt/airflow/.venv
RUN uv sync --project data-platform --frozen --no-editable --no-install-workspace

# Runtime
# --- --- --- ---
FROM apache/airflow:slim-${AIRFLOW_VERSION}-python${PYTHON_VERSION} AS webserver

USER root

# The base image ships outdated Debian packages (Trivy)
RUN apt-get update \
    && apt-get upgrade -y \
    && rm -rf /var/lib/apt/lists/*

# The base image installs its own Airflow in a venv at /home/airflow/.local.
# We never run it: our venv (/opt/airflow/.venv) comes first on PATH and holds
# Airflow and every dependency we use. Its outdated packages (PyJWT, certifi,
# urllib3, uv…) only fail the Trivy scan, so we drop it. The base /entrypoint
# only references it when the container runs as root, to extend PYTHONPATH.
RUN rm -rf /home/airflow/.local

USER ${AIRFLOW_UID:-50000}

ENV VIRTUAL_ENV=/opt/airflow/.venv \
    PATH="/opt/airflow/.venv/bin:$PATH" \
    PYTHONPATH="/opt/airflow/dags:/opt/airflow/webapp" \
    PORT="8080"

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

WORKDIR /opt/airflow
COPY ./data-platform/dags /opt/airflow/dags
COPY ./data-platform/airflow-webserver-start.sh /opt/airflow/airflow-webserver-start.sh

# Copy data-platform docs
COPY ./docs/reference/data-platform/ /opt/airflow/docs/reference/data-platform/

USER root
RUN chmod +x /opt/airflow/airflow-webserver-start.sh
USER ${AIRFLOW_UID:-50000}

EXPOSE 8080

ENTRYPOINT ["/opt/airflow/airflow-webserver-start.sh"]
