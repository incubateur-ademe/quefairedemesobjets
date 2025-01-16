FROM apache/airflow:2.10.4 AS builder
USER root

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    gdal-bin libgdal-dev




FROM apache/airflow:2.10.4 AS python-builder
ARG POETRY_VERSION=2.0
ENV POETRY_NO_INTERACTION=1 \
    POETRY_CACHE_DIR=/opt/.cache

USER ${AIRFLOW_UID:-50000}
RUN pip install "poetry==${POETRY_VERSION}"


USER root
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    libpq-dev gcc python3-dev

WORKDIR /opt/airflow/
COPY pyproject.toml poetry.lock ./
RUN --mount=type=cache,target=${POETRY_CACHE_DIR} poetry sync --with airflow --no-root



FROM apache/airflow:2.10.4 AS scheduler
USER root
WORKDIR /opt/
RUN apt-get update
RUN apt-get install unzip
RUN curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
RUN unzip awscliv2.zip
RUN ./aws/install

USER ${AIRFLOW_UID:-50000}:0
WORKDIR /opt/airflow
ENV CPLUS_INCLUDE_PATH=/usr/include/gdal \
    C_INCLUDE_PATH=/usr/include/gdal \
    VIRTUAL_ENV=/home/airflow/.local \
    PATH="/opt/airflow/.venv/bin:$PATH"

COPY --from=python-builder ${VIRTUAL_ENV} ${VIRTUAL_ENV}
COPY --from=builder ${CPLUS_INCLUDE_PATH} ${CPLUS_INCLUDE_PATH}


# Set current directory to airflow root
# Copy the dags, logs, config, and plugins directories to the appropriate locations
COPY sync_dags.sh /opt/airflow/sync_dags.sh

# Nécessaire pour faire fonctionner Django dans Airflow
COPY core qfdmo qfdmd dsfr_hacks ./

# Copy airflow directories
COPY dags config plugins ./
RUN mkdir -p /opt/airflow/logs/

CMD ["scheduler"]
