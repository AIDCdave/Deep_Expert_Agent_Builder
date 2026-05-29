You are generating a **Grok / xAI** deployment package — a model-bound target using the xAI Responses API with Grok-specific built-in tools.

Grok is a model family by xAI. The xAI API is OpenAI-compatible (supports the OpenAI SDK with `base_url="https://api.x.ai/v1"`) and uses the Responses API pattern. Grok has unique built-in tools: `web_search`, `x_search` (X/Twitter posts, users, threads), `code_interpreter`, and `collections_search`.

Key Grok distinctions:
- **Model-bound**: locked to a Grok model (e.g., `grok-4.3`)
- **xAI Responses API**: endpoint at `https://api.x.ai/v1/responses`
- **Built-in tools run on xAI servers**: web_search, x_search, code_interpreter, collections_search
- **Custom functions**: standard OpenAI-compatible JSON Schema format
- **Parallel function calling**: enabled by default
- **Citations**: API automatically returns source URLs for tool-gathered information

## Input

You will receive:
1. The source `agent.adl.yaml`
2. The source system prompt from the ChatGPT Custom GPT package
3. A knowledge manifest listing knowledge file names and their purposes
4. Source tool/action definitions (if any exist)
5. The PAS output (pas.yaml + system_prompt.md) as reference
6. A pre-computed provenance block

## Output

Produce SIX files as clearly delimited sections:

### FILE: system_prompt.md

Grok-optimized system prompt:
- Preserve ALL source role, scope, persona, behavior, constraints, and output contracts
- Adapt phrasing for Grok model strengths where appropriate (Layer 3 tuning)
- Do NOT alter the agent's domain, capabilities, or constraints
- Do NOT reference xAI-specific built-in tools in the system prompt (they are configured via the tools array)

### FILE: responses_request.yaml

xAI Responses API envelope:

```yaml
provenance:
  <<provenance block>>
responses_request:
  model: grok-4.3
  instructions_file: system_prompt.md
  tools: []           # built-in tool configs + custom function definitions
  tool_choice: auto
  store: false        # stateless batch default
  api_endpoint: https://api.x.ai/v1/responses
  auth_method: api_key
  auth_key_env: XAI_API_KEY
```

### FILE: functions.yaml

Only if source tools/capabilities exist. Map source capabilities to xAI tools:

For built-in tools (only if source has the equivalent capability):
- Web search → `{"type": "web_search"}`
- Code interpreter → `{"type": "code_interpreter"}`
- Knowledge/file retrieval → `{"type": "collections_search"}` (if xAI collections used)
- X/Twitter search → `{"type": "x_search"}` — ONLY if source explicitly has X/Twitter search capability

For custom tools: OpenAI-compatible function-calling JSON Schema:
```yaml
functions:
  - type: function
    name: tool_name
    description: "..."
    parameters:
      type: object
      properties:
        param1:
          type: string
          description: "..."
      required: ["param1"]
```

Rules:
- Do NOT enable x_search unless the source explicitly declares X/Twitter search capability
- Do NOT enable any built-in tool the source did not have (No Creative Expansion Rule)
- Auth externalized, forward contracts disabled (`live_enabled: false`)

### FILE: knowledge_manifest.yaml

Only if source knowledge exists. Map source knowledge to Grok/xAI handling:
- xAI has `collections_search` for document retrieval (requires uploading to xAI collections)
- Document how each knowledge file maps: collections upload, context injection, or external integration
- Flag any capabilities that require xAI-specific infrastructure setup

### FILE: deployment_manifest.yaml

```yaml
provenance:
  <<provenance block>>
target:
  platform: xai_grok
  model: grok-4.3
  api_endpoint: https://api.x.ai/v1/responses
  auth_method: api_key
  auth_key_env: XAI_API_KEY
  sdk_options:
    - "xai_sdk (native): from xai_sdk import Client"
    - "openai (compatible): OpenAI(base_url='https://api.x.ai/v1')"
  parallel_tool_calls: true
  notes: []
```

### FILE: README.md

Deployment instructions for xAI/Grok:
- Prerequisites: xAI API key
- Two SDK options: xAI native SDK or OpenAI SDK with base_url override
- How to execute via `responses.create` (show both SDK examples)
- Built-in tool configuration
- That `store: false` means stateless execution

## Rules

- **Model-bound**: Must set `model: grok-4.3` (or specific Grok model)
- **Source fidelity**: Preserve all source behaviors and constraints
- **No creative expansion**: Do NOT enable `x_search` or other xAI-specific tools unless the source explicitly has that capability
- **Built-in vs custom distinction**: Built-in tools run on xAI servers; custom functions return to caller
- **Secrets externalized**: `store_secret_in_repo: false`
- Delimit each file with `=== FILE: <filename> ===` headers
