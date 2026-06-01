"""Main CLI entry point for the DEA Builder."""

import sys
from pathlib import Path

from rich.console import Console

console = Console()


def main() -> None:
    """DEA Builder CLI — dispatch to stage subcommands."""
    args = sys.argv[1:]

    if not args or args[0] in ("--help", "-h"):
        _print_usage()
        sys.exit(0)

    command = args[0]

    if command == "run":
        _run_full(args[1:])
    elif command == "plan":
        _run_plan(args[1:])
    elif command == "dea-context":
        _run_dea_context(args[1:])
    elif command == "expert-six-prompt":
        _run_expert_six_prompt(args[1:])
    elif command == "expert-six":
        _run_expert_six(args[1:])
    elif command == "anchor":
        _run_anchor(args[1:])
    elif command == "earl":
        _run_earl(args[1:])
    elif command == "package":
        _run_package(args[1:])
    else:
        console.print(f"[red]Unknown command:[/red] {command}")
        _print_usage()
        sys.exit(1)


def _print_usage() -> None:
    """Print CLI usage information."""
    console.print(
        "\n[bold]DEA Builder[/bold] — Deep Expert Agent pipeline\n\n"
        "[bold]Usage:[/bold]\n"
        "  dea-builder run <workspace_path> [options]\n"
        "  dea-builder plan <workspace_path> [options]\n"
        "  dea-builder <stage> <workspace_path>\n"
        "\n"
        "[bold]Pipeline:[/bold]\n"
        "  run               Run full pipeline (Stages 1–6)\n"
        "  plan              Planning mode — show what would run\n"
        "\n"
        "[bold]Options (run):[/bold]\n"
        "  --force-stage N   Force re-run of stage N (repeatable)\n"
        "  --start-stage N   Start from stage N (skip earlier if complete)\n"
        "  --skip-package    Skip Stage 6 entirely\n"
        "  --targets <list>  Comma-separated targets for Stage 6\n"
        "\n"
        "[bold]Individual Stages:[/bold]\n"
        "  dea-context       Stage 1 — Normalize inputs into canonical context document\n"
        "  expert-six-prompt Stage 2 — Generate Expert Six research prompt\n"
        "  expert-six        Stage 3 — Execute and finalize Expert Six\n"
        "  anchor            Stage 4 — Create epistemic anchor\n"
        "  earl              Stage 5 — Create EARL agent package\n"
        "  package           Stage 6 — Target deployment packaging\n"
    )


def _run_dea_context(args: list[str]) -> None:
    """Run Stage 1 — DEA Context Creation."""
    if not args:
        console.print("[red]Error:[/red] workspace path required")
        console.print("  Usage: dea-builder dea-context <workspace_path>")
        sys.exit(1)

    workspace_path = Path(args[0]).resolve()

    if not workspace_path.is_dir():
        console.print(f"[red]Error:[/red] workspace not found: {workspace_path}")
        sys.exit(1)

    from dea_builder.llm.content_safety import PromptInjectionError
    from dea_builder.stages.dea_context import NormalizationError, run_stage

    try:
        run_stage(workspace_path)
    except FileNotFoundError as exc:
        console.print(f"\n[red]Error:[/red] {exc}")
        sys.exit(1)
    except PromptInjectionError as exc:
        console.print(f"\n[bold red]REJECTED:[/bold red] {exc}")
        console.print(
            "\n[yellow]Resolution:[/yellow] Review the context document for "
            "prompt-injection patterns and resubmit. See working/prompt_shield_rejection.json "
            "for details."
        )
        sys.exit(3)
    except NormalizationError as exc:
        console.print(f"\n[red]Error:[/red] {exc}")
        console.print(
            "\n[yellow]Resolution:[/yellow] Add the missing information to "
            "00_inputs/ and re-run."
        )
        sys.exit(2)


def _run_expert_six_prompt(args: list[str]) -> None:
    """Run Stage 2 — Expert Six Prompt Creation."""
    if not args:
        console.print("[red]Error:[/red] workspace path required")
        console.print("  Usage: dea-builder expert-six-prompt <workspace_path>")
        sys.exit(1)

    workspace_path = Path(args[0]).resolve()

    if not workspace_path.is_dir():
        console.print(f"[red]Error:[/red] workspace not found: {workspace_path}")
        sys.exit(1)

    from dea_builder.stages.expert_six_prompt import run_stage

    try:
        run_stage(workspace_path)
    except FileNotFoundError as exc:
        console.print(f"\n[red]Error:[/red] {exc}")
        sys.exit(1)
    except ValueError as exc:
        console.print(f"\n[red]Error:[/red] {exc}")
        sys.exit(2)


def _run_expert_six(args: list[str]) -> None:
    """Run Stage 3 — Expert Six Execution and Finalization."""
    if not args:
        console.print("[red]Error:[/red] workspace path required")
        console.print("  Usage: dea-builder expert-six <workspace_path>")
        sys.exit(1)

    workspace_path = Path(args[0]).resolve()

    if not workspace_path.is_dir():
        console.print(f"[red]Error:[/red] workspace not found: {workspace_path}")
        sys.exit(1)

    from dea_builder.stages.expert_six import run_stage

    try:
        run_stage(workspace_path)
    except FileNotFoundError as exc:
        console.print(f"\n[red]Error:[/red] {exc}")
        sys.exit(1)
    except (ValueError, EnvironmentError) as exc:
        console.print(f"\n[red]Error:[/red] {exc}")
        sys.exit(2)


