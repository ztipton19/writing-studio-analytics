# src/core/metrics.py

import pandas as pd
import numpy as np
from datetime import datetime


# ============================================================================
# BOOKING BEHAVIOR METRICS
# ============================================================================

def calculate_booking_metrics(df):
    """
    Calculate all booking-related metrics.
    
    Returns dict with:
    - lead_time_stats: mean, median, percentiles
    - lead_time_categories: breakdown by time range
    - booking_patterns: daily, weekly patterns
    """
    metrics = {}
    
    if 'Booking_Lead_Time_Days' not in df.columns:
        return metrics
    
    lead_times = df['Booking_Lead_Time_Days'].dropna()
    
    if len(lead_times) == 0:
        return metrics
    
    # Basic statistics
    metrics['lead_time_stats'] = {
        'mean': lead_times.mean(),
        'median': lead_times.median(),
        'std': lead_times.std(),
        'min': lead_times.min(),
        'max': lead_times.max(),
        'p25': lead_times.quantile(0.25),
        'p75': lead_times.quantile(0.75),
        'p90': lead_times.quantile(0.90),
        'p95': lead_times.quantile(0.95)
    }
    
    # Categorize booking times
    def categorize_lead_time(days):
        if pd.isna(days):
            return 'Unknown'
        elif days < 1:
            return 'Same Day'
        elif days < 2:
            return '1 Day Ahead'
        elif days < 4:
            return '2-3 Days Ahead'
        elif days < 8:
            return '4-7 Days Ahead'
        else:
            return '1-2 Weeks Ahead'
    
    categories = df['Booking_Lead_Time_Days'].apply(categorize_lead_time)
    category_counts = categories.value_counts()
    category_pcts = (category_counts / len(df) * 100).round(1)
    
    metrics['lead_time_categories'] = {
        'counts': category_counts.to_dict(),
        'percentages': category_pcts.to_dict()
    }
    
    return metrics


def calculate_time_patterns(df, date_col='Appointment_DateTime'):
    """
    Calculate session patterns by day of week and time of day.
    
    Returns dict with:
    - by_day_of_week: sessions per day
    - by_hour: sessions per hour
    - by_day_and_hour: heatmap data
    - peak_times: busiest days/hours
    """
    metrics = {}
    
    if date_col not in df.columns:
        return metrics
    
    df_temp = df.copy()
    df_temp['Day_of_Week'] = df_temp[date_col].dt.day_name()
    df_temp['Hour'] = df_temp[date_col].dt.hour
    
    # By day of week
    day_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    day_counts = df_temp['Day_of_Week'].value_counts().reindex(day_order, fill_value=0)
    
    metrics['by_day_of_week'] = {
        'counts': day_counts.to_dict(),
        'busiest_day': day_counts.idxmax(),
        'slowest_day': day_counts.idxmin()
    }
    
    # By hour
    hour_counts = df_temp['Hour'].value_counts().sort_index()
    
    metrics['by_hour'] = {
        'counts': hour_counts.to_dict(),
        'peak_hour': int(hour_counts.idxmax()),
        'slowest_hour': int(hour_counts.idxmin())
    }
    
    # Heatmap data (day × hour)
    heatmap = df_temp.groupby(['Day_of_Week', 'Hour']).size().unstack(fill_value=0)
    heatmap = heatmap.reindex(day_order[:5], fill_value=0)  # Weekdays only
    
    metrics['by_day_and_hour'] = heatmap.to_dict()
    
    return metrics


# ============================================================================
# ATTENDANCE & OUTCOMES METRICS
# ============================================================================

