"""
Code generation and execution engine for dynamic queries.

Allows the LLM to generate pandas code for complex queries that can't be
answered from pre-computed statistics.
"""

import ast
import multiprocessing as mp
import traceback
import warnings
from typing import Any, Dict, Tuple

import numpy as np
import pandas as pd


def _subprocess_exec_worker(code: str, df: pd.DataFrame, queue) -> None:
    """Worker process to execute generated code in an isolated process."""
    warnings.filterwarnings('ignore')
    local_vars = {
        'df': df,
        'pd': pd,
        'np': np,
        'result': None,
    }
    try:
        exec(code, {'__builtins__': {}}, local_vars)
        queue.put({'ok': True, 'result': local_vars.get('result', None)})
    except Exception as exc:  # pragma: no cover - defensive worker boundary
        queue.put({'ok': False, 'error': str(exc)})


class CodeExecutor:
    """Constrained code execution engine for dynamic data queries."""

    def __init__(
        self,
        df: pd.DataFrame,
        verbose: bool = False,
        execution_timeout_seconds: float = 4.0,
        max_rows: int = 250000,
    ):
        self.df = df.copy()
        self.verbose = verbose
        self.execution_history = []
        self.execution_timeout_seconds = execution_timeout_seconds
        self.max_rows = max_rows

        if verbose:
            print(f"CodeExecutor initialized with {len(df)} records, {len(df.columns)} columns")

    def generate_query_code(self, user_query: str, columns: list) -> str:
        """Generate pandas query code using an LLM (template placeholder)."""
        return f"""
# Write pandas code to answer: {user_query}
# Available columns: {', '.join(columns[:10])}

# Your code here - assign result to 'result' variable
result = None
"""

    def execute_code(self, code: str) -> Tuple[bool, Any, str]:
        """Execute pandas code safely and return result."""
        try:
            if len(self.df) > self.max_rows:
                raise ValueError(
                    f"Dataset too large for code execution ({len(self.df):,} rows > {self.max_rows:,} limit)"
                )

            self._validate_generated_code(code)
            success, result, error_msg = self._run_in_subprocess(code)
            if not success:
                raise ValueError(error_msg)

            if self.verbose:
                print(f"Code executed successfully: {result}")

            self.execution_history.append({
                'code': code,
                'success': True,
                'result': str(result),
            })
            return True, result, ""

        except Exception as exc:
            error_msg = f"Execution error: {str(exc)}"
            if self.verbose:
                print(error_msg)
                print(traceback.format_exc())

            self.execution_history.append({
                'code': code,
                'success': False,
                'error': str(exc),
            })
            return False, None, error_msg

    def _run_in_subprocess(self, code: str) -> Tuple[bool, Any, str]:
        """Execute generated code in subprocess with timeout."""
        ctx = mp.get_context('spawn')
        queue = ctx.Queue()
        process = ctx.Process(target=_subprocess_exec_worker, args=(code, self.df, queue))
        process.start()
        process.join(self.execution_timeout_seconds)

        if process.is_alive():
            process.terminate()
            process.join()
            return False, None, f"Execution timed out after {self.execution_timeout_seconds:.1f}s"

        if process.exitcode != 0 and queue.empty():
            return False, None, f"Execution process failed (exit code {process.exitcode})"

        if queue.empty():
            return False, None, "Execution failed without a result"

        payload = queue.get_nowait()
        if payload.get('ok'):
            return True, payload.get('result'), ""
        return False, None, payload.get('error', 'Unknown execution error')

    def _validate_generated_code(self, code: str) -> None:
        """Validate generated code before execution."""
        if not code or len(code) > 4000:
            raise ValueError("Generated code is empty or too large")

        tree = ast.parse(code, mode='exec')
        validator = _SafeCodeValidator()
        validator.visit(tree)

        if not validator.assigns_result:
            raise ValueError("Generated code must assign a value to 'result'")

    def format_code_prompt(self, user_query: str, columns: list, metrics: Dict[str, Any]) -> str:
        """Generate prompt for the LLM to produce query code."""
        columns_str = ', '.join(columns[:15])
        prompt = f"""You are a data analyst. Write pandas code to answer this question.

USER QUESTION: {user_query}

AVAILABLE DATA:
- DataFrame: df
- Columns: {columns_str}
- Total records: {len(self.df)}

PRE-COMPUTED METRICS (for context):
{self._format_metrics_for_code(metrics)}

INSTRUCTIONS:
1. Write pandas code to answer the question
2. Assign the final answer to a variable called 'result'
3. Keep the result as a simple value (number, string, or small dict/list)
4. Use df[column_name] to access columns
5. If you need to filter: df[df['condition']]
6. If you need to count: df[df['condition']].shape[0]
7. If you need to calculate mean: df[df['condition']]['column'].mean()

IMPORTANT:
- The 'result' variable MUST contain the final answer
- Do NOT include print statements
- The result should be ready for natural language formatting

Write only the code, no explanation:"""
        return prompt

    def _format_metrics_for_code(self, metrics: Dict[str, Any]) -> str:
        lines = []
        for key, value in list(metrics.items())[:10]:
            if isinstance(value, dict):
                lines.append(f"{key}: {list(value.keys())[:3]}")
            else:
                lines.append(f"{key}: {value}")
        return "\n".join(lines)

    def safe_execute_query(
        self,
        user_query: str,
        llm_generate_fn,
        columns: list,
        metrics: Dict[str, Any],
    ) -> Tuple[bool, Any, str]:
        """Complete workflow: generate code via LLM, execute, return result."""
        code_prompt = self.format_code_prompt(user_query, columns, metrics)
        try:
            generated_code = llm_generate_fn(code_prompt, max_tokens=512, temperature=0.2)
            if self.verbose:
                print(f"Generated code:\n{generated_code}")
        except Exception as exc:
            return False, None, f"LLM code generation failed: {str(exc)}"

        return self.execute_code(generated_code)

    def get_execution_history(self) -> list:
        return self.execution_history.copy()


