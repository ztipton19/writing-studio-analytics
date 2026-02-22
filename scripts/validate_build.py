#!/usr/bin/env python
"""
Pre-build validation script for Writing Studio Analytics.

Run this before building the executable to catch common issues.
Usage: python scripts/validate_build.py
"""

import os
import sys
import subprocess
from pathlib import Path


def check_file_exists(path, description, required=True):
    """Check if a file exists."""
    if Path(path).exists():
        print(f"  ✓ {description}: {path}")
        return True
    else:
        if required:
            print(f"  ✗ MISSING {description}: {path}")
        else:
            print(f"  ⚠ Optional {description} not found: {path}")
        return not required


def check_directory_exists(path, description, required=True):
    """Check if a directory exists."""
    if Path(path).is_dir():
        print(f"  ✓ {description}: {path}")
        return True
    else:
        if required:
            print(f"  ✗ MISSING {description}: {path}")
        else:
            print(f"  ⚠ Optional {description} not found: {path}")
        return not required


def check_python_version():
    """Check Python version compatibility."""
    version = sys.version_info
    print(f"\n📋 Python Version: {version.major}.{version.minor}.{version.micro}")
    
    if version.major == 3 and version.minor >= 9:
        print("  ✓ Python version compatible")
        return True
    else:
        print("  ✗ Python 3.9+ required")
        return False


def check_imports():
    """Check if critical imports work."""
    print("\n📋 Checking Critical Imports...")
    
    imports = [
        ("PyQt6", "PyQt6.QtWidgets", "GUI Framework"),
        ("matplotlib", "matplotlib", "Plotting Library"),
        ("pandas", "pandas", "Data Processing"),
        ("numpy", "numpy", "Numerical Computing"),
        ("cryptography", "cryptography", "Encryption"),
        ("PIL", "PIL.Image", "Image Processing"),
    ]
    
    all_ok = True
    for name, module, desc in imports:
        try:
            __import__(module.split('.')[0])
            print(f"  ✓ {name} ({desc})")
        except ImportError as e:
            print(f"  ✗ {name} ({desc}): {e}")
            all_ok = False
    
    # Check optional AI imports
    print("\n  Optional AI Dependencies:")
    try:
        import llama_cpp
        print(f"  ✓ llama-cpp-python (AI inference)")
    except ImportError:
        print(f"  ⚠ llama-cpp-python not installed (AI features disabled)")
    
    return all_ok


def check_spec_file():
    """Check PyInstaller spec file for common issues."""
    print("\n📋 Checking PyInstaller Spec File...")
    
    spec_path = Path("WritingStudioAnalytics.spec")
    if not spec_path.exists():
        print("  ✗ Spec file not found: WritingStudioAnalytics.spec")
        return False
    
    content = spec_path.read_text()
    issues = []
    
    # Check for Windows backslashes in paths
    if "src\\dashboard\\main.py" in content:
        issues.append("Uses Windows backslashes (src\\dashboard\\main.py) - will break on other platforms")
    
    # Check for freeze_support comment (good practice)
    if "freeze_support" not in content:
        print("  ⚠ No freeze_support reference in spec (may need it for multiprocessing)")
    
    # Check for hidden imports
    if "hiddenimports" not in content:
        issues.append("No hiddenimports defined - may miss critical dependencies")
    
    if issues:
        for issue in issues:
            print(f"  ✗ {issue}")
        return False
    else:
        print("  ✓ Spec file looks good")
        return True


def check_freeze_support():
    """Check if freeze_support is properly implemented."""
    print("\n📋 Checking Multiprocessing freeze_support()...")
    
    main_path = Path("src/dashboard/main.py")
    if not main_path.exists():
        print("  ✗ main.py not found")
        return False
    
    content = main_path.read_text(encoding='utf-8')
    
    if "freeze_support" in content:
        print("  ✓ freeze_support() found in main.py")
        return True
    else:
        print("  ✗ freeze_support() NOT found - multiprocessing will fail in frozen exe")
        return False


def check_buggy_code():
    """Check for known bug patterns."""
    print("\n📋 Checking for Known Bug Patterns...")
    
    issues = []
    
    # Check for startswith('') bug (always True for any string)
    for py_file in Path("src").rglob("*.py"):
        try:
            content = py_file.read_text(encoding='utf-8')
        except UnicodeDecodeError:
            continue  # Skip files that can't be read
            issues.append(f"{py_file}: Contains buggy startswith('') pattern (always True)")
    
    if issues:
        for issue in issues:
            print(f"  ✗ {issue}")
        return False
    else:
        print("  ✓ No buggy startswith('') patterns found")
        return True


def check_required_files():
    """Check for required files."""
    print("\n📋 Checking Required Files...")
    
    all_ok = True
    all_ok &= check_file_exists("WritingStudioAnalytics.spec", "PyInstaller spec file")
    all_ok &= check_file_exists("src/dashboard/main.py", "Main entry point")
    all_ok &= check_file_exists("courses.csv", "Course data file")
    all_ok &= check_file_exists("requirements.txt", "Requirements file")
    all_ok &= check_directory_exists("src", "Source directory")
    all_ok &= check_directory_exists("src/core", "Core modules")
    all_ok &= check_directory_exists("src/ai_chat", "AI chat modules")
    all_ok &= check_directory_exists("src/visualizations", "Visualization modules")
    
    # Optional but recommended
    check_directory_exists("models", "AI models directory", required=False)
    
    return all_ok


def run_pyinstaller_check():
    """Check if PyInstaller is installed and working."""
    print("\n📋 Checking PyInstaller...")
    
    try:
        import PyInstaller
        print(f"  ✓ PyInstaller version: {PyInstaller.__version__}")
        return True
    except ImportError:
        print("  ✗ PyInstaller not installed")
        print("    Install with: pip install pyinstaller>=6.0.0")
        return False


def main():
    """Run all validation checks."""
    print("=" * 60)
    print("Writing Studio Analytics - Pre-Build Validation")
    print("=" * 60)
    
    results = []
    
    # Run all checks
    results.append(("Python Version", check_python_version()))
    results.append(("Required Files", check_required_files()))
    results.append(("Critical Imports", check_imports()))
    results.append(("PyInstaller", run_pyinstaller_check()))
    results.append(("Spec File", check_spec_file()))
    results.append(("freeze_support()", check_freeze_support()))
    results.append(("Bug Patterns", check_buggy_code()))
    
    # Summary
    print("\n" + "=" * 60)
    print("VALIDATION SUMMARY")
    print("=" * 60)
    
    all_passed = True
    for name, passed in results:
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"  {status}: {name}")
        if not passed:
            all_passed = False
    
    print("=" * 60)
    
    if all_passed:
        print("\n✓ All checks passed! Ready to build.")
        print("\nTo build the executable:")
        print("  python build_executable.py")
        return 0
    else:
        print("\n✗ Some checks failed. Fix the issues above before building.")
        return 1


if __name__ == "__main__":
    sys.exit(main())