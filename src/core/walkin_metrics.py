# src/analytics/walkin_metrics.py

"""
Walk-In Metrics Module

Calculates comprehensive metrics for walk-in data analysis:
- Consultant workload distribution & Gini coefficient
- Temporal patterns (hour/day analysis)
- Duration statistics by session type
- Check-in usage patterns
- Course distribution analysis

Author: Writing Studio Analytics Team
Date: 2026-01-19
"""

import numpy as np

# ============================================================================
# CONSULTANT WORKLOAD ANALYSIS
# ============================================================================

def calculate_consultant_workload(df):
    """
    Calculate consultant workload metrics for "Completed" sessions.
    
    Metrics calculated:
    - Sessions per consultant
    - Hours per consultant
    - Workload distribution statistics
    - Gini coefficient (inequality measure)
    - "Slacking" consultants (below threshold)
    
    Parameters:
    - df: DataFrame with walk-in data (should be Completed sessions only)
    
    Returns:
    - Dictionary with workload metrics
    """
    
    # Filter to only Completed sessions with tutors
    if 'Status' in df.columns:
        completed = df[df['Status'] == 'Completed'].copy()
    else:
        completed = df.copy()
    
    # Check if we have tutor data
    tutor_col = 'Tutor_Anon_ID' if 'Tutor_Anon_ID' in completed.columns else 'Tutor Email'
    
    if tutor_col not in completed.columns:
        return {
            'error': 'No tutor data found',
            'message': 'Tutor_Anon_ID or Tutor Email column required for workload analysis'
        }
    
    # Remove sessions with missing tutor data
    completed = completed[completed[tutor_col].notna()].copy()
    
    if len(completed) == 0:
        return {
            'error': 'No valid sessions',
            'message': 'No Completed sessions with tutor data found'
        }
    
    # Calculate sessions per consultant
    sessions_per_consultant = completed[tutor_col].value_counts()
    
    # Calculate hours per consultant
    if 'Duration Minutes' in completed.columns:
        hours_per_consultant = completed.groupby(tutor_col)['Duration Minutes'].sum() / 60
    else:
        hours_per_consultant = None
    
    # Calculate statistics
    stats = {
        'total_consultants': len(sessions_per_consultant),
        'total_sessions': len(completed),
        'sessions_per_consultant': {
            'mean': sessions_per_consultant.mean(),
            'median': sessions_per_consultant.median(),
            'std': sessions_per_consultant.std(),
            'min': sessions_per_consultant.min(),
            'max': sessions_per_consultant.max(),
            'range': sessions_per_consultant.max() - sessions_per_consultant.min()
        }
    }
    
    # Add hours statistics if available
    if hours_per_consultant is not None:
        stats['hours_per_consultant'] = {
            'mean': hours_per_consultant.mean(),
            'median': hours_per_consultant.median(),
            'std': hours_per_consultant.std(),
            'min': hours_per_consultant.min(),
            'max': hours_per_consultant.max()
        }
    
    # Calculate Gini coefficient
    gini = calculate_gini_coefficient(sessions_per_consultant.values)
    stats['gini_coefficient'] = gini
    stats['gini_interpretation'] = interpret_gini(gini)
    
    # Identify low-performing consultants ("slacking")
    threshold = stats['sessions_per_consultant']['mean'] - stats['sessions_per_consultant']['std']
    low_performers = sessions_per_consultant[sessions_per_consultant < threshold]
    
    stats['low_performers'] = {
        'count': len(low_performers),
        'threshold': threshold,
        'consultants': low_performers.to_dict()
    }
    
    # Add raw data for plotting
    stats['raw_data'] = {
        'sessions_per_consultant': sessions_per_consultant.to_dict(),
        'hours_per_consultant': hours_per_consultant.to_dict() if hours_per_consultant is not None else None
    }
    
    return stats


