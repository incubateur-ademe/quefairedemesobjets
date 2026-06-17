output "bucket_name" {
  value = scaleway_object_bucket.media.name
}

output "bucket_region" {
  value = "fr-par"
}

output "endpoint_url" {
  value = "https://s3.fr-par.scw.cloud"
}

output "access_key" {
  value     = scaleway_iam_api_key.bucket_access.access_key
  sensitive = true
}

output "secret_key" {
  value     = scaleway_iam_api_key.bucket_access.secret_key
  sensitive = true
}
