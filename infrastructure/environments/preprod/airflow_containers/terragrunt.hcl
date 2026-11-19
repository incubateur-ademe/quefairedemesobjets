include "root" {
  path = find_in_parent_folders("root.hcl")
}

include "stack" {
  path = "${dirname(find_in_parent_folders("root.hcl"))}/_envcommon/airflow_containers.hcl"
}

inputs = {
  AIRFLOW__WEBSERVER__INSTANCE_NAME = "✅✅✅✅ PREPROD ✅✅✅✅"
  WEBAPP_URL                        = "https://quefairedemesdechets.incubateur.ademe.dev"
}
