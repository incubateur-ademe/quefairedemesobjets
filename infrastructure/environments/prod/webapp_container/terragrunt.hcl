# Replaces the Scalingo app quefairedemesobjets.
include "root" {
  path = find_in_parent_folders("root.hcl")
}

# deep: the extra_environment_variables below are added to the shared ones.
include "stack" {
  path           = "${dirname(find_in_parent_folders("root.hcl"))}/_envcommon/webapp_container.hcl"
  merge_strategy = "deep"
}

inputs = {
  NOTION_CONTACT_FORM_DATABASE_ID = "1766523d57d7807eaff4e5bd88c49eb0"
  AWS_STORAGE_BUCKET_NAME         = "qfdmo-interface"

  extra_environment_variables = {
    ASSISTANT_POSTHOG_KEY = "phc_CyGuWk8OiY0aUEc7b2BmZnQavKKHLndHZWqLIWQpTgt" # pragma: allowlist secret (PostHog client key, shipped in the JS)
  }

  # Scalingo value.
  CONN_MAX_AGE = 600

  # min_scale 2: no cold start on the public site.
  #
  # max_scale 4 is a Postgres budget, not a traffic budget. Each container
  # keeps workers x threads = 8 connections open during CONN_MAX_AGE, so
  # 4 containers = 32 of the 200 max_connections shared with Airflow, the
  # worker and the human psql sessions. The margin covers the transient
  # doubling during a deploy (old and new containers coexist). Beyond that, a
  # pooler (pgbouncer) is needed, not a bigger number here.
  min_scale = 2
  max_scale = 4
}
