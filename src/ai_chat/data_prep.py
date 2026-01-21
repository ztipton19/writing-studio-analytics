"""
Data preparation utilities for AI Chat.

Converts cleaned DataFrames and metrics into formats suitable for LLM prompts.
"""

import pandas as pd
from typing import Dict, Any, Optional, Tuple


def prepare_data_context(
    df_clean: pd.DataFrame,
    metrics: Dict[str, Any],
    data_mode: str = 'scheduled',
    max_rows: int = 50
) -> Dict[str, Any]:
    """
    Prepare data context for LLM prompt.
    
    Args:
        df_clean: Cleaned DataFrame
        metrics: Metrics dictionary from metrics.py
        data_mode: 'scheduled' or 'walkin'
        max_rows: Maximum number of rows to include in sample
        
    Returns:
        Dict with prepared context:
            - data_mode: Type of data
            - total_records: Total number of records
            - date_range: Date range string
            - columns: List of column names
            - key_metrics: Dict of key metrics
            - data_sample: Sample of data (Markdown table)
            - csv_summary: CSV-formatted summary
    """
    
    # Basic info
    total_records = len(df_clean)
    date_range = get_date_range(df_clean)
    columns = list(df_clean.columns)
    
    # Prepare key metrics (only aggregates, no PII)
    key_metrics = extract_key_metrics(metrics, data_mode)
    
    # Prepare data sample (first N rows, limited columns)
    data_sample = prepare_data_sample(df_clean, max_rows)
    
    # Prepare CSV summary
    csv_summary = prepare_csv_summary(df_clean, metrics, max_rows)
    
    return {
        'data_mode': data_mode,
        'total_records': total_records,
        'date_range': date_range,
        'columns': columns,
        'key_metrics': key_metrics,
        'data_sample': data_sample,
        'csv_summary': csv_summary
    }


def get_date_range(df: pd.DataFrame) -> str:
    """Get date range from DataFrame."""
    date_col = None
    
    # Find date column
    for col in ['Appointment DateTime', 'Check In DateTime', 'Date']:
        if col in df.columns:
            date_col = col
            break
    
    if date_col:
        min_date = df[date_col].min()
        max_date = df[date_col].max()
        return f"{min_date.strftime('%B %d, %Y')} to {max_date.strftime('%B %d, %Y')}"
    
    return "Unknown date range"


def extract_key_metrics(metrics: Dict[str, Any], data_mode: str) -> Dict[str, Any]:
    """
    Extract key metrics for LLM context.
    
    Only includes aggregated statistics, never individual data.
    """
    key_metrics = {}
    
    if data_mode == 'scheduled':
        # Scheduled session metrics
        if 'total_sessions' in metrics:
            key_metrics['total_sessions'] = metrics['total_sessions']
        if 'unique_students' in metrics:
            key_metrics['unique_students'] = metrics['unique_students']
        if 'unique_tutors' in metrics:
            key_metrics['unique_tutors'] = metrics['unique_tutors']
        if 'avg_satisfaction' in metrics:
            key_metrics['avg_satisfaction'] = metrics['avg_satisfaction']
        if 'no_show_rate' in metrics:
            key_metrics['no_show_rate'] = metrics['no_show_rate']
        if 'avg_duration_minutes' in metrics:
            key_metrics['avg_duration'] = metrics['avg_duration_minutes']
            
    else:
        # Walk-in session metrics
        if 'total_sessions' in metrics:
            key_metrics['total_walkins'] = metrics['total_sessions']
        if 'unique_students' in metrics:
            key_metrics['unique_students'] = metrics['unique_students']
        if 'unique_consultants' in metrics:
            key_metrics['unique_consultants'] = metrics['unique_consultants']
        if 'avg_duration_completed' in metrics:
            key_metrics['avg_duration_completed'] = metrics['avg_duration_completed']
        if 'avg_duration_checkin' in metrics:
            key_metrics['avg_duration_checkin'] = metrics['avg_duration_checkin']
        if 'status_distribution' in metrics:
            key_metrics['status_distribution'] = metrics['status_distribution']
    
    return key_metrics


def prepare_data_sample(df: pd.DataFrame, max_rows: int = 50) -> str:
    """
    Prepare data sample as simple table.
    
    Only includes first N rows to avoid overwhelming context.
    """
    sample_df = df.head(max_rows)
    
    # Remove sensitive columns if present
    sensitive_cols = ['Student ID', 'Tutor ID', 'Student Email', 'Tutor Email']
    cols_to_show = [c for c in sample_df.columns if c not in sensitive_cols]
    sample_df = sample_df[cols_to_show]
    
    # Convert to simple string representation
    return str(sample_df.head(5).to_dict('records'))


def prepare_csv_summary(
    df: pd.DataFrame,
    metrics: Dict[str, Any],
    max_rows: int = 50
) -> str:
    """
    Prepare CSV-formatted summary of data.
    
    Useful for LLMs that prefer CSV format.
    """
    sample_df = df.head(max_rows)
    
    # Remove sensitive columns
    sensitive_cols = ['Student ID', 'Tutor ID', 'Student Email', 'Tutor Email']
    cols_to_show = [c for c in sample_df.columns if c not in sensitive_cols]
    sample_df = sample_df[cols_to_show]
    
    # Convert to CSV
    csv_string = sample_df.to_csv(index=False)
    
    return csv_string


def format_metrics_for_prompt(metrics: Dict[str, Any]) -> str:
    """
    Format metrics dictionary for prompt inclusion.
    """
    lines = []
    for key, value in metrics.items():
        if isinstance(value, dict):
            lines.append(f"{key}:")
            for k, v in value.items():
                lines.append(f"  - {k}: {v}")
        elif isinstance(value, (int, float)):
            lines.append(f"{key}: {value}")
        else:
            lines.append(f"{key}: {str(value)}")
    
    return "\n".join(lines)


def prepare_chart_context(chart_path: Optional[str]) -> Optional[Dict[str, Any]]:
    """
    Prepare chart context for multimodal analysis.
    
    Args:
        chart_path: Path to chart image file
        
    Returns:
        Dict with chart info or None if no chart
    """
    if chart_path is None:
        return None
    
    return {
        'chart_available': True,
        'chart_path': chart_path,
        'note': 'A chart is available for visual analysis.'
    }
