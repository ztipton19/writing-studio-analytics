# PyQt Dashboard - Packaging Guide

## Overview

This guide explains how to package the Writing Studio Analytics PyQt dashboard into a standalone executable that can be distributed to your supervisor without requiring Python installation.

## Quick Start

### Option 1: Automated Build (Recommended)

Run the automated build script:

```bash
python build_executable.py
```

This script will:
1. Check for PyInstaller (install if missing)
2. Verify all required files exist
3. Build the executable
4. Offer to test it immediately

### Option 2: Manual Build

```bash
# Install PyInstaller
pip install pyinstaller>=6.0.0

# Build executable
pyinstaller --onefile --windowed \
  --name=WritingStudioAnalytics \
  src/dashboard/main.py \
  --add-data "src:src" \
  --add-data "courses.csv:." \
  --add-data "models:models" \
  --hidden-import matplotlib.backends.backend_qt5agg \
  --hidden-import PyQt5.QtGui \
  --hidden-import PyQt5.QtCore \
  --hidden-import PyQt5.QtWidgets \
  --hidden-import llama_cpp \
  --hidden-import cryptography \
  --clean \
  --noconfirm
```

## What Gets Bundled

The executable includes:

| Component | Size | Description |
|---|---|---|
| Python Runtime | ~50 MB | Embedded Python interpreter |
| PyQt5 | ~60 MB | GUI framework |
| Matplotlib | ~40 MB | Charting library |
| pandas/numpy | ~50 MB | Data processing |
| AI Model (optional) | ~2.3 GB | Gemma 3 4B model |
| Source Code | ~1 MB | Your application code |
| **Total** | **~200-2500 MB** | Depends on AI model |

### Size Reduction Options

**Without AI Model (Recommended for v1.0):**
- Size: ~200 MB
- AI Chat tab shows download instructions
- User can install model later if needed

**With AI Model:**
- Size: ~2.3 GB
- AI Chat works immediately
- Longer download for recipients

## Building Without AI Model

If you want a smaller executable for initial distribution:

1. **Remove model from build:**
   Edit `build_executable.py` or remove the `--add-data "models:models"` flag

2. **AI Chat behavior:**
   - Tab still appears
   - Shows helpful download instructions
   - User can install model via terminal command

## Platform-Specific Builds

### Windows

```bash
python build_executable.py
```

Output: `dist/WritingStudioAnalytics.exe` (~200 MB)

### macOS

```bash
python build_executable.py
```

Output: `dist/WritingStudioAnalytics` (~200 MB)

**For Apple Silicon (M1/M2/M3):**

The build script automatically detects and uses Metal acceleration if available.

### Linux

```bash
python build_executable.py
```

Output: `dist/WritingStudioAnalytics` (~200 MB)

## Testing the Executable

### Before Distribution

1. **Test on your machine:**
   ```bash
   # Windows
   dist\WritingStudioAnalytics.exe
   
   # macOS
   open dist/WritingStudioAnalytics
   
   # Linux
   ./dist/WritingStudioAnalytics
   ```

2. **Test with sample data:**
   - Load a Penji export (CSV or Excel)
   - Verify all tabs render charts
   - Test PDF export
   - Test codebook lookup
   - Test AI Chat (if model included)

3. **Common issues to check:**
   - Charts display correctly
   - PDF exports work
   - File dialogs work
   - Status bar updates
   - No console errors

### Testing on Target Machine

**Minimum Requirements:**
- Windows 10+, macOS 10.13+, or Linux (glibc 2.17+)
- 4 GB RAM (8 GB recommended)
- 200 MB free disk space (2.5 GB if AI model included)

**Dependencies:**
- None! The executable is self-contained

## Distribution

### Internal Distribution (Within University)

1. **Network share:** Copy to shared drive
2. **USB drive:** Direct file copy
3. **Email:** Upload to cloud service and share link

### External Distribution

For sharing outside the university:

1. **Cloud storage:**
   - Google Drive, Dropbox, OneDrive
   - Share download link

2. **File transfer:**
   - WeTransfer (up to 2 GB free)
   - SendGB (up to 5 GB free)

3. **For large files (with AI model):**
   - Split into multiple zip files
   - Provide extraction instructions

## Known Issues and Solutions

### Issue: "Application failed to start"

**Cause:** Missing system libraries or incompatible OS

**Solutions:**
- Verify target OS is supported (Win10+, macOS 10.13+, or modern Linux)
- Check if antivirus is blocking execution
- Try running as administrator (Windows) or with sudo (Linux/macOS)

### Issue: "Charts don't display"

**Cause:** Matplotlib backend issue

