variable "prefix" {
  description = "Prefix for the resources"
  type        = string
}

variable "environment" {
  description = "Environnement de déploiement"
  type        = string
}

variable "databases" {
  description = "Databases to dump, each with the ID of its RDB instance"
  type = list(object({
    instance_id = string
    name        = string
  }))
}

variable "buckets" {
  description = "Names of the buckets to mirror into the backup bucket"
  type        = list(string)
}

variable "schedule" {
  description = "Cron schedule of the backup, Europe/Paris time"
  type        = string
  default     = "0 2 * * *"
}
