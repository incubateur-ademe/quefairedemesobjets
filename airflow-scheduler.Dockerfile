FROM apache/airflow:2.10.4

#---------------------------------
# Installation GDAL
#---------------------------------
USER root
RUN apt-get update

RUN apt-get install -y --no-install-recommends \
    gdal-bin libgdal-dev && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

ENV CPLUS_INCLUDE_PATH=/usr/include/gdal
ENV C_INCLUDE_PATH=/usr/include/gdal

#---------------------------------
# Rebascule sur l'utilisateur airflow
#---------------------------------
# On rebascule sur le dernier utilisateur fourni
# dans l'image de base
# https://hub.docker.com/layers/apache/airflow/2.10.4/images/sha256-94b74c8b65924179b961b8838e9eaff2406d72085c612e0f29b72f886df0677e
USER 50000

# Use user airflow
RUN chown -R ${AIRFLOW_UID:-50000}:0 /opt/airflow
USER ${AIRFLOW_UID:-50000}:0

COPY ./airflow-requirements.txt /opt/airflow/airflow-requirements.txt
COPY ./requirements.txt /opt/airflow/django-requirements.txt
RUN pip install -r /opt/airflow/airflow-requirements.txt
RUN pip install -r /opt/airflow/django-requirements.txt
RUN pip install awscli


# Copy the dags, logs, config, and plugins directories to the appropriate locations
COPY sync_dags.sh /opt/airflow/sync_dags.sh

# Nécessaire pour faire fonctionner Django dans Airflow
COPY ./core/ /opt/airflow/core/
COPY ./qfdmo/ /opt/airflow/qfdmo/
COPY ./qfdmd/ /opt/airflow/qfdmd/
COPY ./dsfr_hacks/ /opt/airflow/dsfr_hacks/

# Classique Airflow
COPY ./dags/ /opt/airflow/dags/
COPY ./config/ /opt/airflow/config/
COPY ./plugins/ /opt/airflow/plugins/
RUN mkdir -p /opt/airflow/logs/

CMD ["scheduler"]
