# What a preview (pr-<n>) is for the shared stack descriptions: the keys of
# preprod/env.hcl and prod/env.hcl that _envcommon/webapp_container.hcl reads.
locals {
  pr_number = get_env("PR_NUMBER")
  preprod   = read_terragrunt_config("${dirname(find_in_parent_folders("root.hcl"))}/preprod/env.hcl").locals

  # Scaleway address of the container, and pr-<n>.<preview_domain> once the
  # preprod gateway serves the previews.
  host         = "qfdmodpreview6b0061c2-lvao-pr-${local.pr_number}-webapp.functions.fnc.fr-par.scw.cloud"
  gateway_host = local.preprod.preview_domain == "" ? "" : "pr-${local.pr_number}.${local.preprod.preview_domain}"

  webapp_environment = "pr-${local.pr_number}"
  warehouse_enabled  = false

  webapp_base_domain    = coalesce(local.gateway_host, local.host)
  webapp_gateway_domain = local.host
  webapp_alias_domains  = []
}
