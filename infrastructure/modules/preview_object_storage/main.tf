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

# ponytail: no dedicated IAM application here — the CI/Terraform key lacks
# IAM write permission. The container reuses the project-wide SCW
# access/secret key instead. Less isolated than a bucket-scoped key;
# revisit if IAM write perms are granted later.
