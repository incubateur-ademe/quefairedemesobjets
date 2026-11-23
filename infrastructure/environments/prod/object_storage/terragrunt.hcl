terraform {
  source = "../../../modules/object_storage"
}

include {
  path = find_in_parent_folders("root.hcl")
}

locals {
  # qfdmo-interface: media of the webapp. lvao-data-source: files uploaded by
  # hand for the source-s3 DAG. lvao-terraform-state: this very backend.
  critical_buckets = ["qfdmo-interface", "lvao-data-source", "lvao-terraform-state"]
  # lvao-opendata is written again by every run of export_opendata_dag.
  other_buckets = ["lvao-opendata"]
}

inputs = {
  critical_buckets = local.critical_buckets
  other_buckets    = local.other_buckets
  # The open data files are published from this bucket.
  public_read_buckets = local.other_buckets
  import_buckets      = concat(local.critical_buckets, local.other_buckets)
}
