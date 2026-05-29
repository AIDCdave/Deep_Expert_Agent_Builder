"""Stage 6 — Target Deployment Packaging.

Converts EARL output (agent.adl.yaml + chatgpt_custom_gpt/) into deployment-
ready packages for multiple target platforms.

Pipeline:
    Phase 0 — Input Assembly + ADL Validation
    Phase 1 — PAS Generation (always, first)
    Phase 2 — Parallel Target Conversion Pipes
    Phase 3 — Fidelity Inspection Pass

Workspace layout produced:
    06_deployments/
        portable_agent_spec/
            pas.yaml
            system_prompt.md
            README.md
        chatgpt_custom_gpt/          (copy from EARL)
        openai_responses/
        claude/
        gemma/
        hermes/
        grok/
        fidelity_report.md
        working/
            execution_trace.json
"""

from __future__ import annotations

import asyncio
import hashlib
import json
import re
import shutil
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml
from langchain_core.messages import HumanMessage, SystemMessage
from rich.console import Console
from rich.panel import Panel

from dea_builder.cost.tracker import TokenTracker, estimate_cost
from dea_builder.io.workspace import STAGE_NAMES, ensure_stage_dirs, load_prompt
from dea_builder.llm.client import get_llm

console = Console()

STAGE_NUM = 6

# All valid target slugs
ALL_TARGETS = [
    "pas",
    "chatgpt-custom-gpt",
    "openai-responses",
    "claude",
    "gemma-4",
    "hermes",
    "grok",
]

# Map target slug → prompt file name (no prompt for chatgpt-custom-gpt, it's a copy)
TARGET_PROMPT_MAP = {
    "pas": "pas.md",
    "openai-responses": "openai_responses.md",
    "claude": "claude.md",
    "gemma-4": "gemma.md",
    "hermes": "hermes.md",
    "grok": "grok.md",
}

