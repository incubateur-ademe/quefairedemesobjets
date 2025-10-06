terraform {
  source = "../../../modules/container"
}

dependencies {
  paths = ["../database", "../object_storage"]
}

include {
  path = find_in_parent_folders("root.hcl")
}

inputs = {
  # Scheduler
  airflow_scheduler_registry_image = "rg.fr-par.scw.cloud/ns-qfdmo/airflow-scheduler:airflow-v3.0"
  airflow_scheduler_cpu_limit      = 4000
  airflow_scheduler_memory_limit   = 8000
  airflow_scheduler_min_scale      = 1
  airflow_scheduler_max_scale      = 1
  airflow_scheduler_timeout        = 300

  # Webserver
  airflow_webserver_registry_image = "rg.fr-par.scw.cloud/ns-qfdmo/airflow-webserver:airflow-v3.0"
  airflow_webserver_cpu_limit      = 2000
  airflow_webserver_memory_limit   = 4000
  airflow_webserver_min_scale      = 1
  airflow_webserver_max_scale      = 1
  airflow_webserver_timeout        = 300

  # DAG processor
  airflow_dag_processor_registry_image = "rg.fr-par.scw.cloud/ns-qfdmo/airflow-dag-processor:airflow-v3.0"
  airflow_dag_processor_cpu_limit      = 2000
  airflow_dag_processor_memory_limit   = 4000
  airflow_dag_processor_min_scale      = 1
  airflow_dag_processor_max_scale      = 1
  airflow_dag_processor_timeout        = 300

  AIRFLOW__WEBSERVER__INSTANCE_NAME   = "✅✅✅✅ ENV de PREVIEW ! ✅✅✅✅"
  AIRFLOW__DATABASE__SQL_ALCHEMY_CONN = "[AIRFLOW__DATABASE__SQL_ALCHEMY_CONN]"
  AIRFLOW_CONN_WEBAPP_DB              = "[AIRFLOW_CONN_WEBAPP_DB]"
  DATABASE_URL                        = "[DATABASE_URL]"
  DB_WAREHOUSE                        = "[DB_WAREHOUSE]"
  ENVIRONMENT                         = "[ENVIRONMENT]"
  POSTGRES_DB                         = "[POSTGRES_DB]"
  POSTGRES_HOST                       = "[POSTGRES_HOST]"
  POSTGRES_PASSWORD                   = "[POSTGRES_PASSWORD]"
  POSTGRES_PORT                       = "[POSTGRES_PORT]"
  POSTGRES_SCHEMA                     = "[POSTGRES_SCHEMA]"
  POSTGRES_USER                       = "[POSTGRES_USER]"
  SCW_ACCESS_KEY                      = "[SCW_ACCESS_KEY]"
  SCW_DEFAULT_ORGANIZATION_ID         = "[SCW_DEFAULT_ORGANIZATION_ID]"
  SCW_DEFAULT_PROJECT_ID              = "[SCW_DEFAULT_PROJECT_ID]"
  SCW_SECRET_KEY                      = "[SCW_SECRET_KEY]"
  SECRET_KEY                          = "[SECRET_KEY]"
  _AIRFLOW_WWW_USER_USERNAME          = "[_AIRFLOW_WWW_USER_USERNAME]"
  _AIRFLOW_WWW_USER_PASSWORD          = "[_AIRFLOW_WWW_USER_PASSWORD]"
}