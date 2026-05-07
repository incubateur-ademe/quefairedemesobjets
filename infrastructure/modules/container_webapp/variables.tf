variable "environment" {
  description = "Environnement de déploiement"
  type        = string
}

variable "prefix" {
  description = "Prefix for the resources"
  type        = string
}

variable "namespace_id" {
  description = "ID du namespace de containers Scaleway (réutilisé depuis le module container/airflow)"
  type        = string
}

variable "registry_image" {
  description = "Image Docker complète, ex. rg.fr-par.scw.cloud/ns-qfdmo/webapp:preview"
  type        = string
}

variable "image_tag" {
  description = "Tag de l'image, exposé à Django via CONTAINER_VERSION"
  type        = string
}

variable "cpu_limit" {
  description = "Limite CPU en mCPU (1000 = 1 vCPU)"
  type        = number
  default     = 1000
}

variable "memory_limit" {
  description = "Limite mémoire en MB"
  type        = number
  default     = 2048
}

variable "min_scale" {
  description = "Nombre minimum d'instances (0 = scale-to-zero)"
  type        = number
  default     = 0
}

variable "max_scale" {
  description = "Nombre maximum d'instances"
  type        = number
  default     = 1
}

variable "timeout" {
  description = "Timeout des requêtes en secondes"
  type        = number
  default     = 300
}

# --- Variables d'environnement Django ---
# Sources : webapp/.env.template (canonique pour le set des variables) et
# secret.txt (valeurs historiques Scalingo). Seules les variables présentes
# dans .env.template sont conservées.

variable "base_url" {
  description = "URL publique de l'application (utilisée par Django pour les liens absolus). Vide jusqu'au second apply ; à renseigner avec l'URL nginx une fois connue."
  type        = string
  default     = ""
}

variable "allowed_hosts" {
  description = "Liste CSV des hosts autorisés par Django"
  type        = string
}

variable "legacy_site_vitrine_domain" {
  description = "Domaine du site vitrine LVAO (utilisé pour les redirections legacy)"
  type        = string
  default     = ""
}

variable "webapp_bucket_name" {
  description = "Nom du bucket S3 pour les médias Django (déduit du module object_storage)"
  type        = string
}

variable "distance_max" {
  description = "Distance max (mètres) pour la recherche d'acteurs sur la carte"
  type        = string
  default     = "30000"
}

variable "django_import_export_limit" {
  description = "Limite d'import/export Django admin (0 = pas de limite)"
  type        = string
  default     = "0"
}

variable "notion_contact_form_database_id" {
  description = "ID de la base Notion utilisée par le formulaire de contact"
  type        = string
  default     = "17c6523d57d78140b87f000cd3ecef4b" # pragma: allowlist secret
}

# --- DSN bases de données (déduits des modules database / database_sample) ---
# Valeurs sensibles : injectées via secret_environment_variables.

variable "database_url" {
  description = "DSN postgres webapp (déduit du module database via dependency.database.outputs.webapp_database_url)"
  type        = string
  sensitive   = true
}

variable "db_warehouse" {
  description = "DSN postgres warehouse (déduit du module database via dependency.database.outputs.warehouse_database_url)"
  type        = string
  sensitive   = true
}

variable "db_webapp_sample" {
  description = "DSN postgres sample (déduit du module database_sample). Vide si le module n'est pas déployé dans cet environnement."
  type        = string
  sensitive   = true
  default     = ""
}

# --- Noms des secrets dans Scaleway Secret Manager ---
# L'isolation par environnement est assurée par le project_id Scaleway (un
# projet par env), donc les secrets ont des noms bruts identiques d'un env
# à l'autre. Les valeurs sont lues à l'apply via data.scaleway_secret_version
# (voir secrets.tf) et injectées dans secret_environment_variables.
# Chaque secret doit exister dans le projet Scaleway avant le premier apply
# (voir secret-scaleway.txt à la racine du repo pour la liste).

variable "secret_name_SECRET_KEY" {
  description = "Nom du secret Scaleway contenant SECRET_KEY (Django)"
  type        = string
  default     = "SECRET_KEY"
}

variable "secret_name_AWS_ACCESS_KEY_ID" {
  description = "Nom du secret Scaleway contenant AWS_ACCESS_KEY_ID (clé Scaleway pour S3)"
  type        = string
  default     = "AWS_ACCESS_KEY_ID"
}

variable "secret_name_AWS_SECRET_ACCESS_KEY" {
  description = "Nom du secret Scaleway contenant AWS_SECRET_ACCESS_KEY"
  type        = string
  default     = "AWS_SECRET_ACCESS_KEY"
}

variable "secret_name_SENTRY_DSN" {
  description = "Nom du secret Scaleway contenant SENTRY_DSN"
  type        = string
  default     = "SENTRY_DSN"
}

variable "secret_name_POSTHOG_PERSONAL_API_KEY" {
  description = "Nom du secret Scaleway contenant POSTHOG_PERSONAL_API_KEY"
  type        = string
  default     = "POSTHOG_PERSONAL_API_KEY"
}

variable "secret_name_NOTION_TOKEN" {
  description = "Nom du secret Scaleway contenant NOTION_TOKEN"
  type        = string
  default     = "NOTION_TOKEN"
}

variable "secret_name_ASSISTANT_POSTHOG_KEY" {
  description = "Nom du secret Scaleway contenant ASSISTANT_POSTHOG_KEY"
  type        = string
  default     = "ASSISTANT_POSTHOG_KEY"
}
