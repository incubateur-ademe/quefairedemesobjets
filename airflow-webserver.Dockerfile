# Builder python
# --- --- --- ---
FROM apache/airflow:3.1.0 AS python-builder

# system dependencies
USER root

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    libpq-dev python3-dev g++ git

# python dependencies
USER ${AIRFLOW_UID:-50000}
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/
WORKDIR /opt/airflow/
COPY pyproject.toml uv.lock ./

COPY ./airflow-fork/ /opt/airflow/airflow-fork/

ENV UV_PROJECT_ENVIRONMENT=/home/airflow/.local
RUN uv sync --group airflow


# Runtime
# --- --- --- ---
FROM apache/airflow:3.1.0 AS webserver

USER root

# install vim for debugging purpose
RUN echo "deb http://deb.debian.org/debian stable main" > /etc/apt/sources.list
RUN apt-get update
RUN apt-get install -y vim

USER ${AIRFLOW_UID:-50000}
ENV VIRTUAL_ENV=/home/airflow/.local \
    PATH="/home/airflow/.local/bin:$PATH" \
    PORT="8080"

COPY --from=python-builder /home/airflow/.local /home/airflow/.local

WORKDIR /opt/airflow
COPY ./dags /opt/airflow/dags

EXPOSE 8080

CMD ["api-server"]
