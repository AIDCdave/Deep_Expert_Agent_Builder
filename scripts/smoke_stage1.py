#!/usr/bin/env python3
"""Smoke test for Stage 1 — DEA Context Creation.

Sets up a test workspace with the Modern UX Design example worksheet,
runs Stage 1 end-to-end, and verifies output.

Usage:
    uv run python scripts/smoke_stage1.py
"""

import shutil
import sys
from pathlib import Path

# Ensure project root is importable
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))

REFERENCE_DIR = PROJECT_ROOT / ".planning" / "reference" / "modern_ux_design_example"
TEST_WORKSPACE = PROJECT_ROOT / "workspaces" / "_test_stage1"


def setup_workspace() -> Path:
    """Create a clean test workspace with the example worksheet."""
    # Clean any previous test run
    if TEST_WORKSPACE.exists():
        shutil.rmtree(TEST_WORKSPACE)

    inputs_dir = TEST_WORKSPACE / "00_inputs"
    inputs_dir.mkdir(parents=True)

    # Copy the completed intake worksheet as the input
    src = REFERENCE_DIR / "completed_intake_worksheet.md"
    if not src.exists():
        print(f"ERROR: reference file not found: {src}")
        sys.exit(1)

    dst = inputs_dir / "completed_intake_worksheet.md"
    shutil.copy2(src, dst)
    print(f"✓ Test workspace created: {TEST_WORKSPACE}")
    print(f"  Input: {dst.name}")
    return TEST_WORKSPACE


def verify_outputs(workspace: Path) -> bool:
    """Verify Stage 1 produced expected outputs."""
    output_dir = workspace / "01_dea_context" / "output"
    working_dir = workspace / "01_dea_context" / "working"

    checks = [
        ("output/context_document.md", output_dir / "context_document.md"),
        ("working/v0_normalized.md", working_dir / "v0_normalized.md"),
        ("working/v1_reviewed.md", working_dir / "v1_reviewed.md"),
        ("working/execution_trace.json", working_dir / "execution_trace.json"),
    ]

    all_pass = True
    print("\n--- Output Verification ---")
    for label, path in checks:
        if path.exists():
            size = path.stat().st_size
            print(f"  ✓ {label} ({size:,} bytes)")
        else:
            print(f"  ✗ {label} — MISSING")
            all_pass = False

    # Check canonical document has expected sections
    if (output_dir / "context_document.md").exists():
        content = (output_dir / "context_document.md").read_text()
        expected_sections = [
            "Target Domain",
            "Downstream Purpose",
            "Agent Definition",
            "Primary Knowledge Domains",
            "Mandatory Inclusions",
            "Prospects",
            "Desired Coverage",
            "Business Context",
            "Constraints",
            "Exclusions",
            "Expertise Baseline",
            "Special Instructions",
        ]
        print("\n--- Section Checks ---")
        for section in expected_sections:
            if section.lower() in content.lower():
                print(f"  ✓ {section}")
            else:
                print(f"  ✗ {section} — NOT FOUND")
                all_pass = False

    return all_pass


def main() -> None:
    """Run the full smoke test."""
    print("=" * 60)
    print("Stage 1 Smoke Test — DEA Context Creation")
    print("=" * 60)

    workspace = setup_workspace()

    print("\n--- Running Stage 1 ---\n")

    from dea_builder.stages.dea_context import NormalizationError, run_stage

    try:
        result = run_stage(workspace)
    except NormalizationError as exc:
        print(f"\n✗ NORMALIZATION FAILED: {exc}")
        print("\nThis likely means the example worksheet doesn't provide enough")
        print("information for all 12 required sections of the Hardened Template.")
        sys.exit(2)
    except Exception as exc:
        print(f"\n✗ UNEXPECTED ERROR: {type(exc).__name__}: {exc}")
        sys.exit(1)

    # Verify
    success = verify_outputs(workspace)

    print("\n" + "=" * 60)
    if success:
        print("✓ SMOKE TEST PASSED")
        print(f"  Cost: ${result.get('total_cost', 0):.4f}")
        print(f"  Time: {result.get('total_latency_s', 0):.1f}s")
    else:
        print("✗ SMOKE TEST FAILED — some outputs missing or incomplete")
        sys.exit(1)
    print("=" * 60)


if __name__ == "__main__":
    main()
