data "scaleway_secret" "webapp" {
  for_each = toset(local.secret_names)
  name     = each.value
}

data "scaleway_secret_version" "webapp" {
  for_each  = data.scaleway_secret.webapp
  secret_id = each.value.id
  revision  = "latest_enabled"
}

locals {
  secret_names = [
    var.secret_name_SECRET_KEY,
    var.secret_name_DATABASE_URL,
    var.secret_name_DB_WAREHOUSE,
    var.secret_name_DB_WEBAPP_SAMPLE,
    var.secret_name_AWS_ACCESS_KEY_ID,
    var.secret_name_AWS_SECRET_ACCESS_KEY,
    var.secret_name_SENTRY_DSN,
    var.secret_name_POSTHOG_PERSONAL_API_KEY,
    var.secret_name_NOTION_TOKEN,
    var.secret_name_ASSISTANT_POSTHOG_KEY,
    var.secret_name_CARTE_POSTHOG_KEY,
  ]

  secrets = {
    SECRET_KEY               = data.scaleway_secret_version.webapp[var.secret_name_SECRET_KEY].data
    DATABASE_URL             = data.scaleway_secret_version.webapp[var.secret_name_DATABASE_URL].data
    DB_WAREHOUSE             = data.scaleway_secret_version.webapp[var.secret_name_DB_WAREHOUSE].data
    DB_WEBAPP_SAMPLE         = data.scaleway_secret_version.webapp[var.secret_name_DB_WEBAPP_SAMPLE].data
    AWS_ACCESS_KEY_ID        = data.scaleway_secret_version.webapp[var.secret_name_AWS_ACCESS_KEY_ID].data
    AWS_SECRET_ACCESS_KEY    = data.scaleway_secret_version.webapp[var.secret_name_AWS_SECRET_ACCESS_KEY].data
    SENTRY_DSN               = data.scaleway_secret_version.webapp[var.secret_name_SENTRY_DSN].data
    POSTHOG_PERSONAL_API_KEY = data.scaleway_secret_version.webapp[var.secret_name_POSTHOG_PERSONAL_API_KEY].data
    NOTION_TOKEN             = data.scaleway_secret_version.webapp[var.secret_name_NOTION_TOKEN].data
    ASSISTANT_POSTHOG_KEY    = data.scaleway_secret_version.webapp[var.secret_name_ASSISTANT_POSTHOG_KEY].data
    CARTE_POSTHOG_KEY        = data.scaleway_secret_version.webapp[var.secret_name_CARTE_POSTHOG_KEY].data
  }
}
