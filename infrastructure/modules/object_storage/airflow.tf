resource "scaleway_object_bucket" "airflow" {
  name = "${var.prefix}-${var.environment}-airflow${var.name_suffix}"
}

resource "scaleway_object_bucket_acl" "airflow" {
  bucket = scaleway_object_bucket.airflow.id
  acl    = "private"
}