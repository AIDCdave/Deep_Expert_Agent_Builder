#!/usr/bin/env bash
# Start LiteLLM proxy for PAS smoke testing.
# Fetches secrets from Azure Key Vault (kv-aidc-eus2) before launching.
set -euo pipefail

VAULT="kv-aidc-eus2"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
CONFIG="$PROJECT_ROOT/litellm.config.yaml"

echo "==> Fetching secrets from Azure Key Vault ($VAULT)..."
export LITELLM_MASTER_KEY=$(az keyvault secret show --vault-name "$VAULT" --name litellm-master-key --query value -o tsv)
export AZURE_OPENAI_API_KEY=$(az keyvault secret show --vault-name "$VAULT" --name aoai-api-key --query value -o tsv)

# AZURE_OPENAI_ENDPOINT should already be in ~/.zshrc
if [ -z "${AZURE_OPENAI_ENDPOINT:-}" ]; then
    echo "ERROR: AZURE_OPENAI_ENDPOINT is not set. Add it to ~/.zshrc or export it."
    exit 1
fi

echo "==> Starting LiteLLM proxy on port 4000..."
echo "    Config: $CONFIG"
echo "    Model alias: general -> azure/aoai-gpt55-trusted"
echo ""
echo "    Test with:"
echo "      curl http://localhost:4000/v1/chat/completions \\"
echo "        -H 'Content-Type: application/json' \\"
echo "        -H 'Authorization: Bearer <LITELLM_MASTER_KEY>' \\"
echo "        -d '{\"model\": \"general\", \"messages\": [{\"role\": \"system\", \"content\": \"You are helpful.\"}, {\"role\": \"user\", \"content\": \"Hello\"}]}'"
echo ""

litellm --config "$CONFIG" --port 4000
