# LiteLLM connection details — LOCAL instance + Azure Key Vault (for the PAS smoke test, SPEC §8.3)

**Date:** 2026-05-28 (revised — supersedes the earlier paperh-Funnel version)
**Author:** Spock (Drach's CTO advisor)
**For:** the coding agent running the Portable Agent Spec smoke test from the agent builder on Wyatt (MacBook Pro)
**Verified:** 2026-05-28 — model mappings, env-var names, and `api_version` pulled live from the paperh LiteLLM config (keys redacted). The local config below mirrors that proven config exactly.

---

## 0. Decision

Do **not** call the remote paperh LiteLLM Funnel. Run **LiteLLM locally on the MacBook Pro**, expose the OpenAI-compatible API on `localhost`, and have the agent builder call it natively. All secrets come from **Azure Key Vault (`kv-aidc-eus2`)** — never inline, never committed.

This is the same LiteLLM stack paperh runs; the only differences are (a) it runs locally and (b) secrets are fetched from Key Vault at startup rather than living in the container env.

---

## 1. Install and run LiteLLM locally

Native Python install in a virtualenv (matches the agent-builder stack; no Docker needed):

```bash
# from the agent builder root, in (or alongside) its venv
python3 -m venv .litellm-venv
source .litellm-venv/bin/activate
pip install 'litellm[proxy]'
# Pin the installed version for reproducibility:
pip freeze | grep -i litellm    # record this in the repo's requirements/notes
```

Run it (after secrets are exported — see §4):

```bash
litellm --config ./litellm.config.yaml --port 4000
```

**Health check (no auth):**

```bash
curl -s http://localhost:4000/health/liveliness    # expect: {"status":"alive"}
```

The OpenAI-compatible API is then at **`http://localhost:4000/v1`**.

## 2. Local `litellm.config.yaml` (mirrors paperh; keys via env)

Commit this file — it contains **only env-var references, no secrets**:

```yaml
model_list:
  - model_name: worker-bee
    litellm_params:
      model: azure/gpt-5.4-nano
      api_base: os.environ/AOAI_ENDPOINT
      api_key: os.environ/AOAI_API_KEY
      api_version: "2024-12-01-preview"
  - model_name: general
    litellm_params:
      model: azure/grok-4-1-fast-non-reasoning
      api_base: os.environ/AOAI_ENDPOINT
      api_key: os.environ/AOAI_API_KEY
      api_version: "2024-12-01-preview"
  - model_name: reasoning
    litellm_params:
      model: azure/gpt-5.5
      api_base: os.environ/AOAI_ENDPOINT
      api_key: os.environ/AOAI_API_KEY
      api_version: "2024-12-01-preview"
  - model_name: grok-reasoning
    litellm_params:
      model: azure/grok-4-20-reasoning
      api_base: os.environ/AOAI_ENDPOINT
      api_key: os.environ/AOAI_API_KEY
      api_version: "2024-12-01-preview"
  - model_name: claude-opus
    litellm_params:
      model: anthropic/claude-opus-4-7
      api_key: os.environ/ANTHROPIC_API_KEY
  - model_name: claude-sonnet
    litellm_params:
      model: anthropic/claude-sonnet-4-6
      api_key: os.environ/ANTHROPIC_API_KEY
  - model_name: claude-haiku
    litellm_params:
      model: anthropic/claude-haiku-4-5
      api_key: os.environ/ANTHROPIC_API_KEY
  - model_name: embedding-3-large
    litellm_params:
      model: azure/text-embedding-3-large
      api_base: os.environ/AOAI_ENDPOINT
      api_key: os.environ/AOAI_API_KEY
      api_version: "2024-12-01-preview"

general_settings:
  master_key: os.environ/LITELLM_MASTER_KEY
```

**Aliases (8):** `worker-bee`, `general`, `reasoning`, `grok-reasoning`, `claude-opus`, `claude-sonnet`, `claude-haiku`, `embedding-3-large`. The PAS smoke test uses **`general`**.

Note: the PAS smoke test only exercises the Azure path (`AOAI_*`). **For the smoke test, omit the three `claude-*` model blocks** — the Anthropic secret is deferred and not in the vault yet, and leaving the blocks in with `ANTHROPIC_API_KEY` unset can fail proxy startup. Add the `claude-*` blocks (and the `anthropic-api-key` secret) back only when you actually need the Claude aliases.

## 3. Point the agent builder at the local endpoint

| Setting | Value |
|---|---|
| Base URL | `http://localhost:4000/v1` |
| Auth | bearer `LITELLM_MASTER_KEY` (from Key Vault) |
| Default alias for PAS smoke test | `general` |

Configure the agent builder's model client (OpenAI SDK or HTTP) with `base_url=http://localhost:4000/v1` and `api_key=$LITELLM_MASTER_KEY`. The agent builder code knows where its model-client config lives; this is the only change — endpoint + key source.

## 4. Secrets via Azure Key Vault (`kv-aidc-eus2`)

### 4.1 Secrets to store

| KV secret name | Holds | Needed for smoke test? |
|---|---|---|
| `litellm-master-key` | the local proxy's auth key (generate a fresh value; does not have to match paperh) | yes |
| `aoai-api-key` | Azure OpenAI API key (backend for Azure aliases) | yes |
| `anthropic-api-key` | Anthropic API key (backend for `claude-*` aliases) | only if calling Claude aliases |

Non-secret config — set directly, NOT in Key Vault: `AOAI_ENDPOINT` = the AIDC Azure OpenAI resource endpoint (e.g. `https://<resource>.cognitiveservices.azure.com`). If you do not have the exact value, retrieve it for parity from paperh: `ssh root@100.116.218.110 "docker exec aidc-litellm printenv AOAI_ENDPOINT"` (this is a URL, not a secret).

### 4.2 Required Key Vault permissions

`kv-aidc-eus2` (RBAC model assumed):

- **Runtime fetch (the coding agent, via Drach's `az login` session):** `Key Vault Secrets User` on the vault. Read-only. This is the minimal role — do NOT grant Contributor or Secrets Officer to the runtime identity.
- **Creating the secrets (Drach, one-time, out-of-band):** `Key Vault Secrets Officer` (or `set` permission under the access-policy model).

If the vault uses the legacy access-policy model instead of RBAC: runtime needs `get` (and `list`); creation needs `set`.

### 4.3 Create the secrets (Drach, out-of-band — real values never in repo/chat)

```bash
az keyvault secret set --vault-name kv-aidc-eus2 --name litellm-master-key --value '<generate-a-strong-key>'
az keyvault secret set --vault-name kv-aidc-eus2 --name aoai-api-key       --value '<azure-openai-key>'
az keyvault secret set --vault-name kv-aidc-eus2 --name anthropic-api-key  --value '<anthropic-key>'   # only if using Claude aliases
```

### 4.4 Fetch at runtime and inject as env vars (do NOT embed values)

Startup wrapper — fetches from KV, exports to env, launches the proxy. Secret values exist only in process memory, never written to disk:

```bash
#!/usr/bin/env bash
set -euo pipefail
VAULT="kv-aidc-eus2"

# Non-secret config (the AIDC Azure OpenAI resource — confirmed 2026-05-28):
export AOAI_ENDPOINT="https://dave-mot32g5b-eastus2.cognitiveservices.azure.com"

# Secrets from Key Vault (requires an active `az login` with read access on the vault; Drach holds Secrets Officer):
export LITELLM_MASTER_KEY="$(az keyvault secret show --vault-name "$VAULT" --name litellm-master-key --query value -o tsv)"
export AOAI_API_KEY="$(az keyvault secret show --vault-name "$VAULT" --name aoai-api-key --query value -o tsv)"
# ANTHROPIC_API_KEY is DEFERRED — the secret is not yet in the vault. Add it and uncomment ONLY when using claude-* aliases:
# export ANTHROPIC_API_KEY="$(az keyvault secret show --vault-name "$VAULT" --name anthropic-api-key --query value -o tsv)"

litellm --config ./litellm.config.yaml --port 4000
```

The two secrets above (`litellm-master-key`, `aoai-api-key`) are stored and verified in `kv-aidc-eus2` as of 2026-05-28. `AOAI_ENDPOINT` is set directly (it is a URL, not a secret).

The agent builder, when it calls the local endpoint, reads `LITELLM_MASTER_KEY` from the same env (export it in the builder's shell the same way, or have the builder fetch it via the Azure SDK `azure-keyvault-secrets` + `DefaultAzureCredential` at startup).

## 5. PAS smoke test (validates SPEC §8.3)

**curl** (uses `jq` to safely embed the system prompt):

```bash
curl -sS http://localhost:4000/v1/chat/completions \
  -H "Authorization: Bearer ${LITELLM_MASTER_KEY}" \
  -H "Content-Type: application/json" \
  -d "$(jq -n --rawfile sp portable_agent_spec/system_prompt.md \
        '{model:"general",messages:[{role:"system",content:$sp},{role:"user",content:"Briefly state your role and what you are designed to do."}]}')"
```

**Python (OpenAI SDK) — preferred, since the PAS is OpenAI-contract:**

```python
from openai import OpenAI
import os

client = OpenAI(
    base_url="http://localhost:4000/v1",
    api_key=os.environ["LITELLM_MASTER_KEY"],
)

system_prompt = open("portable_agent_spec/system_prompt.md").read()
resp = client.chat.completions.create(
    model="general",
    messages=[
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": "Briefly state your role and what you are designed to do."},
    ],
)
print(resp.choices[0].message.content)
```

**Pass condition:** a coherent response consistent with the source agent's role. If `general` returns empty content (the Grok lane has shown this intermittently on paperh), rerun against `reasoning` (GPT-5.5) to confirm it is a model-lane quirk and not a PAS defect.

## 6. PAS vs. `openai_responses` — different contracts, different tests

| Artifact | Contract | Where to test | How |
|---|---|---|---|
| **PAS** (`portable_agent_spec/`) | OpenAI **Chat Completions** (portability floor) | **Local LiteLLM** `http://localhost:4000/v1/chat/completions`, alias `general` | §5 recipe |
| **`openai_responses/`** | OpenAI **Responses API** (model-bound) | **OpenAI Responses endpoint directly** — `https://api.openai.com/v1/responses` with an OpenAI key, model = the one pinned in `responses_request.yaml` | build the `responses.create` call from `responses_request.yaml` + `system_prompt.md`; expect a coherent in-role response |

The PAS test proves portability through the local proxy. The `openai_responses` test proves the model-bound Responses payload against OpenAI itself. Do not try to validate `openai_responses` through the local LiteLLM unless you have first confirmed the pinned LiteLLM version proxies `/v1/responses` — the authoritative target is OpenAI's Responses endpoint, since that is the real deployment surface. (If you do validate `openai_responses`, add an `openai-api-key` secret to Key Vault and fetch it the same way as §4.)

## 7. Security (non-negotiable)

- **No secrets in the repo.** The committed artifacts are `litellm.config.yaml` (env refs only) and the startup wrapper (az fetch commands + the non-secret endpoint). Secret *values* never touch disk or git.
- **Key Vault access is out-of-band.** Drach runs `az login` to establish the session the coding agent uses, and grants Drach's identity `Key Vault Secrets User` on `kv-aidc-eus2`. The coding agent never holds long-lived Azure credentials — it inherits the authenticated `az` session.
- **Do not echo secrets into logs** the smoke test or wrapper writes.
- If the startup wrapper hardcodes the `AOAI_ENDPOINT` URL, that is fine (not a secret), but consider gitignoring the wrapper anyway to avoid accidental future secret additions.
