You are generating a **Gemma 4** deployment package — a model-bound open-model target requiring explicit separation of model-facing prompt, model configuration, and runtime assumptions.

Gemma is an open model family. A prompt alone is NOT enough for deployability — runtime wrapper, inference server, and retrieval configuration must be explicitly addressed.

## Input

You will receive:
1. The source `agent.adl.yaml`
2. The source system prompt from the ChatGPT Custom GPT package
3. A knowledge manifest listing knowledge file names and their purposes
4. Source tool/action definitions (if any exist)
5. The PAS output (pas.yaml + system_prompt.md) as reference
6. A pre-computed provenance block

## Output

Produce FIVE files as clearly delimited sections:

### FILE: prompt.txt

Plain-text model-facing prompt for Gemma:
- Adapt to Gemma's instruction format (direct instruction style, no XML, no markdown formatting that Gemma may not handle well)
- Preserve ALL source role, scope, persona, behavior, constraints, and output contracts
- Structure clearly with section markers: ROLE, TASK, CONSTRAINTS, OUTPUT FORMAT
- Keep it concise — Gemma has smaller context windows than GPT-5.5

### FILE: model_config.yaml

```yaml
provenance:
  <<provenance block>>
model_config:
  requested_model: gemma-4
  validated_model: ASSUMPTION  # mark as assumption unless we have official validation
  validation_status: unvalidated
  tokenizer_notes: "Gemma uses SentencePiece tokenizer; verify prompt fits within context window"
  generation_parameters:
    temperature: null
    top_p: null
    top_k: null
    max_output_tokens: null
  unsupported_settings: []
  notes: []
```

### FILE: knowledge_manifest.yaml

Only if source knowledge exists. Map source knowledge to Gemma-compatible handling:
- Gemma does NOT have built-in knowledge/file-search
- Document whether each knowledge file requires: prompt context injection, RAG pipeline, or external retrieval system
- Flag any knowledge files that exceed what can be prompt-injected
- Generate explicit warnings about retrieval infrastructure requirements

### FILE: runtime_manifest.yaml

```yaml
provenance:
  <<provenance block>>
runtime:
  runtime_type: ASSUMPTION  # e.g., vLLM, TGI, Ollama, Google AI Studio
  inference_server_assumption: "Requires OpenAI-compatible inference server (vLLM, TGI, Ollama, or Google AI Studio)"
  wrapper_required: true
  knowledge_runtime: UNKNOWN  # RAG pipeline required if knowledge files exist
  tool_runtime_required: false  # true if source tools exist
  tool_framework: UNKNOWN      # if tools exist, framework TBD
  deployment_blockers: []
  assumptions: []
```

### FILE: eval_plan.yaml

Evaluation plan adapted for Gemma:
- Map source eval criteria
- Note model-specific behavioral differences to watch for
- Flag capabilities that Gemma may not support natively (e.g., function calling support varies by serving framework)

## Rules

- **Source fidelity**: Preserve all source behaviors, constraints, and intent
- **No creative expansion**: Do not invent capabilities Gemma does not have
- **Mark assumptions**: Any unvalidated claim about Gemma capabilities must be marked as `ASSUMPTION` or `UNKNOWN`
- **Runtime honesty**: Explicitly state what infrastructure is needed — do not pretend Gemma has built-in tool calling or knowledge search unless validated
- **Target Capability Rule**: Do not claim Gemma version behavior unless validated from official docs
- Delimit each file with `=== FILE: <filename> ===` headers
