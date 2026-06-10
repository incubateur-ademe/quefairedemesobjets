output "database_name" {
  value = scaleway_rdb_database.preview.name
}

output "database_username" {
  value = scaleway_rdb_user.preview.name
}

output "database_url" {
  value     = local.preview_db_url
  sensitive = true
}