def calculate_gini_coefficient(values):
    """
    Calculate Gini coefficient for workload distribution.
    
    Gini coefficient measures inequality:
    - 0.0 = Perfect equality (everyone has same workload)
    - 1.0 = Perfect inequality (one person does everything)
    
    Interpretation:
    - 0.0-0.2: Very equal distribution
    - 0.2-0.3: Moderately equal
    - 0.3-0.4: Moderately unequal
    - 0.4+: Very unequal (CONCERN - investigate!)
    
    Parameters:
    - values: Array-like of workload values (e.g., sessions per consultant)
    
    Returns:
    - Float: Gini coefficient between 0 and 1
    """
    if len(values) == 0:
        return 0.0
    
    # Sort values
    sorted_values = np.sort(values)
    n = len(sorted_values)
    
    # Calculate cumulative sum
    cumsum = 0
    for i, val in enumerate(sorted_values):
        cumsum += (2 * (i + 1) - n - 1) * val
    
    # Calculate Gini
    gini = cumsum / (n * np.sum(sorted_values))
    
    return gini


def interpret_gini(gini):
    """
    Provide human-readable interpretation of Gini coefficient.
    
    Returns:
    - String: Interpretation with actionable insights
    """
    if gini < 0.2:
        return "Very equal workload distribution - excellent balance!"
    elif gini < 0.3:
        return "Moderately equal distribution - good balance overall"
    elif gini < 0.4:
        return "Moderately unequal distribution - some imbalance present"
    else:
        return "Very unequal distribution - INVESTIGATE workload assignment!"


# ============================================================================
# TEMPORAL PATTERNS
# ============================================================================

def calculate_temporal_patterns(df):
    """
    Calculate temporal patterns for walk-in sessions.
    
    Analyzes:
    - Sessions by hour of day
    - Sessions by day of week
    - Peak hours identification
    - Peak days identification
    
    Parameters:
    - df: DataFrame with walk-in data
    
    Returns:
    - Dictionary with temporal metrics
    """
    
    metrics = {
        'total_sessions': len(df)
    }
    
    # Sessions by hour of day
    if 'Hour_of_Day' in df.columns:
        sessions_by_hour = df['Hour_of_Day'].value_counts().sort_index()
        
        metrics['by_hour'] = {
            'distribution': sessions_by_hour.to_dict(),
            'peak_hour': int(sessions_by_hour.idxmax()),
            'peak_hour_count': int(sessions_by_hour.max()),
            'quietest_hour': int(sessions_by_hour.idxmin()),
            'quietest_hour_count': int(sessions_by_hour.min())
        }
    elif 'Check_In_DateTime' in df.columns:
        # Calculate from datetime if Hour_of_Day not available
        df_temp = df.copy()
        df_temp['Hour_of_Day'] = df_temp['Check_In_DateTime'].dt.hour
        sessions_by_hour = df_temp['Hour_of_Day'].value_counts().sort_index()
        
        metrics['by_hour'] = {
            'distribution': sessions_by_hour.to_dict(),
            'peak_hour': int(sessions_by_hour.idxmax()),
            'peak_hour_count': int(sessions_by_hour.max()),
            'quietest_hour': int(sessions_by_hour.idxmin()),
            'quietest_hour_count': int(sessions_by_hour.min())
        }
    
    # Sessions by day of week
    if 'Day_of_Week' in df.columns:
        # Order days properly
        day_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        sessions_by_day = df['Day_of_Week'].value_counts()
        
        # Reorder according to day_order
        ordered_days = {day: sessions_by_day.get(day, 0) for day in day_order if day in sessions_by_day}
        
        metrics['by_day'] = {
            'distribution': ordered_days,
            'peak_day': sessions_by_day.idxmax(),
            'peak_day_count': int(sessions_by_day.max()),
            'quietest_day': sessions_by_day.idxmin(),
            'quietest_day_count': int(sessions_by_day.min())
        }
    elif 'Check_In_DateTime' in df.columns:
        # Calculate from datetime if Day_of_Week not available
        df_temp = df.copy()
        df_temp['Day_of_Week'] = df_temp['Check_In_DateTime'].dt.day_name()
        sessions_by_day = df_temp['Day_of_Week'].value_counts()
        
        metrics['by_day'] = {
            'distribution': sessions_by_day.to_dict(),
            'peak_day': sessions_by_day.idxmax(),
            'peak_day_count': int(sessions_by_day.max()),
            'quietest_day': sessions_by_day.idxmin(),
            'quietest_day_count': int(sessions_by_day.min())
        }
    
    # Calculate peak periods (for staffing recommendations)
    if 'by_hour' in metrics:
        # Identify hours with above-average traffic
        avg_sessions = np.mean(list(metrics['by_hour']['distribution'].values()))
        peak_hours = [hour for hour, count in metrics['by_hour']['distribution'].items() if count > avg_sessions]
        
        metrics['peak_periods'] = {
            'hours': peak_hours,
            'average_sessions_per_hour': avg_sessions,
            'recommendation': f"Consider extra staffing during hours: {', '.join(map(str, peak_hours))}"
        }
    
    return metrics


