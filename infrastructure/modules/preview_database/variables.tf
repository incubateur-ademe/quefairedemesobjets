variable "webapp_instance_id" {
  description = "ID de l'instance RDB hôte (ex: instance preprod webapp)"
  type        = string
}

variable "preview_db_name" {
  description = "Nom de la base preview à créer (ex: preview_<sha>)"
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
