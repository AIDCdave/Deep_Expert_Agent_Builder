# Spec — Portable Agent Spec output + ADL-as-hub for the LM Target Implementation Expert

**Date:** 2026-05-28
**Version:** 1.2 (1.0 = original PAS + ADL-hub spec; 1.1 adds the OpenAI Responses API target — see §6 and `AMENDMENT-001-openai-responses-target.md`; 1.2 retargets the PAS smoke test to a **local** LiteLLM instance with Azure Key Vault secrets — see `LITELLM-CONNECTION-DETAILS.md`)
**Author:** Spock (Drach's CTO advisor)
**Target reader:** the coding agent maintaining the Deep Expert Agent Builder / LM_Target_Implementation_Expert
**Status:** Approved by Drach 2026-05-28. Implementation hand-off.

---

## 0. What this changes, in one paragraph

The LM_Target_Implementation_Expert today transforms a source agent into five **sibling** target packages (Custom GPT, Claude, Gemma, Hermes, Grok). This spec adds one always-on output — the **Portable Agent Spec (PAS)**, a model-agnostic deployable expressed against the OpenAI Chat Completions contract — and formalizes **ADL (`agent.adl.yaml`) as the canonical hub** every output derives from and is verified against. It also adds **provenance stamping** so derived outputs can be detected as stale when the source moves. It does **not** restructure the five existing target generators in this pass.

**v1.1 amendment:** adds a sixth `--targets` output, **`openai_responses/`** — the OpenAI Responses API execution payload — parallel to `claude/`, `gemma-4/`, `hermes/`, and `grok/`. This is distinct from the hosted `chatgpt_custom_gpt/` Builder package and from the model-agnostic PAS. See §6.

---

## 1. Background and the layer model (why this design)

Three distinct layers were separated during design. The coding agent must hold them apart:

1. **Harness packaging (Layer 1)** — the file structure a runtime expects. Custom GPT (system prompt + Actions panel + toggles), Hermes (SOUL/prompt + config.yaml + provider manifest), Claude (XML-segmented prompt + tool-use), Gemma, Grok. **Always requires a distinct package.** This is what the five target generators already do.
2. **Model swap behind one harness via LiteLLM (Layer 2)** — within a LiteLLM-fronted harness, swapping the underlying model (a small/general/reasoning lane) requires **no agent rewrite**. The agent definition is identical; only the LiteLLM alias changes. This layer is a *runtime deployment knob, not a Builder output.*
3. **Model-specific content optimization (Layer 3)** — tuning prompt content to a specific model's strengths. Optional. Only meaningful for **model-bound** targets (Custom GPT is locked to GPT; **OpenAI Responses is locked to an OpenAI model**; Claude Projects to Claude; raw Gemma/Grok), because LiteLLM-fronted targets resolve the model dimension at runtime.

**Consequence for the target axis:** a "target" is a *harness packaging format*, not a model. Do not generate per-model variants of a LiteLLM-frontable target. One Hermes package, model chosen at deploy time.

---

## 2. Canonical hub: ADL

`agent.adl.yaml` is the **single source of truth** — the semantic contract. It already is the expert's highest source authority (repository ADL governs over live builder state). This spec formalizes that role:

- Every generated output (the five targets + the new PAS) is an **implementation of the ADL contract** and must be verifiable back against it.
- The expert already builds a "normalized agent model" internally (workflow step 8) before target mapping. **ADL is the serialized, canonical form of that normalized model.** Do not introduce a second canonical format.
- **ADL version pinning:** every `agent.adl.yaml` must carry `adl_version: <IETF-draft-NN>` in its top-level metadata. Generators read it, and every derived output records which `adl_version` it was generated against (see §5 provenance). If a source ADL lacks `adl_version`, emit a warning and stamp `adl_version: UNKNOWN` downstream — do not guess.

Do **not** replace ADL with the PAS. They are different layers: ADL is the blueprint (authority); PAS is a runnable rendering (implementation).

---

## 3. New output: the Portable Agent Spec (PAS)

### 3.1 What it is

A **model-agnostic, directly deployable** rendering of the agent expressed against the **OpenAI Chat Completions contract** (the lingua franca that LiteLLM and OpenRouter normalize every provider to). It carries **no model or provider binding** — the model is selected at deploy time via a LiteLLM alias. This is what makes it portable: hand it to LiteLLM, OpenRouter, or any OpenAI-compatible gateway and run it against any backend model without repackaging.

### 3.2 It is always produced

The PAS is a **default, always-on output** of every transformation run, regardless of which platform targets are requested. Rationale: it is the lowest-common-denominator deployable, it maps directly to the LiteLLM execution path AIDC already runs, and it answers "deploy this against a model we have not named yet" with zero additional work.

### 3.3 PAS file layout

Emit a `portable_agent_spec/` directory:

```
portable_agent_spec/
├── pas.yaml            # metadata + tool schemas + knowledge manifest + param defaults + provenance
├── system_prompt.md    # the model-neutral system prompt (full body)
└── README.md           # how to deploy via LiteLLM / any OpenAI-compatible gateway
```

### 3.4 `pas.yaml` shape

```yaml
pas_version: "1.0"
provenance:
  source_adl_file: <path to agent.adl.yaml>
  adl_version: <IETF-draft-NN | UNKNOWN>
  source_hash: <sha256 of the ADL file>
  generated_at: <ISO-8601 UTC>
  generator: LM_Target_Implementation_Expert
agent:
  name: <string>
  system_prompt_file: system_prompt.md
  tools:                          # OpenAI function-calling JSON-schema format
    - type: function
      function:
        name: <string>
        description: <string>
        parameters: { <JSON Schema> }
      source_action_reference: <string | null>
      auth:
        method: NONE | API_KEY | OAUTH | BEARER_TOKEN | BASIC | OTHER | UNKNOWN
        required_environment_variables: []
        store_secret_in_repo: false
      live_enabled: true | false
      forward_contract: true | false
  knowledge_manifest:             # how knowledge is loaded — PAS does not claim auto-attach
    - source_file: <string>
      loading: RETRIEVAL | PROMPT_INJECTION | RUNTIME_CONFIG | UNSUPPORTED | UNKNOWN
  model_defaults:                 # deployment knobs, NOT agent identity
    temperature: <number | null>
    max_tokens: <number | null>
  # NO `model:` and NO `provider:` field. Model binding happens at deploy time
  # via the LiteLLM alias. Including one here would defeat portability.
```

### 3.5 PAS rules (inherit the expert's existing doctrine)

- **Source fidelity:** the PAS preserves role, scope, persona, constraints, tool boundaries, knowledge references, eval intent. No creative expansion.
- **Tool format:** OpenAI function-calling JSON schema. Preserve required/optional params, auth method, allowed/prohibited operations. Do not widen boundaries.
- **Secrets:** never inline. Externalize to env-var placeholders; `store_secret_in_repo: false`.
- **Forward contracts:** unavailable/unverified tools → `live_enabled: false`, `forward_contract: true`.
- **Knowledge:** the PAS does **not** claim automatic knowledge attachment. The manifest records intended loading method only.

---

## 4. CLI / input surface (keep it minimal)

Three inputs. Do not add more.

| Input | Required | Description |
|-------|----------|-------------|
| `--source` | yes | Source agent root directory. Generators read `agent.adl.yaml` as authority; fall back to the documented source-artifact convention if ADL absent (emit warning). |
| `--targets` | no | Comma-separated platform targets at **concrete-model granularity** where model-bound (e.g. `claude-opus-4-6,gemma-4,grok`). LiteLLM-frontable targets named at harness level (e.g. `hermes`). If omitted, only the PAS is produced. |
| `--output` | no | Output root directory. Defaults to `<source>/_targets/`. Keeps derived outputs physically separate from the source tree. |

The PAS is always produced regardless of `--targets`. `--targets` adds platform spokes on top.

---

## 5. Output directory structure + provenance

```
<output-root>/
├── portable_agent_spec/     # always produced (§3)
├── chatgpt_custom_gpt/      # if requested
├── claude/                  # if requested (model-bound → Layer 3 optimization applies)
├── gemma-4/                 # if requested
├── hermes/                  # if requested (LiteLLM-fronted → ONE package, no per-model variants)
├── grok/                    # if requested
└── openai_responses/        # if requested (model-bound OpenAI Responses API payload — §6)
```

**Provenance stamping (new, required for every output including the five existing targets):** each generated package must carry, in its top-level metadata file, the source provenance block:

```yaml
provenance:
  source_adl_file: <path>
  adl_version: <IETF-draft-NN | UNKNOWN>
  source_hash: <sha256 of the ADL file>
  generated_at: <ISO-8601 UTC>
```

This makes staleness detectable: if the source ADL's current hash differs from the `source_hash` recorded in a derived package, that package is stale and needs regeneration. Cheap at generation time, expensive to retrofit — do it now.

---

## 6. OpenAI Responses API target (added v1.1)

### 6.1 Why this exists

The OpenAI **Assistants API is deprecated and sunsets 2026-08-26**; its official successor is the **Responses API** (`responses.create`). Verified 2026-05-28 against developers.openai.com and OpenAI's deprecation notice. AIDC's batch pipeline against GPT-5.5 packages and sends the agent specification on every call — which is exactly the stateless `responses.create` pattern. This target produces that execution payload.

`openai_responses/` is a **separate target directory, parallel to `claude/`, `gemma-4/`, `hermes/`, and `grok/`** — one of the `--targets` outputs. It is distinct from two neighbors that must not be conflated with it:

- **`chatgpt_custom_gpt/`** is the hosted ChatGPT Builder product (Actions panel, conversation starters, capability toggles; deployed in the ChatGPT UI; no per-call packaging). Keep it as is.
- **`portable_agent_spec/` (PAS)** is the model-agnostic Chat Completions deployable (no model binding; portable across providers via LiteLLM). **Leave it unchanged** — it remains the generalized OpenAI-standard spec for use with OpenAI or any other provider that speaks that standard.

`openai_responses/` is a **model-bound** target (locked to an OpenAI model), so Layer 3 content optimization applies — same class as Custom GPT, Claude, raw Gemma, raw Grok.

### 6.2 File layout

```
openai_responses/
├── system_prompt.md          # the `instructions` field body (may carry OpenAI-specific Layer 3 tuning)
├── responses_request.yaml    # the responses.create envelope: model + instructions ref + tools + params
├── tools.yaml                # OpenAI function + hosted-tool definitions (if source tools/capabilities exist)
├── knowledge_manifest.yaml   # knowledge mapping (file_search vs retrieval vs prompt injection)
└── README.md                 # how to execute via responses.create, stateless batch pattern
```

### 6.3 `responses_request.yaml` shape

```yaml
provenance:                            # same block as every other output (§5)
  source_adl_file: <path>
  adl_version: <IETF-draft-NN | UNKNOWN>
  source_hash: <sha256>
  generated_at: <ISO-8601 UTC>
responses_request:
  model: <openai-model, e.g. gpt-5.5>  # REQUIRED — this IS a model-bound target (unlike PAS)
  instructions_file: system_prompt.md  # maps to the Responses `instructions` field
  tools: <ref to tools.yaml>           # function defs + hosted tools
  tool_choice: auto | none | required | <named>
  store: false                         # stateless batch default — no server-side persistence
  # NO `conversation:` by default — the batch pattern packages and sends each call.
  # Add a conversation reference only if a stateful deployment is explicitly required.
  text:
    format: <text | json_schema | ...> # only if the source declares an output contract
  reasoning:                           # only for reasoning-class OpenAI models
    effort: <minimal | low | medium | high | null>
  temperature: <number | null>
  max_output_tokens: <number | null>
```

### 6.4 Hosted-tool mapping

Custom GPT capability toggles map to Responses API hosted tools:

| Source capability | Responses API tool |
|-------------------|--------------------|
| Web search | `web_search` |
| Code interpreter | `code_interpreter` |
| Knowledge / file retrieval | `file_search` |

Map only capabilities the source actually declares. Do not enable a hosted tool the source did not have — that widens scope (No Creative Expansion Rule).

### 6.5 Rules (inherit existing doctrine)

- Source fidelity preserved; no creative expansion; tool boundaries preserved.
- Secrets externalized; `store_secret_in_repo: false`.
- Forward contracts disabled (`live_enabled: false`).
- Provenance block required (§5).
- Because this target is model-bound, OpenAI-specific Layer 3 prompt tuning is permitted in `system_prompt.md`, but it must not alter role/scope/constraints — only phrasing/structure for the OpenAI model.

---

## 7. Scope of THIS pass (explicit, to prevent gold-plating)

**In scope:**
1. Add the always-on **PAS output** (§3).
2. Formalize **ADL as canonical authority** + `adl_version` pinning (§2).
3. Add **provenance stamping** to every output, including the five existing targets (§5).
4. Add the three-input CLI surface if not already present (§4).
5. Add the **OpenAI Responses API target** (`openai_responses/`) as a new `--targets` output, parallel to the other platform targets (§6).

**Out of scope (do NOT do in this pass):**
- Do **not** restructure the five existing target generators into a formal hub-and-spoke pipeline. They work today. The conceptual model is hub-and-spoke (ADL hub, targets+PAS as spokes), but the refactor that makes each target literally derive from a shared serialized PAS is a **follow-on**, not this pass. Surgical changes only.
- Do **not** generate per-model variants of LiteLLM-fronted targets (Hermes). One package; model set at runtime.
- Do **not** create a second canonical format alongside ADL.
- Do **not** widen the CLI beyond the three inputs.

---

## 8. Acceptance criteria

1. Running the transformer with `--source <agent>` and no `--targets` produces a complete, valid `portable_agent_spec/` directory and nothing else under the output root.
2. The generated `pas.yaml` contains **no** `model:` or `provider:` field, and its `system_prompt.md` is model-neutral (no Claude-specific XML scaffolding, no GPT-specific Actions references).
3. The PAS, pointed at a LiteLLM endpoint with any backend alias, executes and produces a coherent response consistent with the source agent's role. (Smoke test against a **local** LiteLLM instance on the MacBook Pro with secrets from Azure Key Vault — see `LITELLM-CONNECTION-DETAILS.md`; default alias `general`.)
4. Every generated package — PAS and any requested platform target — carries a `provenance` block with `source_hash` and `adl_version`.
5. Re-running after an unrelated edit to the source ADL produces a different `source_hash`, demonstrating staleness is detectable.
6. Requesting `--targets hermes` produces exactly one Hermes package (no nano/general/reasoning variants).
7. Source fidelity check passes: every output's role/scope/constraints/tool-boundaries/knowledge/eval-intent match the ADL contract; secrets externalized; forward contracts disabled.
8. Requesting `--targets openai-responses` produces an `openai_responses/` package, parallel to the other target dirs (NOT merged into `chatgpt_custom_gpt/`, NOT a `model:`-less PAS), whose `responses_request.yaml` sets a concrete OpenAI `model`, `store: false`, and no `conversation` by default. Hosted-tool toggles present in the source map to `web_search` / `code_interpreter` / `file_search`; none are invented.

---

## 9. Relationship to the existing expert

The expert at `LM_Target_Implementation_Expert` already encodes the right doctrine ("the source agent specification is a semantic contract; target artifacts are implementations of that contract") and already builds a normalized agent model internally. This spec:

- **Reuses** that normalized model as the basis for the PAS (serialize it to the OpenAI contract).
- **Names** ADL as the canonical serialization of that model.
- **Adds** the PAS as a first-class always-on output.
- **Adds** provenance stamping across all outputs.

It does not rewrite the expert's doctrine, constraints, or the five existing target generators.

---

## 10. References (for the coding agent)

- Expert system prompt and knowledge files: `LM_Target_Implementation_Expert/05_earl/output/chatgpt_custom_gpt/` (system prompt, `03_knowledge/04_TOOL_ACTION_FUNCTION_TRANSLATION.md`, `08_HERMES_GROK_RUNTIME_AND_PROVIDER_IMPLEMENTATION.md` are most relevant to PAS and Responses shape)
- OpenAI Chat Completions contract = the normalization target for LiteLLM and OpenRouter; the PAS tool format follows OpenAI function-calling JSON schema
- OpenAI Responses API reference: developers.openai.com/api/reference/resources/responses (`responses.create`, `conversations` for optional state). Assistants API deprecation + sunset 2026-08-26: OpenAI deprecation notice + migration guide to Responses
- **Local LiteLLM setup + Azure Key Vault secret handling** (for the §8.3 smoke test): `LITELLM-CONNECTION-DETAILS.md` (this directory). Local instance on the MacBook Pro, not the paperh remote Funnel.
- Companion amendment doc: `AMENDMENT-001-openai-responses-target.md` (this directory) — the standalone delta for hand-off
