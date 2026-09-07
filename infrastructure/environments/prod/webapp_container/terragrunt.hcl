# Webapp Django + worker django-tasks pour prod, en remplacement de l'app
# Scalingo quefairedemesobjets.
#
# Ce fichier EST l'inventaire des variables d'environnement : chaque cle lue
# par l'application apparait ici, soit en clair (config), soit derivee des
# outputs d'une autre stack, soit via get_env (vrai secret, stocke dans
# l'environnement GitHub `prod`). Une variable absente est un diff visible,
# pas un defaut silencieux. preprod/webapp_container porte exactement les
# memes cles, seules les valeurs changent.
#
# Cles Scalingo volontairement abandonnees :
# - lues nulle part dans le code : ASSISTANT_BASE_URL, ASSISTANT_HOSTS,
#   CARTE_POSTHOG_KEY, LVAO_POSTHOG_KEY, CORS_ALLOWED_ORIGINS,
#   MAX_SOLUTION_DISPLAYED_ON_MAP, REDIRECT_LEGACY_PRODUIT_TO_WAGTAIL_PAGES,
#   LEGACY_SITE_VITRINE_DOMAIN, INSEE_KEY, INSEE_SECRET,
#   SCALEWAY_ACCESS_KEY_ID, SCALEWAY_SECRET_KEY
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

  ## Config, en clair (relue en PR, diffable avec la preprod)

  # localhost : la sonde Scaleway. .functions.fnc.fr-par.scw.cloud : le domaine
  # genere du container, pour tester avant la bascule DNS.
  ALLOWED_HOSTS = "quefairedemesdechets.ademe.fr,lvao.ademe.fr,quefairedemesobjets.ademe.fr,longuevieauxobjets.ademe.fr,quefairedemesobjets.fr,quefairedemesdechets.fr,localhost,.functions.fnc.fr-par.scw.cloud"

  AWS_STORAGE_BUCKET_NAME = "qfdmo-interface"

  extra_environment_variables = {
    # templates/admin/base.html et servers.conf.erb testent cette valeur exacte.
    ENVIRONMENT                     = "production"
    BASE_URL                        = "https://quefairedemesdechets.ademe.fr"
    BASE_DOMAIN                     = "quefairedemesdechets.ademe.fr"
    DISTANCE_MAX                    = "30000"
    DJANGO_IMPORT_EXPORT_LIMIT      = "0"
    ASSISTANT_POSTHOG_KEY           = "phc_CyGuWk8OiY0aUEc7b2BmZnQavKKHLndHZWqLIWQpTgt" # pragma: allowlist secret (cle client PostHog, embarquee dans le JS)
    NOTION_CONTACT_FORM_DATABASE_ID = "1766523d57d7807eaff4e5bd88c49eb0"
    # Lues par botocore, pas par Django : depuis botocore 1.36 les checksums
    # CRC sont envoyes par defaut et Scaleway Object Storage les rejette.
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

    ## Vrais secrets, sans ressource source : environnement GitHub `prod`
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
  CONN_MAX_AGE = 600

  # min_scale 2 : pas de cold start sur le site public.
  #
  # max_scale 4 est un budget Postgres, pas un budget trafic. Chaque
  # container garde workers x threads = 16 connexions ouvertes pendant
  # CONN_MAX_AGE, donc 4 containers = 64 des 200 max_connections partagees
  # avec Airflow, le worker et les sessions psql humaines. La marge couvre
  # le doublement transitoire pendant un deploiement (ancien et nouveau
  # container coexistent). Au-dela, il faut un pooler (pgbouncer), pas un
  # chiffre plus grand ici.
  min_scale = 2
  max_scale = 4
}
