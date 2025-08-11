# Builder python
# --- --- --- ---
FROM apache/airflow:2.11.0 AS python-builder

# system dependencies
USER root
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    libpq-dev python3-dev g++

# python dependencies
ARG POETRY_VERSION=2.0
ENV POETRY_NO_INTERACTION=1
USER ${AIRFLOW_UID:-50000}
RUN pip install "poetry==${POETRY_VERSION}"
WORKDIR /opt/airflow/
COPY pyproject.toml poetry.lock ./
RUN poetry sync --with airflow

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
