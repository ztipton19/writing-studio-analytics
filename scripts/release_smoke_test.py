#!/usr/bin/env python
"""Release smoke test for Writing Studio Analytics V2.

Usage examples:
  python scripts/release_smoke_test.py --scheduled-file sample_scheduled.xlsx
  python scripts/release_smoke_test.py --walkin-file sample_walkin.csv
  python scripts/release_smoke_test.py --scheduled-file scheduled.xlsx --walkin-file walkin.csv --run-ai
"""

from __future__ import annotations

import argparse
import os
import sys
import tempfile
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.core.metrics import calculate_all_metrics
from src.core.privacy import anonymize_with_codebook, decrypt_codebook
from src.core.walkin_metrics import calculate_all_metrics as calculate_walkin_metrics
from src.core.data_cleaner import clean_data
from src.core.walkin_cleaner import clean_walkin_data
from src.visualizations.report_generator import generate_full_report
from src.visualizations.walkin_report_generator import generate_walkin_report


def load_table(file_path: Path) -> pd.DataFrame:
    if file_path.suffix.lower() in {".xlsx", ".xls"}:
        return pd.read_excel(file_path)
    return pd.read_csv(file_path)


def run_ai_checks(df_clean: pd.DataFrame, metrics: dict, data_mode: str) -> None:
    from src.ai_chat.chat_handler import ChatHandler
    from src.ai_chat.setup_model import get_model_path

    model_path = get_model_path()
    handler = ChatHandler(model_path=model_path, verbose=False, enable_code_execution=True)
    handler.set_data_for_code_execution(df_clean)

    queries = [
        "How many total sessions are in this dataset?",
        "What is the average session duration?",
        "Which day of the week appears busiest?",
    ]

    for query in queries:
        response, meta = handler.handle_query(query, df_clean, metrics, data_mode)
        if meta.get("error"):
            raise RuntimeError(f"AI query failed: {query} -> {response}")
        if not response or len(response.strip()) == 0:
            raise RuntimeError(f"AI query returned empty response: {query}")


def run_pipeline(file_path: Path, mode: str, run_ai: bool) -> None:
    print(f"\n[SMOKE] Running {mode} pipeline: {file_path}")
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    df = load_table(file_path)
    if len(df) == 0:
        raise ValueError(f"Input file has no rows: {file_path}")

    codebook_password = "smoke-test-pass"

    with tempfile.TemporaryDirectory(prefix="wsa_smoke_") as tmp_dir:
        tmp_path = Path(tmp_dir)

        df_anon, codebook_path, _ = anonymize_with_codebook(
            df,
            create_codebook=True,
            password=codebook_password,
            confirm_password=codebook_password,
            session_type=mode,
        )

        if not codebook_path or not Path(codebook_path).exists():
            raise RuntimeError("Codebook was not created")

        codebook_data = decrypt_codebook(codebook_path, codebook_password)
        if "students" not in codebook_data or "tutors" not in codebook_data:
            raise RuntimeError("Codebook decrypt validation failed")

        if mode == "scheduled":
            df_clean, cleaning_log = clean_data(df_anon, mode="scheduled", remove_outliers=True, log_actions=False)
            metrics = calculate_all_metrics(df_clean)
            out_pdf = tmp_path / "scheduled_smoke_report.pdf"
            report_path = generate_full_report(df_clean, cleaning_log, str(out_pdf))
        else:
            df_clean, cleaning_log = clean_walkin_data(df_anon)
            metrics = calculate_walkin_metrics(df_clean)
            out_pdf = tmp_path / "walkin_smoke_report.pdf"
            report_path = generate_walkin_report(df_clean, cleaning_log, str(out_pdf))

        if not Path(report_path).exists():
            raise RuntimeError(f"Report was not generated: {report_path}")

        if run_ai:
            run_ai_checks(df_clean, metrics, mode)

        # Cleanup codebook created in CWD by anonymize_with_codebook
        try:
            os.remove(codebook_path)
        except OSError:
            pass

    print(f"[PASS] {mode} pipeline passed")


def main() -> int:
    parser = argparse.ArgumentParser(description="Release smoke test for V2 desktop app")
    parser.add_argument("--scheduled-file", type=Path, help="Path to scheduled sessions CSV/XLSX")
    parser.add_argument("--walkin-file", type=Path, help="Path to walk-in sessions CSV/XLSX")
    parser.add_argument("--run-ai", action="store_true", help="Also run 3 AI query checks")
    args = parser.parse_args()

    if not args.scheduled_file and not args.walkin_file:
        parser.error("Provide at least one of --scheduled-file or --walkin-file")

    failures = []

    if args.scheduled_file:
        try:
            run_pipeline(args.scheduled_file, "scheduled", args.run_ai)
        except Exception as exc:
            failures.append(f"scheduled: {exc}")

    if args.walkin_file:
        try:
            run_pipeline(args.walkin_file, "walkin", args.run_ai)
        except Exception as exc:
            failures.append(f"walkin: {exc}")

    print("\n================ Smoke Test Summary ================")
    if failures:
        for item in failures:
            print(f"[FAIL] {item}")
        return 1

    print("[PASS] All requested smoke tests succeeded")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
