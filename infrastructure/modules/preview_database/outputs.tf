output "database_name" {
  value = var.preview_db_name
}

output "database_username" {
  value = var.preview_db_username
}

output "database_url" {
  value     = local.preview_db_url
  sensitive = true
}
