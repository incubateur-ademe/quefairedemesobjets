terraform {
  source = "../../../modules/container_webapp"
}

include "root" {
  path = find_in_parent_folders("root.hcl")
}

include "env" {
  path = find_in_parent_folders("env.hcl")
}

dependency "container_namespace" {
  config_path = "../container_namespace"

  mock_outputs = {
    namespace_id = "fr-par/aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee"
  }
  mock_outputs_allowed_terraform_commands = ["init", "output", "validate", "plan"]
}

dependency "object_storage" {
  config_path = "../object_storage"

  mock_outputs = {
    webapp_bucket_name = "lvao-preview-webapp"
  }
  mock_outputs_allowed_terraform_commands = ["init", "output", "validate", "plan"]
}

dependency "database" {
  config_path = "../database"

  mock_outputs = {
    webapp_database_url    = "postgres://mock:mock@127.0.0.1:5432/webapp?sslmode=require" # pragma: allowlist secret
    warehouse_database_url = "postgres://mock:mock@127.0.0.1:5432/warehouse?sslmode=require" # pragma: allowlist secret
  }
  mock_outputs_allowed_terraform_commands = ["init", "output", "validate", "plan"]
}

inputs = {
  namespace_id   = dependency.container_namespace.outputs.namespace_id
  registry_image = "rg.fr-par.scw.cloud/ns-qfdmod/webapp:test-preview"
  image_tag      = "test-preview"

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
  allowed_hosts              = ".functions.fnc.fr-par.scw.cloud,.containers.fnc.fr-par.scw.cloud"
  legacy_site_vitrine_domain = ""
  webapp_bucket_name         = dependency.object_storage.outputs.webapp_bucket_name

  # DSN bases de données — déduits du module database. Pas de TF_VAR à passer
  # depuis le shell, plus besoin du Secret Manager pour ces valeurs.
  database_url = dependency.database.outputs.webapp_database_url
  db_warehouse = dependency.database.outputs.warehouse_database_url
  # database_sample n'est pas déployé en preview pour l'instant — laissé vide.
  db_webapp_sample = ""

  # Les noms de secrets ont des defaults dans le module (bare names sans
  # préfixe d'environnement). L'isolation par env vient du project_id Scaleway.
  # Override seulement si vous voulez utiliser des noms différents.
}
