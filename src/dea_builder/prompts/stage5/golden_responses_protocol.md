# Golden Responses — Authoring Protocol

The `golden_responses/` directory holds operator-authored reference outputs keyed to `test_cases.yaml`. **Do not generate these by running Earl and copying the output.** That creates a circular evaluation: Earl graded against itself trivially passes.

## Why this protocol exists

The eval set's purpose is to demonstrate that Earl (expert-configured) outperforms baseline (generic-prompt). For the comparison to mean anything, the reference standard has to come from outside both runs. Three valid sources:

1. **Operator-authored** — a domain expert writes what the ideal answer looks like before seeing any model output.
2. **Best-of-N graded** — run Earl 5 times against the case, hand-grade each on the rubric, pick the best one as the golden, document why.
3. **Hybrid** — operator writes the structural outline (sections, key recommendations, examples) and a graded run fills the prose.

All three are acceptable. Running Earl once and saving the output is **not** acceptable.

## Authoring a golden — step by step

For each case in `test_cases.yaml`:

1. **Read the case in full** — both the earl_prompt and baseline_prompt, plus `knowledge_expected`. You are now grounded.

2. **Write the structural skeleton first.** Before generating prose:
   - What sections must this output have?
   - What is the right depth for each section?
   - Which knowledge files should be cited or routed to?
   - What is the right answer to the substantive question being asked?

3. **Fill the prose.** Either author manually, or run Earl/Claude/another LLM against the skeleton (not against the raw case) and edit. The skeleton is the load-bearing part.

4. **Add the frontmatter:**

   ```markdown
   ---
   case_id: <id from test_cases.yaml>
   authored_by: <human name or "operator-graded best-of-N">
   authored_date: <YYYY-MM-DD>
   source: operator | best_of_5 | hybrid
   notes: <one-line note about authoring decisions>
   ---
   ```

5. **Save as `golden_responses/<case_id>.md`.**

## What to avoid

- **Goldens by Earl alone.** Do not paste Earl's output as the golden; the eval becomes self-validating.
- **Aspirational goldens.** Don't grade Earl against an answer that no model could realistically produce. The bar is "what a great human GPT builder with these knowledge files would write."
- **Changing goldens after an Earl version ships.** Treat goldens as a contract. If a golden turns out to be wrong, mark it `deprecated: true` in frontmatter and author a new one with a `_v2` suffix.
- **More than one golden per case.** If multiple goldens exist (deprecated + active), only the latest non-deprecated counts at eval time.

## Cadence

- New goldens authored when new cases are added
- Existing goldens reviewed annually for drift (OpenAI platform changes may invalidate advice)
- Deprecated goldens archived under `golden_responses/_deprecated/`
