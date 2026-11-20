#!/usr/bin/env bash
# Runs bin/post_deploy from the image a webapp stack is about to roll out.
# Called by the CI from the stack's directory, before its apply: if it fails,
# the live version is untouched.
#
# The environment is the stack's inputs as rendered for this apply, so it
# matches what the container gets, except module defaults that are not inputs
# (GUNICORN_*).
set -euo pipefail

ENV_FILE=$(mktemp)
trap 'rm -f "$ENV_FILE"' EXIT

# Captured, never printed: it holds the secrets.
INPUTS=$(terragrunt render --json | jq '.inputs')

# Masks go to the job log before any value is used.
jq -r '
  ((.extra_secret_environment_variables // {}) | to_entries[] | .value),
  (.DATABASE_URL, .SECRET_KEY, .NOTION_TOKEN, .AWS_ACCESS_KEY_ID,
   .AWS_SECRET_ACCESS_KEY, .SENTRY_DSN, .POSTHOG_PERSONAL_API_KEY)
  | select(. != null and . != "") | "::add-mask::\(.)"' <<<"$INPUTS"
jq -r '.DATABASE_URL, .extra_secret_environment_variables.DB_WAREHOUSE
  | select(. != null) | capture("//[^:]+:(?<pw>[^@]+)@")?.pw
  | "::add-mask::\(.)"' <<<"$INPUTS"

jq -r '
  with_entries(select(.key | test("^[A-Z][A-Z0-9_]*$")))
  + (.extra_environment_variables // {})
  + (.extra_secret_environment_variables // {})
  | to_entries[] | "\(.key)=\(.value | tostring)"' <<<"$INPUTS" >"$ENV_FILE"

echo "$SCW_SECRET_KEY" | docker login rg.fr-par.scw.cloud -u nologin --password-stdin
docker run --rm --env-file "$ENV_FILE" "$(jq -r '.registry_image' <<<"$INPUTS")" bash /app/bin/post_deploy
