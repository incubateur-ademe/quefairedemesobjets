terraform {
  source = "../../../modules/object_storage"
}

include {
  path = find_in_parent_folders("root.hcl")
}