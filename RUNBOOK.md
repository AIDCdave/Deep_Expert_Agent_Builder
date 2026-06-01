# DEA Builder Runbook

## Prerequisites

- macOS, Python 3.12+, `uv`
- Azure OpenAI access (`dave-mot32g5b-eastus2.cognitiveservices.azure.com`)
- Environment variables in `~/.zshrc`:

```bash
AZURE_OPENAI_API_KEY=<key>
AZURE_OPENAI_ENDPOINT=https://dave-mot32g5b-eastus2.cognitiveservices.azure.com
AZURE_OPENAI_TRUSTED_DEPLOYMENT=aoai-gpt55-trusted
CONTENT_SAFETY_ENDPOINT=https://aidc-content-safety-ea10c.cognitiveservices.azure.com
EXA_API_KEY=<key>           # Stage 3 research
FIRECRAWL_API_KEY=<key>     # Stage 3 source verification
```

- `CONTENT_SAFETY_KEY` fetched at runtime from Key Vault `kv-aidc-eus2`

## Install

```bash
cd Deep_Expert_Agent_Builder
uv sync
```

## Workspace Layout

```
workspaces/<agent_name>/
  00_inputs/                          # Your input files go here
    completed_intake_worksheet.md     # Or transcript, spec, notes, etc.
  01_dea_context/output/              # Stage 1 output
  02_expert_six_prompt/output/        # Stage 2 output
  03_expert_six/output/               # Stage 3 output
  04_epistemic_anchor/output/         # Stage 4 output
  05_earl/output/                     # Stage 5 output
  06_deployments/output/              # Stage 6 output
  runs/                               # Pipeline trace
```

Create the workspace and place at least one input file in `00_inputs/`.

## Full Pipeline

```bash
dea-builder run <workspace_path>
```

Runs Stages 1–6 sequentially. Skips any stage whose canonical output already exists.

### Options

| Flag | Description |
|------|-------------|
| `--force-stage N` | Re-run stage N even if output exists. Repeatable. |
| `--start-stage N` | Skip stages before N (still dependency-checks them). |
| `--skip-package` | Skip Stage 6 entirely. |
| `--targets <list>` | Comma-separated targets for Stage 6. Default: all. |

### Examples

```bash
# Full run from scratch
dea-builder run ./workspaces/my_agent

# Re-run only EARL + packaging
dea-builder run ./workspaces/my_agent --force-stage 5 --force-stage 6

# Run through EARL, skip packaging
dea-builder run ./workspaces/my_agent --skip-package

# Run only specific deployment targets
dea-builder run ./workspaces/my_agent --force-stage 6 --targets pas,claude,grok

# Start from Stage 4 (1–3 must already be complete)
dea-builder run ./workspaces/my_agent --start-stage 4
```

## Planning Mode (Dry Run)

```bash
dea-builder plan <workspace_path> [--skip-package]
```

Shows per-stage status: output exists, deps met, action (run/skip/blocked). No LLM calls.

## Individual Stages

Run any stage independently. Useful for debugging or iterating on a single stage.

```bash
dea-builder dea-context <workspace_path>         # Stage 1
dea-builder expert-six-prompt <workspace_path>   # Stage 2
dea-builder expert-six <workspace_path>          # Stage 3
dea-builder anchor <workspace_path>              # Stage 4
dea-builder earl <workspace_path>                # Stage 5
dea-builder package <workspace_path> [--targets <list>] [--output <dir>]  # Stage 6
```

Each stage validates its own prerequisites (upstream outputs must exist).

## Stage Dependency Graph

```
1 → 2 → 3 → 4 → 5 → 6
         ↗
    1 ──┘
```

- Stage 2 requires Stage 1
- Stage 3 requires Stages 1 + 2
- Stage 4 requires Stages 1 + 3
- Stage 5 requires Stage 4
- Stage 6 requires Stage 5

## Skip Logic

A stage is skipped if its canonical output file exists:

| Stage | Canonical Output |
|-------|-----------------|
| 1 | `01_dea_context/output/context_document.md` |
| 2 | `02_expert_six_prompt/output/expert_six_research_prompt.md` |
| 3 | `03_expert_six/output/expert_six_final.md` |
| 4 | `04_epistemic_anchor/output/epistemic_anchor.md` |
| 5 | `05_earl/output/agent.adl.yaml` |
| 6 | `06_deployments/output/fidelity_report.md` |

To force re-run: use `--force-stage N` or delete the output file.

## Stage 6 Targets

| Target | Type | Output Dir |
|--------|------|-----------|
| `pas` | Model-agnostic | `portable_agent_spec/` |
| `chatgpt-custom-gpt` | Copy from EARL | `chatgpt_custom_gpt/` |
| `openai-responses` | OpenAI Responses API | `openai_responses/` |
| `claude` | Anthropic | `claude/` |
| `gemma-4` | Open model | `gemma/` |
| `hermes` | Runtime framework | `hermes/` |
| `grok` | xAI | `grok/` |

## Pipeline Trace

Written to `<workspace>/runs/last_pipeline_trace.json` after every `run` invocation.

```json
{
  "workspace": "/path/to/workspace",
  "total_elapsed_s": 465.55,
  "success": true,
  "stages": [
    {"stage": 1, "name": "...", "status": "skipped|success|error", "elapsed_s": 0.0, "error": null}
  ]
}
```

## Cost Estimates

| Stage | Typical Cost | Typical Time |
|-------|-------------|-------------|
| 1 | $0.05 | 1 min |
| 2 | $0.05 | 1 min |
| 3 | $0.50 | 5 min |
| 4 | $0.80 | 5 min |
| 5 | $2.20 | 15 min |
| 6 | $0.57 | 8 min |
| **Total** | **~$4.00** | **~30 min** |

## Exit Codes

| Code | Meaning |
|------|---------|
| 0 | Success |
| 1 | Missing input / file not found / pipeline failure |
| 2 | Validation error (missing fields, bad format) |
| 3 | Prompt injection detected (Stage 1 only) |

## Troubleshooting

**Stage fails with token limit error:** Large agents (100K+ anchor) may exceed the general tier's 128K limit. This is handled automatically for EARL Pass 5 (uses reasoning tier). If other stages fail similarly, check the anchor size.

**Stage 6 fidelity FAIL:** The fidelity inspection may report FAIL for targets that invented capabilities or dropped constraints. Review `06_deployments/output/fidelity_report.md`. This is informational — packages are still generated.

**Missing CONTENT_SAFETY_KEY:** Ensure you can run `az keyvault secret show --vault-name kv-aidc-eus2 --name content-safety-key`. The CLI must be authenticated to Azure.

**Re-running a single stage:** Delete its canonical output file, then run the pipeline. Or use `--force-stage N`.
