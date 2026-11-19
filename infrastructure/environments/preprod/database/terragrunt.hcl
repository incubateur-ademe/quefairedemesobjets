include "root" {
  path = find_in_parent_folders("root.hcl")
}

include "stack" {
  path = "${dirname(find_in_parent_folders("root.hcl"))}/_envcommon/database.hcl"
}

inputs = {
  webapp_node_type   = "DB-PLAY2-NANO"
  webapp_volume_size = 25

  warehouse_node_type   = "DB-PLAY2-NANO"
  warehouse_volume_size = 100

  # Cross-DB postgres_fdw setup between webapp and warehouse.
  create_remote_warehouse_in_webapp_script_path = abspath("${get_terragrunt_dir()}/../../../../scripts/sql/create_remote_warehouse_in_webapp.sql")
  create_remote_webapp_in_warehouse_script_path = abspath("${get_terragrunt_dir()}/../../../../scripts/sql/create_remote_webapp_in_warehouse.sql")
}