# Map target slug → output directory name
TARGET_DIR_MAP = {
    "pas": "portable_agent_spec",
    "chatgpt-custom-gpt": "chatgpt_custom_gpt",
    "openai-responses": "openai_responses",
    "claude": "claude",
    "gemma-4": "gemma",
    "hermes": "hermes",
    "grok": "grok",
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _call_llm(
    tier: str,
    system: str,
    human: str,
    *,
    node_name: str = "",
) -> tuple[str, dict]:
    """Invoke an LLM and return (response_text, trace_record).

    Uses the trusted deployment (Prompt Shields OFF) since all Stage 6
    content is pipeline-generated and has already passed Module 1 scan.
    """
    tracker = TokenTracker()
    tracker.set_current_node(node_name)
    llm = get_llm(tier, trusted=True, callbacks=[tracker])

    t0 = time.monotonic()
    response = llm.invoke([SystemMessage(content=system), HumanMessage(content=human)])
    latency = time.monotonic() - t0

    text = response.content if hasattr(response, "content") else str(response)

    rec = tracker.records[0] if tracker.records else None
    pt = rec.prompt_tokens if rec else 0
    ct = rec.completion_tokens if rec else 0
    cost = estimate_cost(rec.model if rec else "gpt-5.5", pt, ct)

    trace = {
        "node": node_name,
        "tier": tier,
        "model": rec.model if rec else tier,
        "latency_s": round(latency, 2),
        "prompt_tokens": pt,
        "completion_tokens": ct,
        "total_tokens": pt + ct,
        "cost_usd": round(cost, 4),
    }
    return text, trace


def _save(directory: Path, filename: str, content: str) -> Path:
    """Write a file, creating parents as needed. Return the path."""
    path = directory / filename
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return path


def _compute_provenance(adl_path: Path, adl_data: dict) -> dict:
    """Compute the provenance block from ADL file."""
    adl_text = adl_path.read_text(encoding="utf-8")
    source_hash = hashlib.sha256(adl_text.encode("utf-8")).hexdigest()
    adl_version = adl_data.get("adl_version", "UNKNOWN")
    return {
        "source_adl_file": "agent.adl.yaml",
        "adl_version": str(adl_version),
        "source_hash": source_hash,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "generator": "dea-builder/phase6",
    }


def _parse_files_from_response(response_text: str) -> dict[str, str]:
    """Parse LLM response containing === FILE: <name> === delimited sections.

    Returns {filename: content}.
    """
    files: dict[str, str] = {}
    pattern = r"===\s*FILE:\s*(.+?)\s*===\s*\n"
    parts = re.split(pattern, response_text)

    # parts[0] is preamble (discard), then alternating [filename, content]
    i = 1
    while i < len(parts) - 1:
        filename = parts[i].strip()
        content = parts[i + 1].strip()
        # Strip markdown code fences if the LLM wrapped the whole file in them
        if content.startswith("```") and content.endswith("```"):
            lines = content.split("\n")
            content = "\n".join(lines[1:-1])
        files[filename] = content
        i += 2

    return files


def _build_knowledge_manifest(earl_output: Path) -> str:
    """Build a knowledge manifest string from EARL knowledge files."""
    knowledge_dir = earl_output / "chatgpt_custom_gpt" / "03_knowledge"
    if not knowledge_dir.is_dir():
        return "No knowledge files in source."

    lines = ["Knowledge files in source package:"]
    for f in sorted(knowledge_dir.iterdir()):
        if f.is_file() and f.suffix == ".md":
            # Read first line as description
            first_line = f.read_text(encoding="utf-8").split("\n")[0].strip()
            first_line = first_line.lstrip("#").strip()
            lines.append(f"- {f.name}: {first_line}")

    return "\n".join(lines) if len(lines) > 1 else "No knowledge files in source."


def _build_tools_section(earl_output: Path) -> str:
    """Extract tool/action definitions from EARL output."""
    actions_dir = earl_output / "chatgpt_custom_gpt" / "05_actions"
    if not actions_dir.is_dir():
        return "No tools or actions defined in source."

    files = list(actions_dir.iterdir())
    if not files:
        return "No tools or actions defined in source. Actions directory exists but is empty."

    sections = ["Source tool/action definitions:"]
    for f in sorted(files):
        if f.is_file():
            sections.append(f"\n--- {f.name} ---\n{f.read_text(encoding='utf-8')}")

    return "\n".join(sections)


def _build_capabilities_section(adl_data: dict) -> str:
    """Extract capabilities from ADL."""
    caps = adl_data.get("capabilities", {})
    if not caps:
        return "No capabilities declared in ADL."

    lines = ["Source capabilities declared in ADL:"]
    for key, val in caps.items():
        lines.append(f"- {key}: {val}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Phase 0 — Input Assembly
# ---------------------------------------------------------------------------


def _input_assembly(workspace: Path) -> dict[str, Any]:
    """Load and validate all inputs from EARL output."""
    earl_output = workspace / STAGE_NAMES[5] / "output"
    if not earl_output.is_dir():
        raise FileNotFoundError(
            f"EARL output not found at {earl_output}. Run Stage 5 first."
        )

    adl_path = earl_output / "agent.adl.yaml"
    if not adl_path.is_file():
        raise FileNotFoundError(f"agent.adl.yaml not found at {adl_path}")

    adl_data = yaml.safe_load(adl_path.read_text(encoding="utf-8"))

    system_prompt_path = (
        earl_output / "chatgpt_custom_gpt" / "02_instructions" / "system_prompt.md"
    )
    if not system_prompt_path.is_file():
        raise FileNotFoundError(f"System prompt not found at {system_prompt_path}")

    system_prompt = system_prompt_path.read_text(encoding="utf-8")
    adl_text = adl_path.read_text(encoding="utf-8")
    knowledge_manifest = _build_knowledge_manifest(earl_output)
    tools_section = _build_tools_section(earl_output)
    capabilities = _build_capabilities_section(adl_data)
    provenance = _compute_provenance(adl_path, adl_data)

    agent_name = adl_data.get("metadata", {}).get("name", "Unknown Agent")

    return {
        "earl_output": earl_output,
        "adl_path": adl_path,
        "adl_data": adl_data,
        "adl_text": adl_text,
        "system_prompt": system_prompt,
        "knowledge_manifest": knowledge_manifest,
        "tools_section": tools_section,
        "capabilities": capabilities,
        "provenance": provenance,
        "provenance_yaml": yaml.dump(
            {"provenance": provenance}, default_flow_style=False
        ),
        "agent_name": agent_name,
    }


# ---------------------------------------------------------------------------
# Phase 1 — PAS Generation
# ---------------------------------------------------------------------------


def _generate_pas(
    ctx: dict[str, Any], output_dir: Path, working_dir: Path
) -> tuple[dict[str, str], dict]:
    """Generate the Portable Agent Spec (always produced)."""
    console.print("\n[bold cyan]Phase 1:[/bold cyan] Generating Portable Agent Spec...")

    system_prompt = load_prompt(STAGE_NUM, "pas.md")

    human_msg = (
        f"## Source ADL\n\n```yaml\n{ctx['adl_text']}\n```\n\n"
        f"## Source System Prompt\n\n{ctx['system_prompt']}\n\n"
        f"## Knowledge Manifest\n\n{ctx['knowledge_manifest']}\n\n"
        f"## Tools / Actions\n\n{ctx['tools_section']}\n\n"
        f"## Capabilities\n\n{ctx['capabilities']}\n\n"
        f"## Provenance Block\n\n```yaml\n{ctx['provenance_yaml']}```\n"
    )

    response, trace = _call_llm(
        "reasoning", system_prompt, human_msg, node_name="pas_generation"
    )

    # Save raw response
    _save(working_dir, "pas_raw_response.md", response)

    # Parse files from response
    files = _parse_files_from_response(response)

    # Write to output directory
    pas_dir = output_dir / "portable_agent_spec"
    pas_dir.mkdir(parents=True, exist_ok=True)
    for filename, content in files.items():
        _save(pas_dir, filename, content)

    console.print(
        f"  [green]✓[/green] PAS generated: {len(files)} files "
        f"({trace['cost_usd']:.4f} USD, {trace['latency_s']:.1f}s)"
    )

    return files, trace


# ---------------------------------------------------------------------------
# Phase 2 — Target Conversion Pipes
# ---------------------------------------------------------------------------


def _convert_target(
    target: str,
    ctx: dict[str, Any],
    pas_files: dict[str, str],
    output_dir: Path,
    working_dir: Path,
) -> dict:
    """Run a single target conversion pipe. Returns trace record."""
    prompt_file = TARGET_PROMPT_MAP[target]
    dir_name = TARGET_DIR_MAP[target]

    console.print(f"  [cyan]→[/cyan] Converting to {target}...")

    system_prompt = load_prompt(STAGE_NUM, prompt_file)

    # Build PAS reference section
    pas_ref_parts = ["## PAS Reference\n"]
    for fname, content in pas_files.items():
        pas_ref_parts.append(f"### PAS {fname}\n\n{content}\n")
    pas_reference = "\n".join(pas_ref_parts)

    human_msg = (
        f"## Source ADL\n\n```yaml\n{ctx['adl_text']}\n```\n\n"
        f"## Source System Prompt\n\n{ctx['system_prompt']}\n\n"
        f"## Knowledge Manifest\n\n{ctx['knowledge_manifest']}\n\n"
        f"## Tools / Actions\n\n{ctx['tools_section']}\n\n"
        f"## Capabilities\n\n{ctx['capabilities']}\n\n"
        f"{pas_reference}\n\n"
        f"## Provenance Block\n\n```yaml\n{ctx['provenance_yaml']}```\n"
    )

    response, trace = _call_llm(
        "reasoning", system_prompt, human_msg, node_name=f"convert_{target}"
    )

    # Save raw response
    _save(working_dir, f"{target}_raw_response.md", response)

    # Parse and write files
    files = _parse_files_from_response(response)
    target_dir = output_dir / dir_name
    target_dir.mkdir(parents=True, exist_ok=True)
    for filename, content in files.items():
        _save(target_dir, filename, content)

    console.print(
        f"  [green]✓[/green] {target}: {len(files)} files "
        f"({trace['cost_usd']:.4f} USD, {trace['latency_s']:.1f}s)"
    )

    return trace


def _copy_chatgpt_custom_gpt(
    ctx: dict[str, Any], output_dir: Path
) -> None:
    """Copy the ChatGPT Custom GPT package from EARL output and stamp provenance."""
    console.print("  [cyan]→[/cyan] Copying ChatGPT Custom GPT from EARL...")

    src = ctx["earl_output"] / "chatgpt_custom_gpt"
    dst = output_dir / "chatgpt_custom_gpt"

    if dst.exists():
        shutil.rmtree(dst)
    shutil.copytree(src, dst)

    # Stamp provenance into a new file
    provenance_path = dst / "provenance.yaml"
    provenance_path.write_text(
        yaml.dump({"provenance": ctx["provenance"]}, default_flow_style=False),
        encoding="utf-8",
    )

    console.print("  [green]✓[/green] chatgpt-custom-gpt: copied + provenance stamped")


# ---------------------------------------------------------------------------
# Phase 3 — Fidelity Inspection
# ---------------------------------------------------------------------------


def _fidelity_inspection(
    ctx: dict[str, Any],
    targets_generated: list[str],
    output_dir: Path,
    working_dir: Path,
) -> dict:
    """Run fidelity inspection across all generated targets."""
    console.print(
        "\n[bold cyan]Phase 3:[/bold cyan] Running fidelity inspection..."
    )

    system_prompt = load_prompt(STAGE_NUM, "fidelity_inspection.md")

    # Collect all generated target outputs
    target_sections = []
    for target in targets_generated:
        dir_name = TARGET_DIR_MAP[target]
        target_dir = output_dir / dir_name
        if not target_dir.is_dir():
            continue

        section_parts = [f"\n## Target: {target}\n"]
        for f in sorted(target_dir.rglob("*")):
            if f.is_file() and f.suffix in (".md", ".yaml", ".yml", ".txt"):
                rel = f.relative_to(target_dir)
                content = f.read_text(encoding="utf-8")
                section_parts.append(f"### {rel}\n\n{content}\n")
        target_sections.append("\n".join(section_parts))

    human_msg = (
        f"## Source ADL\n\n```yaml\n{ctx['adl_text']}\n```\n\n"
        f"## Source System Prompt\n\n{ctx['system_prompt']}\n\n"
        f"## Knowledge Manifest\n\n{ctx['knowledge_manifest']}\n\n"
        f"## Tools / Actions\n\n{ctx['tools_section']}\n\n"
        f"# Generated Target Packages\n\n"
        + "\n\n".join(target_sections)
    )

    response, trace = _call_llm(
        "reasoning", system_prompt, human_msg, node_name="fidelity_inspection"
    )

    # Save report
    _save(output_dir, "fidelity_report.md", response)
    _save(working_dir, "fidelity_raw_response.md", response)

    console.print(
        f"  [green]✓[/green] Fidelity report generated "
        f"({trace['cost_usd']:.4f} USD, {trace['latency_s']:.1f}s)"
    )

    return trace


# ---------------------------------------------------------------------------
# Pipeline entry point
# ---------------------------------------------------------------------------


def run_pipeline(
    workspace: Path,
    targets: list[str] | None = None,
    output_root: Path | None = None,
) -> None:
    """Run the Stage 6 Target Deployment Packaging pipeline.

    Args:
        workspace: Path to the agent workspace.
        targets: List of target slugs to generate. None or ["all"] = all targets.
                 PAS is always produced regardless.
        output_root: Override output directory. Default: <workspace>/06_deployments/output/
    """
    console.print(
        Panel(
            "[bold]Stage 6 — Target Deployment Packaging[/bold]\n"
            "Converting EARL output to deployment-ready target packages",
            border_style="blue",
        )
    )

    # Resolve targets
    if targets is None or targets == ["all"] or "all" in (targets or []):
        requested_targets = list(ALL_TARGETS)
    else:
        # Validate
        for t in targets:
            if t not in ALL_TARGETS:
                raise ValueError(
                    f"Unknown target: {t}. Valid targets: {ALL_TARGETS}"
                )
        requested_targets = list(targets)

    # PAS is always included
    if "pas" not in requested_targets:
        requested_targets.insert(0, "pas")

    console.print(f"\n[bold]Targets:[/bold] {', '.join(requested_targets)}")

    # Set up directories
    if output_root:
        output_dir = output_root
        working_dir = output_root / "working"
    else:
        output_dir, working_dir = ensure_stage_dirs(workspace, STAGE_NUM)

    output_dir.mkdir(parents=True, exist_ok=True)
    working_dir.mkdir(parents=True, exist_ok=True)

    traces: list[dict] = []
    t_start = time.monotonic()

    # ---- Phase 0: Input Assembly ----
    console.print("\n[bold cyan]Phase 0:[/bold cyan] Assembling inputs from EARL output...")
    ctx = _input_assembly(workspace)
    console.print(f"  [green]✓[/green] Agent: {ctx['agent_name']}")
    console.print(f"  [green]✓[/green] ADL version: {ctx['provenance']['adl_version']}")
    console.print(f"  [green]✓[/green] Source hash: {ctx['provenance']['source_hash'][:16]}...")

    # ---- Phase 1: PAS Generation (always first) ----
    pas_files, pas_trace = _generate_pas(ctx, output_dir, working_dir)
    traces.append(pas_trace)

    # ---- Phase 2: Target Conversion Pipes ----
    # Filter out PAS (already done) and chatgpt-custom-gpt (copy, not LLM)
    llm_targets = [
        t
        for t in requested_targets
        if t not in ("pas", "chatgpt-custom-gpt")
    ]

    if "chatgpt-custom-gpt" in requested_targets:
        _copy_chatgpt_custom_gpt(ctx, output_dir)

    if llm_targets:
        console.print(
            f"\n[bold cyan]Phase 2:[/bold cyan] "
            f"Converting {len(llm_targets)} target(s)..."
        )
        for target in llm_targets:
            trace = _convert_target(
                target, ctx, pas_files, output_dir, working_dir
            )
            traces.append(trace)

    # ---- Phase 3: Fidelity Inspection ----
    # Include all targets that were generated (PAS + LLM targets + chatgpt copy)
    targets_for_inspection = [
        t for t in requested_targets if t != "chatgpt-custom-gpt"
    ]
    if targets_for_inspection:
        inspect_trace = _fidelity_inspection(
            ctx, targets_for_inspection, output_dir, working_dir
        )
        traces.append(inspect_trace)

    # ---- Summary ----
    total_time = time.monotonic() - t_start
    total_cost = sum(t.get("cost_usd", 0) for t in traces)
    total_tokens = sum(t.get("total_tokens", 0) for t in traces)

    # Write execution trace
    trace_data = {
        "stage": "target_deploy",
        "agent_name": ctx["agent_name"],
        "targets_requested": requested_targets,
        "total_time_s": round(total_time, 2),
        "total_cost_usd": round(total_cost, 4),
        "total_tokens": total_tokens,
        "provenance": ctx["provenance"],
        "llm_calls": traces,
    }
    trace_path = working_dir / "execution_trace.json"
    trace_path.write_text(
        json.dumps(trace_data, indent=2, default=str), encoding="utf-8"
    )

    console.print(
        Panel(
            f"[bold green]Stage 6 Complete[/bold green]\n\n"
            f"Agent: {ctx['agent_name']}\n"
            f"Targets: {', '.join(requested_targets)}\n"
            f"LLM calls: {len(traces)}\n"
            f"Total tokens: {total_tokens:,}\n"
            f"Total cost: ${total_cost:.4f}\n"
            f"Total time: {total_time:.1f}s\n"
            f"Output: {output_dir}",
            border_style="green",
        )
    )
