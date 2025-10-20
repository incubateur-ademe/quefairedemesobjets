FROM prefecthq/prefect:3-python3.12

USER root

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    libpq-dev python3-dev g++ git gdal-bin libgdal-dev curl unzip postgresql-client

# python dependencies
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/
COPY pyproject.toml uv.lock ./
RUN uv sync --group prefect

WORKDIR /opt/prefect/
ENV VIRTUAL_ENV=/opt/prefect/.venv \
    LD_LIBRARY_PATH=/usr/lib \
    PATH="/opt/prefect/.venv/bin:$PATH"
ENV PYTHONPATH=/opt/prefect:/opt/prefect/dags:$PYTHONPATH

# Nécessaire pour faire fonctionner Django dans Prefect
COPY ./core/ /opt/prefect/core/
COPY ./qfdmo/ /opt/prefect/qfdmo/
COPY ./qfdmd/ /opt/prefect/qfdmd/
COPY ./data/ /opt/prefect/data/
COPY ./dbt/ /opt/prefect/dbt/
COPY ./scripts/ /opt/prefect/scripts/
COPY ./dsfr_hacks/ /opt/prefect/dsfr_hacks/

# Copy application code
COPY ./data_platform /opt/prefect/data_platform
COPY ./data_platform/.env /opt/prefect/data_platform/.env

# Create prefect user and adjust permissions
# RUN useradd -m -u 1000 prefect;
# RUN chown -R prefect:prefect /opt/prefect
# USER prefect