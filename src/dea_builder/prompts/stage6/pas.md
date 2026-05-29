You are generating a **Portable Agent Spec (PAS)** — a model-agnostic, OpenAI Chat Completions contract-compliant agent deployment package.

The PAS is the universal floor: it works against ANY OpenAI-compatible runtime (OpenAI, Azure OpenAI, LiteLLM, Ollama, vLLM, etc.) with zero modification.

## Input

You will receive:
1. The source `agent.adl.yaml` — the canonical agent definition
2. The source system prompt from the ChatGPT Custom GPT package
3. A knowledge manifest listing knowledge file names and their purposes
4. Source tool/action definitions (if any exist)
5. A pre-computed provenance block

## Output

Produce THREE files as clearly delimited sections:

### FILE: pas.yaml

A YAML file with this exact structure:

```yaml
provenance:
  <<provenance block provided in input>>
pas:
  schema_version: "1.0"
  instructions_file: system_prompt.md
  tools: []           # OpenAI function-calling JSON Schema definitions translated from source tools
  tool_choice: auto   # or "none" if no tools
  # NO model: field — this is model-agnostic
  # NO provider: field — this is provider-agnostic
  temperature: null
  max_output_tokens: null
```

Rules for `tools`:
- Translate each source tool/action into an OpenAI function-calling JSON Schema definition
- Preserve name, description, parameters exactly — do not invent new tools
- If no source tools exist, use an empty array
- Auth details are externalized (not in the spec)
- Forward contracts: `live_enabled: false`

### FILE: system_prompt.md

The agent's system prompt, adapted for model-agnostic use:
- Preserve the FULL role, scope, persona, behavior, constraints, and output contracts from the source
- Remove any ChatGPT-specific or platform-specific directives (e.g., "As a Custom GPT...", references to Actions panel, Builder UI)
- Do NOT add model-specific optimizations
- Do NOT alter the agent's domain, capabilities, or constraints
- Keep the same structural organization (sections, headers) as the source

### FILE: README.md

A deployment README explaining:
- What the PAS is (model-agnostic OpenAI Chat Completions deployable)
- How to execute it via any OpenAI-compatible endpoint
- A curl example using the system prompt and a sample user message
- That the model is chosen at runtime (not in the spec)

## Rules

- **Source fidelity**: Preserve role, scope, persona, behavior, constraints, tool boundaries, knowledge references, and evaluation intent exactly
- **No creative expansion**: Do not invent tools, capabilities, or behaviors not in the source
- **No model field**: The PAS must contain NO `model:` or `provider:` fields anywhere
- **No platform binding**: Remove all platform-specific references
- Delimit each file clearly with `=== FILE: <filename> ===` headers
