# Roadmap

**Project:** Deep Expert Agent Builder
**Milestone:** v1.0
**Last updated:** 2026-05-29

## Phase 1: DEA Context Creation

**Goal:** Normalize heterogeneous context inputs into a canonical context document conforming to the 12-section Hardened Template.

**Delivers:**
- Context Normalizer pipeline (hardened LLM prompt + template)
- Heterogeneous input handling (worksheets, transcripts, specs, notes, direct)
- Structured error handling (parseable failure output with missing fields / conflicts)
- Two-pass pipeline: normalize → review/refine
- Clean pipeline boundary: no source content carried downstream
- Output: `01_dea_context/output/context_document.md`
- Execution trace

**Status:** complete

---

## Phase 2: Expert Six Prompt Creation

**Goal:** Fill the generic Expert Six Research Prompt template with domain-specific fields extracted from the Stage 1 context document.

**Delivers:**
- Generic template + domain field extraction (TARGET_DOMAIN, RESEARCHER_DOMAIN)
- Two-pass pipeline: extract fields → review coherence
- Self-contained output: filled research prompt + versioned context document copy
- Output: `02_expert_six_prompt/output/expert_six_research_prompt.md` + `context_document.md`
- Execution trace

**Status:** complete

---

## Phase 3: Expert Six Execution and Finalization

**Goal:** Execute research, generate candidate experts, scrub to final Expert Six with rationale.

**Delivers:**
- 4-pass pipeline: query gen → first cut → gap analysis + refine → audit
- Exa semantic search (holistic + gap-targeted queries)
- Firecrawl source verification
- GPT-5.5 reasoning for all synthesis passes
- Self-contained output: `03_expert_six/output/expert_six_final.md` + `context_document.md`
- Selection rationale, alternates, coverage map, audit notes
- Full working trace per pass

**Status:** complete

---

## Phase 4: Epistemic Anchor Creation

**Goal:** Create the deep reasoning substrate for the DEA via proven 2-pass GPT-5.5 pipeline.

**Delivers:**
- Ported from AIDC_Agent_Builder (proven implementation)
- Adapted to new workspace layout (`04_epistemic_anchor/`)
- Input: Expert Six final + DEA context + anchor meta prompt + template
- Two-pass: generate → optimize
- Output: `04_epistemic_anchor/output/epistemic_anchor.md`
- Token tracking + cost analytics
- Execution trace

**Status:** complete

---

## Phase 5: EARL Agent Package Creation

**Goal:** Convert epistemic anchor into a canonical runtime-neutral agent behavior package.

**Delivers:**
- EARL package generation (system prompt, behavior contract, tool policy, safety boundaries)
- Knowledge pack manifest
- Evaluation seed set
- Multi-pass: identity → system prompt → knowledge factoring → reconciliation → realignment → audit
- Trusted deployment (Prompt Shields OFF) for all LLM calls
- Output: `05_earl/output/` (identity, system prompt, knowledge files, eval data)
- Execution trace

**Status:** complete

---

## Phase 6: Target Deployment Packaging

**Goal:** Convert EARL output into deployment-ready packages for 7 target platforms with provenance stamping and fidelity inspection.

**Delivers:**
- 4-phase pipeline: input assembly → PAS generation → parallel target conversion → fidelity inspection
- Portable Agent Spec (PAS) — always-on, model-agnostic, OpenAI Chat Completions contract
- 7 targets: PAS, ChatGPT Custom GPT (copy from EARL), OpenAI Responses API, Claude, Gemma 4, Hermes Agent, Grok
- Per-target prompt files (`src/dea_builder/prompts/stage6/`)
- Provenance stamping (source_hash, adl_version, generated_at) on all packages
- Fidelity inspection pass — cross-target semantic drift detection
- CLI: `dea-builder package <workspace> [--targets <list>] [--output <dir>]`
- LiteLLM config for PAS smoke testing (`litellm.config.yaml` + `scripts/start-litellm.sh`)
- Output: `06_deployments/output/{portable_agent_spec,chatgpt_custom_gpt,openai_responses,claude,gemma,hermes,grok}/`
- Execution trace

**Status:** complete

---

## Phase 7: Main Orchestrator

**Goal:** Coordinate full pipeline end-to-end with stage sequencing, skip logic, and resumability.

**Delivers:**
- `uv run python -m dea_builder run <workspace>` — full pipeline
- `uv run python -m dea_builder plan <workspace>` — planning mode
- `uv run python -m dea_builder <stage> <workspace>` — individual stages
- Stage dependency validation
- Skip completed stages (output already valid)
- Forced re-run (`--force-stage <N>`)
- Top-level pipeline trace linking all stage traces
- Cost summary across all stages

**Status:** not started

---

## Key Principle

Each phase follows the proven two-pass synthesis pattern:

```text
Pass 0 — Holistic generation from all relevant context
Pass 1 — Cleanup, completion, and alignment
```

Python owns orchestration. The LLM owns synthesis. This pipeline is a deterministic build system that uses reasoning models at carefully chosen points.

---
*Roadmap for: Deep Expert Agent Builder v1.0*
*Updated: 2026-05-29*