# ============================================================================
# DAILY PATTERNS METRICS
# ============================================================================

def calculate_daily_patterns(df, date_col='Check_In_DateTime'):
    """
    Calculate session patterns by specific calendar dates.
    
    Returns dict with:
    - top_10_dates: Top 10 busiest dates with session counts
    - bottom_10_dates: Top 10 slowest dates with session counts
    - sessions_by_date: Full daily breakdown (for queries)
    - top_10_date_hour: Top 10 date+hour combinations
    """
    metrics = {}
    
    if date_col not in df.columns:
        return metrics
    
    df_temp = df.copy()
    df_temp['Date'] = df_temp[date_col].dt.date
    
    # Group by date and count sessions
    date_counts = df_temp.groupby('Date').size().sort_values(ascending=False)
    
    # Top 10 busiest dates
    top_10 = date_counts.head(10)
    metrics['top_10_dates'] = {
        'dates': [str(date) for date in top_10.index],
        'counts': top_10.values.tolist(),
        'busiest_date': str(date_counts.idxmax()),
        'busiest_date_count': int(date_counts.max())
    }
    
    # Bottom 10 slowest dates (that had at least one session)
    bottom_10 = date_counts.tail(10)
    metrics['bottom_10_dates'] = {
        'dates': [str(date) for date in bottom_10.index],
        'counts': bottom_10.values.tolist(),
        'slowest_date': str(date_counts.idxmin()),
        'slowest_date_count': int(date_counts.min())
    }
    
    # Full daily breakdown (for queries - may be large)
    metrics['sessions_by_date'] = {
        str(date): int(count) for date, count in date_counts.items()
    }
    
    # Top 10 date+hour combinations
    df_temp['Hour'] = df_temp[date_col].dt.hour
    date_hour_counts = df_temp.groupby(['Date', 'Hour']).size().sort_values(ascending=False).head(10)
    
    metrics['top_10_date_hour'] = {
        'datetime': [f"{str(date)} {hour}:00" for date, hour in date_hour_counts.index],
        'counts': date_hour_counts.values.tolist()
    }
    
    return metrics


def calculate_monthly_patterns(df, date_col='Check_In_DateTime'):
    """
    Calculate session patterns by month and year-month.
    
    Returns dict with:
    - by_month: Sessions by month (January, February, etc.)
    - by_year_month: Sessions by year-month (e.g., 2024-01)
    - by_semester_month: Sessions by month within each semester
    """
    metrics = {}
    
    if date_col not in df.columns:
        return metrics
    
    df_temp = df.copy()
    df_temp['Month'] = df_temp[date_col].dt.month_name()
    df_temp['Month_Num'] = df_temp[date_col].dt.month
    df_temp['Year_Month'] = df_temp[date_col].dt.to_period('M').astype(str)
    
    # By month (aggregated across all years)
    month_order = ['January', 'February', 'March', 'April', 'May', 'June', 
                   'July', 'August', 'September', 'October', 'November', 'December']
    month_counts = df_temp['Month'].value_counts().reindex(month_order, fill_value=0)
    
    metrics['by_month'] = {
        'counts': month_counts.to_dict(),
        'busiest_month': month_counts.idxmax(),
        'busiest_month_count': int(month_counts.max()),
        'slowest_month': month_counts.idxmin(),
        'slowest_month_count': int(month_counts.min())
    }
    
    # By year-month
    year_month_counts = df_temp['Year_Month'].value_counts().sort_index()
    metrics['by_year_month'] = year_month_counts.to_dict()
    
    # By semester-month breakdown
    if 'Semester_Label' in df_temp.columns:
        semester_month = df_temp.groupby(['Semester_Label', 'Month']).size().unstack(fill_value=0)
        metrics['by_semester_month'] = semester_month.to_dict()
    
    return metrics


# ============================================================================
# DURATION STATISTICS
# ============================================================================

