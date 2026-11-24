output "versioned_bucket_names" {
  description = "Buckets whose content cannot be rebuilt"
  value       = [for name in var.critical_buckets : scaleway_object_bucket.this[name].name]
}
