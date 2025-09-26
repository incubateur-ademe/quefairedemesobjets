# Builder python
# --- --- --- ---
FROM apache/airflow:3.1.3 AS python-builder

# system dependencies
USER root

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    libpq-dev python3-dev g++ git

# python dependencies
USER ${AIRFLOW_UID:-50000}:0
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/
WORKDIR /opt/airflow/
COPY pyproject.toml uv.lock ./
RUN uv sync --group airflow


# Runtime
# --- --- --- ---
FROM apache/airflow:slim-3.1.3-python3.13 AS scheduler

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

# Nécessaire pour faire fonctionner Django dans Airflow
COPY ./core/ /opt/airflow/core/
COPY ./data/ /opt/airflow/data/
COPY ./dbt/ /opt/airflow/dbt/
COPY ./dsfr_hacks/ /opt/airflow/dsfr_hacks/
COPY ./qfdmo/ /opt/airflow/qfdmo/
COPY ./scripts/ /opt/airflow/scripts/

# Classique Airflow
COPY ./dags/ /opt/airflow/dags/
COPY ./config/ /opt/airflow/config/
COPY ./plugins/ /opt/airflow/plugins/

WORKDIR /opt/airflow/dbt
USER 0
RUN chown -R ${AIRFLOW_UID:-50000}:0 /opt/airflow/dbt
USER ${AIRFLOW_UID:-50000}:0

ENV DBT_PROFILES_DIR=/opt/airflow/dbt
ENV DBT_PROJECT_DIR=/opt/airflow/dbt

RUN dbt deps

RUN airflow db upgrade

CMD ["scheduler"]
