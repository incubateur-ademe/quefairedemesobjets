terraform {
  source = "../../../modules/container_webapp"
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

dependency "object_storage" {
  config_path = "../object_storage"

  mock_outputs = {
    webapp_bucket_name = "lvao-preview-webapp"
  }
  mock_outputs_allowed_terraform_commands = ["validate", "plan"]
}

inputs = {
  namespace_id   = dependency.container.outputs.namespace_id
  registry_image = "rg.fr-par.scw.cloud/ns-qfdmo/webapp"
  image_tag      = "441deea"

  # Sizing pour preview — scale à 0 quand inactif.
  cpu_limit    = 1000
  memory_limit = 2048
  min_scale    = 0
  max_scale    = 1
  timeout      = 300

  # BASE_URL : laissé vide volontairement. À renseigner ultérieurement avec
  # l'URL publique de nginx (connue après le premier apply). Django tombe
  # sur son default tant que vide — sans incidence pour preview.

  # Wildcard Django : autorise les sous-domaines Scaleway containers.
  # Couvre l'URL nginx ET l'URL interne webapp (health-checks).
  allowed_hosts      = ".functions.fnc.fr-par.scw.cloud,.containers.fnc.fr-par.scw.cloud"
  webapp_bucket_name = dependency.object_storage.outputs.webapp_bucket_name

  # Les noms de secrets ont des defaults dans le module (bare names sans
  # préfixe d'environnement). L'isolation par env vient du project_id Scaleway.
  # Override seulement si vous voulez utiliser des noms différents.
}
