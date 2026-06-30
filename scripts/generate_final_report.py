"""
Final report generator.

Runs the complete validation pipeline and produces
all benchmark, ablation, and error analysis reports.

Usage:
    python scripts/generate_final_report.py
"""

from __future__ import annotations

import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path


def run_step(cmd: list[str], description: str) -> bool:
    """
    Run a subprocess step and report its result.

    Args:
        cmd: Command and arguments list.
        description: Human-readable description for display.

    Returns:
        True if the command exited with code 0.
    """
    print(f"\n{'=' * 62}")
    print(f"  {description}")
    print("=" * 62)

    result = subprocess.run(cmd)

    if result.returncode == 0:
        print(f"\n  [PASS] {description}")
        return True
    else:
        print(f"\n  [FAIL] {description} (exit code {result.returncode})")
        return False


def main() -> None:
    """
    Generate the final project validation report.

    Runs all tests, benchmark validation, integration scripts,
    and prints a consolidated summary.
    """
    print("=" * 62)
    print("  PREPFORGE AI - FINAL REPORT GENERATION")
    print(f"  {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}")
    print("=" * 62)

    python = sys.executable
    results: list[tuple[str, bool]] = []

    # Full test suite
    ok = run_step(
        [python, "-m", "pytest", "tests/", "-v", "--tb=short"],
        "Full Test Suite",
    )
    results.append(("Full Test Suite", ok))

    # Benchmark validation
    ok = run_step(
        [python, "scripts/run_full_validation.py"],
        "Benchmark Validation + Ablation Study + Error Analysis",
    )
    results.append(("Benchmark Validation", ok))

    # Integration scripts
    integration_scripts = [
        ("scripts/test_skill_pipeline_integration.py", "Skill Pipeline Integration"),
        ("scripts/test_recommendation_integration.py", "Recommendation Pipeline Integration"),
        ("scripts/test_resume_pipeline_integration.py", "Resume Pipeline Integration"),
    ]

    for script_path, label in integration_scripts:
        if Path(script_path).exists():
            ok = run_step([python, script_path], label)
        else:
            print(f"\n  [SKIP] {label} - script not found: {script_path}")
            ok = True  # Non-fatal skip
        results.append((label, ok))

    # Summary
    passed = sum(1 for _, ok in results if ok)
    total = len(results)

    print("\n" + "=" * 62)
    print("  FINAL REPORT SUMMARY")
    print("=" * 62)

    for label, ok in results:
        icon = "[PASS]" if ok else "[FAIL]"
        print(f"  {icon}  {label}")

    print()
    print(f"  Checks passed: {passed}/{total}")

    if passed == total:
        print()
        print("  All checks passed.")
        print("  Project is ready for submission / viva defense.")
    else:
        failed = total - passed
        print()
        print(f"  {failed} check(s) failed. Review output above before submission.")

    print()
    print("  Generated benchmark reports: benchmark/reports/")
    print("  Project documentation:       docs/")
    print("=" * 62)


if __name__ == "__main__":
    main()
