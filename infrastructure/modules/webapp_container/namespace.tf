# Dedicated namespace for the webapp containers.
#
# Separate from the Airflow namespace on purpose: the two stacks have
# different lifecycles, and the webapp should not be disturbed by an Airflow
# apply. Preview keeps its own shared namespace and passes namespace_id in,
# so the namespace is only created when the caller does not supply one.
resource "scaleway_container_namespace" "webapp" {
  count = var.namespace_id == null ? 1 : 0

  name        = "${var.prefix}-${var.environment}-webapp"
  description = "Webapp Django et worker django-tasks (${var.environment})"
  tags        = [var.environment, var.prefix, "webapp"]
}

locals {
  namespace_id = coalesce(var.namespace_id, one(scaleway_container_namespace.webapp[*].id))
}
