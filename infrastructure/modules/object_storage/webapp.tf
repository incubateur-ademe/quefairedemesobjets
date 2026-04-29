resource "scaleway_object_bucket" "webapp" {
  count = var.create_webapp_bucket ? 1 : 0
  name  = "${var.prefix}-${var.environment}-webapp"
}

resource "scaleway_object_bucket_acl" "webapp" {
  count  = var.create_webapp_bucket ? 1 : 0
  bucket = scaleway_object_bucket.webapp[0].id
  acl    = "private"
}
