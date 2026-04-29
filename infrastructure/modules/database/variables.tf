variable "environment" {
  description = "Environnement de déploiement"
  type        = string
}

variable "prefix" {
  description = "Prefix for the resources"
  type        = string
}

variable "webapp_node_type" {
  description = "Type de nœud de la base de données webapp"
  type        = string
}

variable "webapp_db_name" {
  description = "Nom de la base de données webapp"
  type        = string
}

variable "webapp_db_username" {
  description = "Nom d'utilisateur de la base de données webapp"
  type        = string
}

variable "webapp_db_password" {
  description = "Mot de passe de la base de données webapp"
  type        = string
  sensitive   = true
}

variable "webapp_volume_size" {
  description = "Taille du volume en GB de la base de données webapp"
  type        = number
}

variable "warehouse_node_type" {
  description = "Type de nœud de la base de données warehouse"
  type        = string
}

variable "warehouse_db_name" {
  description = "Nom de la base de données warehouse"
  type        = string
}

variable "warehouse_db_username" {
  description = "Nom d'utilisateur de la base de données warehouse"
  type        = string
}

variable "warehouse_db_password" {
  description = "Mot de passe de la base de données warehouse"
  type        = string
  sensitive   = true
}

variable "warehouse_volume_size" {
  description = "Taille du volume en GB de la base de données warehouse"
  type        = number
}

variable "airflow_node_type" {
  description = "Type de nœud de la base de données airflow"
  type        = string
}

variable "airflow_db_name" {
  description = "Nom de la base de données airflow"
  type        = string
}

variable "airflow_db_username" {
  description = "Nom d'utilisateur de la base de données airflow"
  type        = string
}

variable "airflow_db_password" {
  description = "Mot de passe de la base de données airflow"
  type        = string
  sensitive   = true
}

variable "airflow_volume_size" {
  description = "Taille du volume en GB de la base de données airflow"
  type        = number
}

variable "create_remote_warehouse_in_webapp_script_path" {
  description = "Chemin absolu vers le script SQL qui configure le foreign server warehouse dans la base webapp. Si null, le script n'est pas exécuté."
  type        = string
  default     = null
}

variable "create_remote_webapp_in_warehouse_script_path" {
  description = "Chemin absolu vers le script SQL qui configure le foreign server webapp dans la base warehouse. Si null, le script n'est pas exécuté."
  type        = string
  default     = null
}