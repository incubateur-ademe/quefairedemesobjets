include "root" {
  path = find_in_parent_folders("root.hcl")
}

include "stack" {
  path = "${dirname(find_in_parent_folders("root.hcl"))}/_envcommon/nginx_containers.hcl"
}

locals {
  preview_domain = read_terragrunt_config(find_in_parent_folders("env.hcl")).locals.preview_domain
}

inputs = {
  # Preview containers of the shared qfdmod-preview namespace, one per PR.
  # Their pr-<n>.<preview_domain> domains are attached by the preview
  # workflows, never by this stack.
  previews = local.preview_domain == "" ? null : {
    domain   = local.preview_domain
    upstream = "https://qfdmodpreview6b0061c2-lvao-pr-{pr}-webapp.functions.fnc.fr-par.scw.cloud"
  }
}
