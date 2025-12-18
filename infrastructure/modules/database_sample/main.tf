resource "scaleway_rdb_database" "webapp_sample" {
  instance_id = var.webapp_instance_id
  name        = var.webapp_db_sample_name
}

resource "scaleway_rdb_user" "webapp_sample" {
  instance_id = var.webapp_instance_id
  name        = var.webapp_db_sample_username
  password    = var.webapp_db_sample_password
}

resource "scaleway_rdb_privilege" "webapp_sample_privilege" {
  instance_id   = var.webapp_instance_id
  user_name     = var.webapp_db_sample_username
  database_name = scaleway_rdb_database.webapp_sample.name
  permission    = "all"
}
