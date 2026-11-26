# Replaces the Scalingo app quefairedemesobjets-preprod.
include "root" {
  path = find_in_parent_folders("root.hcl")
}

# deep: the extra_environment_variables below are added to the shared ones.
include "stack" {
  path           = "${dirname(find_in_parent_folders("root.hcl"))}/_envcommon/webapp_container.hcl"
  merge_strategy = "deep"
}

inputs = {
  NOTION_CONTACT_FORM_DATABASE_ID = "17c6523d57d7808b8cc5f5ccae264f7c"
  AWS_STORAGE_BUCKET_NAME         = "qfdmo-interface-preprod"

  extra_environment_variables = {
    ASSISTANT_POSTHOG_KEY = "phc_PfuGkQV10XB61yHjoJYaYbICaQxeA31xqD8g9YfTGHZ" # pragma: allowlist secret (PostHog client key, shipped in the JS)
  }

  # Scalingo value.
  CONN_MAX_AGE = 300

  min_scale = 1
  max_scale = 2
}
