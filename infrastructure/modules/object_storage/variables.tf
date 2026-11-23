variable "environment" {
  description = "Environnement de déploiement"
  type        = string
}
variable "prefix" {
  description = "Prefix for the resources"
  type        = string
}
variable "critical_buckets" {
  description = "Buckets whose content cannot be rebuilt: versioned, and copied by the backup job"
  type        = list(string)
  default     = []
}

variable "other_buckets" {
  description = "Buckets whose content can be rebuilt: not versioned, not backed up"
  type        = list(string)
  default     = []
}

variable "public_read_buckets" {
  description = "Buckets whose file listing is public"
  type        = list(string)
  default     = []
}

variable "import_buckets" {
  description = "Buckets that already exist and are adopted on the next apply"
  type        = list(string)
  default     = []
}
