"""Shared workspace I/O utilities — used by all 6 stage modules."""

from __future__ import annotations

import importlib.resources
import json
from pathlib import Path
from typing import Any


# ---------------------------------------------------------------------------
# Stage directory naming convention
# ---------------------------------------------------------------------------

STAGE_NAMES: dict[int, str] = {
    1: "01_dea_context",
    2: "02_expert_six_prompt",
    3: "03_expert_six",
    4: "04_epistemic_anchor",
    5: "05_earl",
    6: "06_deployments",
}


# ---------------------------------------------------------------------------
# Directory management
# ---------------------------------------------------------------------------


def ensure_stage_dirs(workspace_dir: Path, stage_num: int) -> tuple[Path, Path]:
    """Create output/ and working/ directories for a stage.

    Returns (output_dir, working_dir).
    """
    stage_name = STAGE_NAMES[stage_num]
    stage_root = workspace_dir / stage_name
    output_dir = stage_root / "output"
    working_dir = stage_root / "working"
    output_dir.mkdir(parents=True, exist_ok=True)
    working_dir.mkdir(parents=True, exist_ok=True)
    return output_dir, working_dir


def ensure_inputs_dir(workspace_dir: Path) -> Path:
    """Ensure 00_inputs/ exists and return its path."""
    inputs_dir = workspace_dir / "00_inputs"
    inputs_dir.mkdir(parents=True, exist_ok=True)
    return inputs_dir


# ---------------------------------------------------------------------------
# Input reading
# ---------------------------------------------------------------------------

INPUT_EXTENSIONS = {".md", ".txt", ".yaml", ".yml", ".json"}


def read_all_inputs(workspace_dir: Path) -> dict[str, str]:
    """Read all supported files from 00_inputs/ (non-recursive).

    Returns {filename: content} for files with recognized extensions.
    Raises FileNotFoundError if 00_inputs/ does not exist or is empty.
    """
    inputs_dir = workspace_dir / "00_inputs"
    if not inputs_dir.is_dir():
        raise FileNotFoundError(
            f"No 00_inputs/ directory found in workspace: {workspace_dir}"
        )

    files: dict[str, str] = {}
    for f in sorted(inputs_dir.iterdir()):
        if f.is_file() and f.suffix.lower() in INPUT_EXTENSIONS:
            files[f.name] = f.read_text(encoding="utf-8")

    if not files:
        raise FileNotFoundError(
            f"No supported input files found in {inputs_dir}. "
            f"Supported extensions: {sorted(INPUT_EXTENSIONS)}"
        )
    return files


# ---------------------------------------------------------------------------
# Output writing
# ---------------------------------------------------------------------------


def write_stage_output(
    workspace_dir: Path, stage_num: int, filename: str, content: str
) -> Path:
    """Write a file to a stage's output/ directory. Returns the written path."""
    output_dir, _ = ensure_stage_dirs(workspace_dir, stage_num)
    path = output_dir / filename
    path.write_text(content, encoding="utf-8")
    return path


def write_working_artifact(
    workspace_dir: Path, stage_num: int, filename: str, content: str
) -> Path:
    """Write a file to a stage's working/ directory. Returns the written path."""
    _, working_dir = ensure_stage_dirs(workspace_dir, stage_num)
    path = working_dir / filename
    path.write_text(content, encoding="utf-8")
    return path


def write_execution_trace(
    workspace_dir: Path, stage_num: int, trace: dict[str, Any]
) -> Path:
    """Write execution_trace.json to a stage's working/ directory."""
    _, working_dir = ensure_stage_dirs(workspace_dir, stage_num)
    path = working_dir / "execution_trace.json"
    path.write_text(json.dumps(trace, indent=2, default=str), encoding="utf-8")
    return path


# ---------------------------------------------------------------------------
# Prompt loading
# ---------------------------------------------------------------------------


def load_prompt(stage_num: int, prompt_filename: str) -> str:
    """Load a prompt template from the prompts/stageN/ package resource.

    Uses importlib.resources so prompts are resolved correctly whether
    the package is installed in editable mode or as a wheel.
    """
    package = f"dea_builder.prompts.stage{stage_num}"
    try:
        ref = importlib.resources.files(package).joinpath(prompt_filename)
        return ref.read_text(encoding="utf-8")
    except (ModuleNotFoundError, FileNotFoundError) as exc:
        raise FileNotFoundError(
            f"Prompt file not found: {package}/{prompt_filename}"
        ) from exc