def calculate_attendance_metrics(df):
    """
    Calculate session outcome metrics.
    
    Returns dict with:
    - overall: completion/cancellation/no-show rates
    - by_day: breakdown by day of week
    - by_semester: breakdown by semester
    """
    metrics = {}
    
    # Overall outcomes
    if 'Attendance_Status' in df.columns and 'Status' in df.columns:
        total = len(df)
        
        completed = df['Attendance_Status'].str.lower().str.contains('present', na=False).sum()
        no_show = df['Attendance_Status'].str.lower().str.contains('absent', na=False).sum()
        cancelled = df['Status'].str.lower().str.contains('cancel', na=False).sum()
        
        metrics['overall'] = {
            'total_sessions': total,
            'completed': completed,
            'no_show': no_show,
            'cancelled': cancelled,
            'completion_rate': round((completed / total) * 100, 1) if total > 0 else 0,
            'no_show_rate': round((no_show / total) * 100, 1) if total > 0 else 0,
            'cancellation_rate': round((cancelled / total) * 100, 1) if total > 0 else 0,
            'show_up_rate': round((completed / (total - cancelled)) * 100, 1) if (total - cancelled) > 0 else 0
        }
    
    # By day of week
    if 'Appointment_DateTime' in df.columns and 'Attendance_Status' in df.columns:
        df_temp = df.copy()
        df_temp['Day_of_Week'] = df_temp['Appointment_DateTime'].dt.day_name()
        df_temp['Is_No_Show'] = df_temp['Attendance_Status'].str.lower().str.contains('absent', na=False)
        
        day_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']
        no_show_by_day = {}
        
        for day in day_order:
            day_data = df_temp[df_temp['Day_of_Week'] == day]
            if len(day_data) > 0:
                rate = (day_data['Is_No_Show'].sum() / len(day_data)) * 100
                no_show_by_day[day] = round(rate, 1)
        
        metrics['by_day'] = no_show_by_day
    
    # By semester
    if 'Semester_Label' in df.columns:
        df_temp = df.copy()
        df_temp['Is_No_Show'] = df_temp.get('Attendance_Status', pd.Series()).str.lower().str.contains('absent', na=False)
        df_temp['Is_Cancelled'] = df_temp.get('Status', pd.Series()).str.lower().str.contains('cancel', na=False)
        
        semester_metrics = df_temp.groupby('Semester_Label').agg({
            'Is_No_Show': lambda x: round((x.sum() / len(x)) * 100, 1),
            'Is_Cancelled': lambda x: round((x.sum() / len(x)) * 100, 1)
        }).to_dict()
        
        metrics['by_semester'] = semester_metrics
    
    return metrics


# ============================================================================
# SESSION LENGTH METRICS
# ============================================================================

def calculate_session_length_metrics(df):
    """
    Calculate session duration statistics.
    
    Returns dict with:
    - overall: mean, median, distribution
    - by_tutor: per-tutor averages
    - outliers: sessions outside normal range
    """
    metrics = {}
    
    if 'Actual_Session_Length' not in df.columns:
        return metrics
    
    lengths = df['Actual_Session_Length'].dropna()
    
    if len(lengths) == 0:
        return metrics
    
    # Overall statistics (in minutes for readability)
    metrics['overall'] = {
        'mean_minutes': round(lengths.mean() * 60, 1),
        'median_minutes': round(lengths.median() * 60, 1),
        'std_minutes': round(lengths.std() * 60, 1),
        'min_minutes': round(lengths.min() * 60, 1),
        'max_minutes': round(lengths.max() * 60, 1),
        'p25_minutes': round(lengths.quantile(0.25) * 60, 1),
        'p75_minutes': round(lengths.quantile(0.75) * 60, 1)
    }
    
    # Distribution buckets
    def bucket_length(hours):
        if pd.isna(hours):
            return 'Unknown'
        minutes = hours * 60
        if minutes < 20:
            return '<20 min'
        elif minutes < 35:
            return '20-35 min'
        elif minutes < 45:
            return '35-45 min (standard)'
        elif minutes < 60:
            return '45-60 min'
        else:
            return '60+ min'
    
    buckets = df['Actual_Session_Length'].apply(bucket_length)
    metrics['distribution'] = buckets.value_counts().to_dict()
    
    # By tutor (top 10)
    if 'Tutor_Anon_ID' in df.columns:
        top_tutors = df['Tutor_Anon_ID'].value_counts().head(10).index
        tutor_stats = df[df['Tutor_Anon_ID'].isin(top_tutors)].groupby('Tutor_Anon_ID')['Actual_Session_Length'].agg([
            ('mean_minutes', lambda x: round(x.mean() * 60, 1)),
            ('count', 'count')
        ]).to_dict()
        
        metrics['by_tutor'] = tutor_stats
    
    return metrics


# ============================================================================
# STUDENT SATISFACTION METRICS
# ============================================================================

