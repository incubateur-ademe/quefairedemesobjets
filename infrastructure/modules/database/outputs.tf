## Web app

output "webapp_instance_id" {
  description = "ID de l'instance RDB webapp"
  value       = scaleway_rdb_instance.webapp.id
}

output "webapp_database_name" {
  description = "Nom de la base de données webapp"
  value       = scaleway_rdb_database.webapp.name
}

output "webapp_endpoint_ip" {
  description = "IP de connexion à l'instance webapp (préférer private_network / load_balancer au endpoint déprécié)"
  value = try(
    scaleway_rdb_instance.webapp.private_network[0].ip,
    scaleway_rdb_instance.webapp.load_balancer[0].ip,
    scaleway_rdb_instance.webapp.private_ip[0].address,
    scaleway_rdb_instance.webapp.endpoint_ip,
  )
}

output "webapp_endpoint_port" {
  description = "Port de connexion à l'instance webapp (préférer private_network / load_balancer au endpoint déprécié)"
  value = try(
    scaleway_rdb_instance.webapp.private_network[0].port,
    scaleway_rdb_instance.webapp.load_balancer[0].port,
    scaleway_rdb_instance.webapp.endpoint_port,
  )
}

output "webapp_db_username" {
  description = "Nom d'utilisateur de la base de données webapp"
  value       = var.webapp_db_username
}

output "webapp_db_password" {
  description = "Mot de passe de la base de données webapp"
  value       = var.webapp_db_password
  sensitive   = true
}

## Warehouse

output "warehouse_instance_id" {
  description = "ID de l'instance RDB warehouse"
  value       = scaleway_rdb_instance.warehouse.id
}

output "warehouse_database_name" {
  description = "Nom de la base de données warehouse"
  value       = scaleway_rdb_database.warehouse_database.name
}

output "warehouse_endpoint_ip" {
  description = "IP de connexion à l'instance warehouse (préférer private_network / load_balancer au endpoint déprécié)"
  value = try(
    scaleway_rdb_instance.warehouse.private_network[0].ip,
    scaleway_rdb_instance.warehouse.load_balancer[0].ip,
    scaleway_rdb_instance.warehouse.private_ip[0].address,
    scaleway_rdb_instance.warehouse.endpoint_ip,
  )
}

output "warehouse_endpoint_port" {
  description = "Port de connexion à l'instance warehouse (préférer private_network / load_balancer au endpoint déprécié)"
  value = try(
    scaleway_rdb_instance.warehouse.private_network[0].port,
    scaleway_rdb_instance.warehouse.load_balancer[0].port,
    scaleway_rdb_instance.warehouse.endpoint_port,
  )
}

output "warehouse_db_username" {
  description = "Nom d'utilisateur de la base de données warehouse"
  value       = var.warehouse_db_username
}

output "warehouse_db_password" {
  description = "Mot de passe de la base de données warehouse"
  value       = var.warehouse_db_password
  sensitive   = true
}

## Airflow

output "airflow_instance_id" {
  description = "ID de l'instance RDB airflow"
  value       = scaleway_rdb_instance.airflow.id
}

output "airflow_database_name" {
  description = "Nom de la base de données airflow"
  value       = scaleway_rdb_database.airflow.name
}

output "airflow_endpoint_ip" {
  description = "IP de connexion à l'instance airflow (préférer private_network / load_balancer au endpoint déprécié)"
  value = try(
    scaleway_rdb_instance.airflow.private_network[0].ip,
    scaleway_rdb_instance.airflow.load_balancer[0].ip,
    scaleway_rdb_instance.airflow.private_ip[0].address,
    scaleway_rdb_instance.airflow.endpoint_ip,
  )
}

output "airflow_endpoint_port" {
  description = "Port de connexion à l'instance airflow (préférer private_network / load_balancer au endpoint déprécié)"
  value = try(
    scaleway_rdb_instance.airflow.private_network[0].port,
    scaleway_rdb_instance.airflow.load_balancer[0].port,
    scaleway_rdb_instance.airflow.endpoint_port,
  )
}

output "airflow_db_username" {
  description = "Nom d'utilisateur de la base de données airflow"
  value       = var.airflow_db_username
}

output "airflow_db_password" {
  description = "Mot de passe de la base de données airflow"
  value       = var.airflow_db_password
  sensitive   = true
}
