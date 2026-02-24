# Builder python
# --- --- --- ---
FROM apache/airflow:2.11.0 AS python-builder

# system dependencies
USER root

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    libpq-dev python3-dev g++ git

# python dependencies
USER ${AIRFLOW_UID:-50000}:0
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/
WORKDIR /opt/airflow/

# Copy workspace structure for uv resolution
COPY pyproject.toml uv.lock ./
COPY webapp/pyproject.toml webapp/pyproject.toml
COPY data-platform/pyproject.toml data-platform/pyproject.toml

# Copy webapp source (needed for package install)
COPY webapp/core/ webapp/core/
COPY webapp/data/ webapp/data/
COPY webapp/dsfr_hacks/ webapp/dsfr_hacks/
COPY webapp/infotri/ webapp/infotri/
COPY webapp/qfdmd/ webapp/qfdmd/
COPY webapp/qfdmo/ webapp/qfdmo/
COPY webapp/search/ webapp/search/
COPY webapp/stats/ webapp/stats/

RUN uv sync --frozen --all-packages --no-editable


# Runtime
# --- --- --- ---
FROM apache/airflow:slim-2.11.0-python3.12 AS scheduler

USER root

# unzip for Airflow DAG
RUN echo "deb http://deb.debian.org/debian stable main" > /etc/apt/sources.list
RUN apt-get update
RUN apt-get install -y unzip curl

RUN apt-get install -y --no-install-recommends \
    gdal-bin libgdal-dev jq

# Installation du client Scaleway CLI
RUN curl -s https://raw.githubusercontent.com/scaleway/scaleway-cli/master/scripts/get.sh | sh

USER ${AIRFLOW_UID:-50000}:0
WORKDIR /opt/airflow
ENV VIRTUAL_ENV=/opt/airflow/.venv \
    LD_LIBRARY_PATH=/usr/lib \
    PATH="/opt/airflow/.venv/bin:$PATH"

COPY --from=python-builder ${VIRTUAL_ENV} ${VIRTUAL_ENV}

COPY ./data-platform/dbt/ /opt/airflow/dbt/
COPY ./scripts/ /opt/airflow/scripts/

# Classique Airflow
COPY ./data-platform/dags/ /opt/airflow/dags/
COPY ./data-platform/config/ /opt/airflow/config/
COPY ./data-platform/plugins/ /opt/airflow/plugins/

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
