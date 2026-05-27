"""Stage 4 — Epistemic Anchor Creation.

Creates the deep reasoning substrate for the DEA via 2-pass GPT-5.5 pipeline.
Ported from AIDC_Agent_Builder (proven implementation).

Architecture: input_assembly → generate_anchor (GPT-5.5) → optimize_anchor (GPT-5.5) → END

Workspace layout:
    04_epistemic_anchor/
        sources/
            anchor_meta_prompt.md
            anchor_template.md
            sample_anchor.md
        output/
            epistemic_anchor.md
        working/
            v0_raw.md
            v1_optimized.md
            manifest.json
            execution_trace.json
"""

from __future__ import annotations

import json
import operator
import time
from pathlib import Path
from typing import Annotated, Any, TypedDict

from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.graph import END, StateGraph

from rich.console import Console
from rich.panel import Panel

from dea_builder.cost.tracker import TokenTracker, estimate_cost
from dea_builder.io.workspace import STAGE_NAMES, ensure_stage_dirs, load_prompt
from dea_builder.llm.client import get_llm
from dea_builder.research.firecrawl import load_cached_extractions

console = Console()


# ---------------------------------------------------------------------------
# State
# ---------------------------------------------------------------------------


class AnchorState(TypedDict):
    """State for the epistemic anchor pipeline."""

    # --- Inputs ---
    source_files: dict[str, str]          # {filename: content}
    scraped_urls: dict[str, str]          # {url: markdown} from Firecrawl cache
    meta_prompt: str                      # system instructions from meta prompt file
    template_text: str                    # anchor template (guidance, not mandate)
    sample_text: str                      # sample output for reference
    context_text: str                     # domain context slate

    # --- Pipeline artifacts ---
    v0_raw: str                           # Pass 0: one-shot generation output
    v1_optimized: str                     # Pass 1: verbose optimized anchor (FINAL)

    # --- Output paths ---
    output_dir: str                       # path to output/ directory
    working_dir: str                      # path to working/ directory

    # --- Execution trace ---
    trace_records: Annotated[list[dict], operator.add]


# ---------------------------------------------------------------------------
# Input Assembly Node
# ---------------------------------------------------------------------------


def input_assembly(state: AnchorState) -> dict[str, Any]:
    """Populate state with source file contents and scraped URL cache.

    Expects ``state["source_files"]`` to contain ``__manifest_path__``.
    Reads all source files from the manifest, routes them to named fields,
    and loads any previously cached Firecrawl extractions.
    """
    source_files: dict[str, str] = {}
    meta_prompt = ""
    template_text = ""
    sample_text = ""
    context_text = ""
    manifest_path = state.get("source_files", {}).get("__manifest_path__", "")
    stage_dir = ""

    if manifest_path:
        mpath = Path(manifest_path)
        stage_dir = str(mpath.parent.parent)
        manifest = json.loads(mpath.read_text(encoding="utf-8"))

        for fname, entry in manifest.get("files", {}).items():
            fpath = entry.get("path", "")
            if not fpath or not entry.get("exists", False):
                continue
            content = Path(fpath).read_text(encoding="utf-8")
            source_files[fname] = content

            # Route to named fields
            lower = fname.lower()
            if "meta_prompt" in lower:
                meta_prompt = content
            elif "template" in lower:
                template_text = content
            elif "sample" in lower:
                sample_text = content
            elif "context" in lower:
                context_text = content

    # Load Firecrawl cache
    scraped_urls: dict[str, str] = {}
    if stage_dir:
        cache_dir = Path(stage_dir) / "working" / "url_cache"
        scraped_urls = load_cached_extractions(cache_dir)

    return {
        "source_files": source_files,
        "scraped_urls": scraped_urls,
        "meta_prompt": meta_prompt,
        "template_text": template_text,
        "sample_text": sample_text,
        "context_text": context_text,
    }


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _build_source_context(state: AnchorState) -> str:
    """Assemble all source material into a single context string."""
    parts: list[str] = []

    if state.get("meta_prompt"):
        parts.append("=== META PROMPT ===\n" + state["meta_prompt"])

    if state.get("template_text"):
        parts.append("=== ANCHOR TEMPLATE (guidance, not mandate) ===\n" + state["template_text"])

    if state.get("context_text"):
        parts.append("=== DOMAIN CONTEXT ===\n" + state["context_text"])

    # Expert corpus and other source files
    for fname, content in state.get("source_files", {}).items():
        if fname.startswith("__"):
            continue
        lower = fname.lower()
        if any(k in lower for k in ("meta_prompt", "template", "sample", "context")):
            continue  # already included above
        parts.append(f"=== SOURCE: {fname} ===\n{content}")

    if state.get("sample_text"):
        parts.append("=== SAMPLE OUTPUT (for reference only) ===\n" + state["sample_text"])

    # Scraped URL content
    scraped = state.get("scraped_urls", {})
    if scraped:
        parts.append(f"=== SCRAPED URL CONTENT ({len(scraped)} URLs) ===")
        for url, md in scraped.items():
            snippet = md[:3000] if len(md) > 3000 else md
            parts.append(f"[{url}]\n{snippet}")

    return "\n\n".join(parts)


