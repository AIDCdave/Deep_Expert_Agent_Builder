# Phase 1: DEA Context Creation — Plan

**Stage:** 1 of 7
**Status:** Planning
**Last updated:** 2026-05-22

---

## What This Phase Delivers

Stage 1 takes a completed Expert Six Intake Worksheet (+ optional supporting docs) and produces a **DEA Application Context Document** — a clean, structured reference describing the agent's purpose, audience, architecture, and knowledge requirements.

This context document becomes the primary input to Stage 2 (Expert Six Prompt Creation).

---

## Inputs

```text
workspaces/<dea_name>/
  00_inputs/
    completed_intake_worksheet.md       # REQUIRED — filled-out Expert Six Worksheet v3
    supporting_docs/                    # OPTIONAL — domain notes, brand guides, prior agents, samples
```

The intake worksheet is the structured input. It has 6 sections:

1. **Domain & Objective** — domain name, purpose statement, stage of work
2. **Requester's Baseline** — expertise level, pre-selected experts
3. **Agent Definition** — role, personality, framing, deliverables, end user
4. **Knowledge Scope & Focus** — primary domains, exclusions
5. **Business Context** — company, business model, platforms, customers, public/private, constraints
6. **Special Instructions** — freeform overrides

Supporting docs (if present) are ingested and appended to context for synthesis.

---

## Outputs

```text
workspaces/<dea_name>/
  01_dea_context/
    dea_application_context.md          # PRIMARY — the synthesized context document
    completed_intake_worksheet.md       # PRESERVED — cleaned copy of the user's worksheet
    supporting_docs_manifest.json       # Inventory of supporting docs processed
    execution_trace.json                # Stage execution trace (model calls, tokens, cost)
```

---

## Two-Pass Synthesis Pattern

```text
Pass 0 — Generate the DEA application context from the completed worksheet + supporting docs
Pass 1 — Clean, normalize, and align against the worksheet and supporting material
```

### Pass 0: Generate Context

**Model:** GPT-5.5 (reasoning tier)

**System prompt directives:**
- Synthesize a complete agent context document from the intake worksheet
- Structure output with clear sections: What This Agent Is, Target Audience, Agent Identity, Agent Architecture, What It Must Deliver, Domain Emphasis
- Use the reference example (`modern_ux_design_example/context_document.md`) as the target output format
- Incorporate all supporting docs as additional context
- Do not invent information not present in the worksheet or supporting docs
- Use the worksheet's language and terminology — do not paraphrase away specificity

**Human message:** Completed worksheet content + supporting docs content

### Pass 1: Align and Complete

**Model:** GPT-5.5 (reasoning tier)

**System prompt directives:**
- Review the generated context document against the original worksheet
- Ensure every worksheet answer is represented in the context document
- Ensure agent identity, framing, and role are precisely captured
- Ensure business constraints and exclusions are explicitly stated
- Ensure the document is self-contained — a reader should not need the worksheet to understand the agent
- Tighten language, remove redundancy, fix inconsistencies
- Do NOT shorten — ensure completeness

**Human message:** Generated context document + original worksheet for cross-reference

---

## Implementation Tasks

### Task 1: Workspace I/O Utilities

Create shared workspace utilities that all stages will use.

**File:** `src/dea_builder/io/workspace.py`

- `ensure_stage_dirs(workspace_dir, stage_num, stage_name)` — create stage output/working dirs
- `read_input_file(workspace_dir, relative_path)` — read from `00_inputs/`
- `read_supporting_docs(workspace_dir)` — inventory and read all files in `00_inputs/supporting_docs/`
- `write_stage_output(workspace_dir, stage_num, filename, content)` — write to stage output dir
- `write_working_artifact(workspace_dir, stage_num, filename, content)` — write to stage working dir

### Task 2: Intake Worksheet Parser

Parse the structured worksheet into a typed data model.

**File:** `src/dea_builder/stages/dea_context.py`

- Parse markdown worksheet into structured sections
- Extract answers from `> [answer]` blocks
- Detect which sections are filled vs. skipped
- Return a `WorksheetData` dataclass with all fields

### Task 3: Supporting Docs Ingestion

**File:** `src/dea_builder/stages/dea_context.py`

- Scan `00_inputs/supporting_docs/` for markdown, text, YAML files
- Read and concatenate content with source attribution
- Write `supporting_docs_manifest.json` with file inventory

### Task 4: Two-Pass Synthesis Pipeline

**File:** `src/dea_builder/stages/dea_context.py`

- `generate_context()` — Pass 0: worksheet + supporting docs → v0 context
- `align_context()` — Pass 1: v0 context + worksheet → v1 aligned context
- LangGraph StateGraph with state, nodes, graph builder (same pattern as Stage 4)
- Token tracking + cost estimation via shared `cost.tracker`
- Save working artifacts: `v0_raw.md`, `v1_aligned.md`
- Copy final to `01_dea_context/dea_application_context.md`
- Preserve cleaned worksheet to `01_dea_context/completed_intake_worksheet.md`

### Task 5: Stage Entry Point

**File:** `src/dea_builder/stages/dea_context.py`

- `run_stage(workspace_dir: Path) -> dict` — main entry point
- Validate inputs exist (worksheet required, supporting docs optional)
- Execute two-pass pipeline
- Write execution trace
- Return final state

### Task 6: CLI Integration

**File:** `src/dea_builder/cli/main.py`

- Add `dea-context` subcommand: `uv run python -m dea_builder dea-context workspaces/<name>`
- Display Rich console output: input summary, pass progress, cost analytics, output summary

### Task 7: Smoke Test

**File:** `scripts/smoke_stage1.py`

- Create a test workspace with the Modern UX Design example worksheet
- Run Stage 1 end-to-end
- Verify output files exist and contain expected content
- Display cost analytics

---

## Verification Criteria

1. Given a completed worksheet, Stage 1 produces a context document matching the structure of the reference example
2. All worksheet answers are represented in the output — nothing is lost
3. Supporting docs (when present) are incorporated and manifested
4. Execution trace records model calls, tokens, latency, and cost
5. Working artifacts (v0_raw.md, v1_aligned.md) are preserved
6. Stage can run independently via CLI
7. Stage exits cleanly when required inputs are missing (worksheet not found)

---

## Dependencies

- **Shared infra (already ported):** `dea_builder.llm.client`, `dea_builder.cost.tracker`
- **New shared:** `dea_builder.io.workspace` (created in Task 1, reused by all stages)
- **Reference:** `.planning/reference/expert_six_worksheet_v3_template.md` (worksheet schema)
- **Reference:** `.planning/reference/modern_ux_design_example/` (target output format)

---

## Files to Create/Modify

| File | Action |
|------|--------|
| `src/dea_builder/io/workspace.py` | Create — shared workspace I/O |
| `src/dea_builder/stages/dea_context.py` | Implement — full Stage 1 |
| `src/dea_builder/cli/main.py` | Modify — add dea-context subcommand |
| `scripts/smoke_stage1.py` | Create — end-to-end smoke test |

---

*Phase 1 Plan — DEA Context Creation*
*Updated: 2026-05-22*
