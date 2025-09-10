# Builder python
# --- --- --- ---
FROM apache/airflow:2.11.0 AS python-builder

# system dependencies
USER root
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    libpq-dev python3-dev g++

# python dependencies
USER ${AIRFLOW_UID:-50000}
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/
WORKDIR /opt/airflow/
COPY pyproject.toml uv.lock ./
RUN uv sync --with airflow

# Runtime
# --- --- --- ---
FROM apache/airflow:2.11.0 AS webserver
USER ${AIRFLOW_UID:-50000}
ENV VIRTUAL_ENV=/home/airflow/.local \
    PATH="/opt/airflow/.venv/bin:$PATH" \
    PORT="8080"

COPY --from=python-builder ${VIRTUAL_ENV} ${VIRTUAL_ENV}

WORKDIR /opt/airflow
COPY ./dags /opt/airflow/dags

EXPOSE 8080

CMD ["webserver", "--port", "8080"]