def _save_artifact(working_dir: str, filename: str, content: str) -> str:
    """Write an artifact to the working directory. Returns path."""
    if not working_dir:
        return ""
    path = Path(working_dir) / filename
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return str(path)


# ---------------------------------------------------------------------------
# Pass 0: Generate — one-shot GPT-5.5
# ---------------------------------------------------------------------------


def generate_anchor(state: AnchorState) -> dict[str, Any]:
    """One-shot generation of the full epistemic anchor document.

    Uses GPT-5.5 reasoning with all source material in context.
    The template is provided as guidance, not as a slot-fill mandate.
    """
    context = _build_source_context(state)

    system_msg = (
        "You are creating an Epistemic Anchoring Foundation Document for an AI agent.\n\n"
        "Your goal is to produce the most complete, coherent, and operationally useful "
        "epistemic anchor possible from the source material provided. The template "
        "describes what an epistemic anchor should contain — use it as guidance for "
        "the types of content needed, but you may reorganize, add sections, or synthesize "
        "beyond what it specifies if doing so produces a better document.\n\n"
        "Key principles:\n"
        "- Reason holistically across all source material\n"
        "- Prioritize agent-encodable instructions over descriptive analysis\n"
        "- Every section should change how an AI agent reasons and acts\n"
        "- Include operational specifics: artifact schemas, failure modes, verification markers\n"
        "- The document will be loaded into an AI agent's context — optimize for that use case\n"
        "- Do NOT pad with generic advice — every claim must be traceable to source material\n\n"
        "Produce the complete document now."
    )

    human_msg = context

    tracker = TokenTracker()
    tracker.set_current_node("generate_anchor")
    llm = get_llm("reasoning", trusted=True, callbacks=[tracker])

    t0 = time.monotonic()
    response = llm.invoke([SystemMessage(content=system_msg), HumanMessage(content=human_msg)])
    latency = time.monotonic() - t0

    v0_raw = response.content if hasattr(response, "content") else str(response)

    # Extract token usage from tracker
    rec = tracker.records[0] if tracker.records else None
    prompt_tokens = rec.prompt_tokens if rec else 0
    completion_tokens = rec.completion_tokens if rec else 0
    cost = estimate_cost("gpt-5.5", prompt_tokens, completion_tokens)

    # Save artifact
    _save_artifact(state.get("working_dir", ""), "v0_raw.md", v0_raw)

    return {
        "v0_raw": v0_raw,
        "trace_records": [{
            "node": "generate_anchor",
            "tier": "reasoning",
            "model": "gpt-5.5",
            "latency_s": round(latency, 2),
            "output_chars": len(v0_raw),
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
            "total_tokens": prompt_tokens + completion_tokens,
            "cost_usd": round(cost, 4),
        }],
    }


# ---------------------------------------------------------------------------
# Pass 1: Optimize — verbose agent-encodability enrichment
# ---------------------------------------------------------------------------


