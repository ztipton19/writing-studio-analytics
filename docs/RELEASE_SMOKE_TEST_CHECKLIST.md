# Release Smoke Test Checklist (V2)

Use this before each supervisor handoff build.

## Command

```bash
python scripts/release_smoke_test.py --scheduled-file <scheduled_export.xlsx> --walkin-file <walkin_export.xlsx> --run-ai
```

## Expected Result

- Script exits with code `0`
- Summary prints `[PASS] All requested smoke tests succeeded`

## What Is Validated

- Input files load (CSV/XLSX)
- Anonymization and codebook creation
- Codebook decrypt validation
- Data cleaning + metrics
- PDF generation for scheduled and/or walk-in
- Three AI query round-trips (when `--run-ai` is passed)

## If It Fails

1. Fix the reported failing stage.
2. Re-run the same command.
3. Do not package EXE until smoke test passes.
