"""Stage 7 — Main Orchestrator.

Coordinates full pipeline execution (Stages 1–6) with:
- Stage dependency validation
- Skip logic (output already exists)
- Forced re-run (--force-stage)
- Per-stage error handling
- Aggregated cost/time reporting
- Planning mode (dry-run)
"""

from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from pathlib import Path

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

console = Console()

# ===================================================================
# Stage definitions
# ===================================================================

STAGE_ORDER = [1, 2, 3, 4, 5, 6]

STAGE_NAMES = {
    1: "DEA Context Creation",
    2: "Expert Six Prompt Creation",
    3: "Expert Six Execution and Finalization",
    4: "Epistemic Anchor Creation",
    5: "EARL Agent Package Creation",
    6: "Target Deployment Packaging",
}

STAGE_COMMANDS = {
    1: "dea-context",
    2: "expert-six-prompt",
    3: "expert-six",
    4: "anchor",
    5: "earl",
    6: "package",
}

# Canonical output file that signals a stage is complete
STAGE_OUTPUTS = {
    1: "01_dea_context/output/context_document.md",
    2: "02_expert_six_prompt/output/expert_six_research_prompt.md",
    3: "03_expert_six/output/expert_six_final.md",
    4: "04_epistemic_anchor/output/epistemic_anchor.md",
    5: "05_earl/output/agent.adl.yaml",
    6: "06_deployments/output/fidelity_report.md",
}

# Stages that each stage depends on (must be complete before running)
STAGE_DEPS = {
    1: [],
    2: [1],
    3: [1, 2],
    4: [1, 3],
    5: [4],
    6: [5],
}


# ===================================================================
# Data classes
# ===================================================================


@dataclass
class StageResult:
    """Result of a single stage execution."""

    stage: int
    name: str
    status: str  # "skipped", "success", "error"
    elapsed_s: float = 0.0
    error: str | None = None


@dataclass
class PipelineResult:
    """Aggregated result of the full pipeline."""

    workspace: Path
    stages: list[StageResult] = field(default_factory=list)
    total_elapsed_s: float = 0.0

    @property
    def success(self) -> bool:
        return all(s.status in ("skipped", "success") for s in self.stages)

    @property
    def stages_run(self) -> int:
        return sum(1 for s in self.stages if s.status == "success")

    @property
    def stages_skipped(self) -> int:
        return sum(1 for s in self.stages if s.status == "skipped")

    @property
    def stages_failed(self) -> int:
        return sum(1 for s in self.stages if s.status == "error")


# ===================================================================
# Core logic
# ===================================================================


def _stage_complete(workspace: Path, stage: int) -> bool:
    """Check if a stage's canonical output exists."""
    output_path = workspace / STAGE_OUTPUTS[stage]
    return output_path.is_file()


def _check_deps(workspace: Path, stage: int) -> list[int]:
    """Return list of missing dependencies for a stage."""
    missing = []
    for dep in STAGE_DEPS[stage]:
        if not _stage_complete(workspace, dep):
            missing.append(dep)
    return missing


def _run_stage(
    workspace: Path,
    stage: int,
    *,
    targets: list[str] | None = None,
    skip_package: bool = False,
) -> StageResult:
    """Execute a single stage, returning its result."""
    name = STAGE_NAMES[stage]

    if stage == 6 and skip_package:
        return StageResult(stage=stage, name=name, status="skipped")

    console.print(f"\n[bold cyan]▶ Stage {stage}:[/bold cyan] {name}")

    start = time.time()
    try:
        if stage == 1:
            from dea_builder.stages.dea_context import run_stage as run_s1
            run_s1(workspace)
        elif stage == 2:
            from dea_builder.stages.expert_six_prompt import run_stage as run_s2
            run_s2(workspace)
        elif stage == 3:
            from dea_builder.stages.expert_six import run_stage as run_s3
            run_s3(workspace)
        elif stage == 4:
            from dea_builder.stages.epistemic_anchor import run_pipeline as run_s4
            run_s4(workspace)
        elif stage == 5:
            from dea_builder.stages.earl import run_pipeline as run_s5
            run_s5(workspace)
        elif stage == 6:
            from dea_builder.stages.target_deploy import run_pipeline as run_s6
            run_s6(workspace, targets=targets)

        elapsed = time.time() - start
        return StageResult(stage=stage, name=name, status="success", elapsed_s=elapsed)

    except Exception as exc:
        elapsed = time.time() - start
        return StageResult(
            stage=stage, name=name, status="error", elapsed_s=elapsed, error=str(exc)
        )


# ===================================================================
# Pipeline modes
# ===================================================================


