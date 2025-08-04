terraform {
  source = "../../../modules/container_registry"
}

include {
  path = find_in_parent_folders("root.hcl")
}