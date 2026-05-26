"""Stage 1 — DEA Context Creation.

Normalizes heterogeneous context inputs into a canonical context document
conforming to the 12-section Hardened Template via the Context Normalizer
pipeline (Pass 0: normalize, Pass 1: review/refine).
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, TypedDict

from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.graph import END, StateGraph
from rich.console import Console
from rich.panel import Panel

from dea_builder.cost.tracker import TokenTracker, estimate_cost
from dea_builder.io.workspace import (
    ensure_stage_dirs,
    load_prompt,
    read_all_inputs,
    write_execution_trace,
    write_stage_output,
    write_working_artifact,
)
from dea_builder.llm.client import get_llm

console = Console()

STAGE_NUM = 1


# ---------------------------------------------------------------------------
# Errors
# ---------------------------------------------------------------------------


@dataclass
class NormalizationFailure:
    """Parsed structured error from the normalizer."""

    error_type: str  # "insufficient information" | "unresolved conflicts"
    missing_fields: list[str] = field(default_factory=list)
    conflicts: list[str] = field(default_factory=list)
    raw_output: str = ""


class NormalizationError(Exception):
    """Raised when the normalizer cannot produce a canonical document."""

    def __init__(self, failure: NormalizationFailure):
        self.failure = failure
        super().__init__(
            f"Context normalization failed — {failure.error_type}. "
            f"{len(failure.missing_fields)} missing fields, "
            f"{len(failure.conflicts)} conflicts."
        )


# ---------------------------------------------------------------------------
# State
# ---------------------------------------------------------------------------


class ContextState(TypedDict, total=False):
    """LangGraph state for the Stage 1 pipeline."""

    workspace_dir: str
    input_files: dict[str, str]
    assembled_input: str
    normalizer_prompt: str
    hardened_template: str
    system_prompt: str
    v0_normalized: str
    v1_reviewed: str
    trace_records: list[dict[str, Any]]


# ---------------------------------------------------------------------------
# Task 2: Input Assembly
# ---------------------------------------------------------------------------


def _assemble_inputs(inputs: dict[str, str]) -> str:
    """Concatenate input files with source attribution headers."""
    parts: list[str] = []
    for filename, content in inputs.items():
        parts.append(f"=== SOURCE: {filename} ===\n\n{content.strip()}\n")
    return "\n\n".join(parts)


def input_assembly(state: ContextState) -> dict:
    """Read inputs and assemble them for the normalizer."""
    workspace = Path(state["workspace_dir"])
    inputs = read_all_inputs(workspace)
    assembled = _assemble_inputs(inputs)

    console.print(
        Panel(
            f"[bold]{len(inputs)} input file(s)[/bold] loaded\n"
            + "\n".join(f"  • {name}" for name in inputs),
            title="Stage 1 — Input Assembly",
            border_style="cyan",
        )
    )

    # Load runtime prompts
    normalizer_prompt = load_prompt(1, "context_normalizer_prompt.md")
    hardened_template = load_prompt(1, "context_document_template.md")

    # Construct system prompt per the README deployment spec
    system_prompt = (
        "You are operating as the Context Normalizer. "
        "Your operating instructions are defined below in the OPERATING INSTRUCTIONS section. "
        "The required output structure is defined below in the OUTPUT TEMPLATE section. "
        "Convert the provided input into a canonical context document that exactly matches "
        "the hardened template. Follow the process and operating principles defined in the "
        "operating instructions without deviation.\n\n"
        "## OPERATING INSTRUCTIONS\n\n"
        f"{normalizer_prompt}\n\n"
        "## OUTPUT TEMPLATE\n\n"
        f"{hardened_template}"
    )

    return {
        "input_files": inputs,
        "assembled_input": assembled,
        "normalizer_prompt": normalizer_prompt,
        "hardened_template": hardened_template,
        "system_prompt": system_prompt,
    }


# ---------------------------------------------------------------------------
# Task 3: Normalizer Pipeline (Pass 0)
# ---------------------------------------------------------------------------


def _parse_failure(output: str) -> NormalizationFailure:
    """Parse a structured ERROR output from the normalizer."""
    error_type = "unknown"
    missing: list[str] = []
    conflicts: list[str] = []

    if "insufficient information" in output.lower():
        error_type = "insufficient information"
    elif "unresolved conflicts" in output.lower():
        error_type = "unresolved conflicts"

    in_missing = False
    in_conflicts = False
    for line in output.splitlines():
        stripped = line.strip()
        if "missing or partial fields" in stripped.lower():
            in_missing = True
            in_conflicts = False
            continue
        elif "conflicting fields" in stripped.lower():
            in_conflicts = True
            in_missing = False
            continue
        elif stripped.lower().startswith("recovery:"):
            in_missing = False
            in_conflicts = False
            continue

        if stripped.startswith("- ") and in_missing:
            missing.append(stripped[2:])
        elif stripped.startswith("- ") and in_conflicts:
            conflicts.append(stripped[2:])

    return NormalizationFailure(
        error_type=error_type,
        missing_fields=missing,
        conflicts=conflicts,
        raw_output=output,
    )


def normalize(state: ContextState) -> dict:
    """Pass 0 — Run the Context Normalizer."""
    console.print("\n[bold cyan]Pass 0:[/bold cyan] Running Context Normalizer...")

    tracker = TokenTracker()
    tracker.current_node = "normalize"
    llm = get_llm("reasoning", callbacks=[tracker])

    messages = [
        SystemMessage(content=state["system_prompt"]),
        HumanMessage(content=state["assembled_input"]),
    ]

    start = time.time()
    response = llm.invoke(messages)
    elapsed = time.time() - start

    output = response.content.strip()

    # Check for structured failure
    if output.startswith("ERROR:"):
        failure = _parse_failure(output)
        # Log failure to trace
        trace_record = {
            "node": "normalize",
            "status": "failure",
            "error_type": failure.error_type,
            "missing_fields": failure.missing_fields,
            "conflicts": failure.conflicts,
            "latency_s": elapsed,
            "tokens": [r.__dict__ for r in tracker.records] if tracker.records else [],
        }
        console.print(f"\n[bold red]Normalization FAILED:[/bold red] {failure.error_type}")
        for item in failure.missing_fields:
            console.print(f"  [red]• Missing:[/red] {item}")
        for item in failure.conflicts:
            console.print(f"  [red]• Conflict:[/red] {item}")

        raise NormalizationError(failure)

    # Success — save v0
    workspace = Path(state["workspace_dir"])
    write_working_artifact(workspace, STAGE_NUM, "v0_normalized.md", output)

    trace_record = {
        "node": "normalize",
        "status": "success",
        "latency_s": elapsed,
        "tokens": [r.__dict__ for r in tracker.records] if tracker.records else [],
    }

    chars = len(output)
    lines = output.count("\n") + 1
    console.print(
        f"  [green]✓[/green] v0_normalized.md — {chars:,} chars, {lines:,} lines, {elapsed:.1f}s"
    )

    return {
        "v0_normalized": output,
        "trace_records": state.get("trace_records", []) + [trace_record],
    }


# ---------------------------------------------------------------------------
# Task 4: Review Pipeline (Pass 1)
# ---------------------------------------------------------------------------

REVIEW_SYSTEM_PROMPT = """\
You are reviewing a canonical context document that will feed an automated Expert Six research pipeline.

