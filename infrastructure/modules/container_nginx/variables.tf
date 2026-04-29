variable "environment" {
  description = "Environnement de déploiement"
  type        = string
}

variable "prefix" {
  description = "Prefix for the resources"
  type        = string
}

variable "namespace_id" {
  description = "ID du namespace de containers Scaleway"
  type        = string
}

variable "registry_image" {
  description = "Image Docker complète, ex. rg.fr-par.scw.cloud/ns-qfdmo/webapp-nginx:preview"
  type        = string
}

variable "cpu_limit" {
  description = "Limite CPU en mCPU"
  type        = number
  default     = 500
}

variable "memory_limit" {
  description = "Limite mémoire en MB"
  type        = number
  default     = 512
}

variable "min_scale" {
  description = "Nombre minimum d'instances. Garder à 1 pour la disponibilité de l'ingress public."
  type        = number
  default     = 1
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

variable "base_domain" {
  description = "Hostname public servi par nginx (utilisé pour la validation Host dans servers.conf.erb)"
  type        = string
}

variable "upstream_domain" {
  description = "Domaine interne du container webapp en amont (ex. <container>.functions.fnc.fr-par.scw.cloud)"
  type        = string
}

variable "disable_cache" {
  description = "Si true, désactive le cache nginx (recommandé pour preview)"
  type        = bool
  default     = true
}

variable "legacy_site_vitrine_domain" {
  description = "Domaine legacy à rediriger vers BASE_DOMAIN (ex. longuevieauxobjets.ademe.local). Vide pour désactiver la redirection."
  type        = string
  default     = ""
}
