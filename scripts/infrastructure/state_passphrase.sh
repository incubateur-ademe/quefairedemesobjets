#!/usr/bin/env bash
# Prints the passphrase that encrypts the OpenTofu states and plans of an
# environment: secret state-passphrase at path /terraform/<environment> in
# Scaleway Secret Manager. Prints nothing for the preview stacks, whose
# states are not encrypted.
#
# Called by infrastructure/environments/root.hcl.
# Usage: state_passphrase.sh <environment>
set -euo pipefail

[[ $1 == preprod || $1 == prod ]] || exit 0

scw secret version access-by-path secret-path="/terraform/$1" secret-name=state-passphrase \
  revision=latest_enabled -o json | jq -ej '.data | @base64d'
