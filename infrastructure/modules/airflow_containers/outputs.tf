output "container_id" {
  description = "ID du container Airflow webserver"
  value       = scaleway_container.airflow_webserver.id
}

output "scheduler_container_id" {
  description = "ID du container Airflow scheduler"
  value       = scaleway_container.airflow_scheduler.id
}

output "dag_processor_container_id" {
  description = "ID du container Airflow dag processor"
  value       = scaleway_container.airflow_dag_processor.id
}

output "registry_image" {
  description = "Image running now (the three images share one tag): pass its tag as IMAGE_TAG to apply by hand without redeploying"
  value       = scaleway_container.airflow_scheduler.registry_image
}

output "domain_name" {
  description = "Nom de domaine public Scaleway du container Airflow webserver (upstream du gateway nginx)"
  value       = scaleway_container.airflow_webserver.domain_name
}

output "custom_domain" {
  description = "Hostname public du webserver via le gateway nginx, s'il est configuré"
  value       = local.custom_domain_enabled ? var.custom_domain : null
}

output "public_endpoint" {
  description = "URL publique du webserver Airflow"
  value = local.custom_domain_enabled ? (
    "https://${var.custom_domain}"
  ) : "https://${scaleway_container.airflow_webserver.domain_name}"
}
