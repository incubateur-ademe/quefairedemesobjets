# Per-PR media bucket. Materialised to environments/preview/pr-<n>/ by the
# _terragrunt-apply.yml workflow; `environment` (pr-<n>) and the state key
# derive from the materialised path.
terraform {
  source = "../../../../modules/preview_object_storage"
}

include {
  path = find_in_parent_folders("root.hcl")
}

inputs = {
  object_expiration_days = 1
}
