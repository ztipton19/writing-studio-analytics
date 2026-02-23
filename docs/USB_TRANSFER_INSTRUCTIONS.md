# USB Transfer Instructions (Python/Source Mode)

This guide is for transferring Writing Studio Analytics to USB without using the EXE.

## Prerequisites

- USB drive with at least 5GB free (8GB+ capacity recommended)
- Windows computer for transfer
- Internet connection on first launch machine (for Python + pip packages)

## Step 1: Verify Project Before Copy

Run from project root:

```powershell
# Run tests
python -m pytest tests/ -v

# Verify source entry point exists
dir src\dashboard\main.py
```

Expected:
- 9 tests pass
- `src\dashboard\main.py` exists

## Step 2: Copy Files to USB

### Option A: Use the existing copy script

```powershell
powershell -ExecutionPolicy Bypass -File COPY_TO_USB.ps1
```

This copies all required Python/source-mode files to:
`X:\WritingStudioAnalytics\`

### Option B: Manual copy

Copy these files/folders into `X:\WritingStudioAnalytics\`:

- `START_PROGRAM.bat`
- `README_FIRST.txt`
- `setup_portable_python.bat`
- `INSTALL_DEPENDENCIES.bat`
- `RUN_WITH_PYTHON.bat`
- `requirements-release.txt`
- `courses.csv` (if used)
- `models\` (must include `gemma-3-4b-it-q4_0.gguf`)
- `docs\`
- `SOURCE_CODE\src\`
- `SOURCE_CODE\tests\`
- `SOURCE_CODE\docs\`
- `SOURCE_CODE\requirements-release.txt`
- `SOURCE_CODE\pytest.ini`

## Step 3: Verify USB Package

Before handoff, confirm:

- `START_PROGRAM.bat` exists
- `RUN_WITH_PYTHON.bat` exists
- `setup_portable_python.bat` exists
- `INSTALL_DEPENDENCIES.bat` exists
- `models\gemma-3-4b-it-q4_0.gguf` exists
- `SOURCE_CODE\src\dashboard\main.py` exists

Typical package size (without EXE): about 3.2GB to 3.5GB.

## Step 4: Supervisor Handoff

Tell supervisor:

1. Open `WritingStudioAnalytics` on the USB.
2. Read `README_FIRST.txt`.
3. Double-click `START_PROGRAM.bat`.
4. Keep the terminal window open while using the app.

First run will:
- Download portable Python
- Install dependencies
- Launch the app

Later runs should be much faster.

## Troubleshooting

### "File too large" while copying
- USB likely FAT32 (4GB file limit)
- Reformat USB as NTFS or exFAT

### First launch takes too long
- Normal on first run due to package installs
- Prefer stable internet for first setup

### App fails to start after setup
- Re-run:
  1) `setup_portable_python.bat`
  2) `INSTALL_DEPENDENCIES.bat`
  3) `RUN_WITH_PYTHON.bat`

### AI Chat model missing
- Ensure `models\gemma-3-4b-it-q4_0.gguf` is present

## Final Checklist

- [ ] USB has full `WritingStudioAnalytics` folder
- [ ] `START_PROGRAM.bat` tested from USB
- [ ] `README_FIRST.txt` present
- [ ] `models` folder present
- [ ] `SOURCE_CODE` backup present

