# Deep Expert Agent Builder

A file-driven, multi-stage pipeline for creating **Deep Expert Agents (DEAs)**.

Converts structured intent-capture material into deployment-ready agent packages through six explicit stages, orchestrated by a deterministic build system that uses reasoning models at carefully chosen points.

## Pipeline

```text
1. DEA Context Creation        → Why this agent? For whom? What work?
2. Expert Six Prompt Creation   → Research specification for expert discovery
3. Expert Six Execution         → Research, rank, finalize the Expert Six
4. Epistemic Anchor Creation    → Deep reasoning substrate (proven 2-pass GPT-5.5)
5. EARL Agent Package           → Runtime-neutral agent behavior contract
6. Target Deployment Packaging  → Platform-specific adaptation
```

## Quick Start

```bash
# Install
git clone https://github.com/AIDCdave/Deep_Expert_Agent_Builder.git
cd Deep_Expert_Agent_Builder
uv sync

# Run full pipeline on a workspace
uv run python -m dea_builder run workspaces/<dea_name>

# Run a specific stage
uv run python -m dea_builder anchor workspaces/<dea_name>

# Planning mode (dry run)
uv run python -m dea_builder plan workspaces/<dea_name>
```

## Workspace Layout

```text
workspaces/<dea_name>/
  00_inputs/           Questionnaire + supporting docs
  01_dea_context/      Application context document
  02_expert_six_prompt/  Research prompt
  03_expert_six/       Expert Six final + candidates
  04_epistemic_anchor/ Epistemic anchor document
  05_earl/             EARL agent package
  06_deployments/      Target-specific packages
  runs/                Pipeline execution traces
```

## Prerequisites

- macOS with Python 3.12+
- [uv](https://docs.astral.sh/uv/) package manager
- Azure OpenAI API access (GPT-5.5 deployment)

### Environment Variables

```bash
# In ~/.zshrc
export AZURE_OPENAI_ENDPOINT="https://your-endpoint.cognitiveservices.azure.com"
export AZURE_OPENAI_API_KEY="your-key"
export AZURE_OPENAI_API_VERSION="2024-12-01-preview"

# In .env (optional — for research tools)
EXA_API_KEY=your-exa-key
FIRECRAWL_API_KEY=your-firecrawl-key
```

## Architecture

See [`.planning/ARCHITECTURE.md`](.planning/ARCHITECTURE.md) for the full architecture overview.

## Core Design Principle

> Python owns orchestration. The LLM owns synthesis.
> This pipeline is a deterministic build system, not an autonomous agent swarm.

Each reasoning-heavy stage follows the proven two-pass pattern:

```text
Pass 0 — Holistic generation from all relevant context
Pass 1 — Cleanup, completion, and alignment
```