def run_pipeline(
    workspace: Path,
    *,
    force_stages: list[int] | None = None,
    skip_package: bool = False,
    targets: list[str] | None = None,
    start_stage: int = 1,
) -> PipelineResult:
    """Run the full pipeline (Stages 1–6) with skip logic.

    Parameters
    ----------
    workspace : Path
        Workspace root directory.
    force_stages : list[int] | None
        Stages to force re-run even if output exists.
    skip_package : bool
        If True, skip Stage 6 entirely.
    targets : list[str] | None
        Target list passed to Stage 6. None = all targets.
    start_stage : int
        First stage to consider (1–6). Earlier stages are still
        dependency-checked but skipped if already complete.
    """
    force_stages = force_stages or []

    console.print(
        Panel(
            "[bold]Full Pipeline Execution[/bold]\n"
            f"Workspace: {workspace.name}",
            title="DEA Builder",
            border_style="blue",
        )
    )

    pipeline_start = time.time()
    result = PipelineResult(workspace=workspace)

    for stage in STAGE_ORDER:
        # Skip stages before start_stage (unless forced)
        if stage < start_stage and stage not in force_stages:
            if _stage_complete(workspace, stage):
                result.stages.append(
                    StageResult(stage=stage, name=STAGE_NAMES[stage], status="skipped")
                )
                continue

        # Skip if output exists and not forced
        if _stage_complete(workspace, stage) and stage not in force_stages:
            console.print(
                f"  [dim]Stage {stage} ({STAGE_NAMES[stage]}): "
                f"output exists, skipping[/dim]"
            )
            result.stages.append(
                StageResult(stage=stage, name=STAGE_NAMES[stage], status="skipped")
            )
            continue

        # Check dependencies
        missing = _check_deps(workspace, stage)
        if missing:
            missing_names = [f"Stage {m} ({STAGE_NAMES[m]})" for m in missing]
            error_msg = f"Missing dependencies: {', '.join(missing_names)}"
            console.print(f"  [red]Stage {stage}: {error_msg}[/red]")
            result.stages.append(
                StageResult(
                    stage=stage,
                    name=STAGE_NAMES[stage],
                    status="error",
                    error=error_msg,
                )
            )
            break  # Cannot continue past a failed dependency

        # Run the stage
        stage_result = _run_stage(
            workspace,
            stage,
            targets=targets,
            skip_package=skip_package,
        )
        result.stages.append(stage_result)

        if stage_result.status == "error":
            console.print(
                f"\n  [red]✗ Stage {stage} failed:[/red] {stage_result.error}"
            )
            break  # Stop pipeline on error

    result.total_elapsed_s = time.time() - pipeline_start
    _print_summary(result)
    return result


def plan_pipeline(workspace: Path, *, skip_package: bool = False) -> None:
    """Planning mode — show what would run without executing.

    Reports:
    - Detected files and completed stages
    - Stages that would run
    - Stages that would be skipped
    - Missing dependencies / blockers
    """
    console.print(
        Panel(
            "[bold]Pipeline Plan (Dry Run)[/bold]\n"
            f"Workspace: {workspace.name}",
            title="DEA Builder",
            border_style="yellow",
        )
    )

    table = Table(title="Stage Status")
    table.add_column("Stage", style="cyan", width=8)
    table.add_column("Name", width=40)
    table.add_column("Output Exists", width=14)
    table.add_column("Deps Met", width=10)
    table.add_column("Action", width=12)

    runnable_count = 0
    skip_count = 0
    blocked_count = 0

    for stage in STAGE_ORDER:
        name = STAGE_NAMES[stage]
        output_exists = _stage_complete(workspace, stage)
        missing_deps = _check_deps(workspace, stage)
        deps_met = len(missing_deps) == 0

        if stage == 6 and skip_package:
            action = "[dim]skip[/dim]"
            skip_count += 1
        elif output_exists:
            action = "[green]skip[/green]"
            skip_count += 1
        elif deps_met:
            action = "[cyan]run[/cyan]"
            runnable_count += 1
        else:
            action = "[red]blocked[/red]"
            blocked_count += 1

        table.add_row(
            str(stage),
            name,
            "[green]✓[/green]" if output_exists else "[red]✗[/red]",
            "[green]✓[/green]" if deps_met else f"[red]missing {missing_deps}[/red]",
            action,
        )

    console.print(table)
    console.print(
        f"\n  [cyan]Would run:[/cyan] {runnable_count} stage(s)  "
        f"[green]Skip:[/green] {skip_count}  "
        f"[red]Blocked:[/red] {blocked_count}"
    )

    if runnable_count == 0 and blocked_count == 0:
        console.print("\n  [green]✓ Pipeline complete — all outputs exist.[/green]")


# ===================================================================
# Reporting
# ===================================================================


def _print_summary(result: PipelineResult) -> None:
    """Print a final summary table."""
    table = Table(title="Pipeline Summary")
    table.add_column("Stage", style="cyan", width=8)
    table.add_column("Name", width=40)
    table.add_column("Status", width=10)
    table.add_column("Time", width=10, justify="right")

    for sr in result.stages:
        if sr.status == "success":
            status_str = "[green]✓[/green]"
        elif sr.status == "skipped":
            status_str = "[dim]skip[/dim]"
        else:
            status_str = "[red]✗[/red]"

        time_str = f"{sr.elapsed_s:.1f}s" if sr.elapsed_s > 0 else "—"
        table.add_row(str(sr.stage), sr.name, status_str, time_str)

    console.print()
    console.print(table)

    total_m = result.total_elapsed_s / 60
    console.print(
        Panel(
            f"[bold]Total time:[/bold] {total_m:.1f} min\n"
            f"[bold]Stages run:[/bold] {result.stages_run}\n"
            f"[bold]Stages skipped:[/bold] {result.stages_skipped}\n"
            f"[bold]Stages failed:[/bold] {result.stages_failed}\n"
            f"[bold]Result:[/bold] {'[green]SUCCESS[/green]' if result.success else '[red]FAILED[/red]'}",
            title="Pipeline Complete" if result.success else "Pipeline Failed",
            border_style="green" if result.success else "red",
        )
    )

    # Write pipeline trace
    trace_path = result.workspace / "runs"
    trace_path.mkdir(parents=True, exist_ok=True)
    trace_file = trace_path / "last_pipeline_trace.json"
    trace_data = {
        "workspace": str(result.workspace),
        "total_elapsed_s": round(result.total_elapsed_s, 2),
        "success": result.success,
        "stages": [
            {
                "stage": sr.stage,
                "name": sr.name,
                "status": sr.status,
                "elapsed_s": round(sr.elapsed_s, 2),
                "error": sr.error,
            }
            for sr in result.stages
        ],
    }
    trace_file.write_text(json.dumps(trace_data, indent=2))
    console.print(f"\n  Trace: {trace_file.relative_to(result.workspace)}")
