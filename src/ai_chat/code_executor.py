"""
Code generation and execution engine for dynamic queries.

Allows the LLM to generate pandas code for complex queries that can't be
answered from pre-computed statistics. Python executes the code safely and
returns results to the LLM for natural language formatting.

This is MUCH faster than having the LLM reason over raw data - pandas/numpy
do the computation in milliseconds, then the LLM just formats the result.
"""

import pandas as pd
import numpy as np
import warnings
from typing import Dict, Any, Tuple, Optional
import traceback


class CodeExecutor:
    """
    Safe code execution engine for dynamic data queries.
    
    Workflow:
    1. LLM generates pandas code to answer a question
    2. CodeExecutor executes it in a safe sandbox
    3. Result returned to LLM for natural language formatting
    
    Benefits:
    - Fast execution (pandas/numpy are optimized)
    - Flexible (can answer any data question)
    - Safe (limited execution environment)
    """
    
    def __init__(self, df: pd.DataFrame, verbose: bool = False):
        """
        Initialize code executor with DataFrame.
        
        Args:
            df: The DataFrame to query
            verbose: Enable verbose logging
        """
        self.df = df.copy()
        self.verbose = verbose
        self.execution_history = []
        
        if verbose:
            print(f"🔧 CodeExecutor initialized with {len(df)} records, {len(df.columns)} columns")
    
    def generate_query_code(self, user_query: str, columns: list) -> str:
        """
        Generate pandas query code using an LLM.
        
        This method is designed to be called by the chat handler when a question
        requires dynamic computation beyond pre-computed stats.
        
        Args:
            user_query: The user's natural language question
            columns: List of available column names
            
        Returns:
            str: Generated pandas code
        """
        # This would be called by the LLM to generate code
        # For now, return a template that the LLM can complete
        return f"""
# Write pandas code to answer: {user_query}
# Available columns: {', '.join(columns[:10])}

# Your code here - assign result to 'result' variable
# Example: result = df[df['column'] > value].shape[0]

result = None
"""
    
    def execute_code(self, code: str) -> Tuple[bool, Any, str]:
        """
        Execute pandas code safely and return result.
        
        Args:
            code: Python/pandas code to execute
            
        Returns:
            (success: bool, result: Any, error_message: str)
        """
        # Suppress pandas warnings
        warnings.filterwarnings('ignore')
        
        # Prepare local namespace for execution
        local_vars = {
            'df': self.df,
            'pd': pd,
            'np': np,
            'result': None
        }
        
        try:
            # Execute the code
            exec(code, {'__builtins__': {}}, local_vars)
            
            # Get the result
            result = local_vars.get('result', None)
            
            if self.verbose:
                print(f"✅ Code executed successfully: {result}")
            
            # Log execution
            self.execution_history.append({
                'code': code,
                'success': True,
                'result': str(result)
            })
            
            return True, result, ""
            
        except Exception as e:
            error_msg = f"Execution error: {str(e)}"
            if self.verbose:
                print(f"❌ {error_msg}")
                print(traceback.format_exc())
            
            # Log failed execution
            self.execution_history.append({
                'code': code,
                'success': False,
                'error': str(e)
            })
            
            return False, None, error_msg
    
    def format_code_prompt(
        self,
        user_query: str,
        columns: list,
        metrics: Dict[str, Any]
    ) -> str:
        """
        Generate a prompt for the LLM to produce query code.
        
        Args:
            user_query: User's natural language question
            columns: Available DataFrame columns
            metrics: Pre-computed metrics (for context)
            
        Returns:
            str: Prompt for LLM to generate code
        """
        columns_str = ', '.join(columns[:15])  # Limit to 15 columns
        
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

EXAMPLES:
- "Count rows where column > 5": result = df[df['column'] > 5].shape[0]
- "Get average of column": result = df['column'].mean()
- "Count unique values": result = df['column'].nunique()
- "Get mode": result = df['column'].mode()[0]

IMPORTANT:
- The 'result' variable MUST contain the final answer
- Do NOT include print statements
- The result should be ready for natural language formatting

Write only the code, no explanation:"""

        return prompt
    
    def _format_metrics_for_code(self, metrics: Dict[str, Any]) -> str:
        """Format metrics for code generation prompt."""
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
        metrics: Dict[str, Any]
    ) -> Tuple[bool, Any, str]:
        """
        Complete workflow: generate code via LLM, execute, return result.
        
        Args:
            user_query: User's natural language question
            llm_generate_fn: Function to call LLM for code generation
            columns: Available DataFrame columns
            metrics: Pre-computed metrics
            
        Returns:
            (success: bool, result: Any, error_message: str)
        """
        # 1. Generate prompt for LLM
        code_prompt = self.format_code_prompt(user_query, columns, metrics)
        
        # 2. Get code from LLM
        try:
            generated_code = llm_generate_fn(code_prompt, max_tokens=512, temperature=0.2)
            
            if self.verbose:
                print(f"📝 Generated code:\n{generated_code}")
        except Exception as e:
            return False, None, f"LLM code generation failed: {str(e)}"
        
        # 3. Execute the code
        success, result, error = self.execute_code(generated_code)
        
        return success, result, error
    
    def get_execution_history(self) -> list:
        """Get history of executed code."""
        return self.execution_history.copy()


# ============================================================================
# HELPER FUNCTIONS FOR COMMON QUERIES
# ============================================================================

def count_matching_rows(df: pd.DataFrame, condition: str) -> int:
    """
    Count rows matching a condition.
    
    Args:
        df: DataFrame
        condition: String condition (e.g., "df['column'] > value")
        
    Returns:
        int: Count of matching rows
    """
    try:
        return int(eval(f"len(df[{condition}])"))
    except:
        return 0


def calculate_percentage(df: pd.DataFrame, numerator_condition: str, denominator_condition: str = None) -> float:
    """
    Calculate percentage of rows matching conditions.
    
    Args:
        df: DataFrame
        numerator_condition: Condition for numerator
        denominator_condition: Optional condition for denominator (default: all rows)
        
    Returns:
        float: Percentage (0-100)
    """
    try:
        numerator = len(df) if not numerator_condition else eval(f"len(df[{numerator_condition}])")
        denominator = len(df) if not denominator_condition else eval(f"len(df[{denominator_condition}])")
        
        if denominator == 0:
            return 0.0
        
        return round((numerator / denominator) * 100, 1)
    except:
        return 0.0


def get_distribution(df: pd.DataFrame, column: str) -> Dict[str, int]:
    """
    Get value distribution for a column.
    
    Args:
        df: DataFrame
        column: Column name
        
    Returns:
        dict: Value counts
    """
    try:
        return df[column].value_counts().to_dict()
    except:
        return {}


def get_column_stats(df: pd.DataFrame, column: str) -> Dict[str, float]:
    """
    Get basic statistics for a numeric column.
    
    Args:
        df: DataFrame
        column: Column name
        
    Returns:
        dict: Statistics (mean, median, min, max, std)
    """
    try:
        col_data = df[column].dropna()
        return {
            'mean': float(col_data.mean()),
            'median': float(col_data.median()),
            'min': float(col_data.min()),
            'max': float(col_data.max()),
            'std': float(col_data.std())
        }
    except:
        return {}
