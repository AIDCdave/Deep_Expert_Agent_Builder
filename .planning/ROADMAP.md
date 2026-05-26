# Roadmap

**Project:** Deep Expert Agent Builder
**Milestone:** v1.0
**Last updated:** 2026-05-26

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

**Goal:** Transform DEA application context into a precise, verbose Expert Six research prompt.

**Delivers:**
- DEA context ingestion
- Two-pass synthesis: generate prompt → tighten/clarify
- Output: `02_expert_six_prompt/expert_six_research_prompt.md`
- Prompt build notes
- Execution trace

**Status:** not started

---

## Phase 3: Expert Six Execution and Finalization

**Goal:** Execute research, generate candidate experts, scrub to final Expert Six with rationale.

**Delivers:**
- Research execution (Exa + Firecrawl integration)
- Candidate generation and ranking
- Interactive or batch finalization
- Output: `03_expert_six/expert_six_final.md`
- Selection rationale, alternates, source manifest
- Execution trace

**Status:** not started

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

**Status:** not started (code exists, needs integration)

---

## Phase 5: EARL Agent Package Creation

**Goal:** Convert epistemic anchor into a canonical runtime-neutral agent behavior package.

**Delivers:**
- EARL package generation (system prompt, behavior contract, tool policy, safety boundaries)
- Knowledge pack manifest
- Evaluation seed set
- Two-pass: generate → align
- Output: `05_earl/output/earl_agent_package.md` + supporting artifacts
- Validation report
- Execution trace

**Status:** not started

---

## Phase 6: Target Deployment Packaging

**Goal:** Adapt EARL package for specific runtime targets via thin adapter layer.

**Delivers:**
- Adapter interface definition
- First concrete adapter (ChatGPT Custom GPT or equivalent)
- Target-specific artifact transformation
- Validation checklist per deployment
- Output: `06_deployments/<target_name>/`
- Deployment trace

**Status:** not started

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
*Updated: 2026-05-20*