def optimize_anchor(state: AnchorState) -> dict[str, Any]:
    """Optimize the raw anchor into a verbose, complete epistemic document.

    This pass enriches and ensures completeness — it does NOT compress.
    The output is the final deliverable used as input to agent creation.
    """
    system_msg = (
        "You are optimizing an Epistemic Anchoring Foundation Document.\n\n"
        "This document will be used as the foundational source for creating "
        "an AI agent. It must be VERBOSE and COMPLETE — do not compress.\n\n"
        "Your task:\n"
        "1. Ensure every expert's distinctive knowledge is fully represented\n"
        "2. Convert any descriptive-only sections into INSTRUCTIVE ones — "
        "every section must change how a downstream agent reasons and acts\n"
        "3. Ensure V&R rules follow IF trigger → MUST verify → THEN rectify format\n"
        "4. Ensure ambiguity shields are clear PAUSE-AND-ASK instructions\n"
        "5. Ensure artifact schemas have enough field specificity for generation\n"
        "6. Ensure reasoning sequences are numbered and unambiguous\n"
        "7. Ensure failure modes are structured as detection signal → correction action\n"
        "8. Add any missing sections the document needs to be a complete epistemic anchor\n"
        "9. Ensure all cross-references are internally consistent\n\n"
        "The output should be the most COMPLETE, VERBOSE, and USEFUL version "
        "of this epistemic anchor. It will be piped into a separate agent "
        "creation process. Do NOT shorten or compress.\n\n"
        "Produce the complete optimized document."
    )

    human_msg = f"=== DOCUMENT TO OPTIMIZE ===\n\n{state['v0_raw']}"

    tracker = TokenTracker()
    tracker.set_current_node("optimize_anchor")
    llm = get_llm("reasoning", trusted=True, callbacks=[tracker])

    t0 = time.monotonic()
    response = llm.invoke([SystemMessage(content=system_msg), HumanMessage(content=human_msg)])
    latency = time.monotonic() - t0

    v1 = response.content if hasattr(response, "content") else str(response)

    # Extract token usage
    rec = tracker.records[0] if tracker.records else None
    prompt_tokens = rec.prompt_tokens if rec else 0
    completion_tokens = rec.completion_tokens if rec else 0
    cost = estimate_cost("gpt-5.5", prompt_tokens, completion_tokens)

    # Save to working/ and output/
    _save_artifact(state.get("working_dir", ""), "v1_optimized.md", v1)
    output_dir = state.get("output_dir", "")
    if output_dir:
        out_path = Path(output_dir)
        out_path.mkdir(parents=True, exist_ok=True)
        (out_path / "epistemic_anchor.md").write_text(v1, encoding="utf-8")

    return {
        "v1_optimized": v1,
        "trace_records": [{
            "node": "optimize_anchor",
            "tier": "reasoning",
            "model": "gpt-5.5",
            "latency_s": round(latency, 2),
            "output_chars": len(v1),
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
            "total_tokens": prompt_tokens + completion_tokens,
            "cost_usd": round(cost, 4),
        }],
    }


# ---------------------------------------------------------------------------
# Graph builder
# ---------------------------------------------------------------------------


def build_graph(*, generate_only: bool = False) -> StateGraph:
    """Build and compile the epistemic anchor pipeline.

    Parameters
    ----------
    generate_only : bool
        If True, stop after Pass 0 (generate). Skip optimize.

    Returns
    -------
    StateGraph
        Compiled graph ready for ``.invoke()``.
    """
    graph = StateGraph(AnchorState)

    graph.add_node("input_assembly", input_assembly)
    graph.add_node("generate_anchor", generate_anchor)

    graph.set_entry_point("input_assembly")
    graph.add_edge("input_assembly", "generate_anchor")

    if generate_only:
        graph.add_edge("generate_anchor", END)
    else:
        graph.add_node("optimize_anchor", optimize_anchor)
        graph.add_edge("generate_anchor", "optimize_anchor")
        graph.add_edge("optimize_anchor", END)

    return graph.compile()


# ---------------------------------------------------------------------------
# Stage entry point
# ---------------------------------------------------------------------------


def run_stage(
    workspace_dir: Path,
    *,
    generate_only: bool = False,
) -> dict[str, Any]:
    """Run Stage 4: Epistemic Anchor Creation.

    Parameters
    ----------
    workspace_dir : Path
        Root workspace directory (e.g. workspaces/<dea_name>/).
    generate_only : bool
        If True, only run Pass 0.

    Returns
    -------
    dict
        Final state after pipeline execution.
    """
    stage_dir = workspace_dir / "04_epistemic_anchor"
    manifest_path = stage_dir / "working" / "manifest.json"

    if not manifest_path.exists():
        raise FileNotFoundError(
            f"Manifest not found: {manifest_path}\n"
            f"Run input validation first to create it."
        )

    initial_state = {
        "source_files": {"__manifest_path__": str(manifest_path)},
        "scraped_urls": {},
        "meta_prompt": "",
        "template_text": "",
        "sample_text": "",
        "context_text": "",
        "v0_raw": "",
        "v1_optimized": "",
        "output_dir": str(stage_dir / "output"),
        "working_dir": str(stage_dir / "working"),
        "trace_records": [],
    }

    graph = build_graph(generate_only=generate_only)
    result = graph.invoke(initial_state)

    # Write execution trace
    trace_path = stage_dir / "working" / "execution_trace.json"
    trace_path.write_text(
        json.dumps(result.get("trace_records", []), indent=2),
        encoding="utf-8",
    )

    return result


