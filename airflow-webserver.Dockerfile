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
COPY pyproject.toml poetry.lock poetry.toml ./
RUN --mount=type=cache,target=${POETRY_CACHE_DIR} poetry sync --with airflow --no-root

FROM apache/airflow:2.10.4 AS webserver
USER ${AIRFLOW_UID:-50000}
ENV VIRTUAL_ENV=/opt/airflow/.venv \
    PATH="/opt/airflow/.venv/bin:$PATH"

COPY --from=python-builder ${VIRTUAL_ENV} ${VIRTUAL_ENV}

WORKDIR /opt/airflow
COPY ./dags/ /opt/airflow/dags/

EXPOSE 8080

# Start the web server on port 8080
CMD ["webserver", "--port", "8080"]
