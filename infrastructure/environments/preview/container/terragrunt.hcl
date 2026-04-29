terraform {
  source = "../../../modules/container"
}

include {
  path = find_in_parent_folders("root.hcl")
}

dependency "database" {
  config_path = "../database"

  mock_outputs = {
    webapp_instance_id = "fr-par/aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee"
  }
  mock_outputs_allowed_terraform_commands = ["validate", "plan"]
}

dependency "object_storage" {
  config_path = "../object_storage"

  mock_outputs = {
    airflow_bucket_name = "lvao-preview-airflow"
    webapp_bucket_name  = "lvao-preview-webapp"
  }
  mock_outputs_allowed_terraform_commands = ["validate", "plan"]
}

# Secrets Airflow (DB Airflow, comptes admin, conn strings warehouse) :
# valeurs renseignées via TF_VAR_* dans le shell juste avant l'apply
# (depuis le password manager). Voir docs/reference/infrastructure/provisioning.md.
#
# Secrets webapp consommés par les DAGs (AWS_*, SENTRY_DSN, NOTION_TOKEN,
# POSTHOG_PERSONAL_API_KEY) : lus à l'apply depuis Scaleway Secret Manager
# via use_secret_manager = true. Mêmes noms bruts que pour le webapp.

inputs = {
  # Scheduler — preview est dimensionné petit
  airflow_scheduler_registry_image = "rg.fr-par.scw.cloud/ns-qfdmo/airflow-scheduler:preview"
  airflow_scheduler_cpu_limit      = 2000
  airflow_scheduler_memory_limit   = 4096
  airflow_scheduler_min_scale      = 0
  airflow_scheduler_max_scale      = 1
  airflow_scheduler_timeout        = 300

  # Webserver
  airflow_webserver_registry_image = "rg.fr-par.scw.cloud/ns-qfdmo/airflow-webserver:preview"
  airflow_webserver_cpu_limit      = 1000
  airflow_webserver_memory_limit   = 2048
  airflow_webserver_min_scale      = 0
  airflow_webserver_max_scale      = 1
  airflow_webserver_timeout        = 300

  AIRFLOW__WEBSERVER__INSTANCE_NAME   = "🟦🟦🟦 ENV de PREVIEW 🟦🟦🟦"
  AIRFLOW__DATABASE__SQL_ALCHEMY_CONN = get_env("TF_VAR_AIRFLOW__DATABASE__SQL_ALCHEMY_CONN", "")
  AIRFLOW_CONN_WEBAPP_DB              = get_env("TF_VAR_AIRFLOW_CONN_WEBAPP_DB", "")
  DATABASE_URL                        = get_env("TF_VAR_DATABASE_URL", "")
  DB_WAREHOUSE                        = get_env("TF_VAR_DB_WAREHOUSE", "")
  DB_WEBAPP_SAMPLE                    = get_env("TF_VAR_DB_WEBAPP_SAMPLE", "")
  ENVIRONMENT                         = "preview"
  POSTGRES_DB                         = get_env("TF_VAR_POSTGRES_DB", "")
  POSTGRES_HOST                       = get_env("TF_VAR_POSTGRES_HOST", "")
  POSTGRES_PASSWORD                   = get_env("TF_VAR_POSTGRES_PASSWORD", "")
  POSTGRES_PORT                       = get_env("TF_VAR_POSTGRES_PORT", "")
  POSTGRES_SCHEMA                     = get_env("TF_VAR_POSTGRES_SCHEMA", "")
  POSTGRES_USER                       = get_env("TF_VAR_POSTGRES_USER", "")
  SCW_ACCESS_KEY                      = get_env("TF_VAR_SCW_ACCESS_KEY", "")
  SCW_DEFAULT_ORGANIZATION_ID         = get_env("TF_VAR_SCW_DEFAULT_ORGANIZATION_ID", "")
  SCW_DEFAULT_PROJECT_ID              = get_env("TF_VAR_SCW_DEFAULT_PROJECT_ID", "")
  SCW_SECRET_KEY                      = get_env("TF_VAR_SCW_SECRET_KEY", "")
  SECRET_KEY                          = get_env("TF_VAR_SECRET_KEY", "")
  _AIRFLOW_WWW_USER_USERNAME          = get_env("TF_VAR_AIRFLOW_WWW_USER_USERNAME", "")
  _AIRFLOW_WWW_USER_PASSWORD          = get_env("TF_VAR_AIRFLOW_WWW_USER_PASSWORD", "")

  # --- Variables webapp consommées par les DAGs ---

  # BASE_URL laissé vide volontairement (à renseigner ultérieurement, voir webapp).
  BASE_URL = ""

  # Wildcard Django — couvre les sous-domaines des containers Scaleway.
  ALLOWED_HOSTS = ".functions.fnc.fr-par.scw.cloud,.containers.fnc.fr-par.scw.cloud"

  # Config S3 — bucket dédié aux écritures de DAGs (séparé du bucket de logs Airflow).
  AWS_S3_REGION_NAME      = "fr-par"
  AWS_S3_ENDPOINT_URL     = "https://s3.fr-par.scw.cloud"
  AWS_STORAGE_BUCKET_NAME = dependency.object_storage.outputs.airflow_bucket_name

  # Active la lecture des secrets webapp (AWS keys, Sentry, Notion, PostHog)
  # depuis Scaleway Secret Manager via leurs noms bruts.
  use_secret_manager = true
}
