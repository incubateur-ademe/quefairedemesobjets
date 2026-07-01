output "bucket_name" {
  value = scaleway_object_bucket.media.name
}

output "bucket_region" {
  value = "fr-par"
}

output "endpoint_url" {
  value = "https://s3.fr-par.scw.cloud"
}
