#!/usr/bin/env python
"""
Build script for creating a standalone executable using PyInstaller spec.

Usage:
    python build_executable.py
"""

import os
import subprocess
import sys
from pathlib import Path


def run_command(cmd, description):
    """Run a command and display progress."""
    print(f"\n{'=' * 60}")
    print(description)
    print(f"{'=' * 60}")
    print(f"Running: {' '.join(cmd)}\n")

    try:
        subprocess.run(cmd, check=True)
        print(f"\n[OK] {description}")
        return True
    except subprocess.CalledProcessError as exc:
        print(f"\n[FAIL] {description}")
        print(f"Error: {exc}")
        return False


def detect_output_path(dist_dir: Path) -> Path:
    """Return expected output executable path for current platform."""
    if sys.platform == "win32":
        return dist_dir / "WritingStudioAnalytics.exe"
    return dist_dir / "WritingStudioAnalytics"


def launch_executable(exe_path: Path) -> None:
    """Launch built executable on current platform."""
    if sys.platform == "win32":
        os.startfile(str(exe_path))  # type: ignore[attr-defined]
    elif sys.platform == "darwin":
        subprocess.Popen(["open", str(exe_path)])
    else:
        subprocess.Popen([str(exe_path)])


def build_executable():
    """Build standalone executable using PyInstaller spec file."""
    print("\nWriting Studio Analytics - EXE Build (V2)")

    spec_file = Path("WritingStudioAnalytics.spec")
    if not spec_file.exists():
        print(f"[FAIL] Spec file not found: {spec_file}")
        return False

    # Validate key runtime files used by the spec.
    required_paths = [
        Path("src/dashboard/main.py"),
        Path("src"),
        Path("courses.csv"),
    ]
    for path in required_paths:
        if not path.exists():
            print(f"[FAIL] Required path missing: {path}")
            return False

    # models/ is optional, but we warn because AI chat depends on it.
    if not Path("models").exists():
        print("[WARN] models/ folder not found. AI Chat may not work until model is added.")

    # Ensure PyInstaller exists.
    try:
        import PyInstaller  # noqa: F401
    except ImportError:
        install_cmd = [sys.executable, "-m", "pip", "install", "pyinstaller>=6.0.0"]
        if not run_command(install_cmd, "Installing PyInstaller"):
            return False

    pyinstaller_cmd = [
        sys.executable,
        "-m",
        "PyInstaller",
        "--clean",
        "--noconfirm",
        str(spec_file),
    ]

    if not run_command(pyinstaller_cmd, "Building executable from spec"):
        return False

    exe_path = detect_output_path(Path("dist"))
    if not exe_path.exists():
        print(f"[FAIL] Expected executable not found: {exe_path}")
        return False

    exe_size_mb = exe_path.stat().st_size / (1024 * 1024)
    print(f"\n[OK] Build successful: {exe_path}")
    print(f"Size: {exe_size_mb:.2f} MB")

    should_launch = input("Launch executable now? (y/n): ").strip().lower() == "y"
    if should_launch:
        try:
            launch_executable(exe_path)
            print(f"[OK] Launched: {exe_path}")
        except Exception as exc:
            print(f"[WARN] Could not launch automatically: {exc}")
            print(f"Run manually: {exe_path}")

    return True


def main():
    """Main entry point."""
    try:
        success = build_executable()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\nBuild cancelled by user")
        sys.exit(1)
    except Exception as exc:
        print(f"\nUnexpected error: {exc}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
