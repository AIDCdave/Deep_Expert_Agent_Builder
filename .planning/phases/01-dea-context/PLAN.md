# Phase 1: DEA Context Creation — Plan

**Stage:** 1 of 7
**Status:** Planning
**Last updated:** 2026-05-26

---

## What This Phase Delivers

Stage 1 takes heterogeneous context inputs and produces a **Canonical Context Document** — a structured, validated specification conforming exactly to the Hardened Template. This document is the sole input to Stage 2 (Expert Six Prompt Creation).

Stage 1 is a normalization boundary. Raw inputs go in; a single canonical document comes out. No source content is carried forward to downstream stages.

---

## Design Documents

Stage 1 is defined by three documents (the first is reference, the other two are runtime):

| Document | Location | Role |
|----------|----------|------|
| Context Normalization Pipeline README | `.planning/reference/context_normalization_pipeline_readme.md` | Architecture reference |
| Context Normalizer Agent Prompt | `src/dea_builder/prompts/stage1/context_normalizer_prompt.md` | LLM operating prompt (runtime) |
| Context Document Hardened Template | `src/dea_builder/prompts/stage1/context_document_template.md` | Required output structure (runtime) |

---

## Inputs

```text
workspaces/<dea_name>/
  00_inputs/
    <any combination of input files>    # See input types below
```

The normalizer handles any combination of:

1. **Intake worksheet** — structured Q&A (e.g., Expert Six Worksheet v3)
2. **Interview transcript** — recording transcript from a conversation
3. **Agentic specification** — a manager agent's sub-agent role description
4. **Free-form document** — unstructured notes, briefs, written context
5. **Direct specification** — context fields written directly

At least one input must provide enough information to populate all required fields of the Hardened Template. Input archiving is the orchestrator's responsibility, not this stage's.

---

## Outputs

```text
workspaces/<dea_name>/
  01_dea_context/
    output/
      context_document.md               # PRIMARY — canonical context document (Hardened Template)
    working/
      v0_normalized.md                  # Pass 0 output (normalizer result)
      v1_reviewed.md                    # Pass 1 output (reviewed/refined)
      execution_trace.json              # Stage trace (model calls, tokens, cost)
```

The canonical context document conforms exactly to the 12-section Hardened Template:

1. Target Domain
2. Downstream Purpose
3. **Agent Definition** (non-negotiable)
4. Primary Knowledge Domains
5. Mandatory Inclusions
6. Prospects
7. Desired Coverage Across the Six
8. Business Context
9. Constraints & Environmental Realities
10. Domain-Specific Exclusions
11. Requester's Expertise Baseline
12. Special Instructions

---

## Pipeline: Normalize → Review

### Pass 0: Normalize (with retry-on-failure)

**Model:** GPT-5.5 (reasoning tier)

**System prompt:** Defined in `context_normalizer_prompt.md`. Deployed with the Hardened Template as reference, per the README:

> *"You are operating as the Context Normalizer. Your operating instructions are defined in Context_Normalizer__Agent_Prompt.md. The required output structure is defined in Context_Document__Hardened_Template.md. Convert the provided input into a canonical context document that exactly matches the hardened template."*

**Human message:** All input file contents, concatenated with source attribution headers.

**The normalizer produces one of two outputs:**

- **Success:** Canonical context document conforming exactly to the Hardened Template. Saved as `v0_normalized.md`.
- **Failure:** Structured error message with parseable format:

```text
ERROR: Context normalization failed — insufficient information.

Missing or partial fields:
- [Section N, Field Name]: [what is needed and why]
...

Recovery: Provide the listed information and re-invoke.
```

Or for conflicts:

```text
ERROR: Context normalization failed — unresolved conflicts.

Conflicting fields:
- [Section N, Field Name]: source A states "X"; source B states "Y". Canonical answer required.
...

Recovery: Resolve conflicts and re-invoke with a single canonical input.
```

**On failure:** The pipeline parses the structured error, logs it to the execution trace, and raises a clear exception with the itemized gaps. The calling harness (orchestrator or user) resolves and re-invokes.

**On success:** Proceed to Pass 1.

### Pass 1: Review and Refine

**Model:** GPT-5.5 (reasoning tier)

**System prompt directives:**
- You are reviewing a canonical context document that will feed an automated Expert Six research pipeline
- The document was produced by a normalizer from source inputs — your job is to ensure it is complete, precise, and optimized for downstream processing
- Cross-check every section for internal consistency
- Ensure Section 3 (Agent Definition) is fully specified with no ambiguity
- Ensure Section 7 (Desired Coverage) is derived from and consistent with Section 4 (Primary Knowledge Domains)
- Ensure all constraints (Section 9) clearly mark firm vs. flexible
- Ensure no vague placeholders remain ("TBD", "various", "to be determined")
- Tighten language for downstream LLM consumption — remove redundancy, sharpen specificity
- Do NOT shorten content that carries signal — verbose is acceptable, vague is not
- Preserve the exact Hardened Template structure — do not reorganize sections
- Output the complete reviewed document

**Human message:** The v0_normalized.md document.

**Output:** Saved as `v1_reviewed.md` and copied to `output/context_document.md`.

---

## Implementation Tasks

### Task 1: Workspace I/O Utilities

Shared workspace utilities reused by all 6 stages.

**File:** `src/dea_builder/io/workspace.py`