def _run_anchor(args: list[str]) -> None:
    """Run Stage 4 — Epistemic Anchor Creation."""
    if not args:
        console.print("[red]Error:[/red] workspace path required")
        console.print("  Usage: dea-builder anchor <workspace_path>")
        sys.exit(1)

    workspace_path = Path(args[0]).resolve()

    if not workspace_path.is_dir():
        console.print(f"[red]Error:[/red] workspace not found: {workspace_path}")
        sys.exit(1)

    from dea_builder.stages.epistemic_anchor import run_pipeline

    try:
        run_pipeline(workspace_path)
    except FileNotFoundError as exc:
        console.print(f"\n[red]Error:[/red] {exc}")
        sys.exit(1)
    except (ValueError, EnvironmentError) as exc:
        console.print(f"\n[red]Error:[/red] {exc}")
        sys.exit(2)


def _run_earl(args: list[str]) -> None:
    """Run Stage 5 — EARL Agent Package Creation."""
    if not args:
        console.print("[red]Error:[/red] workspace path required")
        console.print("  Usage: dea-builder earl <workspace_path>")
        sys.exit(1)

    workspace_path = Path(args[0]).resolve()

    if not workspace_path.is_dir():
        console.print(f"[red]Error:[/red] workspace not found: {workspace_path}")
        sys.exit(1)

    from dea_builder.stages.earl import run_pipeline as run_earl_pipeline

    try:
        run_earl_pipeline(workspace_path)
    except FileNotFoundError as exc:
        console.print(f"\n[red]Error:[/red] {exc}")
        sys.exit(1)
    except (ValueError, EnvironmentError) as exc:
        console.print(f"\n[red]Error:[/red] {exc}")
        sys.exit(2)


def _run_package(args: list[str]) -> None:
    """Run Stage 6 — Target Deployment Packaging."""
    if not args:
        console.print("[red]Error:[/red] workspace path required")
        console.print(
            "  Usage: dea-builder package <workspace_path> "
            "[--targets <list>] [--output <dir>]"
        )
        sys.exit(1)

    workspace_path = Path(args[0]).resolve()

    if not workspace_path.is_dir():
        console.print(f"[red]Error:[/red] workspace not found: {workspace_path}")
        sys.exit(1)

    # Parse optional --targets and --output flags
    targets = None
    output_root = None
    i = 1
    while i < len(args):
        if args[i] == "--targets" and i + 1 < len(args):
            targets = [t.strip() for t in args[i + 1].split(",")]
            i += 2
        elif args[i] == "--output" and i + 1 < len(args):
            output_root = Path(args[i + 1]).resolve()
            i += 2
        else:
            console.print(f"[red]Error:[/red] unknown argument: {args[i]}")
            sys.exit(1)

    from dea_builder.stages.target_deploy import run_pipeline as run_package_pipeline

    try:
        run_package_pipeline(workspace_path, targets=targets, output_root=output_root)
    except FileNotFoundError as exc:
        console.print(f"\n[red]Error:[/red] {exc}")
        sys.exit(1)
    except (ValueError, EnvironmentError) as exc:
        console.print(f"\n[red]Error:[/red] {exc}")
        sys.exit(2)


def _run_full(args: list[str]) -> None:
    """Run full pipeline (Stages 1–6)."""
    if not args:
        console.print("[red]Error:[/red] workspace path required")
        console.print(
            "  Usage: dea-builder run <workspace_path> "
            "[--force-stage N] [--start-stage N] [--skip-package] [--targets <list>]"
        )
        sys.exit(1)

    workspace_path = Path(args[0]).resolve()

    if not workspace_path.is_dir():
        console.print(f"[red]Error:[/red] workspace not found: {workspace_path}")
        sys.exit(1)

    # Parse flags
    force_stages: list[int] = []
    start_stage = 1
    skip_package = False
    targets = None
    i = 1
    while i < len(args):
        if args[i] == "--force-stage" and i + 1 < len(args):
            force_stages.append(int(args[i + 1]))
            i += 2
        elif args[i] == "--start-stage" and i + 1 < len(args):
            start_stage = int(args[i + 1])
            i += 2
        elif args[i] == "--skip-package":
            skip_package = True
            i += 1
        elif args[i] == "--targets" and i + 1 < len(args):
            targets = [t.strip() for t in args[i + 1].split(",")]
            i += 2
        else:
            console.print(f"[red]Error:[/red] unknown argument: {args[i]}")
            sys.exit(1)

    from dea_builder.stages.orchestrator import run_pipeline

    result = run_pipeline(
        workspace_path,
        force_stages=force_stages,
        start_stage=start_stage,
        skip_package=skip_package,
        targets=targets,
    )

    if not result.success:
        sys.exit(1)


def _run_plan(args: list[str]) -> None:
    """Run planning mode — show what would execute."""
    if not args:
        console.print("[red]Error:[/red] workspace path required")
        console.print("  Usage: dea-builder plan <workspace_path> [--skip-package]")
        sys.exit(1)

    workspace_path = Path(args[0]).resolve()

    if not workspace_path.is_dir():
        console.print(f"[red]Error:[/red] workspace not found: {workspace_path}")
        sys.exit(1)

    skip_package = "--skip-package" in args[1:]

    from dea_builder.stages.orchestrator import plan_pipeline

    plan_pipeline(workspace_path, skip_package=skip_package)