def calculate_satisfaction_metrics(df):
    """
    Calculate student satisfaction and confidence metrics.
    
    Returns dict with:
    - confidence: pre/post statistics
    - satisfaction: overall ratings
    - trends: changes over time
    """
    metrics = {}
    
    # Confidence metrics
    if 'Pre_Confidence' in df.columns and 'Post_Confidence' in df.columns:
        pre = df['Pre_Confidence'].dropna()
        post = df['Post_Confidence'].dropna()
        
        metrics['confidence'] = {
            'pre_mean': round(pre.mean(), 2) if len(pre) > 0 else None,
            'post_mean': round(post.mean(), 2) if len(post) > 0 else None,
            'pre_median': round(pre.median(), 2) if len(pre) > 0 else None,
            'post_median': round(post.median(), 2) if len(post) > 0 else None
        }
        
        if 'Confidence_Change' in df.columns:
            changes = df['Confidence_Change'].dropna()
            
            metrics['confidence_change'] = {
                'mean': round(changes.mean(), 2),
                'median': round(changes.median(), 2),
                'improved_pct': round((changes > 0).sum() / len(changes) * 100, 1),
                'declined_pct': round((changes < 0).sum() / len(changes) * 100, 1),
                'no_change_pct': round((changes == 0).sum() / len(changes) * 100, 1)
            }
    
    # Overall satisfaction
    if 'Overall_Satisfaction' in df.columns:
        satisfaction = df['Overall_Satisfaction'].dropna()
        
        if len(satisfaction) > 0:
            metrics['satisfaction'] = {
                'mean': round(satisfaction.mean(), 2),
                'median': round(satisfaction.median(), 2),
                'mode': satisfaction.mode()[0] if len(satisfaction.mode()) > 0 else None,
                'distribution': satisfaction.value_counts().sort_index().to_dict(),
                'response_rate': round(len(satisfaction) / len(df) * 100, 1)
            }
    
    # Trends by semester
    if 'Semester_Label' in df.columns:
        semester_trends = {}
        
        if 'Overall_Satisfaction' in df.columns:
            semester_satisfaction = df.groupby('Semester_Label')['Overall_Satisfaction'].agg([
                ('mean', 'mean'),
                ('count', 'count')
            ]).to_dict()
            semester_trends['satisfaction'] = semester_satisfaction
        
        if 'Confidence_Change' in df.columns:
            semester_confidence = df.groupby('Semester_Label')['Confidence_Change'].mean().to_dict()
            semester_trends['confidence_change'] = semester_confidence
        
        metrics['trends'] = semester_trends
    
    return metrics


# ============================================================================
# TUTOR WORKLOAD METRICS
# ============================================================================

def calculate_tutor_metrics(df):
    """
    Calculate tutor workload and performance metrics.
    
    Returns dict with:
    - workload: sessions per tutor
    - hours: total hours per tutor
    - balance: workload distribution statistics
    """
    metrics = {}
    
    if 'Tutor_Anon_ID' not in df.columns:
        return metrics
    
    # Sessions per tutor
    tutor_sessions = df['Tutor_Anon_ID'].value_counts()
    
    metrics['sessions_per_tutor'] = {
        'mean': round(tutor_sessions.mean(), 1),
        'median': round(tutor_sessions.median(), 1),
        'std': round(tutor_sessions.std(), 1),
        'min': tutor_sessions.min(),
        'max': tutor_sessions.max(),
        'total_tutors': len(tutor_sessions),
        'top_10': tutor_sessions.head(10).to_dict()
    }
    
    # Hours per tutor
    if 'Actual_Session_Length' in df.columns:
        tutor_hours = df.groupby('Tutor_Anon_ID')['Actual_Session_Length'].sum()
        
        metrics['hours_per_tutor'] = {
            'mean': round(tutor_hours.mean(), 1),
            'median': round(tutor_hours.median(), 1),
            'min': round(tutor_hours.min(), 1),
            'max': round(tutor_hours.max(), 1),
            'top_10': tutor_hours.sort_values(ascending=False).head(10).round(1).to_dict()
        }
    
    # Workload balance (coefficient of variation)
    cv = (tutor_sessions.std() / tutor_sessions.mean()) * 100 if tutor_sessions.mean() > 0 else 0
    
    metrics['balance'] = {
        'coefficient_of_variation': round(cv, 1),
        'balance_interpretation': 'balanced' if cv < 30 else 'moderately_unbalanced' if cv < 50 else 'highly_unbalanced'
    }
    
    return metrics


