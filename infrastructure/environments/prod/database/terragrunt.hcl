include "root" {
  path = find_in_parent_folders("root.hcl")
}

include "stack" {
  path = "${dirname(find_in_parent_folders("root.hcl"))}/_envcommon/database.hcl"
}

inputs = {
  webapp_node_type   = "DB-PRO2-XXS"
  webapp_volume_size = 20

  warehouse_node_type   = "DB-PRO2-XXS"
  warehouse_volume_size = 100

  # Metabase (database on warehouse instance)
  metabase_db_username = "metabase"

  # DEPRECATED
  airflow_node_type   = "DB-PLAY2-NANO"
  airflow_volume_size = 20
}
