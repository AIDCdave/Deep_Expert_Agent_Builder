# new-agent

Create a DEA Builder workspace and run the full pipeline.

## Usage

```bash
new-agent <agent_name> <input_file> [targets]
```

## Parameters

| Parameter | Required | Description |
|-----------|----------|-------------|
| `agent_name` | Yes | Workspace directory name. Use underscores, no spaces. |
| `input_file` | Yes | Path to intake worksheet, transcript, or spec. |
| `targets` | No | Comma-separated deployment targets. Default: all. |

## Targets

```
pas, chatgpt-custom-gpt, openai-responses, claude, gemma-4, hermes, grok
```

## Examples

```bash
# All targets
new-agent Collins_Ranch_Content_Strategist ./intake.md

# Specific targets
new-agent Collins_Ranch_Content_Strategist ./intake.md pas,claude,grok

# Single target
new-agent Collins_Ranch_Content_Strategist ./intake.md pas
```

## What it does

1. Creates `~/Deep_Expert_Agent_Builder/workspaces/<agent_name>/00_inputs/`
2. Copies `<input_file>` into `00_inputs/`
3. Runs `dea-builder run` (Stages 1–6) with optional `--targets`

## Exit behavior

- Fails if workspace already exists (prevents overwrites)
- Fails if input file not found
- Pipeline exit code passes through (0 = success, 1 = failure)

## Prerequisites

- `dea-builder` in PATH (`/usr/local/bin/dea-builder`)
- Azure OpenAI env vars configured (see `RUNBOOK.md`)
