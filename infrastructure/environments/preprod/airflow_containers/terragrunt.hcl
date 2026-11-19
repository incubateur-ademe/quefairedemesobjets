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

dependency "database_sample" {
  config_path = "../database_sample"

  mock_outputs_allowed_terraform_commands = ["init", "validate", "plan"]
  mock_outputs = {
    webapp_db_sample_username      = "mock_webapp_sample"
    webapp_db_sample_password      = "mock_password" # pragma: allowlist secret
    webapp_db_sample_database_name = "webapp_sample"
  }
}

dependencies {
  paths = ["../database", "../database_sample", "../object_storage"]
}

include {
  path = find_in_parent_folders("root.hcl")
}

inputs = {
  # Scheduler
  airflow_scheduler_registry_image = "rg.fr-par.scw.cloud/ns-qfdmo/airflow-scheduler:${get_env("IMAGE_TAG", "")}"
  airflow_scheduler_cpu_limit      = 4000
  airflow_scheduler_memory_limit   = 12288
  airflow_scheduler_min_scale      = 1
  airflow_scheduler_max_scale      = 1
  airflow_scheduler_timeout        = 300

  # Webserver
  airflow_webserver_registry_image = "rg.fr-par.scw.cloud/ns-qfdmo/airflow-webserver:${get_env("IMAGE_TAG", "")}"
  airflow_webserver_cpu_limit      = 1000
  airflow_webserver_memory_limit   = 2048
  airflow_webserver_min_scale      = 1
  airflow_webserver_max_scale      = 1
  airflow_webserver_timeout        = 300

  # DAG processor
  airflow_dag_processor_registry_image = "rg.fr-par.scw.cloud/ns-qfdmo/airflow-dag-processor:${get_env("IMAGE_TAG", "")}"
  airflow_dag_processor_cpu_limit      = 1000
  airflow_dag_processor_memory_limit   = 1024
  airflow_dag_processor_min_scale      = 1
  airflow_dag_processor_max_scale      = 1
  airflow_dag_processor_timeout        = 300

  # Public hostname routed by nginx_containers (wildcard CNAME).
  custom_domain = "airflow.preprod.quefairedemesobjets.ademe.fr"

  AIRFLOW__WEBSERVER__INSTANCE_NAME   = "✅✅✅✅ PREPROD ✅✅✅✅"
  AIRFLOW__DATABASE__SQL_ALCHEMY_CONN = "postgresql://${dependency.database.outputs.airflow_db_username}:${dependency.database.outputs.airflow_db_password}@${dependency.database.outputs.airflow_endpoint_ip}:${dependency.database.outputs.airflow_endpoint_port}/${dependency.database.outputs.airflow_database_name}"
  AIRFLOW_METADATA_DB_URL             = "postgresql+psycopg2://${dependency.database.outputs.airflow_db_username}:${dependency.database.outputs.airflow_db_password}@${dependency.database.outputs.airflow_endpoint_ip}:${dependency.database.outputs.airflow_endpoint_port}/${dependency.database.outputs.airflow_database_name}"
  AIRFLOW_CONN_WEBAPP_DB              = "postgres://${dependency.database.outputs.webapp_db_username}:${dependency.database.outputs.webapp_db_password}@${dependency.database.outputs.webapp_endpoint_ip}:${dependency.database.outputs.webapp_endpoint_port}/${dependency.database.outputs.webapp_database_name}?sslmode=require"
  DATABASE_URL                        = "postgres://${dependency.database.outputs.webapp_db_username}:${dependency.database.outputs.webapp_db_password}@${dependency.database.outputs.webapp_endpoint_ip}:${dependency.database.outputs.webapp_endpoint_port}/${dependency.database.outputs.webapp_database_name}?sslmode=require"
  DB_WAREHOUSE                        = "postgres://${dependency.database.outputs.warehouse_db_username}:${dependency.database.outputs.warehouse_db_password}@${dependency.database.outputs.warehouse_endpoint_ip}:${dependency.database.outputs.warehouse_endpoint_port}/${dependency.database.outputs.warehouse_database_name}?sslmode=require"
  DB_WEBAPP_SAMPLE                    = "postgres://${dependency.database_sample.outputs.webapp_db_sample_username}:${dependency.database_sample.outputs.webapp_db_sample_password}@${dependency.database.outputs.webapp_endpoint_ip}:${dependency.database.outputs.webapp_endpoint_port}/${dependency.database_sample.outputs.webapp_db_sample_database_name}?sslmode=require"
  ENVIRONMENT                         = "preprod"
  POSTGRES_DB                         = dependency.database.outputs.warehouse_database_name
  POSTGRES_HOST                       = dependency.database.outputs.warehouse_endpoint_ip
  POSTGRES_PASSWORD                   = dependency.database.outputs.warehouse_db_password
  POSTGRES_PORT                       = tostring(dependency.database.outputs.warehouse_endpoint_port)
  POSTGRES_SCHEMA                     = "public"
  POSTGRES_USER                       = dependency.database.outputs.warehouse_db_username

  AIRFLOW__CORE__ALLOWED_DESERIALIZATION_CLASSES_REGEXP = "airflow\\..* acteurs\\..* clone\\..* cluster\\..* crawl\\..* enrich\\..* ml_deduplication\\..* shared\\..* sources\\..* stats\\..* suggestions\\..* tools\\..* utils\\..*"

  AIRFLOW__DAG_PROCESSOR__MIN_FILE_PROCESS_INTERVAL = 300
  AIRFLOW__DAG_PROCESSOR__PARSING_PROCESSES         = 1

  WEBAPP_URL = "https://quefairedemesdechets.incubateur.ademe.dev"
}
