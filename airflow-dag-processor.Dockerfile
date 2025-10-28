# Builder python
# --- --- --- ---
FROM apache/airflow:3.1.0 AS python-builder

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

COPY ./airflow-fork/ /opt/airflow/airflow-fork/

ENV UV_PROJECT_ENVIRONMENT=/home/airflow/.local
RUN uv sync --group airflow


# Runtime
# --- --- --- ---
FROM apache/airflow:3.1.0 AS dagprocessor

USER root

# unzip for Airflow DAG
RUN echo "deb http://deb.debian.org/debian stable main" > /etc/apt/sources.list
RUN apt-get update
RUN apt-get install -y unzip curl nginx vim

RUN apt-get install -y --no-install-recommends \
    gdal-bin libgdal-dev jq

# Scaleway CLI installation
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
ENV VIRTUAL_ENV=/home/airflow/.local \
    PATH="/home/airflow/.local/bin:$PATH" \
    LD_LIBRARY_PATH=/usr/lib

COPY --from=python-builder /home/airflow/.local /home/airflow/.local

# Necessary to make Django work in Airflow
COPY ./core/ /opt/airflow/core/
COPY ./qfdmo/ /opt/airflow/qfdmo/
COPY ./qfdmd/ /opt/airflow/qfdmd/
COPY ./data/ /opt/airflow/data/
COPY ./dbt/ /opt/airflow/dbt/
COPY ./scripts/ /opt/airflow/scripts/
COPY ./dsfr_hacks/ /opt/airflow/dsfr_hacks/

# Airflow classics
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