def calculate_duration_stats(df):
    """
    Calculate duration statistics for walk-in sessions.
    
    Analyzes:
    - Overall duration statistics
    - Duration by session type (Completed vs Check In)
    - Duration by course type
    - Duration outliers
    
    Parameters:
    - df: DataFrame with walk-in data
    
    Returns:
    - Dictionary with duration metrics
    """
    
    if 'Duration Minutes' not in df.columns:
        return {
            'error': 'No duration data',
            'message': 'Duration Minutes column required for duration analysis'
        }
    
    # Overall statistics
    metrics = {
        'overall': {
            'mean': df['Duration Minutes'].mean(),
            'median': df['Duration Minutes'].median(),
            'std': df['Duration Minutes'].std(),
            'min': df['Duration Minutes'].min(),
            'max': df['Duration Minutes'].max(),
            'total_minutes': df['Duration Minutes'].sum(),
            'total_hours': df['Duration Minutes'].sum() / 60
        }
    }
    
    # By session type
    if 'Status' in df.columns:
        by_status = {}
        for status in df['Status'].unique():
            status_df = df[df['Status'] == status]
            if len(status_df) > 0 and status_df['Duration Minutes'].notna().any():
                by_status[status] = {
                    'count': len(status_df),
                    'mean': status_df['Duration Minutes'].mean(),
                    'median': status_df['Duration Minutes'].median(),
                    'total_minutes': status_df['Duration Minutes'].sum(),
                    'total_hours': status_df['Duration Minutes'].sum() / 60
                }
        
        metrics['by_status'] = by_status
    
    # By course type (top 10)
    if 'Course' in df.columns:
        by_course = {}
        top_courses = df['Course'].value_counts().head(10).index
        
        for course in top_courses:
            course_df = df[df['Course'] == course]
            if len(course_df) > 0 and course_df['Duration Minutes'].notna().any():
                by_course[course] = {
                    'count': len(course_df),
                    'mean': course_df['Duration Minutes'].mean(),
                    'median': course_df['Duration Minutes'].median()
                }
        
        metrics['by_course'] = by_course
    
    # Outlier detection
    q1 = df['Duration Minutes'].quantile(0.25)
    q3 = df['Duration Minutes'].quantile(0.75)
    iqr = q3 - q1
    lower_bound = q1 - 1.5 * iqr
    upper_bound = q3 + 1.5 * iqr
    
    outliers = df[(df['Duration Minutes'] < lower_bound) | (df['Duration Minutes'] > upper_bound)]
    
    metrics['outliers'] = {
        'count': len(outliers),
        'lower_bound': lower_bound,
        'upper_bound': upper_bound,
        'below_lower': len(df[df['Duration Minutes'] < lower_bound]),
        'above_upper': len(df[df['Duration Minutes'] > upper_bound])
    }
    
    # Check if durations were capped
    if 'Duration_Minutes_Original' in df.columns:
        capped = df[df['Duration_Minutes_Original'] != df['Duration Minutes']]
        metrics['capped_durations'] = {
            'count': len(capped),
            'original_max': df['Duration_Minutes_Original'].max(),
            'capped_to': df['Duration Minutes'].max()
        }
    
    return metrics


# ============================================================================
# CHECK-IN USAGE ANALYSIS
# ============================================================================

