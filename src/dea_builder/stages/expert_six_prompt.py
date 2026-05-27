"""Stage 2 — Expert Six Prompt Creation.

Fills the Expert Six Research Prompt generic template with domain-specific
fields extracted from the Stage 1 context document. Two-pass: extract fields
(Pass 0), then review the filled prompt for coherence (Pass 1).

Output: filled research prompt + versioned copy of context document.
"""

from __future__ import annotations

import shutil
import time
from pathlib import Path
from typing import TypedDict

from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.graph import END, StateGraph
from rich.console import Console
from rich.panel import Panel

from dea_builder.cost.tracker import TokenTracker, estimate_cost
from dea_builder.io.workspace import (
    STAGE_NAMES,
    ensure_stage_dirs,
    load_prompt,
    write_execution_trace,
    write_stage_output,
    write_working_artifact,
)
from dea_builder.llm.client import get_llm

console = Console()

STAGE_NUM = 2
TEMPLATE_FILE = "expert_six_research_prompt_template.md"
CONTEXT_DOC_NAME = "context_document.md"

EXTRACT_SYSTEM = """\
You are a field-extraction utility (v1.1). Given a canonical context document \
for an Expert Six agent specification, extract two fields:

1. TARGET_DOMAIN — the exact Domain Name from Section 1. Copy it verbatim.
2. RESEARCHER_DOMAIN — a comma-separated list of 6–8 specializations that \
represent the full breadth of the domain. Derive from Primary Knowledge \
Domains (Section 4), Agent Deliverables (Section 3), and any format-specific \
or channel-specific expertise implied by the context. Cover the complete scope \
— do not summarize or collapse into broad categories.

Output ONLY these two lines, nothing else:
TARGET_DOMAIN: <value>
RESEARCHER_DOMAIN: <value>
"""

REVIEW_SYSTEM = """\
You are a research-prompt quality reviewer. You receive a filled Expert Six \
Research Prompt paired with its source context document. Your job:

1. Verify {{TARGET_DOMAIN}} and {{RESEARCHER_DOMAIN}} are correctly filled \
(no remaining placeholders).
2. Verify the researcher domain is specific and precise — not over-broadened.
3. Verify the filled prompt reads coherently with the context document's \
sections (mandatory inclusions, prospects, exclusions, knowledge domains).
4. If everything is correct, output the filled prompt EXACTLY as-is with no \
changes.
5. If a placeholder was missed or the researcher domain is too vague, fix it \
and output the corrected prompt.

Output ONLY the final research prompt markdown. No commentary.
"""


# ---------------------------------------------------------------------------
# State
# ---------------------------------------------------------------------------


class PipelineState(TypedDict):
    workspace_dir: str
    context_document: str
    template: str
    target_domain: str
    researcher_domain: str
    v0_filled: str
    v1_reviewed: str
    tracker: TokenTracker


# ---------------------------------------------------------------------------
# Nodes
# ---------------------------------------------------------------------------


def load_inputs(state: PipelineState) -> dict:
    """Load context document from Stage 1 output and the prompt template."""
    ws = Path(state["workspace_dir"])
    stage1_output = ws / STAGE_NAMES[1] / "output" / CONTEXT_DOC_NAME

    if not stage1_output.is_file():
        raise FileNotFoundError(
            f"Stage 1 output not found: {stage1_output}\n"
            "Run `dea-builder dea-context` first."
        )

    context_doc = stage1_output.read_text(encoding="utf-8")
    template = load_prompt(STAGE_NUM, TEMPLATE_FILE)

    return {"context_document": context_doc, "template": template}


def extract_fields(state: PipelineState) -> dict:
    """Pass 0 — Extract TARGET_DOMAIN and RESEARCHER_DOMAIN from context doc."""
    tracker: TokenTracker = state["tracker"]
    llm = get_llm("general", trusted=True, callbacks=[tracker])

    response = llm.invoke([
        SystemMessage(content=EXTRACT_SYSTEM),
        HumanMessage(content=state["context_document"]),
    ])

    text = response.content.strip()
    target = ""
    researcher = ""
    for line in text.splitlines():
        if line.startswith("TARGET_DOMAIN:"):
            target = line.split(":", 1)[1].strip()
        elif line.startswith("RESEARCHER_DOMAIN:"):
            researcher = line.split(":", 1)[1].strip()

    if not target or not researcher:
        raise ValueError(
            f"Field extraction failed. LLM output:\n{text}"
        )

    # Fill template
    filled = state["template"].replace("{{TARGET_DOMAIN}}", target)
    filled = filled.replace("{{RESEARCHER_DOMAIN}}", researcher)

    return {
        "target_domain": target,
        "researcher_domain": researcher,
        "v0_filled": filled,
    }


