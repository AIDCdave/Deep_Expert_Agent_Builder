You are generating an **Anthropic Claude** deployment package — a model-bound target using Claude's prompt conventions and tool-use format.

Claude uses XML-style prompt segmentation, its own tool-use format, and specific prompt structure conventions that differ from OpenAI.

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

### FILE: system_prompt.md

Claude-optimized system prompt:
- Restructure using Claude's preferred XML-style organization where beneficial (e.g., `<role>`, `<constraints>`, `<instructions>`)
- Preserve ALL source role, scope, persona, behavior, constraints, and output contracts
- Adapt phrasing for Claude's strengths (direct instruction style, explicit constraint framing)
- Do NOT alter the agent's domain, capabilities, or constraints
- Do NOT add Claude-specific capabilities the source did not have

### FILE: tools.yaml

Only if source tools exist. Claude tool-use format:

```yaml
provenance:
  <<provenance block>>
tools:
  - name: tool_name
    description: "..."
    input_schema:
      type: object
      properties:
        param1:
          type: string
          description: "..."
      required: ["param1"]
```

Rules:
- Translate OpenAI function-calling schema to Claude's `input_schema` format
- Preserve all parameter names, types, descriptions, and required fields exactly
- Do not invent tools or widen boundaries
- Auth externalized, forward contracts disabled (`live_enabled: false`)

### FILE: knowledge_manifest.yaml

Only if source knowledge exists. Map source knowledge to Claude's context handling:
- Claude does not have a native knowledge/file-search equivalent
- Document how each knowledge file maps: prompt context injection, retrieval augmentation, or external integration
- Flag any capabilities that require external infrastructure

### FILE: deployment_manifest.yaml

```yaml
provenance:
  <<provenance block>>
target:
  platform: anthropic_claude
  model: claude-opus-4
  api_endpoint: https://api.anthropic.com/v1/messages
  auth_method: api_key
  auth_key_env: ANTHROPIC_API_KEY
  max_tokens: 8192
  temperature: null
  notes: []
```

### FILE: eval_plan.yaml

Evaluation plan adapted for Claude:
- Map source eval test cases to Claude-compatible format
- Note any eval criteria that need adjustment for Claude's behavior patterns
- Preserve evaluation intent

## Rules

- **Source fidelity**: The Claude package must implement the same semantic contract as the source
- **No creative expansion**: Do not add capabilities, tools, or behaviors not in the source
- **XML segmentation is optional**: Use it where it helps Claude's processing, not as decoration
- **Knowledge equivalence warning**: Claude's runtime context is NOT equivalent to ChatGPT Knowledge — generate explicit warnings
- Delimit each file with `=== FILE: <filename> ===` headers