# ============================================================================
# HELPER FUNCTIONS FOR COMMON QUERIES
# ============================================================================

def count_matching_rows(df: pd.DataFrame, condition: str) -> int:
    """Count rows matching a query condition, e.g. "`column` > 5"."""
    try:
        return int(len(df.query(condition, engine='python')))
    except Exception:
        return 0


def calculate_percentage(df: pd.DataFrame, numerator_condition: str, denominator_condition: str = None) -> float:
    """Calculate percentage of rows matching conditions."""
    try:
        numerator = len(df) if not numerator_condition else len(df.query(numerator_condition, engine='python'))
        denominator = len(df) if not denominator_condition else len(df.query(denominator_condition, engine='python'))
        if denominator == 0:
            return 0.0
        return round((numerator / denominator) * 100, 1)
    except Exception:
        return 0.0


def get_distribution(df: pd.DataFrame, column: str) -> Dict[str, int]:
    """Get value distribution for a column."""
    try:
        return df[column].value_counts().to_dict()
    except Exception:
        return {}


def get_column_stats(df: pd.DataFrame, column: str) -> Dict[str, float]:
    """Get basic statistics for a numeric column."""
    try:
        col_data = df[column].dropna()
        return {
            'mean': float(col_data.mean()),
            'median': float(col_data.median()),
            'min': float(col_data.min()),
            'max': float(col_data.max()),
            'std': float(col_data.std()),
        }
    except Exception:
        return {}


class _SafeCodeValidator(ast.NodeVisitor):
    """AST validator for generated code to reduce risky execution patterns."""

    _DISALLOWED_NODES = (
        ast.Import, ast.ImportFrom, ast.With, ast.AsyncWith,
        ast.Try, ast.Raise, ast.Assert, ast.Delete,
        ast.Global, ast.Nonlocal, ast.Lambda,
        ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef,
        ast.While, ast.For, ast.AsyncFor, ast.Await, ast.Yield, ast.YieldFrom,
    )

    _ALLOWED_BUILTIN_CALLS = {
        'len', 'min', 'max', 'sum', 'abs', 'round', 'int', 'float',
        'str', 'bool', 'list', 'dict', 'set', 'sorted',
    }

    _DISALLOWED_CALL_NAMES = {
        'eval', 'exec', 'open', 'compile', 'input', '__import__',
        'getattr', 'setattr', 'delattr', 'globals', 'locals', 'vars',
        'help', 'dir', 'type', 'memoryview',
    }

    _SAFE_METHODS = {
        'mean', 'median', 'mode', 'min', 'max', 'sum', 'std', 'var', 'nunique',
        'value_counts', 'unique', 'count', 'size', 'shape', 'dropna', 'fillna',
        'astype', 'round', 'sort_values', 'sort_index', 'groupby', 'agg',
        'reset_index', 'rename', 'head', 'tail', 'copy', 'query', 'between',
        'isin', 'to_dict', 'to_list', 'nlargest', 'nsmallest', 'idxmax', 'idxmin',
    }

    def __init__(self) -> None:
        self.allowed_names = {'df', 'pd', 'np', 'result', 'True', 'False', 'None'}
        self.assigns_result = False

    def visit(self, node):
        if isinstance(node, self._DISALLOWED_NODES):
            raise ValueError(f"Disallowed syntax: {type(node).__name__}")
        return super().visit(node)

    def visit_Name(self, node: ast.Name) -> None:
        if node.id.startswith('_'):
            raise ValueError("Private names are not allowed")
        if isinstance(node.ctx, ast.Load) and node.id not in self.allowed_names and node.id not in self._ALLOWED_BUILTIN_CALLS:
            raise ValueError(f"Unknown name: {node.id}")

    def visit_Attribute(self, node: ast.Attribute) -> None:
        if node.attr.startswith('_'):
            raise ValueError("Private attributes are not allowed")
        self.generic_visit(node)

    def visit_Assign(self, node: ast.Assign) -> None:
        for target in node.targets:
            if not isinstance(target, ast.Name):
                raise ValueError("Only simple variable assignments are allowed")
            if target.id.startswith('_'):
                raise ValueError("Private assignment names are not allowed")
            self.allowed_names.add(target.id)
            if target.id == 'result':
                self.assigns_result = True
        self.generic_visit(node)

    def visit_Call(self, node: ast.Call) -> None:
        if isinstance(node.func, ast.Name):
            name = node.func.id
            if name in self._DISALLOWED_CALL_NAMES:
                raise ValueError(f"Disallowed function call: {name}")
            if name not in self._ALLOWED_BUILTIN_CALLS and name not in self.allowed_names:
                raise ValueError(f"Function call not allowed: {name}")
        elif isinstance(node.func, ast.Attribute):
            attr = node.func.attr
            if attr.startswith('_'):
                raise ValueError("Private method calls are not allowed")
            if attr not in self._SAFE_METHODS:
                raise ValueError(f"Method call not allowed: {attr}")
        else:
            raise ValueError("Unsupported call type")
        self.generic_visit(node)
