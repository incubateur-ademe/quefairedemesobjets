# django-tasks worker: replaces the Scalingo `worker:` Procfile entry.
#
# Same image as the webapp, switched to the worker role by CONTAINER_ROLE
# (see webapp/bin/entrypoint.sh). It polls the task queue in Postgres rather
# than serving requests, but Serverless Containers require an HTTP listener
# on `port` for the probe, so the entrypoint runs a stub nginx answering 200
# next to db_worker (same trick as the Airflow dag-processor). min_scale
# stays at 1: scaling to zero would stop tasks being processed.
resource "scaleway_container" "worker" {
  name = "${var.prefix}-${var.environment}-worker"
  tags = concat(
    [
      var.environment,
      var.prefix,
      "worker",
      "created-at-${time_static.created_at.unix}",
    ],
    var.extra_tags,
  )
  namespace_id   = local.namespace_id
  registry_image = var.registry_image
  port           = 8000
  cpu_limit      = var.worker_cpu_limit
  memory_limit   = var.worker_memory_limit
  min_scale      = var.worker_min_scale
  max_scale      = var.worker_max_scale
  privacy        = "private"
  protocol       = "http1"

  # db_worker runs in the foreground: if it dies the container exits and
  # Scaleway restarts it. The probe only covers the stub listener.
  liveness_probe {
    http {
      path = "/"
    }
    failure_threshold = 5
    interval          = "30s"
    timeout           = "10s"
  }

  environment_variables = merge(
    local.environment_variables,
    { CONTAINER_ROLE = "worker" },
  )
  secret_environment_variables = local.secret_environment_variables
}