def calculate_checkin_usage(df):
    """
    Calculate independent space usage metrics for "Check In" sessions.
    
    Analyzes how students use the Writing Studio space independently
    (without meeting with a consultant).
    
    Metrics:
    - Number of check-in sessions
    - Average duration
    - Popular times for independent work
    - Course types for independent work
    
    Parameters:
    - df: DataFrame with walk-in data
    
    Returns:
    - Dictionary with check-in usage metrics
    """
    
    # Filter to Check In sessions only
    if 'Status' not in df.columns:
        return {
            'error': 'No status column',
            'message': 'Status column required to filter Check In sessions'
        }
    
    checkin_df = df[df['Status'] == 'Check In'].copy()
    
    if len(checkin_df) == 0:
        return {
            'total_checkin_sessions': 0,
            'message': 'No Check In sessions found in dataset'
        }
    
    metrics = {
        'total_checkin_sessions': len(checkin_df),
        'percentage_of_all': (len(checkin_df) / len(df)) * 100 if len(df) > 0 else 0
    }
    
    # Duration statistics
    if 'Duration Minutes' in checkin_df.columns:
        metrics['duration'] = {
            'mean': checkin_df['Duration Minutes'].mean(),
            'median': checkin_df['Duration Minutes'].median(),
            'min': checkin_df['Duration Minutes'].min(),
            'max': checkin_df['Duration Minutes'].max(),
            'total_hours': checkin_df['Duration Minutes'].sum() / 60
        }
    
    # Popular times for check-in
    if 'Hour_of_Day' in checkin_df.columns:
        hour_dist = checkin_df['Hour_of_Day'].value_counts().sort_index()
        metrics['peak_hours'] = {
            'distribution': hour_dist.to_dict(),
            'most_common': int(hour_dist.idxmax()) if len(hour_dist) > 0 else None
        }
    
    if 'Day_of_Week' in checkin_df.columns:
        day_dist = checkin_df['Day_of_Week'].value_counts()
        metrics['peak_days'] = {
            'distribution': day_dist.to_dict(),
            'most_common': day_dist.idxmax() if len(day_dist) > 0 else None
        }
    
    # Course types for independent work
    if 'Course' in checkin_df.columns:
        course_dist = checkin_df['Course'].value_counts()
        metrics['courses'] = {
            'distribution': course_dist.to_dict(),
            'most_common': course_dist.idxmax() if len(course_dist) > 0 else None,
            'unique_count': len(course_dist)
        }
    
    return metrics


# ============================================================================
# COURSE DISTRIBUTION ANALYSIS
# ============================================================================

def calculate_course_distribution(df):
    """
    Calculate course/writing type distribution.
    
    Shows what types of writing students are working on.
    
    Parameters:
    - df: DataFrame with walk-in data
    
    Returns:
    - Dictionary with course distribution metrics
    """
    
    if 'Course' not in df.columns:
        return {
            'error': 'No course data',
            'message': 'Course column required for distribution analysis'
        }
    
    course_counts = df['Course'].value_counts()
    
    metrics = {
        'total_unique_courses': len(course_counts),
        'distribution': course_counts.to_dict(),
        'top_5': course_counts.head(5).to_dict(),
        'percentages': (course_counts / len(df) * 100).to_dict()
    }
    
    # Check for "Other" category dominance
    if 'Other' in course_counts:
        other_pct = (course_counts['Other'] / len(df)) * 100
        metrics['other_category'] = {
            'count': int(course_counts['Other']),
            'percentage': other_pct,
            'interpretation': 'High' if other_pct > 30 else 'Moderate' if other_pct > 15 else 'Low'
        }
    
    return metrics


# ============================================================================
# COMPREHENSIVE METRICS (ALL IN ONE)
# ============================================================================

def calculate_all_metrics(df):
    """
    Calculate all walk-in metrics in one function call.
    
    This is a convenience function that runs all metric calculations
    and returns a comprehensive dictionary.
    
    Parameters:
    - df: DataFrame with cleaned walk-in data
    
    Returns:
    - Dictionary with all metrics organized by category
    """
    
    metrics = {
        'dataset_info': {
            'total_records': len(df),
            'date_range': None,
            'status_distribution': df['Status'].value_counts().to_dict() if 'Status' in df.columns else None
        }
    }
    
    # Add date range if available
    if 'Check_In_DateTime' in df.columns:
        min_date = df['Check_In_DateTime'].min()
        max_date = df['Check_In_DateTime'].max()
        metrics['dataset_info']['date_range'] = f"{min_date.date()} to {max_date.date()}"
    
    # Calculate each metric category
    print("Calculating consultant workload metrics...")
    completed_df = df[df['Status'] == 'Completed'].copy() if 'Status' in df.columns else df.copy()
    metrics['consultant_workload'] = calculate_consultant_workload(completed_df)
    
    print("Calculating temporal patterns...")
    metrics['temporal_patterns'] = calculate_temporal_patterns(df)
    
    print("Calculating daily patterns...")
    metrics['daily_patterns'] = calculate_daily_patterns(df)
    
    print("Calculating monthly patterns...")
    metrics['monthly_patterns'] = calculate_monthly_patterns(df)
    
    print("Calculating duration statistics...")
    metrics['duration_stats'] = calculate_duration_stats(df)
    
    print("Calculating check-in usage...")
    metrics['checkin_usage'] = calculate_checkin_usage(df)
    
    print("Calculating course distribution...")
    metrics['course_distribution'] = calculate_course_distribution(df)
    
    print(" All metrics calculated successfully")
    
    return metrics


