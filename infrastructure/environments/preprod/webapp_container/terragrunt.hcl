# Webapp Django + worker django-tasks pour preprod, en remplacement de l'app
# Scalingo quefairedemesobjets-preprod.
#
# Ce fichier EST l'inventaire des variables d'environnement : chaque cle lue
# par l'application apparait ici, soit en clair (config), soit derivee des
# outputs d'une autre stack, soit via get_env (vrai secret, stocke dans
# l'environnement GitHub `preprod`). Une variable absente est un diff visible,
# pas un defaut silencieux.
#
# Cles Scalingo volontairement abandonnees :
# - lues nulle part dans le code : ASSISTANT_BASE_URL, ASSISTANT_HOSTS,
#   CARTE_POSTHOG_KEY, MAX_SOLUTION_DISPLAYED_ON_MAP,
#   REDIRECT_LEGACY_PRODUIT_TO_WAGTAIL_PAGES, LEGACY_SITE_VITRINE_DOMAIN,
#   DB_READONLY, INSEE_KEY, INSEE_SECRET
# - DB_WEBAPP_SAMPLE : l'alias webapp_sample n'est utilise que par la commande
#   locale create_webapp_sample_db ; la base sample est consommee par Airflow
# - propres aux buildpacks Scalingo : LD_LIBRARY_PATH, PROJ_LIB, PYTHONPATH,
#   DISABLE_COLLECTSTATIC
terraform {
  source = "../../../modules/webapp_container"
}

include {
  path = find_in_parent_folders("root.hcl")
}

dependency "database" {
  config_path = "../database"

  mock_outputs = {
    webapp_db_username      = "webapp"
    webapp_db_password      = "mock" # pragma: allowlist secret
    webapp_endpoint_ip      = "10.0.0.1"
    webapp_endpoint_port    = 5432
    webapp_database_name    = "webapp"
    warehouse_db_username   = "warehouse"
    warehouse_db_password   = "mock" # pragma: allowlist secret
    warehouse_endpoint_ip   = "10.0.0.2"
    warehouse_endpoint_port = 5432
    warehouse_database_name = "warehouse"
  }
  mock_outputs_allowed_terraform_commands = ["validate", "plan"]
}

inputs = {
  registry_image = "rg.fr-par.scw.cloud/ns-qfdmo/webapp:${get_env("IMAGE_TAG")}"

  ## Config, en clair (relue en PR, diffable avec la prod)

  # localhost : la sonde Scaleway. .functions.fnc.fr-par.scw.cloud : le domaine
  # genere du container, pour tester avant la bascule DNS.
  ALLOWED_HOSTS = "lvao.incubateur.ademe.dev,quefairedemesobjets.incubateur.ademe.dev,quefairedemesdechets.incubateur.ademe.dev,localhost,.functions.fnc.fr-par.scw.cloud"

  AWS_STORAGE_BUCKET_NAME = "qfdmo-interface-preprod"

  extra_environment_variables = {
    # "staging" et non "preprod" : templates/admin/base.html et
    # servers.conf.erb testent cette valeur exacte.
    ENVIRONMENT                     = "staging"
    BASE_URL                        = "https://quefairedemesdechets.incubateur.ademe.dev"
    BASE_DOMAIN                     = "quefairedemesdechets.incubateur.ademe.dev"
    DISTANCE_MAX                    = "30000"
    DJANGO_IMPORT_EXPORT_LIMIT      = "0"
    ASSISTANT_POSTHOG_KEY           = "phc_PfuGkQV10XB61yHjoJYaYbICaQxeA31xqD8g9YfTGHZ" # pragma: allowlist secret (cle client PostHog, embarquee dans le JS)
    NOTION_CONTACT_FORM_DATABASE_ID = "17c6523d57d7808b8cc5f5ccae264f7c"
    # Lues par botocore, pas par Django : depuis botocore 1.36 les checksums
    # CRC sont envoyes par defaut et Scaleway Object Storage les rejette.
    # Absentes de Scalingo preprod, presentes en prod : alignees sur la prod.
    AWS_REQUEST_CHECKSUM_CALCULATION = "WHEN_REQUIRED"
    AWS_RESPONSE_CHECKSUM_VALIDATION = "WHEN_REQUIRED"
  }

  ## Derive des outputs de la stack database

  DATABASE_URL = format(
    "postgresql://%s:%s@%s:%s/%s?sslmode=require", # pragma: allowlist secret
    dependency.database.outputs.webapp_db_username,
    dependency.database.outputs.webapp_db_password,
    dependency.database.outputs.webapp_endpoint_ip,
    dependency.database.outputs.webapp_endpoint_port,
    dependency.database.outputs.webapp_database_name,
  )

  extra_secret_environment_variables = {
    DB_WAREHOUSE = format(
      "postgresql://%s:%s@%s:%s/%s?sslmode=require", # pragma: allowlist secret
      dependency.database.outputs.warehouse_db_username,
      dependency.database.outputs.warehouse_db_password,
      dependency.database.outputs.warehouse_endpoint_ip,
      dependency.database.outputs.warehouse_endpoint_port,
      dependency.database.outputs.warehouse_database_name,
    )

    ## Vrais secrets, sans ressource source : environnement GitHub `preprod`
    NOTION_TOKEN             = get_env("NOTION_TOKEN")
    POSTHOG_PERSONAL_API_KEY = get_env("POSTHOG_PERSONAL_API_KEY")
  }

  SECRET_KEY = get_env("SECRET_KEY")
  SENTRY_DSN = get_env("SENTRY_DSN")

  # Cle dediee au bucket (celle de Scalingo), pas la cle projet Scaleway.
  AWS_ACCESS_KEY_ID     = get_env("AWS_ACCESS_KEY_ID")
  AWS_SECRET_ACCESS_KEY = get_env("AWS_SECRET_ACCESS_KEY")

  ## Runtime

  # Valeur Scalingo. Note : settings/base.py:434 la lit mais ne l'injecte pas
  # dans DATABASES, elle est donc sans effet tant que ce n'est pas corrige.
  CONN_MAX_AGE = 300

  min_scale = 1
  max_scale = 2
}
