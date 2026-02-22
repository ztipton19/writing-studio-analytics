# USB Transfer Instructions

This document walks you through transferring the Writing Studio Analytics project to a USB drive for your supervisor.

## Prerequisites

- **USB Drive**: Minimum 8GB free space, recommended 16GB+ capacity (full package is ~6.6GB)
- **Windows computer** for the transfer
- **Internet connection** (only needed for initial portable Python setup if using that option)

---

## Step 1: Verify the Build

Before transferring, verify everything works:

```powershell
# Run tests
python -m pytest tests/ -v

# Check executable exists
dir dist\WritingStudioAnalytics.exe
```

**Expected Results:**
- All 9 tests pass
- Executable is ~3.45GB (3,450,787,388 bytes)

---

## Step 2: Create USB Package Structure

On your USB drive, create this folder structure:

```
USB_DRIVE:/
├── WritingStudioAnalytics/
│   ├── START_PROGRAM.bat              ← Main launcher
│   ├── WritingStudioAnalytics.exe     ← Compiled application
│   ├── README_FIRST.txt               ← Instructions for supervisor
│   │
│   ├── setup_portable_python.bat      ← Python setup (backup option)
│   ├── INSTALL_DEPENDENCIES.bat       ← Dependency installer
│   ├── RUN_WITH_PYTHON.bat            ← Python launcher
│   │
│   ├── courses.csv                    ← Sample course data
│   │
│   ├── models/
│   │   └── gemma-3-4b-it-q4_0.gguf   ← AI model file
│   │
│   ├── SOURCE_CODE/                   ← Full source code
│   │   ├── src/
│   │   ├── docs/
│   │   ├── tests/
│   │   ├── requirements-release.txt
│   │   └── ...
│   │
│   └── docs/                          ← Documentation
│       ├── SUPERVISOR_HANDOFF_V2.md
│       ├── FINAL_HANDOFF_CHECKLIST.md
│       └── ...
```

---

## Step 3: Copy Files to USB

### Option A: Manual Copy (Recommended)

1. **Create the main folder** on USB:
   ```
   X:\WritingStudioAnalytics\
   ```

2. **Copy these files from project root:**
   - `START_PROGRAM.bat`
   - `README_FIRST.txt`
   - `setup_portable_python.bat`
   - `INSTALL_DEPENDENCIES.bat`
   - `RUN_WITH_PYTHON.bat`
   - `courses.csv`
   - `requirements-release.txt`

3. **Copy the executable:**
   - From: `dist\WritingStudioAnalytics.exe`
   - To: `X:\WritingStudioAnalytics\WritingStudioAnalytics.exe`

4. **Copy the models folder:**
   - From: `models\`
   - To: `X:\WritingStudioAnalytics\models\`
   - **CRITICAL**: Must include `gemma-3-4b-it-q4_0.gguf`

5. **Copy source code** (for backup/development):
   - Create: `X:\WritingStudioAnalytics\SOURCE_CODE\`
   - Copy: `src\`, `docs\`, `tests\`, `requirements-release.txt`

6. **Copy documentation:**
   - From: `docs\`
   - To: `X:\WritingStudioAnalytics\docs\`

### Option B: Use a Copy Script

Create and run this PowerShell script:

```powershell
# set USB drive letter
$USB = "E:"  # Change to your USB drive letter

# Create destination
$DEST = "$USB\WritingStudioAnalytics"
New-Item -ItemType Directory -Force -Path $DEST

# Copy root files
Copy-Item "START_PROGRAM.bat" $DEST
Copy-Item "README_FIRST.txt" $DEST
Copy-Item "setup_portable_python.bat" $DEST
Copy-Item "INSTALL_DEPENDENCIES.bat" $DEST
Copy-Item "RUN_WITH_PYTHON.bat" $DEST
Copy-Item "courses.csv" $DEST
Copy-Item "requirements-release.txt" $DEST

# Copy executable
Copy-Item "dist\WritingStudioAnalytics.exe" $DEST

# Copy models
Copy-Item -Recurse -Force "models" $DEST

# Copy source code
$SRC_DEST = "$DEST\SOURCE_CODE"
New-Item -ItemType Directory -Force -Path $SRC_DEST
Copy-Item -Recurse -Force "src" $SRC_DEST
Copy-Item -Recurse -Force "docs" $SRC_DEST
Copy-Item -Recurse -Force "tests" $SRC_DEST
Copy-Item "requirements-release.txt" $SRC_DEST
Copy-Item "pytest.ini" $SRC_DEST

# Copy docs to root as well
Copy-Item -Recurse -Force "docs" $DEST

Write-Host "Copy complete!"
```

---

## Step 4: Verify USB Package

Before handing off, verify:

1. **File check** - Ensure these exist:
   - [ ] `START_PROGRAM.bat`
   - [ ] `WritingStudioAnalytics.exe` (~3.45GB)
   - [ ] `README_FIRST.txt`
   - [ ] `models/gemma-3-4b-it-q4_0.gguf`
   - [ ] `SOURCE_CODE/src/dashboard/main.py`

2. **Test run** - On a different computer (if possible):
   - Double-click `START_PROGRAM.bat`
   - Verify application launches
   - Check AI Chat tab loads model

---

## Step 5: Handoff to Supervisor

1. **Explain the basics:**
   - "Double-click START_PROGRAM.bat to run"
   - "First launch takes 10-30 seconds"
   - "Keep the black window open while using the app"

2. **Point them to README_FIRST.txt** for:
   - Troubleshooting
   - System requirements
   - Alternative Python method

3. **Mention the backup option:**
   - If executable fails, use the Python scripts
   - `setup_portable_python.bat` → `INSTALL_DEPENDENCIES.bat` → `RUN_WITH_PYTHON.bat`

---

## Important Notes

### What's NOT Included on USB
- `.git/` folder (version control)
- `__pycache__/` folders
- `build/` folder (temporary build files)
- `*.pyc` files
- Virtual environments

### What IS Included
- Compiled executable (all dependencies bundled)
- AI model for chat feature
- Full source code for future development
- All documentation

### Size Breakdown
| Component | Size |
|-----------|------|
| Executable | ~3.45GB |
| AI Model (`models/gemma-3-4b-it-q4_0.gguf`) | ~3.16GB (stored separately) |
| Source Code + Tests + Docs + Scripts | ~0.01GB |
| **Total package (typical)** | **~6.6GB** |

---

## Troubleshooting Transfer Issues

### "File too large" error
- USB drive might be FAT32 (4GB file limit)
- Solution: Format USB as NTFS or exFAT

### Slow copy speed
- Large file transfer (~6.6GB package, with two very large files)
- Expected: 5-15 minutes via USB 3.0
- Longer via USB 2.0

### Executable won't run on target computer
- Try the Python method instead
- Run `setup_portable_python.bat` first

---

## Final Checklist

Before handing off the USB:

- [ ] All files copied to USB
- [ ] Executable is ~3.45GB
- [ ] AI model file exists in models/ folder
- [ ] Full package is about ~6.6GB total
- [ ] START_PROGRAM.bat tested and works
- [ ] README_FIRST.txt is present
- [ ] Source code backup included
- [ ] Documentation included
- [ ] Supervisor knows to read README_FIRST.txt

---

**You're done!** The USB package is self-contained and ready for handoff.
