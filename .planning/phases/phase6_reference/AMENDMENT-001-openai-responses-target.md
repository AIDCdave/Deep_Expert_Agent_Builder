# Amendment 001 — Add the OpenAI Responses API target

**Date:** 2026-05-28
**Author:** Spock (Drach's CTO advisor)
**Amends:** `SPEC.md` (Portable Agent Spec + ADL-as-hub) — rolls it from **v1.0 → v1.1**
**Target reader:** the coding agent maintaining the LM_Target_Implementation_Expert
**Status:** Approved by Drach 2026-05-28.

This is a **self-contained delta**. You can implement it without re-reading the full SPEC, though §6 of SPEC v1.1 now carries the same content in context.

---

## 1. What changes, in one line

Add a sixth `--targets` output, **`openai_responses/`** — the OpenAI Responses API execution payload — as a directory **parallel to `claude/`, `gemma-4/`, `hermes/`, and `grok/`**. Nothing else in the pipeline changes.

## 2. Why

Verified against live docs on 2026-05-28:

- The OpenAI **Assistants API is deprecated and sunsets 2026-08-26**. Its official successor is the **Responses API** (`responses.create`). (OpenAI deprecation notice + Assistants→Responses migration guide; developers.openai.com/api/reference/resources/responses.)
- AIDC's batch pipeline executes against GPT-5.5 by **packaging and sending the full agent specification on every call** — which is precisely the stateless `responses.create` pattern (no server-side thread, `store: false`, no `conversation`).
- The pipeline therefore needs a first-class **Responses API** execution artifact. The existing `chatgpt_custom_gpt/` target is the *hosted Builder product* (Actions panel, UI deployment) — not the programmatic batch form. They are different surfaces of OpenAI and must be separate outputs.

## 3. What does NOT change (guard rails)

- **PAS (`portable_agent_spec/`) is untouched.** It stays the model-agnostic Chat Completions deployable — no model binding, portable across providers via LiteLLM. It is the generalized OpenAI-standard spec usable with OpenAI *or any other provider speaking that standard*. Do **not** fold Responses concepts into it.
- **`chatgpt_custom_gpt/` is untouched.** It remains the hosted ChatGPT Builder package.
- **ADL stays the canonical hub.** The Responses target is one more derivation of the ADL contract, verified back against it like every other output.
- **CLI surface stays three inputs** (`--source`, `--targets`, `--output`). `openai-responses` is just a new value accepted in `--targets`.

## 4. The new target: `openai_responses/`

### 4.1 Classification

- A **model-bound** target (locked to a specific OpenAI model). Layer 3 (OpenAI-specific content optimization) applies — same class as Custom GPT, Claude, raw Gemma, raw Grok. It is NOT LiteLLM-fronted, so it carries an explicit `model`.
- Produced **only when requested** via `--targets ...,openai-responses`. (Unlike the PAS, which is always produced.)

### 4.2 Directory layout

```
openai_responses/
├── system_prompt.md          # the `instructions` field body (OpenAI-specific Layer 3 tuning permitted)
├── responses_request.yaml    # the responses.create envelope
├── tools.yaml                # OpenAI function + hosted-tool definitions (if source tools/capabilities exist)
├── knowledge_manifest.yaml   # knowledge mapping (file_search vs retrieval vs prompt injection)
└── README.md                 # how to execute via responses.create, stateless batch pattern
```

### 4.3 `responses_request.yaml` shape

```yaml
provenance:                            # identical block to every other output
  source_adl_file: <path>
  adl_version: <IETF-draft-NN | UNKNOWN>
  source_hash: <sha256 of the ADL file>
  generated_at: <ISO-8601 UTC>
responses_request:
  model: <openai-model, e.g. gpt-5.5>  # REQUIRED — model-bound target (this is the key contrast with PAS)
  instructions_file: system_prompt.md  # maps to the Responses `instructions` field
  tools: <ref to tools.yaml>           # function defs + hosted tools
  tool_choice: auto | none | required | <named>
  store: false                         # stateless batch default — no server-side persistence
  # NO `conversation:` by default. The batch pattern packages and sends each call.
  # Add a conversation reference ONLY if a stateful deployment is explicitly required.
  text:
    format: <text | json_schema | ...> # only if the source declares an output contract
  reasoning:                           # only for reasoning-class OpenAI models
    effort: <minimal | low | medium | high | null>
  temperature: <number | null>
  max_output_tokens: <number | null>
```

### 4.4 Hosted-tool mapping

Map source capabilities to Responses hosted tools — and ONLY those the source actually declares:

| Source capability | Responses API tool |
|-------------------|--------------------|
| Web search | `web_search` |
| Code interpreter | `code_interpreter` |
| Knowledge / file retrieval | `file_search` |

Do not enable a hosted tool the source did not have (No Creative Expansion Rule).

### 4.5 Rules (inherited)

- Source fidelity preserved; tool boundaries preserved; no creative expansion.
- Secrets externalized (`store_secret_in_repo: false`); forward contracts disabled (`live_enabled: false`).
- Provenance block required.
- Layer 3 tuning in `system_prompt.md` may adjust phrasing/structure for the OpenAI model but must not alter role, scope, or constraints.

## 5. Acceptance criterion (delta)

Requesting `--targets openai-responses` produces an `openai_responses/` directory **parallel to** the other target dirs (not merged into `chatgpt_custom_gpt/`, not a `model:`-less PAS), whose `responses_request.yaml`:

- sets a concrete OpenAI `model`,
- sets `store: false` and includes no `conversation` by default,
- carries the standard `provenance` block,
- and whose hosted-tool entries (if any) map 1:1 from source capabilities to `web_search` / `code_interpreter` / `file_search` with none invented.

All pre-existing acceptance criteria from SPEC v1.0 continue to hold unchanged.

## 6. Implementation note

The Responses payload is close to the PAS shape — `instructions` ≈ PAS system prompt, `tools` ≈ PAS tool schemas. The cleanest implementation renders `openai_responses/` from the same normalized agent model the PAS uses, then (a) binds a concrete OpenAI `model`, (b) wraps tools/instructions in the Responses envelope, and (c) maps capabilities to hosted tools. Reuse, do not re-derive.