- `ensure_stage_dirs(workspace_dir, stage_num, stage_name)` — create stage output/working dirs
- `read_all_inputs(workspace_dir)` — read all files from `00_inputs/`, return `{filename: content}`
- `write_stage_output(workspace_dir, stage_num, filename, content)` — write to stage output dir
- `write_working_artifact(workspace_dir, stage_num, filename, content)` — write to stage working dir
- `load_prompt(stage_num, prompt_filename)` — load a prompt template from `prompts/stageN/`

### Task 2: Input Assembly

Read and prepare all input files for the normalizer.

**File:** `src/dea_builder/stages/dea_context.py`

- Read all files from `00_inputs/`
- Concatenate with source attribution headers (e.g., `=== SOURCE: completed_intake_worksheet.md ===`)
- Classify input types (worksheet, transcript, spec, free-form) — internal only, not part of output
- Return assembled context string for the normalizer

### Task 3: Normalizer Pipeline (Pass 0)

**File:** `src/dea_builder/stages/dea_context.py`

- Load `context_normalizer_prompt.md` and `context_document_template.md` at runtime
- Construct system prompt per the README deployment spec
- Invoke GPT-5.5 with assembled inputs
- Parse response: detect `ERROR:` prefix → failure path; otherwise → success path
- On failure: parse structured error into a typed result, log to trace, raise with itemized gaps
- On success: save `v0_normalized.md`
- LangGraph StateGraph (same pattern as Stage 4)
- Token tracking via `cost.tracker`

### Task 4: Review Pipeline (Pass 1)

**File:** `src/dea_builder/stages/dea_context.py`

- Take `v0_normalized.md` as input
- Invoke GPT-5.5 with review directives
- Save `v1_reviewed.md`
- Copy final to `output/context_document.md`
- Token tracking via `cost.tracker`

### Task 5: Stage Entry Point

**File:** `src/dea_builder/stages/dea_context.py`

- `run_stage(workspace_dir: Path) -> dict` — main entry point
- Validate at least one input file exists in `00_inputs/`
- Execute Pass 0 (normalize) → Pass 1 (review)
- Write execution trace
- Return final state

### Task 6: CLI Integration

**File:** `src/dea_builder/cli/main.py`

- Add `dea-context` subcommand: `uv run python -m dea_builder dea-context workspaces/<name>`
- Rich console output: input inventory, pass progress, error display (if failure), cost analytics

### Task 7: Smoke Test

**File:** `scripts/smoke_stage1.py`

- Create a test workspace with the Modern UX Design example worksheet
- Run Stage 1 end-to-end
- Verify output conforms to Hardened Template structure
- Verify all 12 sections present and populated
- Display cost analytics

---

## Error Handling

The normalizer's structured failure format is a first-class pipeline feature:

1. **Parse failure output** — extract missing fields and/or conflicts into typed data
2. **Log to execution trace** — record the failure, itemized gaps, and attempt number
3. **Raise `NormalizationError`** — with the parsed gaps attached, so the caller can resolve
4. **No silent fallback** — a partial document is never emitted. Failure is explicit and structured.

The orchestrator (Phase 7) will implement the retry loop: resolve gaps → re-invoke. For now, Stage 1 fails cleanly with actionable error output.

---

## Key Design Decision: Clean Pipeline Boundary

Source content (worksheets, transcripts, notes) is NOT carried forward to downstream stages. The canonical context document is the sole interface between Stage 1 and Stage 2+. This is intentional:

- The normalizer is a one-way valve — signal goes through, noise stays behind
- Each stage's output is the complete, self-contained input for the next stage
- Raw inputs remain in `00_inputs/` for audit but are never piped downstream

---

## Verification Criteria

1. Given sufficient input, Stage 1 produces a context document conforming exactly to the 12-section Hardened Template
2. All required fields are populated with specific, non-placeholder content
3. Section 3 (Agent Definition) is complete — this is non-negotiable
4. Section 7 (Desired Coverage) is consistent with Section 4 (Primary Knowledge Domains)
5. Insufficient input produces a structured `ERROR:` with parseable missing-field list
6. Conflicting inputs produce a structured `ERROR:` with parseable conflict list
7. Execution trace records model calls, tokens, latency, cost, and any failure attempts
8. Working artifacts (v0_normalized.md, v1_reviewed.md) are preserved
9. Stage can run independently via CLI
10. No source content leaks into the output directory beyond the canonical document

---

## Dependencies

- **Shared infra (already ported):** `dea_builder.llm.client`, `dea_builder.cost.tracker`
- **New shared:** `dea_builder.io.workspace` (created in Task 1, reused by all stages)
- **Runtime prompts:** `src/dea_builder/prompts/stage1/context_normalizer_prompt.md`
- **Runtime template:** `src/dea_builder/prompts/stage1/context_document_template.md`
- **Test data:** `.planning/reference/modern_ux_design_example/completed_intake_worksheet.md`

---

## Files to Create/Modify

| File | Action |
|------|--------|
| `src/dea_builder/io/workspace.py` | Create — shared workspace I/O |
| `src/dea_builder/stages/dea_context.py` | Implement — full Stage 1 |
| `src/dea_builder/cli/main.py` | Modify — add dea-context subcommand |
| `scripts/smoke_stage1.py` | Create — end-to-end smoke test |

Files already in place:
| File | Status |
|------|--------|
| `src/dea_builder/prompts/stage1/context_normalizer_prompt.md` | ✅ Copied |
| `src/dea_builder/prompts/stage1/context_document_template.md` | ✅ Copied |
| `.planning/reference/context_normalization_pipeline_readme.md` | ✅ Copied |

---

*Phase 1 Plan — DEA Context Creation*
*Updated: 2026-05-26*
