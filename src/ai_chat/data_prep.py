"""
Data preparation utilities for AI Chat.

Converts cleaned DataFrames and metrics into formats suitable for LLM prompts.
"""

import pandas as pd
import numpy as np
from typing import Dict, Any, Optional, Tuple


def prepare_data_context(
    df_clean: pd.DataFrame,
    metrics: Dict[str, Any],
    data_mode: str = 'scheduled',
    max_rows: int = 5
) -> Dict[str, Any]:
    """
    Prepare data context for LLM prompt.
    
    OPTIMIZED VERSION: Sends schema + pre-computed metrics instead of raw CSV.
    This dramatically reduces context size and speeds up inference.
    
    Args:
        df_clean: Cleaned DataFrame
        metrics: Metrics dictionary from metrics.py
        data_mode: 'scheduled' or 'walkin'
        max_rows: Maximum number of rows to include in sample (kept minimal)
        
    Returns:
        Dict with prepared context:
            - data_mode: Type of data
            - total_records: Total number of records
            - date_range: Date range string
            - columns: List of column names
            - data_types: Column data types
            - value_ranges: Min/max for numeric columns
            - key_metrics: Dict of key metrics (PRE-COMPUTED)
            - data_sample: Tiny sample (5 rows max, for understanding structure)
    """
    
    # Basic info
    total_records = len(df_clean)
    date_range = get_date_range(df_clean)
    columns = list(df_clean.columns)
    
    # Data types (helps LLM understand schema)
    data_types = get_data_types(df_clean)
    
    # Value ranges (helps LLM understand data without seeing raw values)
    value_ranges = get_value_ranges(df_clean)
    
    # Prepare key metrics (only aggregates, no PII) - THIS IS THE KEY
    key_metrics = extract_key_metrics(metrics, data_mode)
    
    # Prepare tiny data sample (just for structure understanding, not for counting)
    data_sample = prepare_data_sample(df_clean, max_rows)
    
    return {
        'data_mode': data_mode,
        'total_records': total_records,
        'date_range': date_range,
        'columns': columns,
        'data_types': data_types,
        'value_ranges': value_ranges,
        'key_metrics': key_metrics,
        'data_sample': data_sample
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
    
    ENHANCED VERSION: Extracts comprehensive pre-computed statistics from
    calculate_all_metrics() to answer most common questions without computation.
    
    Only includes aggregated statistics, never individual data.
    """
    key_metrics = {}
    
    if data_mode == 'scheduled':
        # Scheduled session metrics - pull from comprehensive metrics structure
        
        # Attendance metrics
        if 'attendance' in metrics and 'overall' in metrics['attendance']:
            att = metrics['attendance']['overall']
            key_metrics['attendance'] = {
                'total_sessions': att.get('total_sessions', 0),
                'completed': att.get('completed', 0),
                'no_show': att.get('no_show', 0),
                'cancelled': att.get('cancelled', 0),
                'completion_rate': att.get('completion_rate', 0),
                'no_show_rate': att.get('no_show_rate', 0),
                'cancellation_rate': att.get('cancellation_rate', 0)
            }
        
        # Booking metrics (lead time - answers "how many booked >7 days ahead?")
        if 'booking' in metrics:
            booking = metrics['booking']
            
            if 'lead_time_stats' in booking:
                lt = booking['lead_time_stats']
                key_metrics['booking_lead_time'] = {
                    'mean_days': lt.get('mean', 0),
                    'median_days': lt.get('median', 0),
                    'min_days': lt.get('min', 0),
                    'max_days': lt.get('max', 0)
                }
            
            # Lead time categories - this directly answers common questions!
            if 'lead_time_categories' in booking:
                lt_cat = booking['lead_time_categories']
                if 'counts' in lt_cat and 'percentages' in lt_cat:
                    key_metrics['booking_categories'] = {
                        'same_day_count': lt_cat['counts'].get('Same Day', 0),
                        'same_day_pct': lt_cat['percentages'].get('Same Day', 0),
                        '1_day_count': lt_cat['counts'].get('1 Day Ahead', 0),
                        '1_day_pct': lt_cat['percentages'].get('1 Day Ahead', 0),
                        '2_3_days_count': lt_cat['counts'].get('2-3 Days Ahead', 0),
                        '2_3_days_pct': lt_cat['percentages'].get('2-3 Days Ahead', 0),
                        '4_7_days_count': lt_cat['counts'].get('4-7 Days Ahead', 0),
                        '4_7_days_pct': lt_cat['percentages'].get('4-7 Days Ahead', 0),
                        '7_plus_days_count': lt_cat['counts'].get('7+ days ahead', 0),
                        '7_plus_days_pct': lt_cat['percentages'].get('7+ days ahead', 0)
                    }
        
        # Time patterns (peak hours/days)
        if 'time_patterns' in metrics:
            tp = metrics['time_patterns']
            
            if 'by_day_of_week' in tp:
                day = tp['by_day_of_week']
                key_metrics['daily_patterns'] = {
                    'busiest_day': day.get('busiest_day', 'N/A'),
                    'slowest_day': day.get('slowest_day', 'N/A')
                }
            
            if 'by_hour' in tp:
                hour = tp['by_hour']
                key_metrics['hourly_patterns'] = {
                    'peak_hour': hour.get('peak_hour', 0),
                    'slowest_hour': hour.get('slowest_hour', 0)
                }
        
        # Satisfaction metrics
        if 'satisfaction' in metrics:
            sat = metrics['satisfaction']
            
            if 'satisfaction' in sat:
                overall_sat = sat['satisfaction']
                key_metrics['satisfaction'] = {
                    'mean': overall_sat.get('mean', 0),
                    'median': overall_sat.get('median', 0),
                    'response_rate': overall_sat.get('response_rate', 0)
                }
            
            if 'confidence' in sat:
                conf = sat['confidence']
                key_metrics['confidence'] = {
                    'pre_mean': conf.get('pre_mean', 0),
                    'post_mean': conf.get('post_mean', 0)
                }
            
            if 'confidence_change' in sat:
                change = sat['confidence_change']
                key_metrics['confidence_change'] = {
                    'mean_change': change.get('mean', 0),
                    'improved_pct': change.get('improved_pct', 0),
                    'declined_pct': change.get('declined_pct', 0)
                }
        
        # Session length metrics
        if 'session_length' in metrics and 'overall' in metrics['session_length']:
            sl = metrics['session_length']['overall']
            key_metrics['session_length'] = {
                'mean_minutes': sl.get('mean_minutes', 0),
                'median_minutes': sl.get('median_minutes', 0)
            }
        
        # Tutor metrics
        if 'tutors' in metrics:
            tutor = metrics['tutors']
            if 'sessions_per_tutor' in tutor:
                spt = tutor['sessions_per_tutor']
                key_metrics['tutor_workload'] = {
                    'total_tutors': spt.get('total_tutors', 0),
                    'mean_sessions_per_tutor': spt.get('mean', 0)
                }
        
        # Student metrics
        if 'students' in metrics:
            stud = metrics['students']
            if 'first_time_vs_repeat' in stud:
                ftr = stud['first_time_vs_repeat']
                key_metrics['student_mix'] = {
                    'first_time_pct': ftr.get('first_time_pct', 0),
                    'repeat_pct': ftr.get('repeat_pct', 0)
                }
            
            if 'sessions_per_student' in stud:
                sps = stud['sessions_per_student']
                key_metrics['student_engagement'] = {
                    'total_students': sps.get('total_students', 0),
                    'mean_sessions_per_student': sps.get('mean', 0)
                }
        
        # Location metrics (CORD vs ZOOM)
        if 'location' in metrics and 'totals' in metrics['location']:
            loc = metrics['location']['totals']
            key_metrics['location'] = {
                'total_sessions': loc.get('total_sessions', 0),
                'cord_count': loc.get('cord_count', 0),
                'cord_pct': loc.get('cord_pct', 0),
                'zoom_count': loc.get('zoom_count', 0),
                'zoom_pct': loc.get('zoom_pct', 0)
            }
        
        # Incentive metrics
        if 'incentives' in metrics:
            inc = metrics['incentives']
            if 'incentive_breakdown' in inc:
                ib = inc['incentive_breakdown']
                key_metrics['incentives'] = {
                    'any_incentive_pct': ib.get('any_incentive', {}).get('percentage', 0),
                    'extra_credit_pct': ib.get('extra_credit', {}).get('percentage', 0)
                }
            
            if 'mean_difference' in inc:
                key_metrics['incentive_impact'] = inc['mean_difference']
        
        # Daily patterns (NEW - answers "what date had most sessions?")
        if 'daily_patterns' in metrics:
            dp = metrics['daily_patterns']
            key_metrics['daily_patterns'] = {
                'busiest_date': dp.get('top_10_dates', {}).get('busiest_date', 'N/A'),
                'busiest_date_count': dp.get('top_10_dates', {}).get('busiest_date_count', 0),
                'slowest_date': dp.get('bottom_10_dates', {}).get('slowest_date', 'N/A'),
                'slowest_date_count': dp.get('bottom_10_dates', {}).get('slowest_date_count', 0),
                'top_10_dates': dp.get('top_10_dates', {}).get('dates', []),
                'top_10_counts': dp.get('top_10_dates', {}).get('counts', [])
            }
        
        # Monthly patterns (NEW - answers "what month had most sessions?")
        if 'monthly_patterns' in metrics:
            mp = metrics['monthly_patterns']
            key_metrics['monthly_patterns'] = {
                'busiest_month': mp.get('by_month', {}).get('busiest_month', 'N/A'),
                'busiest_month_count': mp.get('by_month', {}).get('busiest_month_count', 0),
                'slowest_month': mp.get('by_month', {}).get('slowest_month', 'N/A'),
                'slowest_month_count': mp.get('by_month', {}).get('slowest_month_count', 0)
            }
        
        # Semester trends (NEW - answers "how did satisfaction change from spring to fall?")
        if 'semester_trends' in metrics:
            st = metrics['semester_trends']
            key_metrics['semester_trends'] = {
                'sessions_by_semester': st.get('sessions', {}),
                'completion_rate_by_semester': st.get('completion_rate_by_semester', {}),
                'satisfaction_by_semester': st.get('satisfaction_by_semester', {}),
                'no_show_rate_by_semester': st.get('no_show_rate_by_semester', {}),
                'confidence_change_by_semester': st.get('confidence_change_by_semester', {}),
                'session_length_by_semester': st.get('session_length_by_semester', {})
            }
            
    else:
        # Walk-in session metrics
        if 'attendance' in metrics and 'overall' in metrics['attendance']:
            att = metrics['attendance']['overall']
            key_metrics['attendance'] = {
                'total_sessions': att.get('total_sessions', 0),
                'completed': att.get('completed', 0),
                'no_show': att.get('no_show', 0)
            }
        
        # Session length for walk-ins
        if 'session_length' in metrics and 'overall' in metrics['session_length']:
            sl = metrics['session_length']['overall']
            key_metrics['session_length'] = {
                'mean_minutes': sl.get('mean_minutes', 0),
                'median_minutes': sl.get('median_minutes', 0)
            }
        
        # Time patterns for walk-ins (day of week and hour)
        if 'time_patterns' in metrics:
            tp = metrics['time_patterns']
            
            if 'by_day_of_week' in tp:
                day = tp['by_day_of_week']
                key_metrics['weekly_patterns'] = {
                    'busiest_day': day.get('busiest_day', 'N/A'),
                    'slowest_day': day.get('slowest_day', 'N/A')
                }
            
            if 'by_hour' in tp:
                hour = tp['by_hour']
                key_metrics['hourly_patterns'] = {
                    'peak_hour': hour.get('peak_hour', 0),
                    'slowest_hour': hour.get('slowest_hour', 0)
                }
        
        # Daily patterns for walk-ins (NEW - answers "what date had most walk-ins?")
        if 'daily_patterns' in metrics:
            dp = metrics['daily_patterns']
            key_metrics['daily_patterns'] = {
                'busiest_date': dp.get('top_10_dates', {}).get('busiest_date', 'N/A'),
                'busiest_date_count': dp.get('top_10_dates', {}).get('busiest_date_count', 0),
                'slowest_date': dp.get('bottom_10_dates', {}).get('slowest_date', 'N/A'),
                'slowest_date_count': dp.get('bottom_10_dates', {}).get('slowest_date_count', 0),
                'top_10_dates': dp.get('top_10_dates', {}).get('dates', []),
                'top_10_counts': dp.get('top_10_dates', {}).get('counts', [])
            }
        
        # Monthly patterns for walk-ins (NEW - answers "what month had most walk-ins?")
        if 'monthly_patterns' in metrics:
            mp = metrics['monthly_patterns']
            key_metrics['monthly_patterns'] = {
                'busiest_month': mp.get('by_month', {}).get('busiest_month', 'N/A'),
                'busiest_month_count': mp.get('by_month', {}).get('busiest_month_count', 0),
                'slowest_month': mp.get('by_month', {}).get('slowest_month', 'N/A'),
                'slowest_month_count': mp.get('by_month', {}).get('slowest_month_count', 0)
            }
    
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


def get_data_types(df: pd.DataFrame) -> Dict[str, str]:
    """
    Get data types for all columns.
    
    Helps LLM understand schema without seeing raw data.
    """
    data_types = {}
    
    for col in df.columns:
        dtype = df[col].dtype
        
        # Use numpy dtype kind for more reliable checking
        dtype_kind = dtype.kind if hasattr(dtype, 'kind') else None
        dtype_name = str(dtype.name) if hasattr(dtype, 'name') else str(dtype)
        
        if dtype_kind in ['i', 'u', 'f']:  # integer, unsigned, float
            data_types[col] = 'numeric'
        elif dtype_kind in ['M', 'm']:  # datetime, timedelta
            data_types[col] = 'datetime'
        elif dtype_kind == 'b':  # boolean
            data_types[col] = 'boolean'
        elif dtype_name == 'category':
            data_types[col] = 'categorical'
        else:
            data_types[col] = 'categorical'
    
    return data_types


def get_value_ranges(df: pd.DataFrame) -> Dict[str, Dict[str, Any]]:
    """
    Get min/max for numeric columns and unique values for categorical columns.
    
    Helps LLM understand data range without seeing raw values.
    """
    value_ranges = {}
    
    for col in df.columns:
        dtype = df[col].dtype
        
        # Use numpy dtype kind for more reliable checking
        dtype_kind = dtype.kind if hasattr(dtype, 'kind') else None
        dtype_name = str(dtype.name) if hasattr(dtype, 'name') else str(dtype)
        
        if dtype_kind in ['i', 'u', 'f']:  # integer, unsigned, float
            # Numeric columns: min/max
            if not df[col].isna().all():
                value_ranges[col] = {
                    'min': float(df[col].min()),
                    'max': float(df[col].max()),
                    'type': 'numeric_range'
                }
        elif dtype_kind in ['O', 'U', 'S'] or dtype_name == 'category':
            # Categorical columns: sample unique values
            unique_vals = df[col].dropna().unique()
            sample_vals = list(unique_vals[:5])  # Just first 5
            value_ranges[col] = {
                'sample_values': sample_vals,
                'unique_count': len(unique_vals),
                'type': 'categorical_sample'
            }
    
    return value_ranges


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
