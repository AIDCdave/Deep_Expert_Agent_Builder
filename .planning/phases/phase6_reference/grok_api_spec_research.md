# Grok / xAI API Specification — Research Notes (2026-05-28)

Source: https://docs.x.ai/docs/guides/

## What is Grok?

Grok is a **model family** by xAI, accessed via the xAI API. Current flagship: **Grok 4.3**. The API is **OpenAI-compatible** — it supports both the OpenAI SDK (with `base_url="https://api.x.ai/v1"`) and xAI's native SDK (`xai_sdk`).

## API Surface

### Responses API (`/v1/responses`)
- xAI uses the **Responses API** as its primary endpoint (same pattern as OpenAI)
- Stateless by default
- Supports streaming
- Model-bound: must specify `model: "grok-4.3"` (or other Grok model)

### Function Calling
- Standard OpenAI-compatible function calling schema:
  ```json
  {
    "type": "function",
    "name": "function_name",
    "description": "...",
    "parameters": { JSON Schema }
  }
  ```
- Supports `tool_choice`: `"auto"`, `"required"`, `"none"`, or named function
- Parallel function calling enabled by default (disable with `parallel_tool_calls: false`)
- Function calls returned in whole chunks (not streamed across chunks)

### Built-in Tools (xAI-hosted)
| Tool | Type | Description |
|---|---|---|
| `web_search` | Built-in | Search the web and browse pages |
| `x_search` | Built-in | Search X posts, users, threads |
| `code_interpreter` / `code_execution` | Built-in | Execute Python in sandbox |
| `collections_search` | Built-in | Query uploaded document collections |

**Key rule:** Built-in tools execute on xAI servers. Custom functions pause and return to caller.

### Source Capability → Grok Tool Mapping
| Source capability | Grok tool |
|---|---|
| Web search | `{"type": "web_search"}` |
| Code interpreter | `{"type": "code_interpreter"}` |
| Knowledge/file retrieval | `{"type": "collections_search"}` (if xAI collections) or custom function |

### Citations
- API automatically returns source URLs for information gathered via tools
- Accessible in response metadata

## SDK Options
1. **xAI Native SDK** (`xai_sdk`): `Client`, `chat.create()`, tool helpers
2. **OpenAI SDK** (compatible): `OpenAI(base_url="https://api.x.ai/v1")`, `client.responses.create()`

## What This Means for Target Packaging

A Grok deployment package must produce:
1. **system_prompt.md** — Layer 3 tuned for Grok model capabilities
2. **responses_request.yaml** — xAI Responses API envelope with:
   - `model: grok-4.3` (model-bound)
   - `tools:` array with function definitions + built-in tool configs
   - `tool_choice: auto`
3. **functions.yaml** — Custom function definitions (OpenAI-compatible JSON Schema)
4. **knowledge_manifest.yaml** — How source knowledge maps to Grok (collections, context injection, etc.)
5. **deployment_manifest.yaml** — xAI API configuration, auth, endpoint
6. **README.md** — Deployment instructions

Key distinctions from other targets:
- **Model-bound**: locked to a Grok model version
- **OpenAI-compatible**: uses Responses API pattern (same as OpenAI Responses target)
- **xAI-specific built-in tools**: `web_search`, `x_search`, `code_interpreter`, `collections_search`
- **NOT the same as OpenAI Responses**: different endpoint (`api.x.ai`), different built-in tools, xAI-specific features (X search, citations)
