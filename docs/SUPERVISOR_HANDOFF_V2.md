# Supervisor Handoff (V2 Desktop)

This is the canonical handoff guide for the EXE-based V2 release.

## Scope

- Runtime: PyQt desktop app (`src/dashboard/main.py`)
- Build: PyInstaller spec (`WritingStudioAnalytics.spec`)
- Packaging script: `build_executable.py`
- Local AI only (no cloud API calls)

## Pre-Release Checklist (Owner)

1. Generate pinned dependencies:
   - `python scripts/freeze_release_requirements.py`
   - Confirm `requirements-release.txt` exists and is committed.
2. Run smoke tests with real sample files:
   - `python scripts/release_smoke_test.py --scheduled-file <scheduled_export.xlsx> --walkin-file <walkin_export.xlsx>`
   - Optional AI checks: add `--run-ai`.
   - Or run all checks together: `python scripts/pre_release_gate.py --scheduled-file <scheduled_export.xlsx> --walkin-file <walkin_export.xlsx> --run-ai`
3. Build the executable:
   - `python build_executable.py`
4. Verify output exists:
   - Windows: `dist/WritingStudioAnalytics.exe`
   - macOS/Linux: `dist/WritingStudioAnalytics`

## Supervisor Runbook

1. Launch executable.
2. Open Penji export file (CSV/XLSX).
3. Confirm detected mode is correct (scheduled vs walk-in).
4. Process data and export PDF report.
5. If codebook is enabled:
   - Store `.enc` file in secure folder.
   - Store password separately from codebook file.
6. Use AI Chat for aggregated questions only.

## AI Chat Notes

- Model is local and versioned by file in `models/`.
- If model is missing, AI tab will not answer until model is added.
- Recommended maintenance: re-evaluate model currency every semester.

## Security Posture

- Codebook encryption uses PBKDF2 + Fernet.
- New codebooks use per-file random salt.
- Legacy codebooks remain decryptable.
- AI code execution is constrained by AST validation and restricted execution context.

## Recovery / Troubleshooting

1. Build fails:
   - Re-run `python build_executable.py`.
   - Ensure `WritingStudioAnalytics.spec`, `src/`, and `courses.csv` are present.
2. Codebook unlock fails:
   - Verify correct password.
   - Verify matching codebook file.
3. AI failures:
   - Check model exists in `models/`.
   - Retry with simpler query phrasing.
4. Audit trail:
   - Windows log file: `%LOCALAPPDATA%\\WritingStudioAnalytics\\audit.log`
   - Each line is JSON with timestamp + event metadata.

## Ownership Transfer Package

Hand over these items together:

1. Executable from `dist/`
2. `docs/SUPERVISOR_HANDOFF_V2.md`
3. `requirements-release.txt`
4. A tested sample dataset pair (scheduled + walk-in) used during smoke testing
5. Any current model file used in production (`models/*.gguf`)
