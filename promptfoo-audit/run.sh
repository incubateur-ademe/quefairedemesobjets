#!/usr/bin/env bash
# Lance l'audit promptfoo.
# Les clés API sont lues depuis le fichier .env (à créer à partir de .env.example)
#   ANTHROPIC_KEY : https://console.anthropic.com/
#   MISTRAL_API_KEY : https://console.mistral.ai/api-keys/
#   GOOGLE_API_KEY : https://aistudio.google.com/apikey
#   DEEPSEEK_API_KEY : https://platform.deepseek.com/api_keys
set -euo pipefail
cd "$(dirname "$0")"

# Charger .env s'il existe
if [ -f .env ]; then
  set -a
  source .env
  set +a
fi

for key in ANTHROPIC_KEY MISTRAL_API_KEY GOOGLE_API_KEY DEEPSEEK_API_KEY; do
  if [ -z "${!key:-}" ]; then
    echo "⚠️  $key manquante : créez un fichier .env ou exportez-la" >&2
  fi
done

export PROMPTFOO_DISABLE_TELEMETRY=1
promptfoo eval -c promptfooconfig.yaml --output results.json "$@"
echo "Résultats : promptfoo view → http://localhost:15500"
