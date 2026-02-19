import pandas as pd

from src.ai_chat.code_executor import CodeExecutor


def test_code_executor_blocks_disallowed_import():
    df = pd.DataFrame({'x': [1, 2, 3]})
    executor = CodeExecutor(df, verbose=False)

    ok, result, err = executor.execute_code("import os\nresult = 1")

    assert ok is False
    assert result is None
    assert "Disallowed syntax" in err


def test_code_executor_enforces_row_limit():
    df = pd.DataFrame({'x': [1, 2]})
    executor = CodeExecutor(df, verbose=False, max_rows=1)

    ok, result, err = executor.execute_code("result = len(df)")

    assert ok is False
    assert result is None
    assert "Dataset too large" in err


def test_code_executor_timeout_guard():
    df = pd.DataFrame({'x': [1]})
    # Tiny timeout makes process startup itself exceed threshold.
    executor = CodeExecutor(df, verbose=False, execution_timeout_seconds=0.0001)

    ok, result, err = executor.execute_code("result = len(df)")

    assert ok is False
    assert result is None
    assert "timed out" in err.lower()
