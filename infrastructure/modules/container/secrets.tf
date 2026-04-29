# Lecture des secrets webapp depuis Scaleway Secret Manager.
# Activée via var.use_secret_manager (default false pour préserver preprod/prod).
# L'isolation par environnement vient du project_id Scaleway, donc les noms
# sont identiques d'un env à l'autre.

locals {
  webapp_secret_names = var.use_secret_manager ? toset([
    var.secret_name_AWS_ACCESS_KEY_ID,
    var.secret_name_AWS_SECRET_ACCESS_KEY,
    var.secret_name_SENTRY_DSN,
    var.secret_name_NOTION_TOKEN,
    var.secret_name_POSTHOG_PERSONAL_API_KEY,
  ]) : toset([])
}

data "scaleway_secret" "webapp" {
  for_each = local.webapp_secret_names
  name     = each.value
}

data "scaleway_secret_version" "webapp" {
  for_each  = data.scaleway_secret.webapp
  secret_id = each.value.id
  revision  = "latest_enabled"
}

locals {
  webapp_secrets = var.use_secret_manager ? {
    AWS_ACCESS_KEY_ID        = data.scaleway_secret_version.webapp[var.secret_name_AWS_ACCESS_KEY_ID].data
    AWS_SECRET_ACCESS_KEY    = data.scaleway_secret_version.webapp[var.secret_name_AWS_SECRET_ACCESS_KEY].data
    SENTRY_DSN               = data.scaleway_secret_version.webapp[var.secret_name_SENTRY_DSN].data
    NOTION_TOKEN             = data.scaleway_secret_version.webapp[var.secret_name_NOTION_TOKEN].data
    POSTHOG_PERSONAL_API_KEY = data.scaleway_secret_version.webapp[var.secret_name_POSTHOG_PERSONAL_API_KEY].data
  } : {}
}
