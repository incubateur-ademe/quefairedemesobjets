output "airflow_bucket_name" {
  description = "Nom du bucket S3 pour les logs Airflow"
  value       = scaleway_object_bucket.airflow.name
}

output "webapp_bucket_name" {
  description = "Nom du bucket S3 pour les médias Django (Wagtail uploads, etc.). Vide si create_webapp_bucket = false."
  value       = try(scaleway_object_bucket.webapp[0].name, "")
}

output "webapp_bucket_endpoint" {
  description = "Endpoint régional du bucket webapp. Vide si create_webapp_bucket = false."
  value       = try(scaleway_object_bucket.webapp[0].endpoint, "")
}
