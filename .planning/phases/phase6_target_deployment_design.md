# Phase 6 — Target Deployment Packaging — Design

**Date:** 2026-05-28
**Status:** DRAFT — for discussion before implementation
**Input specs:** Spock SPEC.md v1.1, AMENDMENT-001, LITELLM-CONNECTION-DETAILS.md

---

## 0. One-paragraph summary

Phase 6 takes the EARL output (Module 5's `agent.adl.yaml` + `chatgpt_custom_gpt/` package) and produces deployment-ready packages for multiple target platforms. It always produces a **Portable Agent Spec (PAS)** first, then runs **parallel target-specific conversion pipes** for each requested platform (Claude, Gemma 4, Hermes, Grok, OpenAI Responses). After all targets complete, a **fidelity inspection pass** validates every output against the original source context. The existing `chatgpt_custom_gpt/` output from EARL is copied as-is (it IS the source).

---

## 1. Target platforms (6 total)

| Target slug | Directory | Model-bound? | Notes |
|---|---|---|---|
| `pas` | `portable_agent_spec/` | No (model-agnostic) | Always produced. OpenAI Chat Completions contract. No `model:` field. |
| `chatgpt-custom-gpt` | `chatgpt_custom_gpt/` | Yes (GPT) | Copy from EARL output. Source of truth. Add provenance block. |
| `openai-responses` | `openai_responses/` | Yes (GPT-5.5) | OpenAI Responses API `responses.create` envelope. Stateless batch. |
| `claude` | `claude/` | Yes (Claude) | XML-segmented prompt + Claude tool-use defs + deployment manifest. |
| `gemma-4` | `gemma/` | Yes (Gemma 4) | Model-facing prompt + runtime manifest + model config. |
| `hermes` | `hermes/` | No (LiteLLM-fronted) | ONE package. Model chosen at deploy time. Agent config + provider manifest. |
| `grok` | `grok/` | Yes (Grok/xAI) | xAI function-calling + deployment manifest. |

---

## 2. Execution architecture

```text
┌────────────────────────────────────────────────────────────────────────────┐
│ PHASE 0 — Input assembly + ADL validation                                  │
│   Read agent.adl.yaml, compute source_hash, validate adl_version           │
│   Load chatgpt_custom_gpt/ package as source content                       │
└──────────────────────────────────┬─────────────────────────────────────────┘
                                   ▼
┌────────────────────────────────────────────────────────────────────────────┐
│ PHASE 1 — PAS generation (always, first)                                   │
│   Single reasoning LLM call                                                │
│   Input: ADL + system prompt + knowledge files                             │
│   Output: portable_agent_spec/ (pas.yaml + system_prompt.md + README.md)   │
└──────────────────────────────────┬─────────────────────────────────────────┘
                                   ▼
┌────────────────────────────────────────────────────────────────────────────┐
│ PHASE 2 — Parallel target conversion pipes                                 │
│                                                                            │
│   Each pipe: independent LLM call (reasoning tier)                         │
│   Input: full GPT stack (source) + PAS (reference) + target-specific       │
│          conversion spec (from prompts/stage6/<target>.md)                  │
│                                                                            │
│   ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐   │
│   │  Claude  │  │ Gemma-4  │  │  Hermes  │  │   Grok   │  │ OpenAI   │   │
│   │   pipe   │  │   pipe   │  │   pipe   │  │   pipe   │  │ Responses│   │
│   └──────────┘  └──────────┘  └──────────┘  └──────────┘  └──────────┘   │
│                                                                            │
│   chatgpt_custom_gpt/ → copy + provenance stamp (no LLM needed)            │
└──────────────────────────────────┬─────────────────────────────────────────┘
                                   ▼
┌────────────────────────────────────────────────────────────────────────────┐
│ PHASE 3 — Fidelity inspection pass                                         │
│   Single reasoning LLM call                                                │
│   Input: original context doc + ADL + all generated targets                │
│   Output: fidelity_report.md (per-target PASS/FAIL/WARN, drift detected)   │
│   Any FAIL → warn but still emit (user decides)                            │
└────────────────────────────────────────────────────────────────────────────┘
```

### Parallelism

- Phase 2 pipes are fully independent — can run concurrently (async LLM calls)
- Each pipe uses `get_llm("reasoning", trusted=True)` (GPT-5.5)
- If only one target requested, only that pipe runs (plus PAS, always)

---

## 3. Per-target conversion pipe design

Each target gets a dedicated prompt file at `src/dea_builder/prompts/stage6/<target>.md` containing:
- Target platform profile (artifact structure, file layout, schemas)
- Conversion rules specific to that platform
- Extracted from the LM Target Expert's knowledge files (Files 03-08)

### Pipe inputs (per call)

```yaml
system_message:
  - Target-specific conversion prompt (from prompts/stage6/<target>.md)
human_message:
  - Source ADL (agent.adl.yaml)
  - Source system prompt (chatgpt_custom_gpt/02_instructions/system_prompt.md)
  - Source knowledge manifest (file names + descriptions, NOT full content)
  - Source tools/actions (if any exist)
  - PAS output (pas.yaml + system_prompt.md) — as reference/guide
  - Provenance block (pre-computed: source_hash, adl_version, generated_at)
```

**Note:** Full knowledge file content is NOT sent. Only the manifest (names, purpose descriptions) is provided. This keeps cost down and prevents context overflow while preserving enough information for structural packaging.

### Pipe outputs (per target)

Each pipe returns a structured response containing:
- All files for that target directory
- Provenance block stamped on metadata file
- Compatibility warnings / assumptions

---

## 4. Output directory structure

```
<workspace>/06_deployments/
├── portable_agent_spec/
│   ├── pas.yaml
│   ├── system_prompt.md
│   └── README.md
├── chatgpt_custom_gpt/          # copy from 05_earl/output/
│   └── (full package + provenance stamp)
├── openai_responses/
│   ├── system_prompt.md
│   ├── responses_request.yaml
│   ├── tools.yaml               # if source tools exist
│   ├── knowledge_manifest.yaml  # if source knowledge exists
│   └── README.md
├── claude/
│   ├── system_prompt.md
│   ├── tools.yaml               # if source tools exist
│   ├── knowledge_manifest.yaml  # if source knowledge exists
│   ├── deployment_manifest.yaml
│   └── eval_plan.yaml
├── gemma/
│   ├── prompt.txt
│   ├── model_config.yaml
│   ├── knowledge_manifest.yaml  # if source knowledge exists
│   ├── runtime_manifest.yaml
│   └── eval_plan.yaml
├── hermes/
│   ├── SOUL.md                  # agent identity (slot #1 of Hermes prompt stack)
│   ├── AGENTS.md                # project context / conventions / instructions
│   ├── config.yaml              # model preference, toolsets, deployment settings
│   ├── tools_manifest.yaml      # source tools → Hermes toolset/MCP mapping
│   ├── knowledge_manifest.yaml  # if source knowledge exists
│   └── README.md
├── grok/
│   ├── system_prompt.md
│   ├── responses_request.yaml   # xAI Responses API envelope (model: grok-4.3)
│   ├── functions.yaml           # custom function defs (OpenAI-compatible schema)
│   ├── knowledge_manifest.yaml  # if source knowledge exists
│   ├── deployment_manifest.yaml # xAI API config, auth, endpoint
│   └── README.md
└── fidelity_report.md           # Phase 3 inspection output
```

---

## 5. Provenance stamping (all outputs)

Every target's metadata file includes:

```yaml
provenance:
  source_adl_file: agent.adl.yaml
  adl_version: "1.0"             # or UNKNOWN if missing
  source_hash: <sha256 of agent.adl.yaml>
  generated_at: <ISO-8601 UTC>
  generator: dea-builder/phase6
```

Staleness detection: if current ADL hash != recorded `source_hash`, package is stale.

---

## 6. CLI design

### Standalone command

```bash
dea-builder package <workspace_path> [--targets <list>] [--output <dir>]
```

- `--targets`: comma-separated. Values: `pas`, `chatgpt-custom-gpt`, `openai-responses`, `claude`, `gemma-4`, `hermes`, `grok`, `all`. Default: `all`.
- `--output`: output root. Default: `<workspace>/06_deployments/`
- PAS is always produced regardless of `--targets` (per spec).

### Main pipeline integration

```bash
dea-builder run <workspace_path> [--skip-package] [--targets <list>]
```

- `--skip-package`: skip Phase 6 entirely
- `--targets`: passed through to Phase 6 if not skipped

---

## 7. LiteLLM smoke test infrastructure

Per Spock's LITELLM-CONNECTION-DETAILS.md:

- **Local LiteLLM proxy** on `localhost:4000`
- Secrets from Azure Key Vault (`kv-aidc-eus2`): `litellm-master-key`, `aoai-api-key`
- Config: `litellm.config.yaml` (committed, env-var refs only)
- Startup wrapper: `scripts/start-litellm.sh` (fetches from KV, exports, launches)
- PAS test: `http://localhost:4000/v1/chat/completions` with alias `general`
- OpenAI Responses test: `https://api.openai.com/v1/responses` (model-bound, direct)

---

## 8. Key design decisions (consolidated from user answers)

| # | Decision | Rationale |
|---|---|---|
| 1 | PAS first, then parallel target pipes, then inspection | PAS acts as guide/reference for targets; inspection catches drift |
| 2 | ChatGPT Custom GPT = copy from EARL (no LLM) | Already produced; add provenance stamp only |
| 3 | OpenAI Responses = new separate target | Assistants deprecated → Responses API is the programmatic batch surface |
| 4 | Each target gets its own conversion prompt | Targeted, independent, parallelizable; reasoning models for all |
| 5 | PAS is reference, not intermediate | Targets derive from full GPT stack + PAS as guide, not PAS alone |
| 6 | Fidelity inspection against original context | Catches semantic drift, boundary widening, missing constraints |
| 7 | CLI default = all targets | `--targets` filters to specific ones; main pipeline can skip Phase 6 |
| 8 | Hermes = single package, no per-model variants | LiteLLM-fronted; model chosen at runtime |

---

## 9. Files to create

| File | Purpose |
|---|---|
| `src/dea_builder/stages/target_deploy.py` | Phase 6 Python stage (LangGraph: input_assembly → pas_gen → parallel_targets → inspect) |
| `src/dea_builder/prompts/stage6/__init__.py` | Prompt loader |
| `src/dea_builder/prompts/stage6/pas.md` | PAS conversion prompt |
| `src/dea_builder/prompts/stage6/claude.md` | Claude conversion prompt |
| `src/dea_builder/prompts/stage6/gemma.md` | Gemma conversion prompt |
| `src/dea_builder/prompts/stage6/hermes.md` | Hermes conversion prompt |
| `src/dea_builder/prompts/stage6/grok.md` | Grok conversion prompt |
| `src/dea_builder/prompts/stage6/openai_responses.md` | OpenAI Responses conversion prompt |
| `src/dea_builder/prompts/stage6/fidelity_inspection.md` | Fidelity inspection prompt |
| `litellm.config.yaml` | LiteLLM proxy config (committed) |
| `scripts/start-litellm.sh` | Startup wrapper (KV fetch) |

---

## 10. Scope boundaries (from Spock + user)

**In scope this pass:**
- PAS always-on output
- ADL as canonical authority + `adl_version: '1.0'` pinning (no format change)
- Provenance stamping on all outputs
- Per-target conversion pipes (6 targets, Hermes and Grok fully independent)
- Fidelity inspection pass
- CLI surface (3 inputs)
- LiteLLM infrastructure for smoke test
- Independent research on Hermes agent spec pattern (separate from Grok)

**Out of scope:**
- Restructuring targets to formally derive from PAS (follow-on)
- Per-model variants of LiteLLM-fronted targets
- Second canonical format alongside ADL
- CLI beyond 3 inputs
- Automated acceptance test execution (manual smoke test)
- adl_version format changes (future full-stack version sync)

---

## 11. Estimated cost per run

- PAS: 1 reasoning call (~$0.15)
- Targets: up to 5 parallel reasoning calls (~$0.75)
- Fidelity inspection: 1 reasoning call (~$0.15)
- **Total: ~$1.05** per workspace (assuming all targets)

---

## Decisions confirmed (2026-05-28)

1. **Source knowledge in target context**: System prompt + knowledge manifest (names/descriptions) + tools. NOT full knowledge file content. Keeps cost down, prevents overflow.

2. **Hermes and Grok**: Fully separate research and output. The LM Target Expert's File 08 conflated them — they are independent targets. Hermes agent spec pattern to be researched independently.

3. **ADL `adl_version`**: Stays at `1.0`. No format change. Future full-stack version sync will handle this.
