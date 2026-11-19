#!/usr/bin/env bash
# Prints the inputs a Terragrunt stack keeps in Scaleway Secret Manager, as a
# JSON object: secret <stack> at path /terraform/<environment>. A stack
# without a secrets.example.json has none: {}.
#
# Called by infrastructure/environments/root.hcl from the stack's directory.
# Usage: stack_secrets.sh <environment> <stack>
set -euo pipefail

[[ -f secrets.example.json ]] || { echo '{}'; exit 0; }

scw secret version access-by-path secret-path="/terraform/$1" secret-name="$2" \
  revision=latest_enabled -o json | jq -er '.data | @base64d'
