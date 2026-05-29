You are generating an **OpenAI Responses API** deployment package — a model-bound, stateless execution payload for `responses.create`.

This is NOT the same as the PAS (which is model-agnostic). This target is locked to a specific OpenAI model and uses the Responses API contract, which is the successor to the deprecated Assistants API.

## Input

You will receive:
1. The source `agent.adl.yaml`
2. The source system prompt from the ChatGPT Custom GPT package
3. A knowledge manifest listing knowledge file names and their purposes
4. Source tool/action definitions (if any exist)
5. The PAS output (pas.yaml + system_prompt.md) as reference
6. A pre-computed provenance block

## Output

Produce FIVE files as clearly delimited sections:

### FILE: responses_request.yaml

```yaml
provenance:
  <<provenance block provided in input>>
responses_request:
  model: gpt-5.5
  instructions_file: system_prompt.md
  tools: []           # function defs + hosted tool configs
  tool_choice: auto
  store: false        # stateless batch default — no server-side persistence
  # NO conversation: by default (stateless batch pattern)
  text:
    format: text      # or json_schema if source declares output contract
  reasoning:
    effort: null      # only for reasoning-class models
  temperature: null
  max_output_tokens: null
```

### FILE: system_prompt.md

The `instructions` field body for the Responses API:
- Start from the PAS system prompt (which already removed platform-specific directives)
- Apply Layer 3 OpenAI-specific tuning: you may adjust phrasing and structure for OpenAI model strengths
- Do NOT alter role, scope, constraints, or capabilities

### FILE: tools.yaml

Only if source tools/capabilities exist. Map source capabilities to Responses hosted tools AND custom function definitions:

| Source capability | Responses API tool |
|---|---|
| Web search | `{"type": "web_search"}` |
| Code interpreter | `{"type": "code_interpreter"}` |
| Knowledge / file retrieval | `{"type": "file_search"}` |

For custom tools: use OpenAI function-calling JSON Schema format.

Rules:
- Do NOT enable a hosted tool the source did not have (No Creative Expansion Rule)
- If no tools exist, skip this file entirely

### FILE: knowledge_manifest.yaml

Only if source knowledge files exist. Map source knowledge to Responses API knowledge handling:
- List each source knowledge file and how it maps (file_search, prompt injection, context embedding)
- Note any gaps or limitations

### FILE: README.md

Deployment instructions explaining:
- How to execute via `responses.create`
- The stateless batch pattern (no conversation persistence)
- That `store: false` means no server-side thread
- A Python example using the OpenAI SDK

## Rules

- **Model-bound**: Must set `model: gpt-5.5` (concrete OpenAI model)
- **Stateless**: `store: false`, no `conversation:` by default
- **Source fidelity**: Preserve all source behaviors and constraints
- **No creative expansion**: Do not enable hosted tools the source did not have
- **Secrets externalized**: `store_secret_in_repo: false`
- **Forward contracts disabled**: `live_enabled: false`
- Delimit each file with `=== FILE: <filename> ===` headers
