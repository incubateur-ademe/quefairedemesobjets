terraform {
  source = "../../../modules/airflow_containers"
}

dependency "database" {
  config_path = "../database"

  mock_outputs_allowed_terraform_commands = ["init", "validate", "plan"]
  mock_outputs = {
    webapp_instance_id      = "mock-webapp-id"
    webapp_database_name    = "webapp"
    webapp_endpoint_ip      = "127.0.0.1"
    webapp_endpoint_port    = 5432
    webapp_db_username      = "mock_webapp"
    webapp_db_password      = "mock_password" # pragma: allowlist secret
    warehouse_instance_id   = "mock-warehouse-id"
    warehouse_database_name = "warehouse"
    warehouse_endpoint_ip   = "127.0.0.1"
    warehouse_endpoint_port = 5432
    warehouse_db_username   = "mock_warehouse"
    warehouse_db_password   = "mock_password" # pragma: allowlist secret
    airflow_instance_id     = "mock-airflow-id"
    airflow_database_name   = "airflow"
    airflow_endpoint_ip     = "127.0.0.1"
    airflow_endpoint_port   = 5432
    airflow_db_username     = "mock_airflow"
    airflow_db_password     = "mock_password" # pragma: allowlist secret
  }
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
  airflow_scheduler_memory_limit   = 12288
  airflow_scheduler_min_scale      = 1
  airflow_scheduler_max_scale      = 1
  airflow_scheduler_timeout        = 300

  # Webserver
  airflow_webserver_registry_image = "rg.fr-par.scw.cloud/ns-qfdmo/airflow-webserver:airflow-v3.0"
  airflow_webserver_cpu_limit      = 1000
  airflow_webserver_memory_limit   = 2048
  airflow_webserver_min_scale      = 1
  airflow_webserver_max_scale      = 1
  airflow_webserver_timeout        = 300

  # DAG processor
  airflow_dag_processor_registry_image = "rg.fr-par.scw.cloud/ns-qfdmo/airflow-dag-processor:airflow-v3.0"
  airflow_dag_processor_cpu_limit      = 1000
  airflow_dag_processor_memory_limit   = 2048
  airflow_dag_processor_min_scale      = 1
  airflow_dag_processor_max_scale      = 1
  airflow_dag_processor_timeout        = 300

  AIRFLOW__WEBSERVER__INSTANCE_NAME   = "✅✅✅✅ ENV de AIRFLOW v3.0 ! ✅✅✅✅"
  AIRFLOW__DATABASE__SQL_ALCHEMY_CONN = "postgresql://${dependency.database.outputs.airflow_db_username}:${dependency.database.outputs.airflow_db_password}@${dependency.database.outputs.airflow_endpoint_ip}:${dependency.database.outputs.airflow_endpoint_port}/${dependency.database.outputs.airflow_database_name}"
  AIRFLOW_CONN_WEBAPP_DB              = "postgres://${dependency.database.outputs.webapp_db_username}:${dependency.database.outputs.webapp_db_password}@${dependency.database.outputs.webapp_endpoint_ip}:${dependency.database.outputs.webapp_endpoint_port}/${dependency.database.outputs.webapp_database_name}?sslmode=require"
  DATABASE_URL                        = "postgres://${dependency.database.outputs.webapp_db_username}:${dependency.database.outputs.webapp_db_password}@${dependency.database.outputs.webapp_endpoint_ip}:${dependency.database.outputs.webapp_endpoint_port}/${dependency.database.outputs.webapp_database_name}?sslmode=require"
  DB_WAREHOUSE                        = "postgres://${dependency.database.outputs.warehouse_db_username}:${dependency.database.outputs.warehouse_db_password}@${dependency.database.outputs.warehouse_endpoint_ip}:${dependency.database.outputs.warehouse_endpoint_port}/${dependency.database.outputs.warehouse_database_name}?sslmode=require"
  DB_WEBAPP_SAMPLE                    = "[DB_WEBAPP_SAMPLE]"
  ENVIRONMENT                         = "[ENVIRONMENT]"
  POSTGRES_DB                         = "[POSTGRES_DB]"
  POSTGRES_HOST                       = dependency.database.outputs.warehouse_endpoint_ip
  POSTGRES_PASSWORD                   = dependency.database.outputs.warehouse_db_password
  POSTGRES_PORT                       = tostring(dependency.database.outputs.warehouse_endpoint_port)
  POSTGRES_SCHEMA                     = "[POSTGRES_SCHEMA]"
  POSTGRES_USER                       = "[POSTGRES_USER]"
  SCW_ACCESS_KEY                      = "[SCW_ACCESS_KEY]"
  SCW_DEFAULT_ORGANIZATION_ID         = "[SCW_DEFAULT_ORGANIZATION_ID]"
  SCW_DEFAULT_PROJECT_ID              = "[SCW_DEFAULT_PROJECT_ID]"
  SCW_SECRET_KEY                      = "[SCW_SECRET_KEY]"
  SECRET_KEY                          = "[SECRET_KEY]"
  _AIRFLOW_WWW_USER_USERNAME          = "[_AIRFLOW_WWW_USER_USERNAME]"
  _AIRFLOW_WWW_USER_PASSWORD          = "[_AIRFLOW_WWW_USER_PASSWORD]"

  AIRFLOW__API_AUTH__JWT_SECRET                         = "[AIRFLOW__API_AUTH__JWT_SECRET]"
  AIRFLOW_CONN_SCALEWAYLOGS                             = "[AIRFLOW_CONN_SCALEWAYLOGS]"
  AIRFLOW__CORE__ALLOWED_DESERIALIZATION_CLASSES_REGEXP = "[AIRFLOW__CORE__ALLOWED_DESERIALIZATION_CLASSES_REGEXP]"
}