def review_prompt(state: PipelineState) -> dict:
    """Pass 1 — Review filled prompt for coherence with context document."""
    tracker: TokenTracker = state["tracker"]
    llm = get_llm("worker-bee", trusted=True, callbacks=[tracker])

    user_content = (
        "## Filled Research Prompt\n\n"
        f"{state['v0_filled']}\n\n"
        "---\n\n"
        "## Source Context Document\n\n"
        f"{state['context_document']}"
    )

    response = llm.invoke([
        SystemMessage(content=REVIEW_SYSTEM),
        HumanMessage(content=user_content),
    ])

    return {"v1_reviewed": response.content.strip()}


# ---------------------------------------------------------------------------
# Graph
# ---------------------------------------------------------------------------


def build_graph() -> StateGraph:
    """Build the Stage 2 pipeline graph."""
    graph = StateGraph(PipelineState)
    graph.add_node("load_inputs", load_inputs)
    graph.add_node("extract_fields", extract_fields)
    graph.add_node("review_prompt", review_prompt)

    graph.set_entry_point("load_inputs")
    graph.add_edge("load_inputs", "extract_fields")
    graph.add_edge("extract_fields", "review_prompt")
    graph.add_edge("review_prompt", END)

    return graph


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------


def run_stage(workspace_dir: Path) -> Path:
    """Run Stage 2 — Expert Six Prompt Creation.

    Returns path to the output research prompt.
    """
    console.print(
        Panel(
            "Stage 2 — Expert Six Prompt Creation",
            style="bold cyan",
        )
    )

    tracker = TokenTracker()
    t0 = time.time()

    graph = build_graph()
    compiled = graph.compile()

    initial_state: PipelineState = {
        "workspace_dir": str(workspace_dir),
        "context_document": "",
        "template": "",
        "target_domain": "",
        "researcher_domain": "",
        "v0_filled": "",
        "v1_reviewed": "",
        "tracker": tracker,
    }

    console.print("Loading Stage 1 context document...")
    final_state = compiled.invoke(initial_state)

    elapsed = time.time() - t0

    # Save working artifacts
    write_working_artifact(
        workspace_dir, STAGE_NUM, "v0_filled.md", final_state["v0_filled"]
    )
    write_working_artifact(
        workspace_dir, STAGE_NUM, "v1_reviewed.md", final_state["v1_reviewed"]
    )

    # Save output — the research prompt
    output_path = write_stage_output(
        workspace_dir, STAGE_NUM, "expert_six_research_prompt.md",
        final_state["v1_reviewed"],
    )

    # Copy context document into Stage 2 output for self-contained handoff
    output_dir, _ = ensure_stage_dirs(workspace_dir, STAGE_NUM)
    stage1_ctx = (
        Path(workspace_dir) / STAGE_NAMES[1] / "output" / CONTEXT_DOC_NAME
    )
    dest = output_dir / CONTEXT_DOC_NAME
    shutil.copy2(stage1_ctx, dest)

    # Execution trace
    cost = sum(
        estimate_cost(r.model, r.prompt_tokens, r.completion_tokens)
        for r in tracker.records
    )
    trace = {
        "stage": STAGE_NUM,
        "elapsed_seconds": round(elapsed, 1),
        "target_domain": final_state["target_domain"],
        "researcher_domain": final_state["researcher_domain"],
        "estimated_cost_usd": round(cost, 4),
        "token_records": tracker.to_dicts(),
        "context_document_source": str(stage1_ctx),
    }
    write_execution_trace(workspace_dir, STAGE_NUM, trace)

    # Summary
    console.print(f"  Target domain: [bold]{final_state['target_domain']}[/bold]")
    console.print(f"  Researcher domain: [bold]{final_state['researcher_domain']}[/bold]")
    console.print(
        Panel(
            f"Total time: {elapsed:.1f}s\n"
            f"Estimated cost: ${cost:.4f}\n"
            f"Output: {output_path.relative_to(workspace_dir.parent) if workspace_dir.parent in output_path.parents else output_path}",
            title="Stage 2 Complete",
            style="bold green",
        )
    )

    return output_path
