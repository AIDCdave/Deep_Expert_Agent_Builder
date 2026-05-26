# Deep Expert Agent Builder

## What This Is

A file-driven, multi-stage pipeline for creating Deep Expert Agents (DEAs). Converts structured intent-capture material into deployment-ready agent packages through seven phases: DEA Context Creation, Expert Six Prompt Creation, Expert Six Execution, Epistemic Anchor Creation, EARL Agent Package Creation, Target Deployment Packaging, and Main Orchestration.

## Core Value

Automate the full lifecycle of creating a deep expert agent — from "why do we need this agent?" to "here's the deployable package" — through deterministic orchestration around a small number of high-value reasoning model calls.

## Requirements

### Validated

- [x] Two-pass GPT-5.5 pattern produces superior holistic synthesis (proven in epistemic anchor)
- [x] File-driven I/O with clear workspace layout (proven in AIDC_Agent_Builder)
- [x] Per-stage token tracking and cost analytics (proven)
- [x] Local macOS execution with uv (proven)

### Active

- [ ] 6-stage pipeline: DEA Context → Expert Six Prompt → Expert Six → Anchor → EARL → Deployment
- [ ] Main orchestrator coordinates all stages with resumability
- [ ] Workspace layout: `workspaces/<dea_name>/00_inputs/` through `06_deployments/`
- [ ] Configuration-driven model routing (synthesis, cleanup, fast)
- [ ] Stage-specific CLI: `uv run python -m dea_builder <stage> <workspace>`
- [ ] Full pipeline CLI: `uv run python -m dea_builder run <workspace>`
- [ ] Planning mode: `uv run python -m dea_builder plan <workspace>`
- [ ] Execution trace per stage + pipeline-level trace
- [ ] Deterministic validation (Python) + judgment validation (LLM) separation
- [ ] Stage skip when outputs already valid
- [ ] Forced re-run of specific stages

### Out of Scope

- Web UI or hosted service
- Database-backed workflow system
- Multi-user collaboration
- Kubernetes / containerization
- Autonomous agent orchestration (this is a deterministic build system)
- Custom model training

## Context

- **Runtime:** Local macOS ("Wyatt"), Python 3.12+, uv
- **LLM:** Direct Azure Cognitive Services (AzureChatOpenAI)
- **Endpoint:** `https://dave-mot32g5b-eastus2.cognitiveservices.azure.com`
- **Models:** GPT-5.5 (synthesis + cleanup), GPT-5.4-nano (fast/mechanical)
- **Research:** Exa (search), Firecrawl (extraction)
- **Framework:** LangGraph StateGraph for stage internals
- **Proven pattern:** Stage 4 (Epistemic Anchor) ported from AIDC_Agent_Builder
- **Stage 1 prompts:** Context Normalizer Agent Prompt + Hardened Template (runtime, packaged)

## Constraints

- GPT-5.5 requires `max_completion_tokens` (not `max_tokens`)
- Local execution only — no cloud deployment
- File-based state — no database
- Each stage independently testable
- Architecture doc is the source of truth: `.planning/ARCHITECTURE.md`

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Two-pass synthesis pattern | Holistic generation + cleanup > multi-step template filling | Proven ✅ |
| Separate repo from AIDC_Agent_Builder | Broader scope, clean architecture, independent evolution | Active |
| 7 phases (6 stages + orchestrator) | Each stage = one phase, orchestrator last | Active |
| GPT-5.5 for synthesis, Nano for mechanical | Cost optimization with quality preservation | Active |
| File-driven, no database | Inspectable, reproducible, simple | Active |
| EARL as runtime-neutral layer | Decouples agent definition from deployment target | Active |
| Context Normalizer + Hardened Template | Stage 1 uses hardened LLM prompt with explicit output contract | Active |
| Structured error handling | Normalizer returns parseable ERROR with missing fields / conflicts | Active |
| Clean pipeline boundaries | Each stage output is sole input to next; no source content carried forward | Active |

---
*Last updated: 2026-05-26*
