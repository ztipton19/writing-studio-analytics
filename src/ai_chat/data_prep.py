"""
Data Preparation Utilities for AI Chat

Prepares CSV data for LLM context.
"""

import pandas as pd
from typing import Dict, Any, Optional


def prepare_csv_for_context(
    df: pd.DataFrame,
    max_rows: int = 1000,
    include_metrics: bool = True
) -> str:
    """
    Prepare DataFrame as formatted string for LLM context.
    
    Args:
        df: Cleaned DataFrame
        max_rows: Maximum rows to include (to manage context length)
        include_metrics: Whether to include summary metrics
        
    Returns:
        Formatted string suitable for LLM prompt
    """
    # Calculate summary statistics
    total_records = len(df)
    columns = list(df.columns)
    
    # Build summary section
    context_parts = []
    context_parts.append("=" * 60)
    context_parts.append("WRITING STUDIO DATA SUMMARY")
    context_parts.append("=" * 60)
    context_parts.append(f"Total Records: {total_records:,}")
    context_parts.append(f"Columns: {', '.join(columns)}")
    context_parts.append("")
    
    # Add date range if available
    date_cols = [col for col in df.columns if 'Date' in col or 'date' in col.lower()]
    if date_cols:
        date_col = date_cols[0]
        try:
            dates = pd.to_datetime(df[date_col], errors='coerce')
            date_range = f"{dates.min().strftime('%B %d, %Y')} to {dates.max().strftime('%B %d, %Y')}"
            context_parts.append(f"Date Range: {date_range}")
        except Exception:
            pass
    
    # Add basic statistics for numeric columns
    numeric_cols = df.select_dtypes(include=['int64', 'float64']).columns.tolist()
    if numeric_cols:
        context_parts.append("")
        context_parts.append("KEY STATISTICS:")
        for col in numeric_cols[:5]:  # Limit to first 5 numeric columns
            try:
                mean_val = df[col].mean()
                min_val = df[col].min()
                max_val = df[col].max()
                context_parts.append(f"  - {col}: avg={mean_val:.2f}, min={min_val}, max={max_val}")
            except Exception:
                pass
    
    # Sample rows (first few + random sample)
    context_parts.append("")
    context_parts.append("=" * 60)
    context_parts.append("SAMPLE DATA")
    context_parts.append("=" * 60)
    
    # First few rows
    sample_rows = min(10, len(df))
    context_parts.append(f"\nFirst {sample_rows} rows:")
    context_parts.append(df.head(sample_rows).to_string(index=False))
    
    # Random sample if enough data
    if len(df) > 100:
        sample_size = min(20, max_rows - sample_rows)
        sample_df = df.sample(n=sample_size, random_state=42) if len(df) > sample_size else df
        context_parts.append(f"\n\nRandom sample ({len(sample_df)} rows):")
        context_parts.append(sample_df.to_string(index=False))
    
    context_text = "\n".join(context_parts)
    
    return context_text


def prepare_metrics_dict(
    df: pd.DataFrame,
    session_type: str = 'scheduled'
) -> Dict[str, Any]:
    """
    Extract key metrics from DataFrame.
    
    Args:
        df: Cleaned DataFrame
        session_type: 'scheduled' or 'walkin'
        
    Returns:
        Dictionary of key metrics
    """
    metrics = {
        'total_records': len(df),
        'total_sessions': df['Unique ID'].nunique() if 'Unique ID' in df.columns else len(df),
        'columns': list(df.columns),
        'session_type': session_type
    }
    
    # Date metrics
    date_cols = [col for col in df.columns if 'Date' in col or 'date' in col.lower()]
    if date_cols:
        date_col = date_cols[0]
        try:
            dates = pd.to_datetime(df[date_col], errors='coerce')
            metrics['date_range'] = f"{dates.min().strftime('%B %Y')} to {dates.max().strftime('%B %Y')}"
            metrics['date_span_days'] = (dates.max() - dates.min()).days
        except Exception:
            pass
    
    # Time-based metrics for scheduled sessions
    if session_type == 'scheduled':
        if 'Hour of Day' in df.columns:
            busiest_hour = df['Hour of Day'].mode().iloc[0] if len(df) > 0 else None
            metrics['busiest_hour'] = int(busiest_hour) if busiest_hour is not None else None
        
        if 'Day of Week' in df.columns:
            busiest_day = df['Day of Week'].mode().iloc[0] if len(df) > 0 else None
            metrics['busiest_day'] = busiest_day
        
        if 'Duration (minutes)' in df.columns:
            avg_duration = df['Duration (minutes)'].mean()
            metrics['avg_duration_minutes'] = round(avg_duration, 1) if pd.notna(avg_duration) else None
    
    # Walk-in specific metrics
    elif session_type == 'walkin':
        if 'Status' in df.columns:
            status_counts = df['Status'].value_counts()
            metrics['status_distribution'] = status_counts.to_dict()
    
    # Student/Tutor counts (if not anonymized yet)
    if 'Student Email' in df.columns:
        metrics['unique_students'] = df['Student Email'].nunique()
    if 'Tutor Email' in df.columns:
        metrics['unique_tutors'] = df['Tutor Email'].nunique()
    
    return metrics


def format_metrics_for_prompt(metrics: Dict[str, Any]) -> str:
    """
    Format metrics dictionary as string for prompt.
    
    Args:
        metrics: Dictionary of metrics
        
    Returns:
        Formatted string
    """
    lines = ["KEY METRICS:", ""]
    
    for key, value in metrics.items():
        if key == 'columns':
            lines.append(f"  - Available fields: {', '.join(value[:10])}...")
        elif isinstance(value, dict):
            lines.append(f"  - {key}:")
            for k, v in value.items():
                lines.append(f"    - {k}: {v}")
        elif isinstance(value, (int, float)):
            lines.append(f"  - {key}: {value:,}")
        else:
            lines.append(f"  - {key}: {value}")
    
    return "\n".join(lines)


def prepare_chat_context(
    df: pd.DataFrame,
    session_state: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Prepare complete context for chat interaction.
    
    Args:
        df: Cleaned DataFrame
        session_state: Streamlit session state
        
    Returns:
        Dictionary with all context components
    """
    session_type = session_state.get('data_mode', 'scheduled')
    
    # Prepare CSV payload
    csv_payload = prepare_csv_for_context(df)
    
    # Extract metrics
    metrics = prepare_metrics_dict(df, session_type)
    metrics_str = format_metrics_for_prompt(metrics)
    
    # Build full context
    context = {
        'session_type': session_type,
        'csv_payload': csv_payload,
        'metrics': metrics,
        'metrics_str': metrics_str,
        'date_range': metrics.get('date_range', 'Unknown'),
        'total_records': metrics['total_records']
    }
    
    return context
