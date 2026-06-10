# Shared container namespace for all preview environments (lvao-preview).
# Applied once during bootstrap; the per-PR container stacks read its
# namespace_id through a terragrunt dependency.
terraform {
  source = "../../../modules/preview_namespace"
}

include {
  path = find_in_parent_folders("root.hcl")
}
