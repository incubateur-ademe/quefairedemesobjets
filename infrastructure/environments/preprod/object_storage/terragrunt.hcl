terraform {
  source = "../../../modules/object_storage"
}

include {
  path = find_in_parent_folders("root.hcl")
}

inputs = {
  # Overwritten every week by the copy of the prod media (sync_databases.yml).
  other_buckets  = ["qfdmo-interface-preprod"]
  import_buckets = ["qfdmo-interface-preprod"]
}