# ============================================================================
# STUDENT ENGAGEMENT METRICS
# ============================================================================

def calculate_student_metrics(df):
    """
    Calculate student engagement and retention metrics.
    
    Returns dict with:
    - repeat_students: frequency distribution
    - first_timers: percentage
    - power_users: top students by sessions
    """
    metrics = {}
    
    if 'Student_Anon_ID' not in df.columns:
        return metrics
    
    # Sessions per student
    student_sessions = df['Student_Anon_ID'].value_counts()
    
    metrics['sessions_per_student'] = {
        'mean': round(student_sessions.mean(), 1),
        'median': round(student_sessions.median(), 1),
        'max': student_sessions.max(),
        'total_students': len(student_sessions)
    }
    
    # Power users (top 5)
    metrics['power_users'] = student_sessions.head(5).to_dict()
    
    # First-timers vs repeat
    if 'Is_First_Timer' in df.columns:
        first_time = df['Is_First_Timer'].sum()
        repeat = (~df['Is_First_Timer']).sum() - df['Is_First_Timer'].isna().sum()
        total = first_time + repeat
        
        metrics['first_time_vs_repeat'] = {
            'first_time_count': first_time,
            'repeat_count': repeat,
            'first_time_pct': round((first_time / total) * 100, 1) if total > 0 else 0,
            'repeat_pct': round((repeat / total) * 100, 1) if total > 0 else 0
        }
    
    return metrics


# ============================================================================
# SEMESTER COMPARISON METRICS
# ============================================================================

def calculate_semester_metrics(df):
    """
    Calculate metrics broken down by semester.
    
    Returns dict with semester-level summaries.
    """
    metrics = {}
    
    if 'Semester_Label' not in df.columns:
        return metrics
    
    # Total sessions per semester
    semester_counts = df['Semester_Label'].value_counts().sort_index()
    metrics['total_sessions'] = semester_counts.to_dict()
    
    # Growth rates
    if len(semester_counts) > 1:
        growth_rates = {}
        semesters = semester_counts.sort_index()
        
        for i in range(1, len(semesters)):
            prev = semesters.iloc[i-1]
            curr = semesters.iloc[i]
            growth = ((curr - prev) / prev) * 100 if prev > 0 else 0
            growth_rates[semesters.index[i]] = round(growth, 1)
        
        metrics['growth_rates'] = growth_rates
    
    return metrics


# ============================================================================
# MASTER FUNCTION: CALCULATE ALL METRICS
# ============================================================================

def calculate_all_metrics(df):
    """
    Calculate all metrics at once.
    
    Returns comprehensive metrics dictionary with all categories.
    
    Usage:
        metrics = calculate_all_metrics(df)
        print(metrics['booking']['lead_time_stats']['median'])
        print(metrics['attendance']['overall']['completion_rate'])
    """
    return {
        'booking': calculate_booking_metrics(df),
        'time_patterns': calculate_time_patterns(df),
        'attendance': calculate_attendance_metrics(df),
        'session_length': calculate_session_length_metrics(df),
        'satisfaction': calculate_satisfaction_metrics(df),
        'tutors': calculate_tutor_metrics(df),
        'students': calculate_student_metrics(df),
        'semesters': calculate_semester_metrics(df)
    }


# ============================================================================
# EXPORT FUNCTIONS
# ============================================================================

def export_metrics_to_dict(metrics, flat=False):
    """
    Export metrics to JSON-serializable dictionary.
    
    If flat=True, flattens nested structure with dot notation keys.
    """
    if not flat:
        return metrics
    
    # Flatten nested dictionary
    def flatten_dict(d, parent_key='', sep='.'):
        items = []
        for k, v in d.items():
            new_key = f"{parent_key}{sep}{k}" if parent_key else k
            if isinstance(v, dict):
                items.extend(flatten_dict(v, new_key, sep=sep).items())
            else:
                items.append((new_key, v))
        return dict(items)
    
    return flatten_dict(metrics)


def export_metrics_to_csv(metrics, filepath='metrics.csv'):
    """
    Export flattened metrics to CSV file.
    """
    flat_metrics = export_metrics_to_dict(metrics, flat=True)
    
    df = pd.DataFrame([flat_metrics]).T
    df.columns = ['value']
    df.index.name = 'metric'
    
    df.to_csv(filepath)
    
    return filepath