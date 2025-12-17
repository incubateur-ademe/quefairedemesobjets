variable "webapp_instance_id" {
  description = "ID de l'instance RDB webapp (depuis le module database)"
  type        = string
}

variable "webapp_db_sample_name" {
  description = "Nom de la base de données sample pour webapp (optionnel)"
  type        = string
  default     = null
}

variable "webapp_db_sample_username" {
  description = "Nom d'utilisateur de la base de données sample webapp"
  type        = string
}

variable "webapp_db_sample_password" {
  description = "Mot de passe de la base de données sample webapp"
  type        = string
  sensitive   = true
}

