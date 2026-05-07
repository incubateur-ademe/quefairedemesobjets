# Secrets lus depuis Scaleway Secret Manager (un projet par env assure
# l'isolation, les noms sont bruts).
data "scaleway_secret" "webapp" {
  for_each = toset(local.secret_manager_names)
  name     = each.value
}

data "scaleway_secret_version" "webapp" {
  for_each  = data.scaleway_secret.webapp
  secret_id = each.value.id
  revision  = "latest_enabled"
}

locals {
  secret_manager_names = [
    var.secret_name_SECRET_KEY,
    var.secret_name_AWS_ACCESS_KEY_ID,
    var.secret_name_AWS_SECRET_ACCESS_KEY,
    var.secret_name_SENTRY_DSN,
    var.secret_name_POSTHOG_PERSONAL_API_KEY,
    var.secret_name_NOTION_TOKEN,
    var.secret_name_ASSISTANT_POSTHOG_KEY,
  ]

  # Secrets injectés directement (DSN bases de données déduits des autres
  # modules — non stockés dans le Secret Manager pour éviter la duplication
  # avec l'état Terraform du module database).
  secrets_from_modules = {
    DATABASE_URL     = var.database_url
    DB_WAREHOUSE     = var.db_warehouse
    DB_WEBAPP_SAMPLE = var.db_webapp_sample
  }

  # `data` renvoyé par scaleway_secret_version est encodé en base64 ;
  # on le décode ici pour exposer la valeur brute aux conteneurs.
  secrets_from_manager = {
    SECRET_KEY               = base64decode(data.scaleway_secret_version.webapp[var.secret_name_SECRET_KEY].data)
    AWS_ACCESS_KEY_ID        = base64decode(data.scaleway_secret_version.webapp[var.secret_name_AWS_ACCESS_KEY_ID].data)
    AWS_SECRET_ACCESS_KEY    = base64decode(data.scaleway_secret_version.webapp[var.secret_name_AWS_SECRET_ACCESS_KEY].data)
    SENTRY_DSN               = base64decode(data.scaleway_secret_version.webapp[var.secret_name_SENTRY_DSN].data)
    POSTHOG_PERSONAL_API_KEY = base64decode(data.scaleway_secret_version.webapp[var.secret_name_POSTHOG_PERSONAL_API_KEY].data)
    NOTION_TOKEN             = base64decode(data.scaleway_secret_version.webapp[var.secret_name_NOTION_TOKEN].data)
    ASSISTANT_POSTHOG_KEY    = base64decode(data.scaleway_secret_version.webapp[var.secret_name_ASSISTANT_POSTHOG_KEY].data)
  }

  secrets = merge(local.secrets_from_modules, local.secrets_from_manager)
}
