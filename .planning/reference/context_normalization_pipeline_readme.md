# README — Expert Six Context Normalization Pipeline

## Purpose

A two-template processing pipeline that converts heterogeneous context inputs into a canonical context document for the Expert Six framework. The output pairs with the Expert Six Research Prompt to drive identification of the Foundational Six experts for agent construction.

## The two templates

1. **`Context_Normalizer__Agent_Prompt.md`** — the operating prompt
2. **`Context_Document__Hardened_Template.md`** — the required output structure

## Deployment

Deploy the following as the system prompt, with both template files loaded as reference documents:

```
You are operating as the Context Normalizer. Your operating instructions are defined in Context_Normalizer__Agent_Prompt.md. The required output structure is defined in Context_Document__Hardened_Template.md. Convert the provided input into a canonical context document that exactly matches the hardened template. Follow the process and operating principles defined in the agent prompt without deviation.
```

## Execution

1. Deploy the system prompt above with both template files loaded as reference.
2. Input is provided to the pipeline — intake worksheet, interview transcript, agentic specification, free-form notes, direct specification, or any combination.
3. The normalizer produces one of two outputs:
   - **Success:** the canonical context document, conforming exactly to the hardened template.
   - **Failure:** a structured error message itemizing missing fields and/or unresolved conflicts, with a `Recovery:` directive. The exact failure output format is defined in `Context_Normalizer__Agent_Prompt.md` (Steps 3 and 4) and must be referenced when implementing the consuming pipeline.
4. On failure, the calling harness resolves the itemized gaps and re-invokes the pipeline.
5. On success, save the output as `Context__[Domain_Name]__[YYYYMMDD].md`.
6. Pair the saved document with the Expert Six Research Prompt to execute downstream identification.
