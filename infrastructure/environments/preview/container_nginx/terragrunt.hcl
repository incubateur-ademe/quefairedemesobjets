terraform {
  source = "../../../modules/container_nginx"
}

include "root" {
  path = find_in_parent_folders("root.hcl")
}

include "env" {
  path = find_in_parent_folders("env.hcl")
}

dependency "container" {
  config_path = "../container"

  mock_outputs = {
    namespace_id = "fr-par/aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee"
  }
  mock_outputs_allowed_terraform_commands = ["validate", "plan"]
}

dependency "container_webapp" {
  config_path = "../container_webapp"

  mock_outputs = {
    domain_name = "lvao-preview-webapp-mock.functions.fnc.fr-par.scw.cloud"
  }
  mock_outputs_allowed_terraform_commands = ["validate", "plan"]
}

inputs = {
  namespace_id   = dependency.container.outputs.namespace_id
  registry_image = "rg.fr-par.scw.cloud/ns-qfdmo/webapp-nginx:preview"

  cpu_limit    = 500
  memory_limit = 512
  min_scale    = 1
  max_scale    = 1
  timeout      = 300

  # Le domaine public exact n'est connu qu'après le premier apply.
  # On accepte la version "any-host" en s'appuyant sur le wildcard côté Django :
  # nginx valide juste son propre BASE_DOMAIN, qui pointe sur l'URL Scaleway générée.
  # Si non renseigné, on prend le domaine interne du webapp (sert au moins à
  # passer le test SNI) ; en pratique l'opérateur set TF_VAR_PREVIEW_NGINX_BASE_DOMAIN.
  base_domain     = get_env("TF_VAR_PREVIEW_NGINX_BASE_DOMAIN", dependency.container_webapp.outputs.domain_name)
  upstream_domain = dependency.container_webapp.outputs.domain_name

  disable_cache = true

  # Pas de redirection legacy en preview.
  legacy_site_vitrine_domain = ""
}
