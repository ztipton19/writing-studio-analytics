#!/usr/bin/env python
"""Pre-release gate for V2 handoff.

Runs baseline checks in order and exits non-zero on first failure.
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path


def run(cmd: list[str], label: str) -> None:
    print(f"\n=== {label} ===")
    print(" ".join(cmd))
    subprocess.run(cmd, check=True)


def main() -> int:
    parser = argparse.ArgumentParser(description="Run pre-release quality gate")
    parser.add_argument("--scheduled-file", type=Path, help="Optional scheduled sample for smoke test")
    parser.add_argument("--walkin-file", type=Path, help="Optional walk-in sample for smoke test")
    parser.add_argument("--run-ai", action="store_true", help="Enable AI checks in smoke test")
    parser.add_argument("--build", action="store_true", help="Build executable after checks")
    args = parser.parse_args()

    py = sys.executable

    run([py, "-m", "compileall", "src", "tests", "scripts", "build_executable.py"], "Compile Check")
    run([py, "-m", "pytest", "-q"], "Unit Tests")

    if args.scheduled_file or args.walkin_file:
        smoke_cmd = [py, "scripts/release_smoke_test.py"]
        if args.scheduled_file:
            smoke_cmd += ["--scheduled-file", str(args.scheduled_file)]
        if args.walkin_file:
            smoke_cmd += ["--walkin-file", str(args.walkin_file)]
        if args.run_ai:
            smoke_cmd += ["--run-ai"]
        run(smoke_cmd, "Smoke Test")

    if args.build:
        run([py, "build_executable.py"], "Build")

    print("\n[PASS] Pre-release gate complete")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
