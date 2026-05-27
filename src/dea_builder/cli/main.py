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

    if command == "dea-context":
        _run_dea_context(args[1:])
    elif command == "expert-six-prompt":
        _run_expert_six_prompt(args[1:])
    elif command == "expert-six":
        _run_expert_six(args[1:])
    elif command == "anchor":
        _run_anchor(args[1:])
    elif command == "earl":
        _run_earl(args[1:])
    else:
        console.print(f"[red]Unknown command:[/red] {command}")
        _print_usage()
        sys.exit(1)


def _print_usage() -> None:
    """Print CLI usage information."""
    console.print(
        "\n[bold]DEA Builder[/bold] — Deep Expert Agent pipeline\n\n"
        "[bold]Usage:[/bold]\n"
        "  dea-builder dea-context <workspace_path>\n"
        "  dea-builder expert-six-prompt <workspace_path>\n"
        "\n"
        "[bold]Stages:[/bold]\n"
        "  dea-context       Stage 1 — Normalize inputs into canonical context document\n"
        "  expert-six-prompt Stage 2 — Generate Expert Six research prompt (coming)\n"
        "  expert-six        Stage 3 — Execute and finalize Expert Six (coming)\n"
        "  anchor            Stage 4 — Create epistemic anchor (coming)\n"
        "  earl              Stage 5 — Create EARL agent package (coming)\n"
        "  package           Stage 6 — Target deployment packaging (coming)\n"
        "  run               Run full pipeline (coming)\n"
        "  plan              Planning mode (coming)\n"
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
