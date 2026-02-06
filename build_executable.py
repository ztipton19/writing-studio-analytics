#!/usr/bin/env python
"""
Build script for creating standalone executable using PyInstaller.

This script bundles the Writing Studio Analytics PyQt application into a single
executable that can be run on any machine without installing dependencies.

Usage:
    python build_executable.py
"""

import subprocess
import sys
import os
from pathlib import Path


def run_command(cmd, description):
    """Run a command and display progress."""
    print(f"\n{'='*60}")
    print(f"{description}")
    print(f"{'='*60}")
    print(f"Running: {' '.join(cmd)}\n")
    
    try:
        result = subprocess.run(cmd, check=True, capture_output=False, text=True)
        print(f"\n✅ {description} - SUCCESS")
        return True
    except subprocess.CalledProcessError as e:
        print(f"\n❌ {description} - FAILED")
        print(f"Error: {e}")
        return False


def build_executable():
    """Build standalone executable using PyInstaller."""
    
    print("""
╔════════════════════════════════════════════════════════════╗
║  Writing Studio Analytics - PyInstaller Packaging Script       ║
╚════════════════════════════════════════════════════════════╝
""")
    
    # Check if PyInstaller is installed
    try:
        import PyInstaller
        print(f"✅ PyInstaller found: {PyInstaller.__version__}")
    except ImportError:
        print("❌ PyInstaller not installed!")
        print("\nInstalling PyInstaller...")
        cmd = [sys.executable, "-m", "pip", "install", "pyinstaller>=6.0.0"]
        if not run_command(cmd, "Installing PyInstaller"):
            return False
    
    # Verify main entry point exists
    main_script = Path("src/dashboard/main.py")
    if not main_script.exists():
        print(f"❌ Main script not found: {main_script}")
        return False
    print(f"✅ Main script found: {main_script}")
    
    # Verify required directories exist
    required_dirs = {
        "src/": "Source code",
        "models/": "AI model directory",
    }
    
    for dir_path, description in required_dirs.items():
        if not Path(dir_path).exists():
            print(f"⚠️  Warning: {description} directory not found: {dir_path}")
        else:
            print(f"✅ {description} found: {dir_path}")
    
    # Check for courses.csv
    if Path("courses.csv").exists():
        print(f"✅ courses.csv found")
    else:
        print(f"⚠️  Warning: courses.csv not found")
    
    # Build PyInstaller command
    pyinstaller_cmd = [
        "pyinstaller",
        "--onefile",                          # Single executable file
        "--windowed",                         # No console window
        "--name=WritingStudioAnalytics",        # Output executable name
        f"{main_script}",                      # Main script
        f"--add-data=src:src",               # Bundle source code
        f"--add-data=courses.csv:.",           # Bundle course reference
        f"--add-data=models:models",           # Bundle AI models
        "--collect-all=PyQt6",                # Bundle all PyQt6 files (plugins, DLLs, etc.)
        "--collect-binaries=PyQt6",           # Collect PyQt6 binaries
        "--collect-data=PyQt6",               # Collect PyQt6 data files
        "--hidden-import=PyQt6.QtGui",
        "--hidden-import=PyQt6.QtCore",
        "--hidden-import=PyQt6.QtWidgets",
        "--hidden-import=matplotlib.backends.backend_qtagg",
        "--hidden-import=llama_cpp",
        "--hidden-import=cryptography",
        "--hidden-import=pandas",
        "--hidden-import=numpy",
        "--hidden-import=scipy",
        "--hidden-import=seaborn",
        "--clean",                             # Clean build cache
        "--noconfirm",                         # Don't ask for confirmation
    ]
    
    print(f"\n{'='*60}")
    print("Building Executable")
    print(f"{'='*60}")
    print(f"Target: WritingStudioAnalytics.exe (Windows) or .app (macOS)")
    print(f"Mode: Single file, windowed (no console)")
    print(f"Bundling:")
    print(f"  • Source code (src/)")
    print(f"  • Course reference (courses.csv)")
    print(f"  • AI models (models/)")
    print()
    
    # Run PyInstaller
    if not run_command(pyinstaller_cmd, "Building executable with PyInstaller"):
        print("\n❌ Build failed!")
        return False
    
    # Check if executable was created
    dist_dir = Path("dist")
    if sys.platform == "darwin":  # macOS
        exe_name = "WritingStudioAnalytics"
    elif sys.platform == "win32":  # Windows
        exe_name = "WritingStudioAnalytics.exe"
    else:  # Linux
        exe_name = "WritingStudioAnalytics"
    
    exe_path = dist_dir / exe_name
    
    if exe_path.exists():
        exe_size_mb = exe_path.stat().st_size / (1024 * 1024)
        print(f"\n{'='*60}")
        print("✅ Build Successful!")
        print(f"{'='*60}")
        print(f"\nExecutable created: {exe_path}")
        print(f"File size: {exe_size_mb:.2f} MB")
        print()
        print("Next steps:")
        print("1. Test the executable with sample data")
        print("2. Copy to target machine(s)")
        print("3. No installation required - just run!")
        print()
        
        # Optional: Prompt to test immediately
        if input("Test executable now? (y/n): ").lower() == 'y':
            test_cmd = [str(exe_path)] if sys.platform == "darwin" else ["start", str(exe_path)]
            try:
                subprocess.Popen(test_cmd)
                print(f"\n🚀 Launched: {exe_path}")
            except Exception as e:
                print(f"\n⚠️  Could not launch: {e}")
                print(f"Run manually: {exe_path}")
        
        return True
    else:
        print(f"\n❌ Executable not found: {exe_path}")
        print("Check the PyInstaller output above for errors.")
        return False


def main():
    """Main entry point."""
    try:
        success = build_executable()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n⚠️  Build cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()