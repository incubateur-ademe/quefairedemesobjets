resource "scaleway_object_bucket" "media" {
  name = "${var.prefix}-${var.environment}-media"
  tags = {
    environment = var.environment
    role        = "preview-media"
  }

  # Previews are throwaway: let destroy succeed even if objects remain
  # (lifecycle would reap them eventually, but we don't want to wait).
  force_destroy = true

  # Object-level lifecycle: every object older than N days is auto-deleted.
  # Acts as a safety net even if the per-PR destroy never runs.
  lifecycle_rule {
    id      = "expire-objects"
    enabled = true
    expiration {
      days = var.object_expiration_days
    }
    abort_incomplete_multipart_upload_days = 1
  }
}

resource "scaleway_object_bucket_acl" "media" {
  bucket = scaleway_object_bucket.media.id
  acl    = "private"
}

# Bucket-scoped IAM application: gives the container an access key that
# can only touch this bucket, nothing else in the project.
resource "scaleway_iam_application" "bucket_access" {
  name        = "${var.prefix}-${var.environment}-media"
  description = "Bucket-scoped credentials for preview ${var.environment}"
}

resource "scaleway_iam_policy" "bucket_access" {
  name           = "${var.prefix}-${var.environment}-media"
  application_id = scaleway_iam_application.bucket_access.id

  rule {
    project_ids          = [var.project_id]
    permission_set_names = ["ObjectStorageFullAccess"]
  }
}

resource "scaleway_iam_api_key" "bucket_access" {
  application_id = scaleway_iam_application.bucket_access.id
  description    = "Used by the preview ${var.environment} webapp container"
}
