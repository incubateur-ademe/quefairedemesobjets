FROM apache/airflow:2.10.0

# Use user airflow
RUN chown -R ${AIRFLOW_UID:-50000}:0 /opt/airflow
USER ${AIRFLOW_UID:-50000}:0

COPY ./airflow-requirements.txt /opt/airflow/requirements.txt
RUN pip install -r /opt/airflow/requirements.txt

# Copy the dags, logs, config, and plugins directories to the appropriate locations
COPY ./airflow-dags/ /opt/airflow/dags/

EXPOSE 8080

# Start the web server on port 8080
CMD ["webserver", "--port", "8080"]
