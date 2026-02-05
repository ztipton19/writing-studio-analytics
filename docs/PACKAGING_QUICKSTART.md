# Quick Start: Building the Executable

## Build Now (One Command)

```bash
python build_executable.py
```

That's it! The script handles everything.

## What Happens

1. **Checks dependencies** - Installs PyInstaller if needed
2. **Verifies files** - Confirms src/, models/, courses.csv exist
3. **Builds executable** - Creates `dist/WritingStudioAnalytics`
4. **Offers to test** - Asks if you want to run it immediately

## Output

- **File:** `dist/WritingStudioAnalytics` (macOS/Linux) or `dist/WritingStudioAnalytics.exe` (Windows)
- **Size:** ~200 MB (without AI model) or ~2.3 GB (with AI model)
- **Dependencies:** None - completely standalone!

## Testing the Build

```bash
# macOS
open dist/WritingStudioAnalytics

# Windows
dist\WritingStudioAnalytics.exe

# Linux
./dist/WritingStudioAnalytics
```

## Distribution

Just copy the executable to your supervisor's computer:
- Via USB drive
- Via network share
- Via cloud storage (Google Drive, Dropbox, etc.)

**No installation required** - just double-click and run!

## Common Questions

**Q: Can I build without the AI model?**  
A: Yes! Remove `--add-data "models:models"` from build_executable.py. The AI Chat tab will show download instructions instead.

**Q: How big is the executable?**  
A: ~200 MB without AI model, ~2.3 GB with model bundled.

**Q: What platform does it run on?**  
A: Build on each platform separately (Windows, macOS, Linux). Cross-platform builds don't work well.

**Q: First launch is slow - why?**  
A: Normal! First launch unpacks embedded files (~10-30 seconds). Subsequent launches are fast.

**Q: Can I update the executable later?**  
A: Yes - just rebuild and redistribute. Keep version numbers clear.

## Full Documentation

See `docs/PYQT_PACKAGING_GUIDE.md` for complete details including:
- Advanced build options
- Custom icons
- Troubleshooting
- Security considerations
- Versioning strategy