**Solution:**
- Rebuild with `matplotlib.use('Qt5Agg')` at the top of main.py (already done in current code)

### Issue: "AI Chat shows model not found"

**Cause:** AI model not bundled or user needs to install

**Solution:**
- **If you bundled model:** Verify `models/` directory exists in executable
- **If you didn't bundle model:** User needs to run:
  ```bash
  python src/ai_chat/setup_model.py
  ```
  (Requires Python installation)

### Issue: "Executable is too slow"

**Cause:** First-run unpacking overhead

**Solution:**
- First launch takes 10-30 seconds (unpacking embedded files)
- Subsequent launches are fast
- This is normal for PyInstaller `--onefile` mode

### Issue: "PDF export fails"

**Cause:** Missing fonts or permissions

**Solutions:**
- Verify user has write permissions in current directory
- Check if reportlab can find system fonts
- Try running from a different directory

## Security Considerations

### Codebook Passwords

The codebook lookup dialog is included in the executable. Remind users:

- ⚠️ **Never share codebook files via email**
- ⚠️ **Never share codebook passwords via unencrypted channels**
- ✅ **Codebook passwords are required (12+ characters)**

### Data Privacy

The executable:
- ✅ Anonymizes all PII before analysis
- ✅ Never connects to external servers
- ✅ Runs entirely on user's machine
- ✅ Stores all data locally

### Distribution Security

- ✅ Executable is self-contained (no network dependencies)
- ✅ No telemetry or analytics collection
- ✅ Can be distributed via secure channels

## Versioning and Updates

### Version Number

Current version: `2.0 (PyQt Edition)`

Update in `src/dashboard/main.py`:

```python
def show_about(self):
    """Show about dialog."""
    about_text = """
    <h3>Writing Studio Analytics</h3>
    <p>Version 2.0.1 (PyQt Edition)</p>  # Update here
    ...
```

### Updating Recipients

When releasing updates:

1. Increment version number
2. Rebuild executable
3. Distribute with clear version identifier
4. Provide changelog

### Rollback Strategy

Keep previous versions in case of issues:

```
dist/
  WritingStudioAnalytics_v2.0.0.exe
  WritingStudioAnalytics_v2.0.1.exe  # Current
```

## Troubleshooting Build Errors

### PyInstaller: "module not found"

**Cause:** Missing hidden import

**Solution:** Add to build command:
```bash
--hidden-import module_name
```

### PyInstaller: "file not found"

**Cause:** Data file not included

**Solution:** Add to build command:
```bash
--add-data "path/to/file:destination"
```

### PyInstaller: "RecursionError"

**Cause:** Circular import or too many imports

**Solution:**
- Exclude problematic modules: `--exclude-module module_name`
- Or use `--onedir` instead of `--onefile`

### Build hangs during analysis

**Cause:** Analyzing too many modules

**Solution:** Exclude unnecessary modules:
```bash
--exclude-module streamlit  # Only used in web version
--exclude-module tornado    # Only used in web version
```

## Advanced Options

### Custom Icon

Add application icon:

```bash
pyinstaller --icon=assets/icon.ico ...  # Windows
pyinstaller --icon=assets/icon.icns ... # macOS
```

### Splash Screen

Add splash screen for faster perceived startup:

```bash
--splash assets/splash.png
```

### Code Signing (macOS)

For distribution outside the university:

```bash
codesign --sign "Developer ID" dist/WritingStudioAnalytics
```

## Support and Documentation

### User Documentation

Create a simple README for recipients:

```markdown
# Writing Studio Analytics - Quick Start

## Installation
1. Download WritingStudioAnalytics.exe
2. Double-click to run (no installation required)

## Usage
1. Click "Open File"
2. Select your Penji export (CSV or Excel)
3. View charts in tabs
4. Export PDF report when ready

## AI Chat
- AI Chat requires ~2.3 GB model download
- Click AI Chat tab and follow instructions
- Optional - analytics work without it

## Support
Contact: your.email@university.edu
```

### Technical Support

For build issues:

1. Check PyInstaller logs in `build/` directory
2. Review `PyQt_GUIDe.md` for implementation details
3. Consult PyInstaller documentation: https://pyinstaller.org/

## Summary

**Build Command:**
```bash
python build_executable.py
```

**Output:** `dist/WritingStudioAnalytics.exe` or `WritingStudioAnalytics` (macOS/Linux)

**Ready to distribute:** ✅ No installation required
**Size:** ~200 MB (without AI model) or ~2.3 GB (with AI model)
**Compatibility:** Windows 10+, macOS 10.13+, modern Linux

Your supervisor can simply double-click the executable and start analyzing Writing Studio data!