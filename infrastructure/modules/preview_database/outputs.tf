# Named like the outputs of the database module that
# _envcommon/webapp_container.hcl reads.
output "webapp_database_name" {
  value = var.preview_db_name
}

output "webapp_db_username" {
  value = var.preview_db_username
}

output "webapp_db_password" {
  value     = random_password.preview.result
  sensitive = true
}

output "webapp_endpoint_ip" {
  value = local.host
}

output "webapp_endpoint_port" {
  value = local.port
}