# ---------------------------------------------------------------------------
# Manifest generation + pipeline wrapper (for CLI integration)
# ---------------------------------------------------------------------------

STAGE_NUM = 4


def _prepare_manifest(workspace_dir: Path) -> Path:
    """Build manifest.json from upstream outputs and bundled source prompts.

    Assembles:
      - Context document from Stage 1 output
      - Expert Six from Stage 3 output
      - anchor_meta_prompt.md, anchor_template.md, anchor_sample.md from prompts/stage4
    """
    ws = Path(workspace_dir)
    _, working_dir = ensure_stage_dirs(ws, STAGE_NUM)

    # Upstream files
    context_path = ws / STAGE_NAMES[1] / "output" / "context_document.md"
    expert_six_path = ws / STAGE_NAMES[3] / "output" / "expert_six_final.md"

    if not context_path.is_file():
        raise FileNotFoundError(f"Context document not found: {context_path}")
    if not expert_six_path.is_file():
        raise FileNotFoundError(f"Expert Six not found: {expert_six_path}")

    # Bundled prompt sources — copy to sources/ for traceability
    sources_dir = ws / STAGE_NAMES[4] / "sources"
    sources_dir.mkdir(parents=True, exist_ok=True)

    source_map = {
        "anchor_meta_prompt.md": "anchor_meta_prompt.md",
        "anchor_template.md": "anchor_template.md",
        "anchor_sample.md": "anchor_sample.md",
    }
    for dest_name, prompt_name in source_map.items():
        content = load_prompt(STAGE_NUM, prompt_name)
        dest = sources_dir / dest_name
        dest.write_text(content, encoding="utf-8")

    # Build manifest
    files = {}
    all_sources = {
        "context_document.md": context_path,
        "expert_six_final.md": expert_six_path,
        "anchor_meta_prompt.md": sources_dir / "anchor_meta_prompt.md",
        "anchor_template.md": sources_dir / "anchor_template.md",
        "anchor_sample.md": sources_dir / "anchor_sample.md",
    }
    for fname, fpath in all_sources.items():
        files[fname] = {
            "path": str(fpath),
            "exists": fpath.is_file(),
        }

    manifest = {"stage": STAGE_NUM, "files": files}
    manifest_path = working_dir / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    return manifest_path


def run_pipeline(workspace_dir: Path) -> Path:
    """Full Stage 4 pipeline: prepare manifest → generate → optimize.

    Returns path to the final epistemic anchor output.
    """
    console.print(
        Panel("Stage 4 — Epistemic Anchor Creation", style="bold cyan")
    )

    ws = Path(workspace_dir)
    t0 = time.time()

    # Prepare
    console.print("Assembling inputs from upstream stages...")
    manifest_path = _prepare_manifest(ws)
    console.print(f"  Manifest: {manifest_path.relative_to(ws)}")

    # Run existing pipeline
    console.print("\n[bold]Pass 0:[/bold] Generating epistemic anchor (GPT-5.5)...")
    result = run_stage(ws)

    # Extract trace info
    trace_records = result.get("trace_records", [])
    elapsed = time.time() - t0
    total_cost = sum(r.get("cost_usd", 0) for r in trace_records)

    # Output path
    output_path = ws / STAGE_NAMES[4] / "output" / "epistemic_anchor.md"

    console.print(
        Panel(
            f"Total time: {elapsed:.1f}s\n"
            f"Estimated cost: ${total_cost:.4f}\n"
            f"Passes: {len(trace_records)}\n"
            f"Output: {output_path.relative_to(ws.parent) if ws.parent in output_path.parents else output_path}",
            title="Stage 4 Complete",
            style="bold green",
        )
    )

    return output_path
