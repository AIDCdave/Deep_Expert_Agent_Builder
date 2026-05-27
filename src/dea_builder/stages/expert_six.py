"""Stage 3 — Expert Six Execution and Finalization.

Four-pass pipeline:
  Pass 0 — GPT-5.5 generates a holistic Exa search query from context + research prompt
  Pass 1 — Exa search, then GPT-5.5 synthesizes first-cut Expert Six
  Pass 2 — GPT-5.5 gap analysis, targeted Exa + Firecrawl, refined Expert Six
  Pass 3 — GPT-5.5 final audit against context document
"""

from __future__ import annotations

import json
import re
import shutil
import time
from pathlib import Path

from langchain_core.messages import HumanMessage, SystemMessage
from rich.console import Console
from rich.panel import Panel

from dea_builder.cost.tracker import TokenTracker, estimate_cost
from dea_builder.io.workspace import (
    STAGE_NAMES,
    ensure_stage_dirs,
    write_execution_trace,
    write_stage_output,
    write_working_artifact,
)
from dea_builder.llm.client import get_llm
from dea_builder.research import exa as exa_client
from dea_builder.research.firecrawl import scrape_urls

console = Console()

STAGE_NUM = 3

# ---------------------------------------------------------------------------
# System prompts
# ---------------------------------------------------------------------------

PASS0_SYSTEM = """\
You are a search-query specialist. Given a domain-specific Expert Six research \
prompt and its companion context document, generate ONE holistic Exa search \
query designed to surface the best expert practitioners in this domain.

The query should:
- Be a natural language statement (Exa uses semantic search, not keywords)
- Target practitioners with deep, long-form digital footprints
- Cover the breadth of knowledge domains specified in the context document
- Avoid generic terms that would return shallow results

Output ONLY the query string on a single line. No commentary, no quotes.
"""

PASS1_SYSTEM = """\
You are a Senior Investigative Researcher. You have received:
1. An Expert Six research prompt defining your task and criteria
2. A domain-specific context document defining the target domain
3. Search results from Exa containing potential experts and their source URLs

Using ALL THREE inputs, produce your first-cut Expert Six. For each expert:
- Full name
- Primary specialization within the target domain
- Why they qualify (evidence from search results or known body of work)
- 2-3 primary source URLs demonstrating their expertise
- Which knowledge domain(s) from the context document they cover

Also produce a COVERAGE MAP at the end showing which knowledge domains from \
Section 4 of the context document are covered by which expert(s), and flag \
any gaps.

Output in markdown format.
"""

PASS2_GAP_SYSTEM = """\
You are reviewing a first-cut Expert Six against the source context document. \
Your job:

1. Check coverage: does the proposed six cover ALL Primary Knowledge Domains \
from Section 4 of the context document?
2. Identify THIN areas: any domain with only one expert covering it, or \
domains not covered at all.
3. For each gap or thin area, generate a targeted Exa search query to find \
alternative/additional experts specifically for that gap.

Output as JSON with this structure:
{
  "gaps": [
    {
      "domain": "<knowledge domain that's thin or uncovered>",
      "reason": "<why it's a gap>",
      "search_query": "<targeted Exa query to find experts for this gap>"
    }
  ],
  "assessment": "<1-2 sentence overall coverage assessment>"
}

If coverage is complete and well-balanced, output:
{"gaps": [], "assessment": "<confirmation>"}
"""

PASS2_REFINE_SYSTEM = """\
You are a Senior Investigative Researcher finalizing the Expert Six. You have:
1. Your first-cut Expert Six
2. The original context document and research prompt
3. Additional search results from targeted gap-filling queries
4. Scraped source content verifying expert digital footprints

Produce the REFINED Expert Six. For each expert include:
- Full name
- Primary specialization
- Qualification rationale (with evidence)
- Source map: 3-5 verified URLs with brief description of each
- Knowledge domains covered (from Section 4)

Also include:
- 2-3 ALTERNATES (near-misses) with brief rationale for why they didn't make the six
- Updated COVERAGE MAP

Output in markdown format.
"""

PASS3_SYSTEM = """\
You are performing the final audit of an Expert Six selection. You have:
1. The refined Expert Six document
2. The original context document

Audit criteria:
- Does the six provide complete coverage of ALL knowledge domains in Section 4?
- Does each expert have a verified, significant digital footprint?
- Are the experts complementary (not redundant)?
- Does the collective expertise match the Agent Role described in Section 3?
- Are there any obvious omissions given the domain?
- Do the alternates make sense as backup options?

If the Expert Six is well-optimized, output it in its final form with any \
minor corrections. If significant issues exist, fix them and note what changed.

Output the FINAL Expert Six document in clean markdown. Include:
1. The six experts with full profiles
2. Selection rationale (why THIS six, as a collective)
3. Alternates
4. Coverage map
5. Any audit notes
"""


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------


