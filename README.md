# Writing Studio Analytics (V2 Desktop)

Privacy-first analytics for Penji exports, built for University of Arkansas Writing Studio.

## Runtime

V2 is the desktop app (PyQt). The old Streamlit runtime has been removed from this branch.

## Quick Start

```bash
pip install -r requirements.txt
python src/dashboard/main.py
```

## Build EXE

```bash
python build_executable.py
```

This builds from `WritingStudioAnalytics.spec` and outputs:
- `dist/WritingStudioAnalytics.exe` (Windows)
- `dist/WritingStudioAnalytics` (macOS/Linux)

## Core Features

- Scheduled + walk-in session analytics
- FERPA-oriented anonymization
- Optional encrypted codebook for supervisor lookup
- PDF report export
- Local AI chat (no external API calls)

## Security Notes

- Codebooks use PBKDF2 + Fernet encryption
- Each codebook now uses a random per-file salt (with legacy decrypt support)
- AI chat runs locally; no cloud inference

## Project Entry Points

- Desktop UI: `src/dashboard/main.py`
- EXE build script: `build_executable.py`
- PyInstaller spec: `WritingStudioAnalytics.spec`

## Troubleshooting

- If AI chat model is missing, use setup instructions in `docs/ai-chat-setup-guide.md`.
- If packaging fails, use `docs/PYQT_PACKAGING_GUIDE.md` and `docs/PACKAGING_QUICKSTART.md`.

## Handoff and Release

**Status:** Production ready for supervisor handoff

- **Final handoff checklist:** `docs/FINAL_HANDOFF_CHECKLIST.md` ⭐
- Canonical supervisor handoff: `docs/SUPERVISOR_HANDOFF_V2.md`
- Release smoke test checklist: `docs/RELEASE_SMOKE_TEST_CHECKLIST.md`
- Smoke test script: `scripts/release_smoke_test.py`
- Pre-release gate script: `scripts/pre_release_gate.py`
- Pinned release dependencies: `requirements-release.txt`

### Quick Verification
```bash
python -m pytest tests/ -v              # Run all tests (expect 9/9 passing)
python build_executable.py              # Build standalone EXE
```

## License

MIT. See `LICENSE`.
