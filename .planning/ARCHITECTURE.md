# AIDC DEA Builder — Architecture Overview

## Purpose

The AIDC DEA Builder is a file-driven, multi-stage pipeline for creating **Deep Expert Agents (DEAs)**.

It converts structured intent-capture material into a deployment-ready agent package through seven stages:

1. **DEA Context Creation**
2. **Expert Six Prompt Creation**
3. **Expert Six Execution and Finalization**
4. **Epistemic Anchor Creation**
5. **EARL Agent Package Creation**
6. **Target Deployment Packaging**
7. **Main Orchestrator** (pending)

The first implementation should remain intentionally simple:

- local Python execution
- Unix/macOS development environment
- `uv` or Python virtual environment
- file-based inputs and outputs from beginning to end
- direct Azure Cognitive Services inference (no LiteLLM proxy)
- GPT-5.5 as the preferred reasoning model for synthesis
- GPT-5.4-nano or equivalent fast model only for small mechanical tasks
- deterministic orchestration around a small number of high-value model calls

The system is designed first as a reliable local artifact factory. It can later evolve into a UI, hosted workflow, service, or broader agent-building platform, but the current architectural priority is to make each stage clear, inspectable, repeatable, and independently testable.

---

## Core Architectural Principle

The system should separate **reasoning-heavy synthesis** from **mechanical orchestration**.

Python should own:

- directory setup
- input validation
- file placement
- manifest creation
- stage execution
- model routing
- trace capture
- cost and token accounting
- output validation
- resumability
- deterministic packaging

The LLM should own:

- synthesis
- expert reasoning
- context transformation
- completeness review
- instruction generation where judgment is required
- alignment of generated artifacts with the DEA intent

This pipeline is not an autonomous agent swarm. It is a deterministic build system that uses reasoning models at carefully chosen points.

---

## Key Learning from Epistemic Anchor Implementation

The existing epistemic-anchor builder produced the most important architectural lesson so far.

Three approaches were tested:

| Approach | Result |
|---|---|
| Multi-stage pipeline | Overprocessed the material, increased cost, and produced poorer fragmented output |
| Pure one-shot generation | Produced a coherent draft but required cleanup |
| Two-pass generation | Produced the best result: holistic generation followed by context-aligned cleanup |

The durable pattern is:

```text
Pass 0 — Holistic generation from all relevant context
Pass 1 — Cleanup, completion, and alignment against the solution context
```

This pattern should be reused for reasoning-heavy synthesis stages, especially:

- Expert Six prompt creation
- Expert Six finalization
- Epistemic anchor creation
- EARL agent package creation

The important negative lesson is also clear: do not break a reasoning-heavy synthesis task into many small template-filling calls unless the task is genuinely mechanical. That loses cross-reference quality, increases orchestration complexity, and can degrade output.

---

## Six-Stage Pipeline

```text
┌────────────────────────────────────────────────────────────┐
│  1. DEA Context Creation                                   │
│  Why are we building this DEA, for whom, and for what use?  │
└───────────────┬────────────────────────────────────────────┘
                ▼
┌────────────────────────────────────────────────────────────┐
│  2. Expert Six Prompt Creation                             │
│  Convert DEA context into a precise research prompt         │
└───────────────┬────────────────────────────────────────────┘
                ▼
┌────────────────────────────────────────────────────────────┐
│  3. Expert Six Execution and Finalization                   │
│  Execute research, generate candidates, scrub to final six   │
└───────────────┬────────────────────────────────────────────┘
                ▼
┌────────────────────────────────────────────────────────────┐
│  4. Epistemic Anchor Creation                              │
│  Create the deep reasoning substrate for the DEA             │
└───────────────┬────────────────────────────────────────────┘
                ▼
┌────────────────────────────────────────────────────────────┐
│  5. EARL Agent Package Creation                            │
│  Create the canonical runtime-neutral agent package          │
└───────────────┬────────────────────────────────────────────┘
                ▼
┌────────────────────────────────────────────────────────────┐
│  6. Target Deployment Packaging                            │
│  Adapt the EARL package for a specific runtime target        │
└────────────────────────────────────────────────────────────┘
```

---

## Stage 1 — DEA Context Creation

### Purpose

Stage 1 creates the **Deep Expert Agent Application Context**.

This stage answers:

```text
Why are we building this DEA?
Who will use it?
What work should it help perform?
What domain or operating context must it understand?
What does success look like?
What boundaries or non-goals matter?
```

