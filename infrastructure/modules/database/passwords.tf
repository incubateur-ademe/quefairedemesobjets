# The passwords of the database users are generated here, never typed.
# Rotate one with: tofu apply -replace='random_password.db["webapp"]'
locals {
  password_names = toset(concat(
    ["webapp", "webapp_metabase", "warehouse", "warehouse_metabase", "airflow"],
    local.metabase_enabled ? ["metabase"] : [],
  ))
}

resource "random_password" "db" {
  for_each = local.password_names

  length  = 32
  special = true
  # Scaleway RDB requires at least one special char, digit, lowercase and
  # uppercase letter. Restricted to chars that don't need URL-encoding in a
  # postgres:// DSN (no @, :, /, ?, #, %).
  override_special = "-_.~!*"
  min_special      = 1
  min_numeric      = 1
  min_lower        = 1
  min_upper        = 1

  # A password adopted from before keeps its own shape
  lifecycle {
    ignore_changes = all
  }
}

# Passwords typed before they were generated here: while the stack secret
# still holds them, they are imported so that nothing rotates. OpenTofu shows
# an import id in the plan: they appear once, in the output of that apply.
# To delete, with the *_password variables, once every environment is applied.
locals {
  adopted_passwords = {
    for name, password in {
      webapp             = var.webapp_db_password
      webapp_metabase    = var.webapp_db_metabase_password
      warehouse          = var.warehouse_db_password
      warehouse_metabase = var.warehouse_db_metabase_password
      airflow            = var.airflow_db_password
      metabase           = var.metabase_db_password
    } : name => password if password != null
  }
}

import {
  for_each = setintersection(nonsensitive(keys(local.adopted_passwords)), local.password_names)
  to       = random_password.db[each.key]
  id       = nonsensitive(local.adopted_passwords[each.key])
}
