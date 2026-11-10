# What the `webapp_container` stack (Django webapp + django-tasks worker) is in
# every environment. An environment's terragrunt.hcl includes this file and
# adds what is its own.
#
# The two files are the inventory of the application's environment variables:
# every key the application reads is written here or there, in clear (config),
# derived from the outputs of another stack, or listed in secrets.example.json
# (read from Secret Manager by root.hcl). A missing variable is a visible
# diff, not a silent default.
#
# Scalingo keys left out on purpose:
# - read nowhere in the code: ASSISTANT_BASE_URL, ASSISTANT_HOSTS,
#   CARTE_POSTHOG_KEY, LVAO_POSTHOG_KEY, CORS_ALLOWED_ORIGINS,
#   MAX_SOLUTION_DISPLAYED_ON_MAP, REDIRECT_LEGACY_PRODUIT_TO_WAGTAIL_PAGES,
#   LEGACY_SITE_VITRINE_DOMAIN, DB_READONLY, INSEE_KEY, INSEE_SECRET,
#   SCALEWAY_ACCESS_KEY_ID, SCALEWAY_SECRET_KEY
# - DB_WEBAPP_SAMPLE: the webapp_sample alias is only used by the local
#   create_webapp_sample_db command; Airflow is the consumer of the sample
#   database
# - specific to the Scalingo buildpacks: LD_LIBRARY_PATH, PROJ_LIB,
#   PYTHONPATH, DISABLE_COLLECTSTATIC
locals {
  env = read_terragrunt_config(find_in_parent_folders("env.hcl")).locals
}

terraform {
  source = "${get_terragrunt_dir()}/../../../modules/webapp_container"
}

dependency "database" {
  config_path = "${get_terragrunt_dir()}/../database"

  mock_outputs = {
    webapp_db_username      = "webapp"
    webapp_db_password      = "mock" # pragma: allowlist secret
    webapp_endpoint_ip      = "10.0.0.1"
    webapp_endpoint_port    = 5432
    webapp_database_name    = "webapp"
    warehouse_db_username   = "warehouse"
    warehouse_db_password   = "mock" # pragma: allowlist secret
    warehouse_endpoint_ip   = "10.0.0.2"
    warehouse_endpoint_port = 5432
    warehouse_database_name = "warehouse"
  }
  # Not plan: the CI applies its plan, it must never carry mock outputs.
  mock_outputs_allowed_terraform_commands = ["validate"]
}

inputs = {
  registry_image = "rg.fr-par.scw.cloud/ns-qfdmo/webapp:${get_env("IMAGE_TAG", "")}"

  # An explicit list and not "*": while the container is public, anyone can
  # call its generated domain (.functions.fnc.fr-par.scw.cloud) with the
  # X-Forwarded-Host of their choice. Domains declared in env.hcl. The probes
  # go through HealthzMiddleware, whatever the host.
  ALLOWED_HOSTS = join(",", concat(
    [local.env.webapp_base_domain],
    local.env.webapp_alias_domains,
    [".functions.fnc.fr-par.scw.cloud"],
  ))
  BASE_URL = "https://${local.env.webapp_base_domain}"

  AWS_S3_REGION_NAME  = "fr-par"
  AWS_S3_ENDPOINT_URL = "https://s3.fr-par.scw.cloud"

  extra_environment_variables = {
    # bin/post_deploy runs in CI before the rollout, not at container start.
    RUN_MIGRATIONS_ON_START = "false"
    # templates/admin/base.html and servers.conf.erb test this exact value.
    ENVIRONMENT                = local.env.webapp_environment
    BASE_DOMAIN                = local.env.webapp_base_domain
    DISTANCE_MAX               = "30000"
    DJANGO_IMPORT_EXPORT_LIMIT = "0"
    # Read by botocore, not by Django: since botocore 1.36 the CRC checksums
    # are sent by default and Scaleway Object Storage rejects them.
    AWS_REQUEST_CHECKSUM_CALCULATION = "WHEN_REQUIRED"
    AWS_RESPONSE_CHECKSUM_VALIDATION = "WHEN_REQUIRED"
  }

  DATABASE_URL = format(
    "postgresql://%s:%s@%s:%s/%s?sslmode=require", # pragma: allowlist secret
    dependency.database.outputs.webapp_db_username,
    dependency.database.outputs.webapp_db_password,
    dependency.database.outputs.webapp_endpoint_ip,
    dependency.database.outputs.webapp_endpoint_port,
    dependency.database.outputs.webapp_database_name,
  )

  extra_secret_environment_variables = {
    DB_WAREHOUSE = format(
      "postgresql://%s:%s@%s:%s/%s?sslmode=require", # pragma: allowlist secret
      dependency.database.outputs.warehouse_db_username,
      dependency.database.outputs.warehouse_db_password,
      dependency.database.outputs.warehouse_endpoint_ip,
      dependency.database.outputs.warehouse_endpoint_port,
      dependency.database.outputs.warehouse_database_name,
    )
  }
}
