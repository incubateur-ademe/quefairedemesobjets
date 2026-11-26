# What the `nginx_containers` stack is in every environment. An environment's
# terragrunt.hcl includes this file and adds what is its own.
locals {
  env              = read_terragrunt_config(find_in_parent_folders("env.hcl"))
  metabase_enabled = local.env.locals.metabase_enabled
}

terraform {
  source = "${get_terragrunt_dir()}/../../../modules/nginx_containers"
}

dependency "airflow_containers" {
  config_path = "${get_terragrunt_dir()}/../airflow_containers"

  mock_outputs_allowed_terraform_commands = ["init", "validate", "plan"]
  mock_outputs = {
    domain_name = "mock-airflow-webserver.functions.fnc.fr-par.scw.cloud"
  }
}

dependency "metabase_containers" {
  config_path = "${get_terragrunt_dir()}/../metabase_containers"
  enabled     = local.metabase_enabled

  mock_outputs_allowed_terraform_commands = ["init", "validate", "plan"]
  mock_outputs = {
    domain_name = "mock-metabase.functions.fnc.fr-par.scw.cloud"
  }
}

dependencies {
  paths = concat(
    ["${get_terragrunt_dir()}/../airflow_containers"],
    local.metabase_enabled ? ["${get_terragrunt_dir()}/../metabase_containers"] : [],
  )
}

inputs = {
  nginx_registry_image = "rg.fr-par.scw.cloud/ns-qfdmo/nginx-gateway:${get_env("IMAGE_TAG", "")}"
  nginx_cpu_limit      = 500
  nginx_memory_limit   = 512
  nginx_min_scale      = 1
  nginx_max_scale      = 2
  nginx_timeout        = 300

  # CNAME *.<domain> -> terragrunt output domain_name
  # must already resolve before apply (ACME HTTP-01 challenge per hostname).
  routes = merge(
    {
      airflow = {
        hostname = "airflow.${local.env.locals.domain}"
        upstream = dependency.airflow_containers.outputs.domain_name
      }
    },
    local.metabase_enabled ? {
      metabase = {
        hostname = "metabase.${local.env.locals.domain}"
        upstream = dependency.metabase_containers.outputs.domain_name
      }
    } : {},
  )
}
