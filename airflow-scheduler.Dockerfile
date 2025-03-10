# Builder python
# --- --- --- ---
FROM apache/airflow:2.10.4 AS python-builder

# system dependencies
USER root
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    libpq-dev gcc python3-dev

# python dependencies
RUN apt-get install -y --no-install-recommends \
    gdal-bin libgdal-dev && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

ENV CPLUS_INCLUDE_PATH=/usr/include/gdal
ENV C_INCLUDE_PATH=/usr/include/gdal

#---------------------------------
# Dépendance pour Annuaire Entreprise
#---------------------------------
RUN echo "deb http://deb.debian.org/debian stable main" > /etc/apt/sources.list
RUN apt-get update && apt-get install -y unzip

#---------------------------------
# Rebascule sur l'utilisateur airflow
#---------------------------------
# On rebascule sur le dernier utilisateur fourni
# dans l'image de base
# https://hub.docker.com/layers/apache/airflow/2.10.4/images/sha256-94b74c8b65924179b961b8838e9eaff2406d72085c612e0f29b72f886df0677e
USER 50000

# Use user airflow
RUN chown -R ${AIRFLOW_UID:-50000}:0 /opt/airflow
USER ${AIRFLOW_UID:-50000}:0
ARG POETRY_VERSION=2.0
ENV POETRY_NO_INTERACTION=1
RUN pip install "poetry==${POETRY_VERSION}"
WORKDIR /opt/airflow/
COPY pyproject.toml poetry.lock ./
RUN poetry sync --with airflow


# Runtime
# --- --- --- ---
FROM apache/airflow:2.10.4 AS scheduler

USER root
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    gdal-bin libgdal-dev

USER ${AIRFLOW_UID:-50000}:0
WORKDIR /opt/airflow
ENV VIRTUAL_ENV=/home/airflow/.local \
    LD_LIBRARY_PATH=/usr/lib \
    PATH="/opt/airflow/.venv/bin:$PATH"

COPY --from=python-builder ${VIRTUAL_ENV} ${VIRTUAL_ENV}

# Nécessaire pour faire fonctionner Django dans Airflow
COPY ./core/ /opt/airflow/core/
COPY ./qfdmo/ /opt/airflow/qfdmo/
COPY ./qfdmd/ /opt/airflow/qfdmd/
COPY ./data/ /opt/airflow/data/
COPY ./dbt/ /opt/airflow/dbt/
COPY ./dsfr_hacks/ /opt/airflow/dsfr_hacks/

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

CMD ["scheduler"]
