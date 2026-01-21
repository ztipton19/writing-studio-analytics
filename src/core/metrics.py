# src/core/metrics.py

import pandas as pd
from src.core.location_metrics import calculate_location_metrics

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
            return '7+ days ahead'
    
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
# INCENTIVE ANALYSIS METRICS
# ============================================================================

def calculate_incentive_metrics(df):
    """
    Calculate metrics related to student incentives and their correlation
    with tutor ratings of session quality.

    Research question: Do incentivized students (extra credit or required visits)
    have lower-quality sessions as perceived by tutors?

    Returns dict with:
    - incentive_breakdown: counts and percentages for each incentive type
    - tutor_rating_by_incentive: average tutor ratings by incentive type
    - statistical_tests: correlation analysis results
    """
    metrics = {}

    # Check if required columns exist
    required_cols = ['Extra_Credit', 'Class_Required', 'Incentivized', 'Tutor_Session_Rating']
    if not all(col in df.columns for col in required_cols):
        return metrics

    # Filter to completed sessions only (where tutor rating exists)
    df_completed = df[df['Tutor_Session_Rating'].notna()].copy()

    if len(df_completed) == 0:
        return metrics

    # Incentive breakdown
    total = len(df_completed)
    extra_credit_count = df_completed['Extra_Credit'].sum()
    class_required_count = df_completed['Class_Required'].sum()
    incentivized_count = df_completed['Incentivized'].sum()
    no_incentive_count = total - incentivized_count

    metrics['incentive_breakdown'] = {
        'total_sessions_with_rating': total,
        'extra_credit': {
            'count': int(extra_credit_count),
            'percentage': round((extra_credit_count / total) * 100, 1)
        },
        'class_required': {
            'count': int(class_required_count),
            'percentage': round((class_required_count / total) * 100, 1)
        },
        'any_incentive': {
            'count': int(incentivized_count),
            'percentage': round((incentivized_count / total) * 100, 1)
        },
        'no_incentive': {
            'count': int(no_incentive_count),
            'percentage': round((no_incentive_count / total) * 100, 1)
        }
    }

    # Tutor ratings by incentive type
    tutor_ratings = {}

    # Extra credit vs no extra credit
    extra_credit_ratings = df_completed[df_completed['Extra_Credit']]['Tutor_Session_Rating']
    no_extra_credit_ratings = df_completed[~df_completed['Extra_Credit']]['Tutor_Session_Rating']

    if len(extra_credit_ratings) > 0:
        tutor_ratings['extra_credit'] = {
            'mean': round(extra_credit_ratings.mean(), 2),
            'median': round(extra_credit_ratings.median(), 2),
            'std': round(extra_credit_ratings.std(), 2),
            'count': len(extra_credit_ratings)
        }

    if len(no_extra_credit_ratings) > 0:
        tutor_ratings['no_extra_credit'] = {
            'mean': round(no_extra_credit_ratings.mean(), 2),
            'median': round(no_extra_credit_ratings.median(), 2),
            'std': round(no_extra_credit_ratings.std(), 2),
            'count': len(no_extra_credit_ratings)
        }

    # Class required vs not required
    class_required_ratings = df_completed[df_completed['Class_Required']]['Tutor_Session_Rating']
    not_required_ratings = df_completed[~df_completed['Class_Required']]['Tutor_Session_Rating']

    if len(class_required_ratings) > 0:
        tutor_ratings['class_required'] = {
            'mean': round(class_required_ratings.mean(), 2),
            'median': round(class_required_ratings.median(), 2),
            'std': round(class_required_ratings.std(), 2),
            'count': len(class_required_ratings)
        }

    if len(not_required_ratings) > 0:
        tutor_ratings['not_required'] = {
            'mean': round(not_required_ratings.mean(), 2),
            'median': round(not_required_ratings.median(), 2),
            'std': round(not_required_ratings.std(), 2),
            'count': len(not_required_ratings)
        }

    # Any incentive vs no incentive
    incentivized_ratings = df_completed[df_completed['Incentivized']]['Tutor_Session_Rating']
    not_incentivized_ratings = df_completed[~df_completed['Incentivized']]['Tutor_Session_Rating']

    if len(incentivized_ratings) > 0:
        tutor_ratings['incentivized'] = {
            'mean': round(incentivized_ratings.mean(), 2),
            'median': round(incentivized_ratings.median(), 2),
            'std': round(incentivized_ratings.std(), 2),
            'count': len(incentivized_ratings)
        }

    if len(not_incentivized_ratings) > 0:
        tutor_ratings['not_incentivized'] = {
            'mean': round(not_incentivized_ratings.mean(), 2),
            'median': round(not_incentivized_ratings.median(), 2),
            'std': round(not_incentivized_ratings.std(), 2),
            'count': len(not_incentivized_ratings)
        }

    metrics['tutor_rating_by_incentive'] = tutor_ratings

    # Calculate difference in means
    if 'incentivized' in tutor_ratings and 'not_incentivized' in tutor_ratings:
        diff = tutor_ratings['incentivized']['mean'] - tutor_ratings['not_incentivized']['mean']
        metrics['mean_difference'] = {
            'incentivized_minus_not_incentivized': round(diff, 2),
            'interpretation': 'Incentivized students have higher ratings' if diff > 0 else 'Incentivized students have lower ratings' if diff < 0 else 'No difference'
        }

    # Student satisfaction ratings by incentive type
    satisfaction_ratings = {}

    # Filter to sessions with satisfaction data
    df_with_satisfaction = df_completed[df_completed['Overall_Satisfaction'].notna()].copy()

    if len(df_with_satisfaction) > 0:
        # Extra credit vs no extra credit
        extra_credit_satisfaction = df_with_satisfaction[df_with_satisfaction['Extra_Credit']]['Overall_Satisfaction']
        no_extra_credit_satisfaction = df_with_satisfaction[~df_with_satisfaction['Extra_Credit']]['Overall_Satisfaction']

        if len(extra_credit_satisfaction) > 0:
            satisfaction_ratings['extra_credit'] = {
                'mean': round(extra_credit_satisfaction.mean(), 2),
                'median': round(extra_credit_satisfaction.median(), 2),
                'std': round(extra_credit_satisfaction.std(), 2),
                'count': len(extra_credit_satisfaction)
            }

        if len(no_extra_credit_satisfaction) > 0:
            satisfaction_ratings['no_extra_credit'] = {
                'mean': round(no_extra_credit_satisfaction.mean(), 2),
                'median': round(no_extra_credit_satisfaction.median(), 2),
                'std': round(no_extra_credit_satisfaction.std(), 2),
                'count': len(no_extra_credit_satisfaction)
            }

        # Class required vs not required
        class_required_satisfaction = df_with_satisfaction[df_with_satisfaction['Class_Required']]['Overall_Satisfaction']
        not_required_satisfaction = df_with_satisfaction[~df_with_satisfaction['Class_Required']]['Overall_Satisfaction']

        if len(class_required_satisfaction) > 0:
            satisfaction_ratings['class_required'] = {
                'mean': round(class_required_satisfaction.mean(), 2),
                'median': round(class_required_satisfaction.median(), 2),
                'std': round(class_required_satisfaction.std(), 2),
                'count': len(class_required_satisfaction)
            }

        if len(not_required_satisfaction) > 0:
            satisfaction_ratings['not_required'] = {
                'mean': round(not_required_satisfaction.mean(), 2),
                'median': round(not_required_satisfaction.median(), 2),
                'std': round(not_required_satisfaction.std(), 2),
                'count': len(not_required_satisfaction)
            }

        # Any incentive vs no incentive
        incentivized_satisfaction = df_with_satisfaction[df_with_satisfaction['Incentivized']]['Overall_Satisfaction']
        not_incentivized_satisfaction = df_with_satisfaction[~df_with_satisfaction['Incentivized']]['Overall_Satisfaction']

        if len(incentivized_satisfaction) > 0:
            satisfaction_ratings['incentivized'] = {
                'mean': round(incentivized_satisfaction.mean(), 2),
                'median': round(incentivized_satisfaction.median(), 2),
                'std': round(incentivized_satisfaction.std(), 2),
                'count': len(incentivized_satisfaction)
            }

        if len(not_incentivized_satisfaction) > 0:
            satisfaction_ratings['not_incentivized'] = {
                'mean': round(not_incentivized_satisfaction.mean(), 2),
                'median': round(not_incentivized_satisfaction.median(), 2),
                'std': round(not_incentivized_satisfaction.std(), 2),
                'count': len(not_incentivized_satisfaction)
            }

    metrics['satisfaction_rating_by_incentive'] = satisfaction_ratings

    # Statistical testing (t-test for comparison)
    from scipy import stats

    statistical_tests = {}

    # T-test: Incentivized vs Not Incentivized
    if len(incentivized_ratings) >= 2 and len(not_incentivized_ratings) >= 2:
        t_stat, p_value = stats.ttest_ind(incentivized_ratings, not_incentivized_ratings, equal_var=False)
        statistical_tests['incentivized_vs_not'] = {
            't_statistic': round(t_stat, 3),
            'p_value': round(p_value, 4),
            'significant_at_05': p_value < 0.05,
            'significant_at_01': p_value < 0.01
        }

    # T-test: Class Required vs Not Required
    if len(class_required_ratings) >= 2 and len(not_required_ratings) >= 2:
        t_stat, p_value = stats.ttest_ind(class_required_ratings, not_required_ratings, equal_var=False)
        statistical_tests['class_required_vs_not'] = {
            't_statistic': round(t_stat, 3),
            'p_value': round(p_value, 4),
            'significant_at_05': p_value < 0.05,
            'significant_at_01': p_value < 0.01
        }

    # T-test: Extra Credit vs No Extra Credit
    if len(extra_credit_ratings) >= 2 and len(no_extra_credit_ratings) >= 2:
        t_stat, p_value = stats.ttest_ind(extra_credit_ratings, no_extra_credit_ratings, equal_var=False)
        statistical_tests['extra_credit_vs_not'] = {
            't_statistic': round(t_stat, 3),
            'p_value': round(p_value, 4),
            'significant_at_05': p_value < 0.05,
            'significant_at_01': p_value < 0.01
        }

    metrics['statistical_tests'] = statistical_tests

    # Statistical tests for satisfaction ratings
    satisfaction_tests = {}

    if len(df_with_satisfaction) > 0:
        # T-test: Incentivized vs Not Incentivized (satisfaction)
        if len(incentivized_satisfaction) >= 2 and len(not_incentivized_satisfaction) >= 2:
            t_stat, p_value = stats.ttest_ind(incentivized_satisfaction, not_incentivized_satisfaction, equal_var=False)
            satisfaction_tests['incentivized_vs_not'] = {
                't_statistic': round(t_stat, 3),
                'p_value': round(p_value, 4),
                'significant_at_05': p_value < 0.05,
                'significant_at_01': p_value < 0.01
            }

        # T-test: Class Required vs Not Required (satisfaction)
        if len(class_required_satisfaction) >= 2 and len(not_required_satisfaction) >= 2:
            t_stat, p_value = stats.ttest_ind(class_required_satisfaction, not_required_satisfaction, equal_var=False)
            satisfaction_tests['class_required_vs_not'] = {
                't_statistic': round(t_stat, 3),
                'p_value': round(p_value, 4),
                'significant_at_05': p_value < 0.05,
                'significant_at_01': p_value < 0.01
            }

        # T-test: Extra Credit vs No Extra Credit (satisfaction)
        if len(extra_credit_satisfaction) >= 2 and len(no_extra_credit_satisfaction) >= 2:
            t_stat, p_value = stats.ttest_ind(extra_credit_satisfaction, no_extra_credit_satisfaction, equal_var=False)
            satisfaction_tests['extra_credit_vs_not'] = {
                't_statistic': round(t_stat, 3),
                'p_value': round(p_value, 4),
                'significant_at_05': p_value < 0.05,
                'significant_at_01': p_value < 0.01
            }

    metrics['satisfaction_statistical_tests'] = satisfaction_tests

    # Rating distribution by incentive status
    rating_dist = {}

    if len(incentivized_ratings) > 0:
        rating_dist['incentivized'] = incentivized_ratings.value_counts().sort_index().to_dict()

    if len(not_incentivized_ratings) > 0:
        rating_dist['not_incentivized'] = not_incentivized_ratings.value_counts().sort_index().to_dict()

    metrics['rating_distribution'] = rating_dist

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
        'semesters': calculate_semester_metrics(df),
        'incentives': calculate_incentive_metrics(df),
        'location': calculate_location_metrics(df)
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