This is the intent and requirements capture layer. It does **not** create the Expert Six prompt directly as its main output. It creates the context from which the Expert Six prompt will later be generated.

### Inputs

```text
00_inputs/
  <any combination of input files>
```

Stage 1 accepts **heterogeneous context inputs** in any combination:

- Intake worksheet (structured Q&A, e.g., Expert Six Worksheet v3)
- Interview transcript
- Agentic specification (a manager agent's sub-agent role description)
- Free-form document (notes, briefs, written context)
- Direct specification (context fields written directly)

At least one input must provide enough information to populate all required fields of the Hardened Template.

### Outputs

```text
01_dea_context/
  output/
    context_document.md               # Canonical context document (Hardened Template)
  working/
    v0_normalized.md
    v1_reviewed.md
    execution_trace.json
```

### Notes

Stage 1 uses the **Context Normalizer** — a hardened LLM prompt that converts heterogeneous inputs into a canonical context document conforming exactly to a 12-section Hardened Template. The normalizer produces one of two outputs:

- **Success:** Canonical context document. No deviations from template structure.
- **Failure:** Structured error itemizing missing fields and/or unresolved conflicts, with a recovery directive.

The pipeline pattern is:

```text
Pass 0 — Normalize: Context Normalizer prompt + Hardened Template → canonical document (or structured failure)
Pass 1 — Review: cross-check for internal consistency, sharpen for downstream LLM consumption
```

Source content is NOT carried forward to downstream stages. The canonical context document is the sole interface between Stage 1 and Stage 2+. Raw inputs remain in `00_inputs/` for audit.

The result should be clear enough that a later process can build a precise Expert Six prompt without re-asking the foundational intent questions.

---

## Stage 2 — Expert Six Prompt Creation

### Purpose

Stage 2 consumes the DEA application context and creates the **Expert Six research prompt**.

This is a distinct stage because the Expert Six prompt must be explicit, detailed, and tuned to the intended DEA. It is not a generic research instruction. It is the research specification that determines which expert lenses will shape the eventual agent.

This stage answers:

```text
What kinds of experts should be found?
Which subdomains matter?
What selection criteria should be used?
What trade-offs should the research surface?
What output format should the Expert Six result follow?
How should alternates be identified?
How should the experts be evaluated against the DEA context?
```

### Inputs

```text
01_dea_context/
  dea_application_context.md

00_inputs/
  samples/
    sample_expert_six_prompt.md   # optional
```

Optional supporting inputs may include:

- previous high-quality Expert Six prompts
- domain-specific selection criteria
- known candidate experts to include or exclude
- style and format templates

### Outputs

```text
02_expert_six_prompt/
  expert_six_research_prompt.md
  prompt_build_notes.md
  execution_trace.json
```

### Notes

This stage should produce a research prompt that can be handed to a research engine, browser assistant, Claude Code research skill, or equivalent system.

This prompt should be deliberately verbose and unambiguous. It should include:

- DEA context summary
- expert selection objectives
- target expert categories
- research depth expectations
- required evidence style
- required output format
- alternate-candidate handling
- final selection guidance
- warnings against shallow fame-based selection

The two-pass pattern is again appropriate:

```text
Pass 0 — Generate the Expert Six research prompt from DEA context
Pass 1 — Tighten, clarify, and enforce the expected output template
```

---

## Stage 3 — Expert Six Execution and Finalization

### Purpose

Stage 3 executes the Expert Six prompt and produces the final Expert Six document.

This stage has two internal movements:

```text
3A — Execute the Expert Six research prompt
3B — Scrub, rank, and finalize the Expert Six against the DEA context
```

Stage 3 should normally produce a richer candidate set first, then reduce that set to the final six experts. The intermediate set may include the initial six plus alternates.

### Inputs

```text
01_dea_context/
  dea_application_context.md

02_expert_six_prompt/
  expert_six_research_prompt.md

03_expert_six/
  selection_policy.yaml          # optional
```

Research tools may include:

- Exa
- Firecrawl
- browser-assisted research
- Claude Code research skill
- GPT-5.5 or Claude synthesis

### Outputs

```text
03_expert_six/
  raw_research.md
  candidate_experts.json
  candidate_experts.md
  alternates.md
  expert_six_final.md
  selection_rationale.md
  source_manifest.json
  execution_trace.json
```

### Notes

This stage should be capable of both interactive and batch operation.

In interactive mode, the system presents the candidate set, alternates, trade-offs, and context fit. The user may approve, reject, swap, or reprioritize experts.

In batch mode, the system uses the DEA context and selection policy to produce the final Expert Six automatically.

The final document should not merely list experts. It should explain:

- why each expert belongs
- what domain lens each contributes
- what failure modes each helps avoid
- where the experts complement or challenge each other
- how the collective wisdom applies to the target DEA
- which alternates were rejected and why

This stage should preserve the same architectural lesson from the epistemic-anchor builder: do not overprocess the reasoning into many small calls. Use tools for search and source capture, then use holistic synthesis and one cleanup/alignment pass for finalization.

---

## Stage 4 — Epistemic Anchor Creation

### Purpose

Stage 4 creates the epistemic anchor: the deep reasoning substrate for the DEA.

The epistemic anchor is not the agent itself. It is the rich domain, reasoning, operating, and judgment foundation from which the agent will later be built.

### Inputs

```text
01_dea_context/
  dea_application_context.md

03_expert_six/
  expert_six_final.md

04_epistemic_anchor/
  sources/
    anchor_meta_prompt.md
    anchor_template.md
    sample_anchor.md
```

### Outputs

```text
04_epistemic_anchor/
  output/
    epistemic_anchor.md
  working/
    v0_raw.md
    v1_optimized.md
    manifest.json
    execution_trace.json
```

### Notes

This stage already has a proven implementation pattern.

The recommended implementation is:

```text
Phase 1 — Ingest and validate source files
Phase 2 — Generate and optimize
```

The model-call pattern should remain:

```text
Pass 0 — GPT-5.5 holistic generation from all source material
Pass 1 — GPT-5.5 optimization and alignment pass
```

The goal is verbose, complete, internally consistent, and instructive output. Compression is not the objective.

---

## Stage 5 — EARL Agent Package Creation

### Purpose

Stage 5 creates the **EARL Agent Package**.

EARL is the canonical runtime-neutral agent-definition package. It converts the epistemic anchor into an agent behavior contract and supporting artifacts, but it should not overfit to a particular deployment runtime.

This stage answers:

```text
What is this agent?
Who is it for?
What does it do?
What does it not do?
How should it behave?
What knowledge does it require?
What tool policy applies?
What safety boundaries matter?
What examples should be used to evaluate it?
```

### Inputs

```text
04_epistemic_anchor/
  output/
    epistemic_anchor.md

05_earl/
  earl_context.md
  earl_meta_prompt.md
  agent_runtime_assumptions.yaml
```

### Outputs

```text
05_earl/
  output/
    earl_agent_package.md
    canonical_system_prompt.md
    agent_behavior_contract.md
    knowledge_pack_manifest.json
    tool_policy.md
    safety_boundaries.md
    eval_seed_set.md
    deployment_assumptions.md
  working/
    v0_earl_raw.md
    v1_earl_aligned.md
    validation_report.json
    execution_trace.json
```

### Notes

EARL should produce the canonical definition of the agent’s intelligence, behavior, boundaries, and evaluation seeds.

The correct boundary is:

```text
EARL = canonical agent behavior and knowledge package
Deployment Packaging = runtime-specific adaptation
```

This separation preserves reversibility. If a deployment surface changes, only Stage 6 should need adjustment.

---

## Stage 6 — Target Deployment Packaging

### Purpose

Stage 6 converts the EARL output (`agent.adl.yaml` + `chatgpt_custom_gpt/`) into deployment-ready packages for multiple target platforms. It produces a Portable Agent Spec (PAS) as the always-on model-agnostic output, then generates platform-specific packages in parallel, followed by a cross-target fidelity inspection.

### Pipeline

```text
Phase 0 — Input Assembly + ADL Validation
Phase 1 — PAS Generation (always, first)
Phase 2 — Parallel Target Conversion Pipes
Phase 3 — Fidelity Inspection Pass
```

### Targets (7)

| Target | Type | Key Characteristics |
|---|---|---|
| `pas` | Model-agnostic | OpenAI Chat Completions contract, always produced first |
| `chatgpt-custom-gpt` | Copy + stamp | Copied from EARL, provenance stamped |
| `openai-responses` | Model-bound | OpenAI Responses API, `responses.create` envelope |
| `claude` | Model-bound | XML-segmented prompts, Anthropic tool-use format |
| `gemma-4` | Model-bound | Open model, explicit runtime manifest + model config |
| `hermes` | Runtime framework | SOUL.md + AGENTS.md + config.yaml conventions |
| `grok` | Model-bound | xAI Responses API, built-in tools (web_search, x_search) |

Key distinctions:

- **Hermes** is a runtime framework (model-agnostic), not a model. It has specific file conventions (SOUL.md for identity, AGENTS.md for project context, config.yaml for runtime).
- **Grok** is model-bound (xAI), uses the Responses API at `api.x.ai/v1`, and has unique built-in tools (`x_search`, `collections_search`).
- Hermes and Grok are fully independent targets — never conflated.

### Inputs

```text
05_earl/
  output/
    agent.adl.yaml                              # Canonical agent definition
    chatgpt_custom_gpt/
      02_instructions/system_prompt.md           # Source system prompt
      03_knowledge/*.md                          # Knowledge files
      05_actions/                                # Tool/action definitions
```

Pipe inputs per target: system prompt + knowledge manifest (names/descriptions only, not full content) + tools + PAS as reference. Full knowledge file content is NOT sent to reduce cost.

### Outputs

```text
06_deployments/
  output/
    portable_agent_spec/
      pas.yaml
      system_prompt.md
      README.md
    chatgpt_custom_gpt/                          # Full copy from EARL + provenance.yaml
    openai_responses/
      responses_request.yaml
      system_prompt.md
      tools.yaml
      knowledge_manifest.yaml
      README.md
    claude/
      system_prompt.md
      tools.yaml
      knowledge_manifest.yaml
      deployment_manifest.yaml
      eval_plan.yaml
    gemma/
      prompt.txt
      model_config.yaml
      knowledge_manifest.yaml
      runtime_manifest.yaml
      eval_plan.yaml
    hermes/
      SOUL.md
      AGENTS.md
      config.yaml
      tools_manifest.yaml
      knowledge_manifest.yaml
      README.md
    grok/
      system_prompt.md
      responses_request.yaml
      functions.yaml
      knowledge_manifest.yaml
      deployment_manifest.yaml
      README.md
    fidelity_report.md
  working/
    execution_trace.json
    *_raw_response.md                            # Per-target raw LLM responses
```

### Provenance

Every generated package includes a provenance block:

```yaml
provenance:
  source_adl_file: agent.adl.yaml
  adl_version: "1.0"
  source_hash: <sha256 of agent.adl.yaml>
  generated_at: <ISO 8601 UTC>
  generator: dea-builder/phase6
```

### Fidelity Inspection

The inspection pass validates ALL generated targets against the source ADL and system prompt. It checks:

- Role, scope, persona, constraint preservation
- Tool boundary preservation (no invented capabilities)
- Knowledge reference preservation
- Output contract preservation
- Platform-specific correctness (adaptations vs behavioral changes)

Severity: PASS (faithful), WARN (minor gaps/assumptions), FAIL (semantic drift).

### CLI

```bash
# All targets (default)
dea-builder package <workspace>

# Specific targets
dea-builder package <workspace> --targets pas,claude,grok

# Custom output directory
dea-builder package <workspace> --output /path/to/output
```

### Implementation

- **Stage module:** `src/dea_builder/stages/target_deploy.py`
- **Prompt files:** `src/dea_builder/prompts/stage6/{pas,openai_responses,claude,gemma,hermes,grok,fidelity_inspection}.md`
- **LLM tier:** Reasoning (GPT-5.5 trusted) for all generation and inspection passes
- **LiteLLM:** `litellm.config.yaml` + `scripts/start-litellm.sh` for PAS smoke testing

---

## Main Orchestrator

The system needs an orchestrated main program that coordinates the full pipeline.

The main program should:

- initialize workspace directories
- place input files into expected locations
- validate stage prerequisites
- execute Stage 1 through Stage 6 programs
- skip completed stages when outputs are already valid
- support forced re-run of one or more stages
- write a top-level execution trace
- surface costs, warnings, and missing inputs
- preserve intermediate artifacts

The orchestrator should not contain all stage logic directly. It should call stage modules with clear contracts.

### Example CLI

```bash
uv run python -m aidc_builder run ./workspaces/<dea_name>
```

With target packaging:

```bash
uv run python -m aidc_builder run ./workspaces/<dea_name> --target chatgpt-custom-gpt
```

### Stage-Specific CLI

```bash
dea-builder dea-context ./workspaces/<dea_name>
dea-builder expert-six-prompt ./workspaces/<dea_name>
dea-builder expert-six ./workspaces/<dea_name>
dea-builder anchor ./workspaces/<dea_name>
dea-builder earl ./workspaces/<dea_name>
dea-builder package ./workspaces/<dea_name> [--targets pas,claude,grok] [--output <dir>]
```

### Planning Mode

```bash
uv run python -m aidc_builder plan ./workspaces/<dea_name>
```

Planning mode should report:

- detected files
- missing files
- completed stages
- runnable stages
- blocked stages
- estimated model calls
- estimated cost
- configured model routes
- target deployment profile

---

## Workspace Layout

```text
workspaces/
  <dea_name>/
    00_inputs/
      <heterogeneous input files>

    01_dea_context/
      output/
        context_document.md
      working/
        v0_normalized.md
        v1_reviewed.md
        execution_trace.json

    02_expert_six_prompt/
      expert_six_research_prompt.md
      prompt_build_notes.md
      execution_trace.json

    03_expert_six/
      raw_research.md
      candidate_experts.json
      candidate_experts.md
      alternates.md
      expert_six_final.md
      selection_rationale.md
      source_manifest.json
      execution_trace.json

    04_epistemic_anchor/
      sources/
      output/
        epistemic_anchor.md
      working/
        v0_raw.md
        v1_optimized.md
        manifest.json
        execution_trace.json

    05_earl/
      output/
        earl_agent_package.md
        canonical_system_prompt.md
        agent_behavior_contract.md
        knowledge_pack_manifest.json
        tool_policy.md
        safety_boundaries.md
        eval_seed_set.md
        deployment_assumptions.md
      working/
        v0_earl_raw.md
        v1_earl_aligned.md
        validation_report.json
        execution_trace.json

    06_deployments/
      <target_name>/
        packaged_agent_artifacts
        validation_checklist.md
        deployment_trace.json

    runs/
      <timestamp>/
        pipeline_trace.json
        stage_summaries/
```

---

## Shared Implementation Components

The implementation should share common modules across all stage programs.

```text
aidc_builder/
  cli/
  orchestration/
  stages/
    dea_context.py
    expert_six_prompt.py
    expert_six.py
    epistemic_anchor.py
    earl.py
    target_deploy.py
  llm/
  research/
  io/
  validation/
  tracing/
  cost/
  config/
  artifacts/
```

### Common Responsibilities

```text
llm/          Azure OpenAI client, tiered model routing, trusted deployment, content safety scan
research/    Exa and Firecrawl integration
io/          file loading, writing, directory conventions
validation/  schema checks, required file checks, output checks
tracing/     execution trace and model-call trace
cost/        token and cost accounting
config/      YAML configuration and environment resolution
artifacts/   workspace and artifact management
```

---

## Model Routing

Model routing should be configuration-driven.

Example:

```yaml
models:
  synthesis: azure/gpt-5.5
  cleanup: azure/gpt-5.5
  fast: azure/gpt-5.5-nano

routing:
  dea_context:
    generate: synthesis
    cleanup: cleanup
  expert_six_prompt:
    generate: synthesis
    cleanup: cleanup
  expert_six:
    synthesize: synthesis
    finalize: cleanup
  epistemic_anchor:
    generate: synthesis
    optimize: cleanup
  earl:
    generate: synthesis
    align: cleanup
  deployment_package:
    transform: fast
```

The current experience indicates:

- GPT-5.5 is preferred for major synthesis
- GPT-5.5 Nano may be useful for quick validation and small transforms
- Grok should not be a default model route based on current observed quality

---

## Content Filter Architecture — Trusted Pipeline

Azure OpenAI deployments include Prompt Shields (jailbreak detection) by default. The epistemic anchor and EARL system prompts contain large volumes of behavioral constraint language ("must not", "never", "do not") that triggers jailbreak false positives on the reasoning-tier deployment.

The solution is a two-deployment architecture with a single trust boundary:

```text
┌─────────────────────────────────────────────────────────────────────┐
│  Module 1 — TRUST BOUNDARY                                          │
│                                                                     │
│  1. Prompt Shields scan (Azure AI Content Safety API)               │
│     → Scans human-authored context input before pipeline ingestion  │
│     → Halts pipeline on detection                                   │
│                                                                     │
│  2. LLM calls on DEFAULT deployment (Prompt Shields ON)             │
│     → Normalize and review human content with full protection       │
└───────────────────────────┬─────────────────────────────────────────┘
                            ▼
┌─────────────────────────────────────────────────────────────────────┐
│  Modules 2–6 — TRUSTED PIPELINE                                     │
│                                                                     │
│  All LLM calls use `aoai-gpt55-trusted` deployment                  │
│  (Prompt Shields OFF, harm filters at default Medium)               │
│                                                                     │
│  Content is entirely pipeline-generated — no human input,           │
│  no external documents. Already passed Module 1 scan.               │
└─────────────────────────────────────────────────────────────────────┘
```

### Key Decisions

- **Prompt Shields for direct attacks OFF** on the trusted deployment. All harm category filters and protected material filters remain at platform defaults.
- **Standalone Prompt Shields scan** at Module 1 via the Azure AI Content Safety REST API. This is separate from per-deployment filters — it's an explicit API call before any LLM inference.
- **CONTENT_SAFETY_KEY** is stored in Azure Key Vault (`kv-aidc-eus2`), fetched at startup via `az keyvault secret show`. Mirrors the AIDC `fetch-secrets.sh` pattern.
- **Fail-loud startup validation**: all required env vars (`AZURE_OPENAI_TRUSTED_DEPLOYMENT`, `CONTENT_SAFETY_ENDPOINT`) and Key Vault secrets are validated before any LLM or API call. Missing config fails at boot, not at first inference.

### Azure Resources

| Resource | Name | Purpose |
|----------|------|---------|
| RAI Content Filter | `aidc-trusted-author-filter` | Jailbreak OFF, all else default |
| GPT-5.5 Deployment | `aoai-gpt55-trusted` | Trusted deployment with above filter |
| Content Safety | `aidc-content-safety` | Standalone Prompt Shields API for Module 1 |
| Key Vault Secret | `content-safety-key` in `kv-aidc-eus2` | Content Safety API key |

See `.planning/issues/azure_trusted_deployment_spec.md` for full configuration details.

---

## Execution Trace

Every stage should emit a trace.

A minimum trace should include:

```json
{
  "stage": "expert_six_prompt",
  "started_at": "...",
  "completed_at": "...",
  "status": "success",
  "input_files": [],
  "output_files": [],
  "model_calls": [],
  "token_estimates": {},
  "cost_estimates": {},
  "warnings": []
}
```

The top-level orchestrator should also emit a pipeline trace that links all stage traces.

This is required for cost visibility, reproducibility, debugging, and later quality improvement.

---

## Validation Strategy

Validation should be deterministic wherever possible.

Python should validate:

- required directories
- required files
- YAML and JSON schema validity
- minimum content length
- expected headings
- output artifact presence
- known target profile names
- stage dependency completion
- trace existence

The LLM should validate only judgment-heavy concerns, such as:

- whether the Expert Six prompt is sufficiently specific
- whether selected experts fit the DEA context
- whether the epistemic anchor is instructive and complete
- whether the EARL package is behaviorally coherent
- whether deployment packaging lost critical meaning

Do not ask a model to validate what code can validate.

---

## Current Implementation Priority

The logical build order is:

```text
1. Workspace schema and orchestration skeleton
2. Stage 1 — DEA Context Creation
3. Stage 2 — Expert Six Prompt Creation
4. Stage 3 — Expert Six Execution and Finalization
5. Stage 4 — Epistemic Anchor Creation integration
6. Stage 5 — EARL Agent Package Creation
7. Stage 6 — Target Deployment Packaging for the first active target
```

The existing epistemic-anchor implementation should be integrated rather than redesigned. Its two-pass generate-and-optimize pattern is the strongest working reference in the system.

---

## Non-Goals for the First Implementation

The first implementation should not attempt to build:

- a web UI
- a database-backed workflow system
- a hosted service
- Kubernetes deployment
- multi-user collaboration
- elaborate deployment adapters for every runtime
- autonomous agent orchestration
- custom model training
- complex state management beyond files and traces

Those can be considered later if the file-driven pipeline proves stable and useful.

---

## Architecture Summary

The AIDC DEA Builder is a seven-stage, file-driven artifact factory for creating Deep Expert Agents.

The key design choices are:

- use files as the source of truth
- use a main orchestrator to run stage programs
- separate DEA context creation from Expert Six prompt creation
- execute and finalize the Expert Six as its own stage
- preserve the proven two-pass synthesis pattern
- keep EARL canonical and runtime-neutral
- keep deployment packaging as a thin adapter layer
- capture traces, costs, inputs, and outputs for every run
- avoid premature UI, database, service, or deployment complexity

The architecture should remain boring, explicit, and inspectable.

That is the correct posture for building the full DEA lifecycle without burying the implementation under its own machinery.
