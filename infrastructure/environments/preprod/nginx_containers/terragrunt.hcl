terraform {
  source = "../../../modules/nginx_containers"
}

dependency "airflow_containers" {
  config_path = "../airflow_containers"

  mock_outputs_allowed_terraform_commands = ["init", "validate", "plan"]
  mock_outputs = {
    domain_name = "mock-airflow-webserver.functions.fnc.fr-par.scw.cloud"
  }
}

dependency "metabase_containers" {
  config_path = "../metabase_containers"

  mock_outputs_allowed_terraform_commands = ["init", "validate", "plan"]
  mock_outputs = {
    domain_name = "mock-metabase.functions.fnc.fr-par.scw.cloud"
  }
}

dependencies {
  paths = ["../airflow_containers", "../metabase_containers"]
}

include {
  path = find_in_parent_folders("root.hcl")
}

inputs = {
  nginx_registry_image = "rg.fr-par.scw.cloud/ns-qfdmo/nginx-gateway:<TAG>"
  nginx_cpu_limit      = 500
  nginx_memory_limit   = 512
  nginx_min_scale      = 1
  nginx_max_scale      = 2
  nginx_timeout        = 300

  # CNAME *.preprod.quefairedemesobjets.ademe.fr -> terragrunt output domain_name
  # must already resolve before apply (ACME HTTP-01 challenge per hostname).
  routes = {
    airflow = {
      hostname = "airflow.preprod.quefairedemesobjets.ademe.fr"
      upstream = dependency.airflow_containers.outputs.domain_name
    }
    metabase = {
      hostname = "metabase.preprod.quefairedemesobjets.ademe.fr"
      upstream = dependency.metabase_containers.outputs.domain_name
    }
  }
}