# ============================================================================
# EXECUTIVE SUMMARY GENERATION
# ============================================================================

def generate_executive_summary(metrics):
    """
    Generate executive summary from calculated metrics.
    
    Extracts key findings, concerns, and recommendations from the
    comprehensive metrics dictionary.
    
    Parameters:
    - metrics: Dictionary from calculate_all_metrics()
    
    Returns:
    - Dictionary with executive summary points:
      * overview: Brief summary paragraph
      * key_findings: List of important observations
      * concerns: List of issues requiring attention
      * recommendations: List of actionable suggestions
    """
    
    summary = {
        'key_findings': [],
        'concerns': [],
        'recommendations': []
    }
    
    # Overall dataset overview
    attendance = metrics.get('attendance', {}).get('overall', {})
    location = metrics.get('location', {}).get('totals', {})
    total_sessions = attendance.get('total_sessions', location.get('total_sessions', 'N/A'))
    completion_rate = attendance.get('completion_rate', 0)
    
    summary['overview'] = (
        f"This report analyzes {total_sessions} tutoring sessions, "
        f"with an overall completion rate of {completion_rate:.1f}%. "
        f"The analysis covers booking behavior, student satisfaction, "
        f"tutor performance, and session quality metrics."
    )
    
    # Location breakdown
    if location:
        cord_count = location.get('cord_count', 0)
        cord_pct = location.get('cord_pct', 0)
        zoom_count = location.get('zoom_count', 0)
        zoom_pct = location.get('zoom_pct', 0)
        
        summary['key_findings'].append(
            f"Total Sessions: {total_sessions:,} | In House: {cord_pct:.1f}% (CORD) | Online: {zoom_pct:.1f}% (ZOOM)"
        )
    
    # Attendance and outcomes findings
    if attendance:
        no_show_rate = attendance.get('no_show_rate', 0)
        cancellation_rate = attendance.get('cancellation_rate', 0)
        
        summary['key_findings'].append(
            f"Session outcomes: {completion_rate:.1f}% completed, "
            f"{cancellation_rate:.1f}% cancelled, {no_show_rate:.1f}% no-show"
        )
        
        # Concerns about high no-show or cancellation rates
        if no_show_rate > 15:
            summary['concerns'].append(
                f"High no-show rate ({no_show_rate:.1f}%) - consider reminder system"
            )
        
        if cancellation_rate > 20:
            summary['concerns'].append(
                f"High cancellation rate ({cancellation_rate:.1f}%) - review booking policies"
            )
    
    # Booking behavior findings
    booking = metrics.get('booking', {})
    if booking and 'lead_time_stats' in booking:
        lead_time = booking['lead_time_stats']
        median_days = lead_time.get('median', 0)
        
        summary['key_findings'].append(
            f"Students typically book {median_days:.1f} days in advance (median)"
        )
        
        if median_days < 1:
            summary['recommendations'].append(
                "Students are booking very last minute - consider promoting advance booking"
            )
    
    # Time patterns findings
    time_patterns = metrics.get('time_patterns', {})
    if time_patterns:
        by_day = time_patterns.get('by_day_of_week', {})
        if by_day:
            busiest_day = by_day.get('busiest_day', 'N/A')
            summary['key_findings'].append(f"Busiest day of week: {busiest_day}")
        
        by_hour = time_patterns.get('by_hour', {})
        if by_hour:
            peak_hour = by_hour.get('peak_hour', 'N/A')
            summary['key_findings'].append(f"Peak usage hour: {peak_hour}:00")
    
    # Student satisfaction findings
    satisfaction = metrics.get('satisfaction', {})
    if satisfaction:
        overall_sat = satisfaction.get('satisfaction', {})
        if overall_sat:
            mean_sat = overall_sat.get('mean', 0)
            summary['key_findings'].append(
                f"Overall student satisfaction: {mean_sat:.2f}/7.00"
            )
            
            if mean_sat < 4.0:
                summary['concerns'].append(
                    f"Below-average satisfaction ({mean_sat:.2f}) - investigate session quality"
                )
        
        # Confidence changes
        confidence_change = satisfaction.get('confidence_change', {})
        if confidence_change:
            improved_pct = confidence_change.get('improved_pct', 0)
            summary['key_findings'].append(
                f"{improved_pct:.1f}% of students showed increased confidence after sessions"
            )
            
            if improved_pct < 50:
                summary['recommendations'].append(
                    "Low confidence improvement rate - review session content and tutoring techniques"
                )
        
        # Response rates
        response_rate = overall_sat.get('response_rate', 0) if overall_sat else 0
        if response_rate < 50:
            summary['concerns'].append(
                f"Low survey response rate ({response_rate:.1f}%) - improve student engagement"
            )
    
    # Tutor workload findings
    tutors = metrics.get('tutors', {})
    if tutors:
        workload = tutors.get('balance', {})
        if workload:
            balance_status = workload.get('balance_interpretation', 'unknown')
            cv = workload.get('coefficient_of_variation', 0)
            summary['key_findings'].append(
                f"Tutor workload distribution: {balance_status} (CV: {cv:.1f}%)"
            )
            
            if balance_status == 'highly_unbalanced':
                summary['concerns'].append(
                    f"Highly unbalanced tutor workload - review scheduling practices"
                )
                summary['recommendations'].append(
                    "Implement workload balancing strategies for fair consultant assignment"
                )
    
    # Session length findings
    session_length = metrics.get('session_length', {})
    if session_length:
        overall = session_length.get('overall', {})
        if overall:
            mean_minutes = overall.get('mean_minutes', 0)
            summary['key_findings'].append(
                f"Average session length: {mean_minutes:.1f} minutes"
            )
    
    # Student engagement findings
    students = metrics.get('students', {})
    if students:
        first_time = students.get('first_time_vs_repeat', {})
        if first_time:
            first_time_pct = first_time.get('first_time_pct', 0)
            repeat_pct = first_time.get('repeat_pct', 0)
            summary['key_findings'].append(
                f"Student mix: {first_time_pct:.1f}% first-timers, {repeat_pct:.1f}% repeat visitors"
            )
            
            if first_time_pct < 30:
                summary['recommendations'].append(
                    "Low first-timer rate - consider outreach programs to new students"
                )
    
    # Incentive analysis findings
    incentives = metrics.get('incentives', {})
    if incentives and 'tutor_rating_by_incentive' in incentives:
        incentive_breakdown = incentives.get('incentive_breakdown', {})
        if incentive_breakdown:
            any_incentive_pct = incentive_breakdown.get('any_incentive', {}).get('percentage', 0)
            summary['key_findings'].append(
                f"{any_incentive_pct:.1f}% of sessions were incentivized (extra credit or required)"
            )
        
        tutor_ratings = incentives.get('tutor_rating_by_incentive', {})
        mean_diff = incentives.get('mean_difference', {})
        
        if mean_diff:
            diff = mean_diff.get('incentivized_minus_not_incentivized', 0)
            if abs(diff) > 0.2:  # Meaningful difference
                direction = 'higher' if diff > 0 else 'lower'
                summary['key_findings'].append(
                    f"Incentivized students have {direction} tutor ratings ({diff:+.2f})"
                )
    
    # Semester growth findings
    semesters = metrics.get('semesters', {})
    if semesters:
        growth = semesters.get('growth_rates', {})
        if growth:
            latest_semester = list(growth.keys())[-1] if growth else None
            latest_growth = growth.get(latest_semester, 0)
            
            if latest_growth != 0:
                direction = 'growth' if latest_growth > 0 else 'decline'
                summary['key_findings'].append(
                    f"Latest semester {direction}: {latest_growth:+.1f}%"
                )
                
                if latest_growth < -10:
                    summary['concerns'].append(
                        f"Significant decline in sessions - investigate causes"
                    )
    
    # Remove duplicates while preserving order
    seen = set()
    unique_findings = []
    for finding in summary['key_findings']:
        if finding not in seen:
            seen.add(finding)
            unique_findings.append(finding)
    summary['key_findings'] = unique_findings
    
    # Same for concerns and recommendations
    seen = set()
    unique_concerns = []
    for concern in summary['concerns']:
        if concern not in seen:
            seen.add(concern)
            unique_concerns.append(concern)
    summary['concerns'] = unique_concerns
    
    seen = set()
    unique_recs = []
    for rec in summary['recommendations']:
        if rec not in seen:
            seen.add(rec)
            unique_recs.append(rec)
    summary['recommendations'] = unique_recs
    
    return summary
