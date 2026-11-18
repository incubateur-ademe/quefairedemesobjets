variable "webapp_instance_id" {
  description = "ID de l'instance RDB hôte (ex: instance preprod webapp)"
  type        = string
}

variable "preview_db_name" {
  description = "Nom de la base preview à créer (ex: preview_pr_123)"
  type        = string
}

variable "preview_db_username" {
  description = "Nom d'utilisateur de la base preview"
  type        = string
}

variable "sample_db_uri" {
  description = "URI postgres de la base sample source (pg_dump source)"
  type        = string
  sensitive   = true
}

variable "create_extensions_script_path" {
  description = "Chemin absolu vers create_extensions.sql"
  type        = string
}

variable "image_tag" {
  description = "Image tag du déploiement (pr-<n>-<sha>) — change à chaque push pour forcer un re-seed"
  type        = string
}

variable "clear_db" {
  description = "When true, re-seed the database on every apply (controlled by the preview:cleardb PR label)"
  type        = bool
  default     = false
}

variable "isoprod" {
  description = "When true, seed from the latest backup of the production webapp database instead of the sample (controlled by the preview:isoprod PR label)"
  type        = bool
  default     = false
}

variable "prod_instance_name" {
  description = "Nom de l'instance RDB de production dont le dernier backup alimente les previews isoprod"
  type        = string
  default     = "lvao-prod-webapp"
}

variable "wagtail_french_script_path" {
  description = "Chemin absolu vers create_wagtail_french_config.sql (requis avant de restaurer un dump de production)"
  type        = string
}
