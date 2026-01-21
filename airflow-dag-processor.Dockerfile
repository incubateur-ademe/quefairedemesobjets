# Builder python
# --- --- --- ---
FROM apache/airflow:slim-3.1.3-python3.12 AS python-builder

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
FROM apache/airflow:slim-3.1.3-python3.12 AS dagprocessor

USER root

# unzip for Airflow DAG
RUN echo "deb http://deb.debian.org/debian stable main" > /etc/apt/sources.list
RUN apt-get update
RUN apt-get install -y unzip curl nginx

RUN apt-get install -y --no-install-recommends \
    gdal-bin libgdal-dev jq

# Installation du client Scaleway CLI
RUN curl -s https://raw.githubusercontent.com/scaleway/scaleway-cli/master/scripts/get.sh | sh

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
    PATH="/opt/airflow/.venv/bin:$PATH"

COPY --from=python-builder ${VIRTUAL_ENV} ${VIRTUAL_ENV}

# Nécessaire pour faire fonctionner Django dans Airflow
COPY ./core/ /opt/airflow/core/
COPY ./qfdmo/ /opt/airflow/qfdmo/
COPY ./qfdmd/ /opt/airflow/qfdmd/
COPY ./data/ /opt/airflow/data/
COPY ./dbt/ /opt/airflow/dbt/
COPY ./scripts/ /opt/airflow/scripts/
COPY ./dsfr_hacks/ /opt/airflow/dsfr_hacks/

# Classique Airflow
COPY ./dags/ /opt/airflow/dags/
COPY ./config/ /opt/airflow/config/
COPY ./plugins/ /opt/airflow/plugins/

COPY airflow-dag-processor-start.sh /opt/airflow/airflow-dag-processor-start.sh

WORKDIR /opt/airflow
USER 0
RUN chown -R ${AIRFLOW_UID:-50000}:0 /opt/airflow/dbt
RUN touch /run/nginx.pid
RUN chown -R ${AIRFLOW_UID:-50000}:0 /var/lib/nginx /var/log/nginx /run/nginx.pid
RUN chmod +x /opt/airflow/airflow-dag-processor-start.sh
USER ${AIRFLOW_UID:-50000}:0

EXPOSE 80

ENTRYPOINT ["/opt/airflow/airflow-dag-processor-start.sh"]
CMD [""]
