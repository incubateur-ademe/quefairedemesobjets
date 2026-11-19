# Keys that only Airflow uses are generated here, never typed. Replacing one
# (tofu apply -replace=<address>) rolls the containers out with the new value.

# Django needs one to load the settings of the webapp; nothing is signed with it.
resource "random_password" "django_secret_key" {
  length  = 64
  special = false
}

# Shared by the three containers: they are updated by the same apply.
resource "random_password" "jwt_secret" {
  length  = 64
  special = false
}

# Key pair of the scheduler for the on-demand ml-deduplication instance: the
# public key is injected at its creation, the private one opens the session.
resource "tls_private_key" "ml_deduplication" {
  algorithm = "ED25519"
}
