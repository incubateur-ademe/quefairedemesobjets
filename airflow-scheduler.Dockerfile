FROM apache/airflow:2.10.4 AS builder
USER root

RUN apt-get update \
    apt-get install -y --no-install-recommends \
    gdal-bin libgdal-dev

FROM apache/airflow:2.10.4 AS python-builder
ARG POETRY_VERSION=1.8
ENV POETRY_NO_INTERACTION=1 \
    POETRY_CACHE_DIR=/opt/.cache

USER ${AIRFLOW_UID:-50000}
WORKDIR /opt/airflow/
COPY pyproject.toml poetry.lock ./
RUN pip install "poetry==${POETRY_VERSION}"
RUN --mount=type=cache,target=$POETRY_CACHE_DIR poetry install --with airflow --no-root




FROM apache/airflow:2.10.4 AS scheduler
USER ${AIRFLOW_UID:-50000}
ENV CPLUS_INCLUDE_PATH=/usr/include/gdal \
    C_INCLUDE_PATH=/usr/include/gdal \
    VIRTUAL_ENV=/opt/airflow/.venv \
    PATH="/opt/airflow/.venv/bin:$PATH"

COPY --from=python-builder ${VIRTUAL_ENV} ${VIRTUAL_ENV}
COPY --from=builder ${CPLUS_INCLUDE_PATH} ${CPLUS_INCLUDE_PATH}

# Use user airflow
WORKDIR /opt/airflow
USER ${AIRFLOW_UID:-50000}:0
RUN chown -R ${AIRFLOW_UID:-50000}:0 .

# Set current directory to airflow root
# Copy the dags, logs, config, and plugins directories to the appropriate locations
COPY sync_dags.sh /opt/airflow/sync_dags.sh
RUN curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip" \
    unzip awscliv2.zip  \
    ./aws/install
# Nécessaire pour faire fonctionner Django dans Airflow
COPY core qfdmo qfdmd dsfr_hacks ./

# Copy airflow directories
COPY dags config plugins ./
RUN mkdir -p /opt/airflow/logs/

CMD ["scheduler"]
