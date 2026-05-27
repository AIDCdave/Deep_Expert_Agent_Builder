# Azure Trusted Deployment — Configuration Spec

**Date:** 2026-05-27
**Requested by:** DEA Builder coding agent
**Target reader:** Spock (CTO advisor) — for Azure AI Foundry configuration
**Implements:** BRIEF.md §4 Tasks 4.1–4.4
**Refinements:** Spock review 2026-05-27 — Key Vault for CONTENT_SAFETY_KEY, fail-loud env var validation

---

## Overview

The DEA Builder pipeline needs two new Azure resources to implement the trusted/untrusted pipeline architecture from Spock's brief. All three items below are configured in the same Azure subscription and region as the existing GPT-5.5 deployment.

**Existing resource:** `dave-mot32g5b-eastus2` (Azure OpenAI, East US 2)
**Existing endpoint:** `https://dave-mot32g5b-eastus2.cognitiveservices.azure.com`

---

## Item 1: Content Filter Configuration

**Where:** Azure AI Foundry → Azure OpenAI resource → Content filters → + Create content filter

| Field | Value |
|-------|-------|
| **Name** | `aidc-trusted-author-filter` |
| Prompt Shields for direct attacks (jailbreak) | **OFF** |
| Prompt Shields for indirect attacks | Off (default) |
| Hate severity threshold (prompt) | Medium (default) |
| Hate severity threshold (completion) | Medium (default) |
| Violence severity threshold (prompt) | Medium (default) |
| Violence severity threshold (completion) | Medium (default) |
| Sexual severity threshold (prompt) | Medium (default) |
| Sexual severity threshold (completion) | Medium (default) |
| Self-Harm severity threshold (prompt) | Medium (default) |
| Self-Harm severity threshold (completion) | Medium (default) |
| Protected material — text | On (default) |
| Protected material — code | On (default) |

**The only non-default setting is Prompt Shields for direct attacks → OFF.** Everything else stays at platform defaults.

No Limited Access approval is required for this configuration.

**Status:** ✅ CREATED — RAI policy `aidc-trusted-author-filter` with Jailbreak `enabled: false`.

---

## Item 2: Trusted GPT-5.5 Deployment

**Where:** Azure AI Foundry → Azure OpenAI resource → Deployments → + Create new deployment

| Field | Value |
|-------|-------|
| **Deployment name** | `aoai-gpt55-trusted` |
| **Model** | GPT-5.5 (same model as existing deployment) |
| **SKU / capacity** | Same as existing GPT-5.5 deployment |
| **Content filter** | `aidc-trusted-author-filter` (created in Item 1) |

This creates a second GPT-5.5 deployment on the same resource. Same endpoint URL, same API key — the deployment name in the API path is the only difference.

**Env var to add to `~/.zshrc`:**

```bash
export AZURE_OPENAI_TRUSTED_DEPLOYMENT="aoai-gpt55-trusted"
```

If a different deployment name is preferred, set this env var to match. **The pipeline will raise a clear error at startup if this env var is missing or empty** — no silent defaults.

**Status:** ✅ CREATED — deployment `aoai-gpt55-trusted` with `aidc-trusted-author-filter` attached, `provisioningState: Succeeded`.

---

## Item 3: Azure AI Content Safety Resource

**Purpose:** Standalone Prompt Shields API for scanning human-authored input at the Module 1 trust boundary. This is separate from the per-deployment content filters — it's an explicit API call the pipeline makes before any LLM inference.

**Where:** Azure AI Foundry → AI Services → Content Safety → Create (or reuse an existing Content Safety resource in the AIDC subscription)

| Field | Value |
|-------|-------|
| **Resource name** | `aidc-content-safety` (or existing) |
| **Region** | East US 2 (co-locate with the OpenAI resource) |
| **SKU** | S0 (Standard) |

After creation, retrieve the endpoint and key from the resource's Keys and Endpoint page.

**Secret handling (Spock refinement 1):**

- `CONTENT_SAFETY_ENDPOINT` — stored in `~/.zshrc` (endpoint is not sensitive).
- `CONTENT_SAFETY_KEY` — **stored in Azure Key Vault `kv-aidc-eus2`**, secret name `content-safety-key`. The pipeline fetches it at startup using `az keyvault secret show` via the developer's authenticated `az` CLI session. This mirrors the AIDC `fetch-secrets.sh` pattern.
- `CONTENT_SAFETY_KEY` is **NOT** exported in `~/.zshrc` or `.env`.

**Env var to add to `~/.zshrc`:**

```bash
export CONTENT_SAFETY_ENDPOINT="https://aidc-content-safety-ea10c.cognitiveservices.azure.com"
```

**Status:** ✅ CREATED — resource `aidc-content-safety` in East US 2, S0. Key stored in `kv-aidc-eus2` as secret `content-safety-key`.

---

## Pipeline Wiring Summary

```
Human input ──► Module 1 ──────────────────────► Modules 2-6
                  │                                   │
                  ├─ Prompt Shields scan              └─ All LLM calls use
                  │  (Item 3: Content Safety API)        aoai-gpt55-trusted
                  │                                      (Item 2: Shields OFF)
                  └─ LLM calls use default deployment
                     (existing: Shields ON)
```

- **Module 1** scans human input via the Content Safety API (Item 3), then runs normalize/review against the **existing** GPT-5.5 deployment (Shields ON — this is the one module processing human-authored content).
- **Modules 2–6** use `aoai-gpt55-trusted` (Item 2) for all LLM calls. Content is entirely pipeline-generated at this point — no human input, no external documents.

---

## Startup Validation (Spock refinement 2 — fail-loud)

The pipeline validates all required env vars at startup, before any LLM or API call:

| Var / Secret | Source | Validated by | Error if missing |
|---|---|---|---|
| `AZURE_OPENAI_ENDPOINT` | `~/.zshrc` | `llm/client.py:_load_env()` | Clear error with example |
| `AZURE_OPENAI_API_KEY` | `~/.zshrc` | `llm/client.py:_load_env()` | Clear error |
| `AZURE_OPENAI_TRUSTED_DEPLOYMENT` | `~/.zshrc` | `llm/client.py:get_llm(trusted=True)` | "must be set… see spec Item 2" |
| `CONTENT_SAFETY_ENDPOINT` | `~/.zshrc` | `llm/content_safety.py` | "must be set… see spec Item 3" |
| `CONTENT_SAFETY_KEY` | Key Vault `kv-aidc-eus2` | `llm/content_safety.py:_fetch_key_from_vault()` | Clear error with vault/secret names + "az login" hint |

No silent defaults. Missing vars fail at boot, not at first inference.

---

## Validation After Setup

Once all three items are configured and env vars are set, the coding agent will run:

1. `dea-builder dea-context workspaces/Olivia_Park` — Module 1 smoke test (Prompt Shields scan + normalize/review on default deployment)
2. `dea-builder earl workspaces/Olivia_Park` — Module 5 full run (all passes on trusted deployment, full 83K anchor, no workarounds)

**Expected result:** Zero content filter failures on Module 5. Olivia Park's epistemic anchor (1907 lines of "must not" / "never" behavioral rules) passes through without triggering jailbreak detection.

---

## Rollback

Either of these reverses the change within minutes:

1. Edit `aidc-trusted-author-filter` → turn Prompt Shields for direct attacks back ON → save
2. Or set `AZURE_OPENAI_TRUSTED_DEPLOYMENT` back to the existing deployment name

No data migration. No model retraining. No state on disk.
