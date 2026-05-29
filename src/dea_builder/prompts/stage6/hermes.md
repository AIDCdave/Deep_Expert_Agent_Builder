You are generating a **Hermes Agent** (Nous Research) deployment package — a model-agnostic runtime framework target with specific file conventions.

Hermes Agent is an open-source autonomous agent framework by Nous Research. It is NOT a model — it is a runtime that uses ANY model (via OpenRouter, OpenAI, Anthropic, self-hosted, etc.). It has its own file conventions: SOUL.md for agent identity, AGENTS.md for project context, and config.yaml for runtime configuration.

Key Hermes concepts:
- **SOUL.md**: Agent identity (slot #1 in system prompt). Personality, tone, style, communication defaults.
- **AGENTS.md**: Project-specific context, architecture, conventions, instructions. Loaded from working directory.
- **config.yaml**: Model preference, terminal backend, toolset configuration, memory settings.
- **Toolsets**: 70+ built-in tools across ~28 toolsets (web_search, terminal, file, browser, vision, memory, delegation, skills, MCP, etc.)
- **Skills**: Portable, shareable via agentskills.io open standard. Agent can create/improve skills during use.
- **Prompt stack**: SOUL.md → tool guidance → memory → skills → AGENTS.md → timestamp → platform hints → overlays

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

### FILE: SOUL.md

The agent identity file (slot #1 of Hermes prompt stack):
- Extract ONLY the personality, tone, communication style, identity, and behavioral characteristics from the source
- Format as concise, stable personality guidance (not task-specific instructions)
- Use markdown headers: # Personality, ## Style, ## What to avoid, ## Technical posture (as applicable)
- Do NOT include project-specific instructions, file paths, or workflow details (those go in AGENTS.md)
- Keep it focused on WHO the agent IS, not WHAT it does

### FILE: AGENTS.md

The project context file:
- Extract the role, scope, domain, constraints, operating instructions, workflow details, output contracts
- Format as project-specific context that tells Hermes HOW to work on this domain
- Use markdown headers: # Project Context, ## Architecture, ## Conventions, ## Constraints, ## Important Notes
- This is where the bulk of the source system prompt content goes
- Include knowledge file references and their purposes

### FILE: config.yaml

Hermes runtime configuration:

```yaml
provenance:
  <<provenance block>>
# Model is a runtime choice — suggest but do not lock
model: openrouter/auto  # Hermes default; user can change to any provider/model
terminal:
  backend: local
toolsets:
  enabled: []  # map from source capabilities to Hermes toolsets
  disabled: []
memory:
  enabled: true
skills:
  auto_create: false  # conservative default for executor agents
```

### FILE: tools_manifest.yaml

Map source tools/capabilities to Hermes toolsets and MCP:

```yaml
provenance:
  <<provenance block>>
tool_mapping:
  - source_tool: "tool_name"
    hermes_toolset: "web"  # or "terminal", "file", "browser", "mcp", etc.
    mapping_type: native | mcp | custom | unsupported
    notes: ""
capabilities:
  web_search: false   # true if source has web search
  code_execution: false
  file_operations: false
  browser: false
  # ... map each source capability
unmapped_tools: []  # tools that have no Hermes equivalent
```

### FILE: knowledge_manifest.yaml

Only if source knowledge exists. Map source knowledge to Hermes context handling:
- Hermes uses AGENTS.md subdirectory context files and memory system
- Document how each knowledge file maps: AGENTS.md injection, memory import, skill attachment, or external reference
- Flag any knowledge that requires infrastructure Hermes doesn't natively provide

### FILE: README.md

Deployment instructions for Hermes Agent:
- Prerequisites: Hermes Agent installed (`curl -fsSL ... | bash`)
- How to deploy: copy SOUL.md to `~/.hermes/`, AGENTS.md to project root, config.yaml to `~/.hermes/`
- Model configuration: how to set the model via `hermes config set model <provider/model>`
- Tool setup: which toolsets to enable
- How to start: `hermes chat` or `hermes setup --portal`

## Rules

- **Model-agnostic**: Do NOT embed a specific model in the agent definition. Model is a runtime config choice.
- **Source fidelity**: Preserve all source behaviors, constraints, and intent across SOUL.md + AGENTS.md
- **SOUL.md vs AGENTS.md split**: Identity/personality in SOUL.md, everything else in AGENTS.md. If it should follow the agent everywhere → SOUL.md. If it belongs to a project → AGENTS.md.
- **No creative expansion**: Do not invent tools, capabilities, or Hermes-specific features the source did not have
- **Toolset mapping honesty**: If a source tool has no Hermes equivalent, mark as `unsupported` — do not force-fit
- Delimit each file with `=== FILE: <filename> ===` headers
