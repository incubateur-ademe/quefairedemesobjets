output "bucket_name" {
  description = "Bucket holding the encrypted backups"
  value       = scaleway_object_bucket.backups.name
}

output "encryption_password" {
  description = "rclone crypt password of the backups, to keep in the password manager"
  value       = random_password.encryption.result
  sensitive   = true
}