The document was produced by a Context Normalizer from source inputs. Your job is to ensure it is complete, precise, and optimized for downstream processing.

Instructions:
- Cross-check every section for internal consistency
- Ensure Section 3 (Agent Definition) is fully specified with no ambiguity
- Ensure Section 7 (Desired Coverage Across the Six) is derived from and consistent with Section 4 (Primary Knowledge Domains)
- Ensure all constraints (Section 9) clearly mark firm vs. flexible
- Ensure no vague placeholders remain ("TBD", "various", "to be determined")
- Tighten language for downstream LLM consumption — remove redundancy, sharpen specificity
- Do NOT shorten content that carries signal — verbose is acceptable, vague is not
- Preserve the exact Hardened Template structure — do not reorganize sections
- Output the complete reviewed document — nothing else in the response, no preamble, no commentary"""


def review(state: ContextState) -> dict:
    """Pass 1 — Review and refine the normalized context document."""
    console.print("\n[bold cyan]Pass 1:[/bold cyan] Reviewing and refining...")

    tracker = TokenTracker()
    tracker.current_node = "review"
    llm = get_llm("reasoning", callbacks=[tracker])

    messages = [
        SystemMessage(content=REVIEW_SYSTEM_PROMPT),
        HumanMessage(content=state["v0_normalized"]),
    ]

    start = time.time()
    response = llm.invoke(messages)
    elapsed = time.time() - start

    output = response.content.strip()

    # Save working artifact and final output
    workspace = Path(state["workspace_dir"])
    write_working_artifact(workspace, STAGE_NUM, "v1_reviewed.md", output)
    write_stage_output(workspace, STAGE_NUM, "context_document.md", output)

    trace_record = {
        "node": "review",
        "status": "success",
        "latency_s": elapsed,
        "tokens": [r.__dict__ for r in tracker.records] if tracker.records else [],
    }

    chars = len(output)
    lines = output.count("\n") + 1
    console.print(
        f"  [green]✓[/green] v1_reviewed.md — {chars:,} chars, {lines:,} lines, {elapsed:.1f}s"
    )
    console.print(
        f"  [green]✓[/green] output/context_document.md written"
    )

    return {
        "v1_reviewed": output,
        "trace_records": state.get("trace_records", []) + [trace_record],
    }


# ---------------------------------------------------------------------------
# Graph
# ---------------------------------------------------------------------------


def build_graph() -> StateGraph:
    """Build the Stage 1 LangGraph pipeline."""
    graph = StateGraph(ContextState)

    graph.add_node("input_assembly", input_assembly)
    graph.add_node("normalize", normalize)
    graph.add_node("review", review)

    graph.set_entry_point("input_assembly")
    graph.add_edge("input_assembly", "normalize")
    graph.add_edge("normalize", "review")
    graph.add_edge("review", END)

    return graph


# ---------------------------------------------------------------------------
# Task 5: Stage Entry Point
# ---------------------------------------------------------------------------


def run_stage(workspace_dir: Path) -> dict[str, Any]:
    """Run Stage 1 — DEA Context Creation.

    Parameters
    ----------
    workspace_dir : Path
        Path to the workspace (e.g., workspaces/Modern_UX_Design).

    Returns
    -------
    dict with keys: v0_normalized, v1_reviewed, trace_records

    Raises
    ------
    FileNotFoundError
        If no input files exist in 00_inputs/.
    NormalizationError
        If the normalizer cannot produce a canonical document due to
        missing fields or unresolved conflicts.
    """
    workspace_dir = Path(workspace_dir).resolve()

    console.print(
        Panel(
            f"[bold]Workspace:[/bold] {workspace_dir.name}",
            title="[bold green]Stage 1 — DEA Context Creation[/bold green]",
            border_style="green",
        )
    )

    # Ensure stage directories exist
    ensure_stage_dirs(workspace_dir, STAGE_NUM)

    # Build and run graph
    graph = build_graph()
    app = graph.compile()

    initial_state: ContextState = {
        "workspace_dir": str(workspace_dir),
        "input_files": {},
        "assembled_input": "",
        "normalizer_prompt": "",
        "hardened_template": "",
        "system_prompt": "",
        "v0_normalized": "",
        "v1_reviewed": "",
        "trace_records": [],
    }

    start = time.time()
    final_state = app.invoke(initial_state)
    total_elapsed = time.time() - start

    # Write execution trace
    trace = {
        "stage": "dea_context",
        "stage_num": STAGE_NUM,
        "workspace": str(workspace_dir),
        "status": "success",
        "total_latency_s": total_elapsed,
        "input_files": list(final_state.get("input_files", {}).keys()),
        "output_files": ["output/context_document.md"],
        "working_files": ["v0_normalized.md", "v1_reviewed.md"],
        "passes": final_state.get("trace_records", []),
    }
    write_execution_trace(workspace_dir, STAGE_NUM, trace)

    # Cost summary
    total_cost = 0.0
    for record in final_state.get("trace_records", []):
        for tok in record.get("tokens", []):
            total_cost += estimate_cost(
                tok.get("model", "gpt-5.5"),
                tok.get("prompt_tokens", 0),
                tok.get("completion_tokens", 0),
            )

    console.print(
        Panel(
            f"[bold]Total time:[/bold] {total_elapsed:.1f}s\n"
            f"[bold]Estimated cost:[/bold] ${total_cost:.4f}\n"
            f"[bold]Output:[/bold] {workspace_dir.name}/01_dea_context/output/context_document.md",
            title="[bold green]Stage 1 Complete[/bold green]",
            border_style="green",
        )
    )

    return {
        "v0_normalized": final_state.get("v0_normalized", ""),
        "v1_reviewed": final_state.get("v1_reviewed", ""),
        "trace_records": final_state.get("trace_records", []),
        "total_cost": total_cost,
        "total_latency_s": total_elapsed,
    }