# ============================================================================
# SUMMARY STATISTICS (FOR EXECUTIVE SUMMARY)
# ============================================================================

def generate_executive_summary(metrics):
    """
    Generate executive summary from calculated metrics.
    
    Extracts key findings and creates human-readable summary.
    
    Parameters:
    - metrics: Dictionary from calculate_all_metrics()
    
    Returns:
    - Dictionary with executive summary points
    """
    
    summary = {
        'key_findings': [],
        'concerns': [],
        'recommendations': []
    }
    
    # Dataset overview
    total_sessions = metrics['dataset_info']['total_records']
    date_range = metrics['dataset_info'].get('date_range', 'Unknown')
    summary['overview'] = f"Analyzed {total_sessions} walk-in sessions from {date_range}"
    
    # Consultant workload findings
    if 'consultant_workload' in metrics and 'error' not in metrics['consultant_workload']:
        workload = metrics['consultant_workload']

        # Report basic stats only (no thresholds or judgments)
        mean_sessions = workload['sessions_per_consultant']['mean']
        total_consultants = workload['total_consultants']

        summary['key_findings'].append(
            f"{total_consultants} consultants handled sessions (average: {mean_sessions:.1f} sessions each)"
        )
    
    # Temporal patterns findings
    if 'temporal_patterns' in metrics:
        temporal = metrics['temporal_patterns']
        
        if 'by_hour' in temporal:
            peak_hour = temporal['by_hour']['peak_hour']
            summary['key_findings'].append(
                f"Peak usage: {peak_hour}:00 ({temporal['by_hour']['peak_hour_count']} sessions)"
            )
        
        if 'by_day' in temporal:
            peak_day = temporal['by_day']['peak_day']
            summary['key_findings'].append(
                f"Busiest day: {peak_day} ({temporal['by_day']['peak_day_count']} sessions)"
            )
    
    # Duration findings
    if 'duration_stats' in metrics and 'error' not in metrics['duration_stats']:
        duration = metrics['duration_stats']
        avg_duration = duration['overall']['mean']
        
        summary['key_findings'].append(
            f"Average session duration: {avg_duration:.1f} minutes"
        )
        
        if 'capped_durations' in duration:
            summary['concerns'].append(
                f"{duration['capped_durations']['count']} sessions had extreme durations (capped)"
            )
    
    # Check-in usage findings
    if 'checkin_usage' in metrics:
        checkin = metrics['checkin_usage']
        
        if checkin.get('total_checkin_sessions', 0) > 0:
            pct = checkin.get('percentage_of_all', 0)
            summary['key_findings'].append(
                f"Independent space usage: {checkin['total_checkin_sessions']} sessions ({pct:.1f}%)"
            )
    
    # Course distribution findings
    if 'course_distribution' in metrics and 'error' not in metrics['course_distribution']:
        courses = metrics['course_distribution']
        top_course = list(courses['top_5'].keys())[0] if courses['top_5'] else 'Unknown'
        
        summary['key_findings'].append(
            f"Most common writing type: {top_course}"
        )
        
        if 'other_category' in courses and courses['other_category']['interpretation'] == 'High':
            summary['recommendations'].append(
                "High 'Other' category usage - consider expanding course options in system"
            )
    
    return summary


# ============================================================================
# MAIN FUNCTION FOR TESTING
# ============================================================================

if __name__ == "__main__":
    print("Walk-In Metrics Module")
    print("=" * 70)
    print("\nThis module provides comprehensive metrics for walk-in data.")
    print("\nMain function: calculate_all_metrics(df)")
    print("\nIndividual metric functions:")
    print("  - calculate_consultant_workload(df)")
    print("  - calculate_temporal_patterns(df)")
    print("  - calculate_duration_stats(df)")
    print("  - calculate_checkin_usage(df)")
    print("  - calculate_course_distribution(df)")
    print("\nUtility functions:")
    print("  - calculate_gini_coefficient(values)")
    print("  - generate_executive_summary(metrics)")
    print("=" * 70)


