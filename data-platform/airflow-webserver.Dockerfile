# Builder python
# --- --- --- ---
FROM apache/airflow:2.11.0 AS python-builder

# system dependencies
USER root
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    libpq-dev python3-dev g++ git

# python dependencies
USER ${AIRFLOW_UID:-50000}
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
FROM apache/airflow:slim-2.11.0-python3.12 AS webserver
USER ${AIRFLOW_UID:-50000}
ENV VIRTUAL_ENV=/home/airflow/.local \
    PATH="/opt/airflow/.venv/bin:$PATH" \
    PORT="8080"

COPY --from=python-builder ${VIRTUAL_ENV} ${VIRTUAL_ENV}

WORKDIR /opt/airflow
COPY ./data-platform/dags /opt/airflow/dags

EXPOSE 8080

CMD ["webserver", "--port", "8080"]
