# pr-<n>.<preview_domain> attached to the preprod gateway, which serves every
# preview (previews input of nginx_containers). Materialised to
# environments/preview/pr-<n>/ like the other units, but applied apart by
# _terragrunt-apply.yml: when it fails (50 domains per container at most),
# the preview stays on its Scaleway address. preview_destroy.sh removes it.
terraform {
  source = "../../../../modules/preview_gateway_domain"
}

include {
  path = find_in_parent_folders("root.hcl")
}

locals {
  preprod = read_terragrunt_config("${get_terragrunt_dir()}/../../../preprod/env.hcl")
}

inputs = {
  domain            = local.preprod.locals.preview_domain
  gateway_namespace = "lvao-preprod-gateway"
  gateway_container = "lvao-nginx"
}
