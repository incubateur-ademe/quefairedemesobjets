FROM apache/airflow:2.10.4 AS base

# Use user airflow
RUN chown -R ${AIRFLOW_UID:-50000}:0 /opt/airflow
USER airflow
WORKDIR /opt/airflow

FROM base AS build

# Install pipenv and compilation dependencies
USER root
RUN apt-get update && apt-get install -y --no-install-recommends gcc python3-dev libpq-dev
USER airflow
RUN pip install pipenv
COPY ./Pipfile .
COPY ./Pipfile.lock .
RUN PIPENV_VENV_IN_PROJECT=1 pipenv install --deploy --categories=airflow
RUN ls -la

FROM base AS runtime

COPY --from=build /opt/airflow/.venv/ .
RUN .venv/bin/activate
EXPOSE 8080

# Start the web server on port 8080
CMD ["webserver", "--port", "8080"]
