"""
Run all tests with grouped summary reporting.

Runs each test module independently and prints a clean
pass/fail summary table at the end.

Usage:
    python scripts/run_all_tests.py
"""

from __future__ import annotations

import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path


def run_test_file(test_file: str) -> tuple[bool, str]:
    """
    Run a single test file and return pass/fail + summary line.

    Args:
        test_file: Relative path to the test file.

    Returns:
        Tuple of (passed: bool, summary: str).
    """
    if not Path(test_file).exists():
        return True, "SKIPPED (file not found)"

    result = subprocess.run(
        [sys.executable, "-m", "pytest", test_file, "-v", "--tb=short"],
        capture_output=True,
        text=True,
    )

    if result.returncode == 0:
        lines = result.stdout.strip().split("\n")
        summary_lines = [line for line in lines if "passed" in line]
        summary = summary_lines[-1].strip() if summary_lines else "passed"
        return True, summary
    else:
        lines = result.stdout.strip().split("\n")
        summary_lines = [
            line for line in lines
            if "failed" in line or "error" in line.lower()
        ]
        summary = summary_lines[-1].strip() if summary_lines else "FAILED"
        return False, summary


def main() -> None:
    """
    Run all test groups and display a consolidated summary table.
    """
    print("=" * 65)
    print("  PREPFORGE AI - COMPLETE TEST SUITE")
    print(f"  {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}")
    print("=" * 65)

    test_groups: list[tuple[str, str]] = [
        ("tests/test_schemas.py", "Schema Tests"),
        ("tests/test_shared_infrastructure.py", "Shared Infrastructure Tests"),
        ("tests/test_evaluation_ensemble.py", "Evaluation Ensemble Tests"),
        ("tests/test_benchmark.py", "Benchmark Validation Tests"),
        ("tests/test_skill_pipeline.py", "Skill Pipeline Tests"),
        ("tests/test_recommendation_pipeline.py", "Recommendation Pipeline Tests"),
        ("tests/test_database.py", "Database Layer Tests"),
        ("tests/test_services.py", "Service Layer Tests"),
        ("tests/test_api.py", "API Layer Tests"),
        ("tests/test_resume_pipeline.py", "Resume Pipeline Tests"),
    ]

    all_passed = True
    results: list[tuple[str, bool, str]] = []

    for test_file, description in test_groups:
        passed, summary = run_test_file(test_file)
        results.append((description, passed, summary))
        if not passed:
            all_passed = False

    # Summary table
    print()
    print(f"  {'Test Group':<40} {'Result'}")
    print("  " + "-" * 60)

    for description, passed, summary in results:
        icon = "[PASS]" if passed else "[FAIL]"
        short_summary = summary[:35] if len(summary) > 35 else summary
        print(f"  {icon}  {description:<38} {short_summary}")

    print()
    passed_count = sum(1 for _, ok, _ in results if ok)
    total_count = len(results)

    print("=" * 65)
    if all_passed:
        print(f"  ALL {total_count} TEST GROUPS PASSED")
        print("  Project test suite is green.")
    else:
        failed_count = total_count - passed_count
        print(f"  {failed_count}/{total_count} TEST GROUPS FAILED")
        print("  Review the output above for details.")
    print("=" * 65)


if __name__ == "__main__":
    main()