def run_stage(workspace_dir: Path) -> Path:
    """Run Stage 3 — Expert Six Execution and Finalization.

    Returns path to the final Expert Six output.
    """
    console.print(
        Panel("Stage 3 — Expert Six Execution and Finalization", style="bold cyan")
    )

    ws = Path(workspace_dir)
    tracker = TokenTracker()
    t0 = time.time()

    # Load inputs from Stage 2 output
    stage2_output = ws / STAGE_NAMES[2] / "output"
    research_prompt_path = stage2_output / "expert_six_research_prompt.md"
    context_doc_path = stage2_output / "context_document.md"

    if not research_prompt_path.is_file():
        raise FileNotFoundError(
            f"Stage 2 output not found: {research_prompt_path}\n"
            "Run `dea-builder expert-six-prompt` first."
        )
    if not context_doc_path.is_file():
        raise FileNotFoundError(
            f"Context document not found: {context_doc_path}\n"
            "Run `dea-builder expert-six-prompt` first."
        )

    research_prompt = research_prompt_path.read_text(encoding="utf-8")
    context_doc = context_doc_path.read_text(encoding="utf-8")

    output_dir, working_dir = ensure_stage_dirs(ws, STAGE_NUM)
    url_cache_dir = working_dir / "url_cache"

    # ------------------------------------------------------------------
    # PASS 0 — Generate Exa query
    # ------------------------------------------------------------------
    console.print("\n[bold]Pass 0:[/bold] Generating Exa search query...")
    llm = get_llm("reasoning", callbacks=[tracker])

    response = llm.invoke([
        SystemMessage(content=PASS0_SYSTEM),
        HumanMessage(content=(
            "## Expert Six Research Prompt\n\n"
            f"{research_prompt}\n\n---\n\n"
            "## Context Document\n\n"
            f"{context_doc}"
        )),
    ])
    exa_query = response.content.strip()
    display_query = f"{exa_query[:120]}..." if len(exa_query) > 120 else exa_query
    console.print(f"  Query: [italic]{display_query}[/italic]")

    # Execute Exa search
    console.print("  Executing Exa search (20 results)...")
    exa_results = exa_client.search(exa_query, num_results=20)
    exa_md = exa_client.results_to_markdown(exa_results)

    # Save Pass 0 artifacts
    write_working_artifact(ws, STAGE_NUM, "pass0_exa_query.json", json.dumps({
        "query": exa_query, "num_results": len(exa_results)
    }, indent=2))
    write_working_artifact(ws, STAGE_NUM, "pass0_exa_results.json", json.dumps(
        exa_client.results_to_json_serializable(exa_results), indent=2
    ))
    console.print(f"  Got {len(exa_results)} results from Exa")

    # ------------------------------------------------------------------
    # PASS 1 — First-cut Expert Six
    # ------------------------------------------------------------------
    console.print("\n[bold]Pass 1:[/bold] Synthesizing first-cut Expert Six...")
    response = llm.invoke([
        SystemMessage(content=PASS1_SYSTEM),
        HumanMessage(content=(
            "## Expert Six Research Prompt\n\n"
            f"{research_prompt}\n\n---\n\n"
            "## Context Document\n\n"
            f"{context_doc}\n\n---\n\n"
            "## Exa Search Results\n\n"
            f"{exa_md}"
        )),
    ])
    first_cut = response.content.strip()
    write_working_artifact(ws, STAGE_NUM, "pass1_first_cut.md", first_cut)
    console.print("  First cut generated")

    # ------------------------------------------------------------------
    # PASS 2 — Gap analysis + targeted research + refinement
    # ------------------------------------------------------------------
    console.print("\n[bold]Pass 2:[/bold] Gap analysis...")

    # 2a: Identify gaps
    response = llm.invoke([
        SystemMessage(content=PASS2_GAP_SYSTEM),
        HumanMessage(content=(
            "## First-Cut Expert Six\n\n"
            f"{first_cut}\n\n---\n\n"
            "## Context Document\n\n"
            f"{context_doc}"
        )),
    ])

    gap_text = response.content.strip()
    write_working_artifact(ws, STAGE_NUM, "pass2_gap_analysis.md", gap_text)

    # Parse gap queries
    gap_queries: list[str] = []
    try:
        json_str = gap_text
        if "```" in json_str:
            json_str = (
                json_str.split("```json")[-1].split("```")[0]
                if "```json" in json_str
                else json_str.split("```")[1]
            )
        gap_data = json.loads(json_str.strip())
        gaps = gap_data.get("gaps", [])
        gap_queries = [g["search_query"] for g in gaps if g.get("search_query")]
        console.print(
            f"  Found {len(gaps)} gap(s): {gap_data.get('assessment', '')[:100]}"
        )
    except (json.JSONDecodeError, KeyError, IndexError):
        console.print(
            "  [yellow]Could not parse gap JSON — proceeding without targeted search[/yellow]"
        )

    # 2b: Targeted Exa searches for gaps
    all_gap_results: list[exa_client.ExaResult] = []
    if gap_queries:
        console.print(f"  Running {len(gap_queries)} targeted Exa queries...")
        for gq in gap_queries:
            gap_results = exa_client.search(gq, num_results=10)
            all_gap_results.extend(gap_results)
        write_working_artifact(ws, STAGE_NUM, "pass2_targeted_queries.json", json.dumps({
            "queries": gap_queries,
            "total_results": len(all_gap_results),
        }, indent=2))
        write_working_artifact(ws, STAGE_NUM, "pass2_exa_results.json", json.dumps(
            exa_client.results_to_json_serializable(all_gap_results), indent=2
        ))

    # 2c: Firecrawl — scrape primary source URLs from first cut
    console.print("  Scraping primary sources with Firecrawl...")
    urls_in_first_cut = re.findall(r'https?://[^\s\)\"\'>\]]+', first_cut)
    urls_to_scrape = list(dict.fromkeys(urls_in_first_cut))[:15]  # dedupe, cap at 15

    scraped = []
    if urls_to_scrape:
        scraped = scrape_urls(urls_to_scrape, url_cache_dir, delay_s=0.5)
        ok_count = sum(1 for s in scraped if s.status in ("ok", "cached"))
        console.print(f"  Scraped {ok_count}/{len(urls_to_scrape)} URLs successfully")

    # 2d: Refine Expert Six with all data
    console.print("  Refining Expert Six...")
    gap_md = (
        exa_client.results_to_markdown(all_gap_results)
        if all_gap_results
        else "No additional search results."
    )
    scraped_summary = (
        "\n".join(
            f"- {s.url} — {'verified' if s.status in ('ok', 'cached') else 'FAILED: ' + s.error}"
            for s in scraped
        )
        if scraped
        else "No URLs scraped."
    )

    response = llm.invoke([
        SystemMessage(content=PASS2_REFINE_SYSTEM),
        HumanMessage(content=(
            "## First-Cut Expert Six\n\n"
            f"{first_cut}\n\n---\n\n"
            "## Context Document\n\n"
            f"{context_doc}\n\n---\n\n"
            "## Research Prompt\n\n"
            f"{research_prompt}\n\n---\n\n"
            "## Additional Search Results (Gap-Filling)\n\n"
            f"{gap_md}\n\n---\n\n"
            "## Source Verification\n\n"
            f"{scraped_summary}"
        )),
    ])
    refined = response.content.strip()
    write_working_artifact(ws, STAGE_NUM, "pass2_refined.md", refined)
    console.print("  Refined Expert Six generated")

    # ------------------------------------------------------------------
    # PASS 3 — Final audit
    # ------------------------------------------------------------------
    console.print("\n[bold]Pass 3:[/bold] Final audit...")
    response = llm.invoke([
        SystemMessage(content=PASS3_SYSTEM),
        HumanMessage(content=(
            "## Refined Expert Six\n\n"
            f"{refined}\n\n---\n\n"
            "## Context Document\n\n"
            f"{context_doc}"
        )),
    ])
    final = response.content.strip()
    write_working_artifact(ws, STAGE_NUM, "pass3_final.md", final)

    # ------------------------------------------------------------------
    # Write outputs
    # ------------------------------------------------------------------
    output_path = write_stage_output(ws, STAGE_NUM, "expert_six_final.md", final)

    # Copy context document for downstream handoff
    dest_ctx = output_dir / "context_document.md"
    shutil.copy2(context_doc_path, dest_ctx)

    # Execution trace
    elapsed = time.time() - t0
    cost = sum(
        estimate_cost(r.model, r.prompt_tokens, r.completion_tokens)
        for r in tracker.records
    )
    trace = {
        "stage": STAGE_NUM,
        "elapsed_seconds": round(elapsed, 1),
        "estimated_cost_usd": round(cost, 4),
        "passes": {
            "pass0_query": exa_query,
            "pass0_exa_results": len(exa_results),
            "pass1_first_cut_length": len(first_cut),
            "pass2_gaps_found": len(gap_queries),
            "pass2_targeted_results": len(all_gap_results),
            "pass2_urls_scraped": len(urls_to_scrape),
            "pass2_urls_verified": sum(
                1 for s in scraped if s.status in ("ok", "cached")
            ),
        },
        "token_records": tracker.to_dicts(),
    }
    write_execution_trace(ws, STAGE_NUM, trace)

    # Summary
    console.print(
        Panel(
            f"Total time: {elapsed:.1f}s\n"
            f"Estimated cost: ${cost:.4f}\n"
            f"Exa queries: {1 + len(gap_queries)}\n"
            f"URLs scraped: {len(urls_to_scrape)}\n"
            f"Output: {output_path.relative_to(ws.parent) if ws.parent in output_path.parents else output_path}",
            title="Stage 3 Complete",
            style="bold green",
        )
    )

    return output_path
