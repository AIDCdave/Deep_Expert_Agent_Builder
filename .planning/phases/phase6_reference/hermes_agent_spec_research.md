# Hermes Agent Specification — Research Notes (2026-05-28)

Source: https://hermes-agent.nousresearch.com/docs/

## What is Hermes Agent?

Hermes Agent is an **open-source autonomous agent framework** by Nous Research. It is NOT a model — it is a **runtime** that can use any model (OpenRouter, OpenAI, Anthropic, self-hosted, etc.). It lives as a persistent agent that grows with the user through skills, memory, and scheduled automations.

## Key Deployment Artifacts

### 1. `SOUL.md` — Agent Identity (slot #1 in system prompt)
- Global personality file at `~/.hermes/SOUL.md` (or `$HERMES_HOME/SOUL.md`)
- Injected directly into slot #1 of system prompt — no wrapper language
- Contains: tone, communication style, directness, identity, personality-level behavior
- Subject to prompt-injection scanning and truncation
- Falls back to built-in default if empty/missing

### 2. `AGENTS.md` — Project Context
- Project-specific context: architecture, conventions, instructions
- Lives in project root, with progressive subdirectory discovery
- First match wins: `.hermes.md` → `AGENTS.md` → `CLAUDE.md` → `.cursorrules`

### 3. `config.yaml` — Agent Configuration
```
~/.hermes/
├── config.yaml       # Settings (model, terminal, TTS, compression, etc.)
├── .env              # API keys and secrets
├── auth.json         # OAuth provider credentials
├── SOUL.md           # Primary agent identity
├── memories/         # Persistent memory (MEMORY.md, USER.md)
├── skills/           # Agent-created skills
├── cron/             # Scheduled jobs
├── sessions/         # Gateway sessions
└── logs/             # Logs
```

Config precedence: CLI args > config.yaml > .env > built-in defaults

### 4. Tools / Toolsets
- 70+ built-in tools across ~28 toolsets
- Categories: web_search, terminal, file, browser, vision, image_gen, memory, delegation, skills, mcp, etc.
- Configured via `hermes tools` or `--toolsets` flag
- MCP integration for extended capabilities
- `execute_code` for programmatic tool calling

### 5. Skills
- Compatible with agentskills.io open standard
- Portable, shareable, community-contributed via Skills Hub
- Agent can autonomously create/improve skills during use

## Prompt Stack (system prompt assembly order)
1. SOUL.md (agent identity)
2. Tool-aware behavior guidance
3. Memory/user context (MEMORY.md, USER.md)
4. Skills guidance
5. Context files (AGENTS.md, .hermes.md)
6. Timestamp
7. Platform-specific formatting hints
8. Optional overlays (/personality)

## Provider Resolution
- Maps (provider, model) tuples to (api_mode, api_key, base_url)
- 18+ providers supported
- 3 API modes: chat_completions, codex_responses, anthropic
- Model chosen at runtime — NOT baked into agent definition

## What This Means for Target Packaging

A Hermes deployment package must produce:
1. **SOUL.md** — translated from source system prompt (personality/identity portion)
2. **AGENTS.md** — project context, conventions, instructions
3. **config.yaml** — model preference, toolset configuration, deployment settings
4. **tools_manifest.yaml** — mapping of source tools to Hermes toolsets/MCP
5. **knowledge_manifest.yaml** — how source knowledge maps to Hermes context
6. **README.md** — deployment instructions

Key distinction from other targets: Hermes is **model-agnostic** (like PAS), but it is a **specific runtime framework** with its own file conventions, tool system, and skill system. The model is NOT embedded in the agent definition — it is a runtime configuration choice.
