# src/visualizations/charts.py

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime
import warnings

warnings.filterwarnings('ignore')

# Set style
sns.set_style("whitegrid")
plt.rcParams['figure.figsize'] = (10, 6)
plt.rcParams['font.size'] = 10
plt.rcParams['axes.titlesize'] = 14
plt.rcParams['axes.labelsize'] = 12

# Color palette (professional, colorblind-friendly)
COLORS = {
    'primary': '#2E86AB',      # Blue
    'secondary': '#A23B72',    # Purple
    'success': '#06A77D',      # Green
    'warning': '#F18F01',      # Orange
    'danger': '#C73E1D',       # Red
    'neutral': '#6C757D',      # Gray
}

PALETTE = [COLORS['primary'], COLORS['secondary'], COLORS['success'], 
           COLORS['warning'], COLORS['danger']]


# ============================================================================
# SECTION 1: EXECUTIVE SUMMARY
# ============================================================================

def create_key_metrics_summary(df, context):
    """
    Chart 1.1: Key metrics text display
    
    Returns dict of key metrics for display in report
    """
    metrics = {}
    
    # Session outcomes
    if 'cancellations' in context:
        ctx = context['cancellations']
        metrics['total_sessions'] = ctx['total_sessions']
        metrics['completion_rate'] = ctx['completion_rate']
        metrics['cancellation_rate'] = ctx['cancellation_rate']
        metrics['no_show_rate'] = ctx['no_show_rate']
    
    # Survey completion
    if 'surveys' in context:
        ctx = context['surveys']
        metrics['pre_survey_rate'] = ctx['pre_survey_completion_rate']
        metrics['post_survey_rate'] = ctx['post_survey_completion_rate']
    
    # Student issues
    if 'student_issues' in context:
        ctx = context['student_issues']
        metrics['issue_rate'] = ctx['issue_rate']
    
    # Average satisfaction (if available)
    if 'Overall_Satisfaction' in df.columns:
        avg_sat = df['Overall_Satisfaction'].mean()
        if not pd.isna(avg_sat):
            metrics['avg_satisfaction'] = round(avg_sat, 2)
    
    # Average confidence change
    if 'Confidence_Change' in df.columns:
        avg_conf = df['Confidence_Change'].mean()
        if not pd.isna(avg_conf):
            metrics['avg_confidence_change'] = round(avg_conf, 2)
    
    # Top 5 power users (most bookings)
    if 'Student_Anon_ID' in df.columns:
        top_users = df['Student_Anon_ID'].value_counts().head(5)
        metrics['power_users'] = top_users.to_dict()
    
    return metrics


def plot_sessions_over_time(df, date_col='Appointment_DateTime'):
    """
    Chart 1.2: Sessions over time (line chart)
    """
    fig, ax = plt.subplots(figsize=(12, 6))
    
    # Group by date
    df_plot = df.copy()
    df_plot['Date'] = df_plot[date_col].dt.date
    daily_counts = df_plot.groupby('Date').size()
    
    # Plot
    ax.plot(daily_counts.index, daily_counts.values, 
            color=COLORS['primary'], linewidth=2, alpha=0.8)
    
    # Add 7-day rolling average
    rolling_avg = daily_counts.rolling(window=7, center=True).mean()
    ax.plot(rolling_avg.index, rolling_avg.values,
            color=COLORS['danger'], linewidth=2, linestyle='--',
            label='7-day average', alpha=0.7)
    
    ax.set_xlabel('Date')
    ax.set_ylabel('Number of Sessions')
    ax.set_title('Daily Session Volume Over Time')
    ax.legend()
    ax.grid(True, alpha=0.3)
    
    plt.xticks(rotation=45)
    plt.tight_layout()
    
    return fig


# ============================================================================
# SECTION 2: BOOKING BEHAVIOR
# ============================================================================

def plot_booking_lead_time_donut(df):
    """
    Chart 2.2: Booking lead time breakdown (donut chart)
    """
    if 'Booking_Lead_Time_Days' not in df.columns:
        return None
    
    # Categorize lead times
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
    
    df_plot = df.copy()
    df_plot['Lead_Time_Category'] = df_plot['Booking_Lead_Time_Days'].apply(categorize_lead_time)
    
    # Count
    category_order = ['Same Day', '1 Day Ahead', '2-3 Days Ahead', 
                     '4-7 Days Ahead', '1-2 Weeks Ahead', 'Unknown']
    counts = df_plot['Lead_Time_Category'].value_counts()
    counts = counts.reindex(category_order, fill_value=0)
    
    # Plot
    fig, ax = plt.subplots(figsize=(8, 8))
    
    wedges, texts, autotexts = ax.pie(counts.values, labels=counts.index,
                                        autopct='%1.1f%%', startangle=90,
                                        colors=PALETTE, pctdistance=0.85)
    
    # Make it a donut
    centre_circle = plt.Circle((0, 0), 0.70, fc='white')
    fig.gca().add_artist(centre_circle)
    
    ax.set_title('When Do Students Book Appointments?', fontsize=14, pad=20)
    
    plt.tight_layout()
    
    return fig


def plot_sessions_by_day_of_week(df, date_col='Appointment_DateTime'):
    """
    Chart 2.3: Sessions by day of week
    """
    df_plot = df.copy()
    df_plot['Day_of_Week'] = df_plot[date_col].dt.day_name()
    
    # Count and order
    day_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    day_counts = df_plot['Day_of_Week'].value_counts().reindex(day_order, fill_value=0)
    
    # Plot
    fig, ax = plt.subplots(figsize=(10, 6))
    
    bars = ax.bar(range(len(day_counts)), day_counts.values, color=COLORS['primary'], alpha=0.8)
    
    ax.set_xticks(range(len(day_counts)))
    ax.set_xticklabels(day_counts.index, rotation=45, ha='right')
    ax.set_ylabel('Number of Sessions')
    ax.set_title('Sessions by Day of Week')
    ax.grid(axis='y', alpha=0.3)
    
    # Add value labels on bars
    for bar in bars:
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2., height,
                f'{int(height):,}',
                ha='center', va='bottom', fontsize=10)
    
    plt.tight_layout()
    
    return fig


def plot_sessions_heatmap_day_time(df, date_col='Appointment_DateTime'):
    """
    Chart 2.4: Sessions by day of week and time of day (heatmap)
    """
    df_plot = df.copy()
    df_plot['Day_of_Week'] = df_plot[date_col].dt.day_name()
    df_plot['Hour'] = df_plot[date_col].dt.hour
    
    # Create pivot table
    day_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']
    heatmap_data = df_plot.groupby(['Day_of_Week', 'Hour']).size().unstack(fill_value=0)
    heatmap_data = heatmap_data.reindex(day_order, fill_value=0)
    
    # Plot
    fig, ax = plt.subplots(figsize=(14, 6))
    
    sns.heatmap(heatmap_data, cmap='YlOrRd', annot=True, fmt='d',
                cbar_kws={'label': 'Number of Sessions'}, ax=ax)
    
    ax.set_xlabel('Hour of Day')
    ax.set_ylabel('Day of Week')
    ax.set_title('Session Volume by Day and Time (Heatmap)')
    
    plt.tight_layout()
    
    return fig


# ============================================================================
# SECTION 3: ATTENDANCE & OUTCOMES
# ============================================================================

def plot_session_outcomes_pie(context):
    """
    Chart 3.1: Session outcomes (pie chart)
    """
    if 'cancellations' not in context:
        return None
    
    ctx = context['cancellations']
    
    labels = ['Attended', 'No-Show', 'Cancelled']
    sizes = [ctx['completed'], ctx['no_show'], ctx['cancelled']]
    colors = [COLORS['success'], COLORS['warning'], COLORS['neutral']]
    
    fig, ax = plt.subplots(figsize=(8, 8))
    
    wedges, texts, autotexts = ax.pie(sizes, labels=labels, autopct='%1.1f%%',
                                        startangle=90, colors=colors,
                                        explode=(0.05, 0, 0))
    
    ax.set_title(f'Session Outcomes (n={ctx["total_sessions"]:,})', fontsize=14, pad=20)
    
    plt.tight_layout()
    
    return fig


def plot_no_show_by_day(df, date_col='Appointment_DateTime'):
    """
    Chart 3.2: No-show rate by day of week
    """
    if 'Attendance_Status' not in df.columns:
        return None
    
    df_plot = df.copy()
    df_plot['Day_of_Week'] = df_plot[date_col].dt.day_name()
    df_plot['Is_No_Show'] = df_plot['Attendance_Status'].str.lower().str.contains('absent', na=False)
    
    # Calculate no-show rate by day
    day_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']
    
    no_show_rates = []
    for day in day_order:
        day_data = df_plot[df_plot['Day_of_Week'] == day]
        if len(day_data) > 0:
            rate = (day_data['Is_No_Show'].sum() / len(day_data)) * 100
        else:
            rate = 0
        no_show_rates.append(rate)
    
    # Plot
    fig, ax = plt.subplots(figsize=(10, 6))
    
    bars = ax.bar(range(len(day_order)), no_show_rates, color=COLORS['warning'], alpha=0.8)
    
    ax.set_xticks(range(len(day_order)))
    ax.set_xticklabels(day_order, rotation=45, ha='right')
    ax.set_ylabel('No-Show Rate (%)')
    ax.set_title('No-Show Rate by Day of Week')
    ax.grid(axis='y', alpha=0.3)
    ax.set_ylim(0, max(no_show_rates) * 1.2 if no_show_rates else 10)
    
    # Add value labels
    for i, (bar, rate) in enumerate(zip(bars, no_show_rates)):
        ax.text(bar.get_x() + bar.get_width()/2., rate,
                f'{rate:.1f}%',
                ha='center', va='bottom', fontsize=10)
    
    plt.tight_layout()
    
    return fig


def plot_outcomes_over_time(df, date_col='Appointment_DateTime'):
    """
    Chart 3.4: No-show and cancellation trends over time
    """
    if 'Semester_Label' not in df.columns:
        return None
    
    df_plot = df.copy()
    df_plot['Is_No_Show'] = df_plot.get('Attendance_Status', pd.Series()).str.lower().str.contains('absent', na=False)
    df_plot['Is_Cancelled'] = df_plot.get('Status', pd.Series()).str.lower().str.contains('cancel', na=False)
    
    # Group by semester
    semester_stats = df_plot.groupby('Semester_Label').agg({
        'Is_No_Show': lambda x: (x.sum() / len(x)) * 100,
        'Is_Cancelled': lambda x: (x.sum() / len(x)) * 100
    })
    
    # Plot
    fig, ax = plt.subplots(figsize=(12, 6))
    
    x = range(len(semester_stats))
    ax.plot(x, semester_stats['Is_No_Show'].values, marker='o', 
            color=COLORS['warning'], linewidth=2, label='No-Show Rate', markersize=8)
    ax.plot(x, semester_stats['Is_Cancelled'].values, marker='s',
            color=COLORS['neutral'], linewidth=2, label='Cancellation Rate', markersize=8)
    
    ax.set_xticks(x)
    ax.set_xticklabels(semester_stats.index, rotation=45, ha='right')
    ax.set_ylabel('Rate (%)')
    ax.set_title('No-Show and Cancellation Trends by Semester')
    ax.legend()
    ax.grid(True, alpha=0.3)
    
    plt.tight_layout()
    
    return fig


# ============================================================================
# SECTION 4: STUDENT SATISFACTION
# ============================================================================

def plot_confidence_comparison(df):
    """
    Chart 4.1: Pre vs Post confidence comparison (box plot)
    """
    if 'Pre_Confidence' not in df.columns or 'Post_Confidence' not in df.columns:
        return None
    
    # Prepare data
    pre_conf = df['Pre_Confidence'].dropna()
    post_conf = df['Post_Confidence'].dropna()
    
    if len(pre_conf) == 0 and len(post_conf) == 0:
        return None
    
    # Create dataframe for seaborn
    data_list = []
    for val in pre_conf:
        data_list.append({'Type': 'Pre-Session', 'Confidence': val})
    for val in post_conf:
        data_list.append({'Type': 'Post-Session', 'Confidence': val})
    
    plot_df = pd.DataFrame(data_list)
    
    # Plot
    fig, ax = plt.subplots(figsize=(10, 6))
    
    sns.boxplot(data=plot_df, x='Type', y='Confidence', palette=[COLORS['danger'], COLORS['success']], ax=ax)
    sns.stripplot(data=plot_df, x='Type', y='Confidence', color='black', alpha=0.2, size=3, ax=ax)
    
    ax.set_ylabel('Confidence Score (1-5)')
    ax.set_xlabel('')
    ax.set_title('Student Confidence: Before vs After Session')
    ax.grid(axis='y', alpha=0.3)
    
    # Add mean values
    pre_mean = pre_conf.mean()
    post_mean = post_conf.mean()
    ax.text(0, pre_mean, f'Mean: {pre_mean:.2f}', ha='right', va='center', fontsize=10, color='red')
    ax.text(1, post_mean, f'Mean: {post_mean:.2f}', ha='left', va='center', fontsize=10, color='green')
    
    plt.tight_layout()
    
    return fig


def plot_confidence_change_distribution(df):
    """
    Chart 4.2: Confidence change distribution (histogram)
    """
    if 'Confidence_Change' not in df.columns:
        return None
    
    changes = df['Confidence_Change'].dropna()
    
    if len(changes) == 0:
        return None
    
    # Plot
    fig, ax = plt.subplots(figsize=(10, 6))
    
    ax.hist(changes, bins=range(-5, 6), color=COLORS['primary'], alpha=0.7, edgecolor='black')
    
    # Add vertical line at 0 (no change)
    ax.axvline(x=0, color='red', linestyle='--', linewidth=2, label='No Change')
    
    # Add mean line
    mean_change = changes.mean()
    ax.axvline(x=mean_change, color='green', linestyle='-', linewidth=2, label=f'Mean: {mean_change:.2f}')
    
    ax.set_xlabel('Change in Confidence (Post - Pre)')
    ax.set_ylabel('Number of Students')
    ax.set_title('How Much Does Confidence Improve?')
    ax.legend()
    ax.grid(axis='y', alpha=0.3)
    
    plt.tight_layout()
    
    return fig


def plot_satisfaction_distribution(df):
    """
    Chart 4.3: Overall satisfaction distribution (bar chart)
    """
    if 'Overall_Satisfaction' not in df.columns:
        return None
    
    satisfaction = df['Overall_Satisfaction'].dropna()
    
    if len(satisfaction) == 0:
        return None
    
    # Count each score
    counts = satisfaction.value_counts().sort_index()
    
    # Plot
    fig, ax = plt.subplots(figsize=(10, 6))
    
    bars = ax.bar(counts.index, counts.values, color=COLORS['success'], alpha=0.8, edgecolor='black')
    
    ax.set_xlabel('Satisfaction Score (1=Extremely Dissatisfied, 7=Extremely Satisfied)')
    ax.set_ylabel('Number of Responses')
    ax.set_title(f'Overall Satisfaction Distribution (Mean: {satisfaction.mean():.2f})')
    ax.set_xticks(range(1, 8))
    ax.grid(axis='y', alpha=0.3)
    
    # Add value labels
    for bar in bars:
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2., height,
                f'{int(height)}',
                ha='center', va='bottom', fontsize=10)
    
    plt.tight_layout()
    
    return fig


def plot_satisfaction_trends(df):
    """
    Chart 4.4: Satisfaction trends over time (line chart with confidence interval)
    """
    if 'Overall_Satisfaction' not in df.columns or 'Semester_Label' not in df.columns:
        return None
    
    # Group by semester
    semester_stats = df.groupby('Semester_Label')['Overall_Satisfaction'].agg(['mean', 'std', 'count'])
    semester_stats = semester_stats.dropna()
    
    if len(semester_stats) == 0:
        return None
    
    # Calculate standard error
    semester_stats['se'] = semester_stats['std'] / np.sqrt(semester_stats['count'])
    
    # Plot
    fig, ax = plt.subplots(figsize=(12, 6))
    
    x = range(len(semester_stats))
    ax.plot(x, semester_stats['mean'].values, marker='o', color=COLORS['success'],
            linewidth=2, markersize=8, label='Mean Satisfaction')
    
    # Add error bars (95% CI)
    ax.errorbar(x, semester_stats['mean'].values, yerr=1.96*semester_stats['se'].values,
                fmt='none', color=COLORS['success'], alpha=0.3, capsize=5)
    
    ax.set_xticks(x)
    ax.set_xticklabels(semester_stats.index, rotation=45, ha='right')
    ax.set_ylabel('Average Satisfaction (1-7)')
    ax.set_title('Satisfaction Trends Over Time (with 95% CI)')
    ax.set_ylim(1, 7)
    ax.grid(True, alpha=0.3)
    ax.legend()
    
    plt.tight_layout()
    
    return fig


# ============================================================================
# SECTION 5: TUTOR ANALYTICS
# ============================================================================

def plot_sessions_per_tutor(df):
    """
    Chart 5.1: Sessions per tutor (horizontal bar chart)
    """
    if 'Tutor_Anon_ID' not in df.columns:
        return None
    
    tutor_counts = df['Tutor_Anon_ID'].value_counts().head(20)  # Top 20 tutors
    
    # Plot
    fig, ax = plt.subplots(figsize=(10, 8))
    
    y_pos = range(len(tutor_counts))
    ax.barh(y_pos, tutor_counts.values, color=COLORS['primary'], alpha=0.8)
    
    ax.set_yticks(y_pos)
    ax.set_yticklabels(tutor_counts.index)
    ax.set_xlabel('Number of Sessions')
    ax.set_title('Sessions per Tutor (Top 20)')
    ax.grid(axis='x', alpha=0.3)
    
    # Add value labels
    for i, (idx, val) in enumerate(tutor_counts.items()):
        ax.text(val, i, f' {val}', va='center', fontsize=9)
    
    plt.tight_layout()
    
    return fig


def plot_tutor_workload_balance(df):
    """
    Chart 5.2: Tutor workload distribution (box plot)
    """
    if 'Tutor_Anon_ID' not in df.columns:
        return None
    
    tutor_counts = df['Tutor_Anon_ID'].value_counts()
    
    # Plot
    fig, ax = plt.subplots(figsize=(10, 6))
    
    ax.boxplot([tutor_counts.values], vert=False, widths=0.5, patch_artist=True,
                boxprops=dict(facecolor=COLORS['primary'], alpha=0.7))
    
    ax.set_xlabel('Sessions per Tutor')
    ax.set_title('Tutor Workload Distribution')
    ax.set_yticks([])
    ax.grid(axis='x', alpha=0.3)
    
    # Add statistics
    stats_text = f"Mean: {tutor_counts.mean():.1f} | Median: {tutor_counts.median():.0f} | Max: {tutor_counts.max()}"
    ax.text(0.5, -0.15, stats_text, transform=ax.transAxes, ha='center', fontsize=10)
    
    plt.tight_layout()
    
    return fig


def plot_session_length_by_tutor(df):
    """
    Chart 5.3: Average session length by tutor (top 10)
    """
    if 'Tutor_Anon_ID' not in df.columns or 'Actual_Session_Length' not in df.columns:
        return None
    
    # Get top 10 tutors by session count
    top_tutors = df['Tutor_Anon_ID'].value_counts().head(10).index
    
    tutor_stats = df[df['Tutor_Anon_ID'].isin(top_tutors)].groupby('Tutor_Anon_ID')['Actual_Session_Length'].agg(['mean', 'std'])
    tutor_stats = tutor_stats.sort_values('mean', ascending=False)
    
    # Plot
    fig, ax = plt.subplots(figsize=(10, 6))
    
    x = range(len(tutor_stats))
    ax.bar(x, tutor_stats['mean'].values * 60, color=COLORS['secondary'], alpha=0.8, 
           yerr=tutor_stats['std'].values * 60, capsize=5, error_kw={'alpha': 0.5})
    
    ax.set_xticks(x)
    ax.set_xticklabels(tutor_stats.index, rotation=45, ha='right')
    ax.set_ylabel('Average Session Length (minutes)')
    ax.set_title('Average Session Length by Tutor (Top 10 by Volume)')
    ax.axhline(y=40, color='red', linestyle='--', linewidth=1, label='Standard 40 min', alpha=0.7)
    ax.grid(axis='y', alpha=0.3)
    ax.legend()
    
    plt.tight_layout()
    
    return fig


# ============================================================================
# SECTION 6: SESSION CONTENT
# ============================================================================

def plot_writing_stages(df):
    """
    Chart 6.1: Top writing stages (bar chart)
    """
    if 'Writing_Stage' not in df.columns:
        return None
    
    stages = df['Writing_Stage'].value_counts().head(10)
    
    if len(stages) == 0:
        return None
    
    # Plot
    fig, ax = plt.subplots(figsize=(10, 6))
    
    ax.barh(range(len(stages)), stages.values, color=COLORS['primary'], alpha=0.8)
    
    ax.set_yticks(range(len(stages)))
    ax.set_yticklabels(stages.index)
    ax.set_xlabel('Number of Sessions')
    ax.set_title('Most Common Writing Stages')
    ax.grid(axis='x', alpha=0.3)
    
    # Add value labels
    for i, val in enumerate(stages.values):
        ax.text(val, i, f' {val}', va='center', fontsize=9)
    
    plt.tight_layout()
    
    return fig


def plot_focus_areas(df):
    """
    Chart 6.2: Top focus areas (bar chart)
    """
    if 'Focus_Area' not in df.columns:
        return None
    
    # This might be messy - let's try it and see
    focus = df['Focus_Area'].dropna()
    
    if len(focus) == 0:
        return None
    
    focus_counts = focus.value_counts().head(15)
    
    # Plot
    fig, ax = plt.subplots(figsize=(12, 8))
    
    ax.barh(range(len(focus_counts)), focus_counts.values, color=COLORS['secondary'], alpha=0.8)
    
    ax.set_yticks(range(len(focus_counts)))
    ax.set_yticklabels(focus_counts.index, fontsize=9)
    ax.set_xlabel('Number of Sessions')
    ax.set_title('Top Focus Areas (Student Requests)')
    ax.grid(axis='x', alpha=0.3)
    
    plt.tight_layout()
    
    return fig


def plot_first_time_vs_returning(df):
    """
    Chart 6.3: First-time vs returning students
    """
    if 'Is_First_Timer' not in df.columns:
        return None
    
    # Count
    first_time = df['Is_First_Timer'].sum()
    returning = (~df['Is_First_Timer']).sum() - df['Is_First_Timer'].isna().sum()
    
    # Plot
    fig, ax = plt.subplots(figsize=(8, 8))
    
    labels = ['Returning Students', 'First-Time Students']
    sizes = [returning, first_time]
    colors = [COLORS['primary'], COLORS['success']]
    
    wedges, texts, autotexts = ax.pie(sizes, labels=labels, autopct='%1.1f%%',
                                        startangle=90, colors=colors)
    
    ax.set_title(f'First-Time vs Returning Students (n={first_time + returning:,})', fontsize=14, pad=20)
    
    plt.tight_layout()
    
    return fig


# ============================================================================
# SECTION 7: SEMESTER COMPARISONS
# ============================================================================

def plot_semester_growth(df):
    """
    Chart 7.1: Semester-over-semester growth (line chart)
    """
    if 'Semester_Label' not in df.columns:
        return None
    
    semester_counts = df['Semester_Label'].value_counts().sort_index()
    
    # Only plot if we have multiple semesters
    if len(semester_counts) < 2:
        return None
    
    # Plot
    fig, ax = plt.subplots(figsize=(12, 6))
    
    x = range(len(semester_counts))
    ax.plot(x, semester_counts.values, marker='o', color=COLORS['primary'],
            linewidth=3, markersize=10)
    
    ax.set_xticks(x)
    ax.set_xticklabels(semester_counts.index, rotation=45, ha='right')
    ax.set_ylabel('Total Sessions')
    ax.set_title('Session Volume: Semester-over-Semester Growth')
    ax.grid(True, alpha=0.3)
    
    # Add value labels
    for i, val in enumerate(semester_counts.values):
        ax.text(i, val, f'{val:,}', ha='center', va='bottom', fontsize=10)
    
    plt.tight_layout()
    
    return fig


def plot_semester_metrics_comparison(df, context):
    """
    Chart 7.2: Small multiples - key metrics by semester
    """
    if 'Semester_Label' not in df.columns:
        return None
    
    semesters = df['Semester_Label'].unique()
    
    # Only plot if we have multiple semesters
    if len(semesters) < 2:
        return None
    
    # Create 2x2 subplot
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    fig.suptitle('Key Metrics Comparison by Semester', fontsize=16, y=1.00)
    
    # Metric 1: Attendance Rate
    df_plot = df.copy()
    df_plot['Attended'] = df_plot.get('Attendance_Status', pd.Series()).str.lower().str.contains('present', na=False)
    attendance = df_plot.groupby('Semester_Label')['Attended'].apply(lambda x: (x.sum() / len(x)) * 100)
    
    axes[0, 0].bar(range(len(attendance)), attendance.values, color=COLORS['success'], alpha=0.8)
    axes[0, 0].set_xticks(range(len(attendance)))
    axes[0, 0].set_xticklabels(attendance.index, rotation=45, ha='right', fontsize=9)
    axes[0, 0].set_ylabel('Attendance Rate (%)')
    axes[0, 0].set_title('Attendance Rate')
    axes[0, 0].grid(axis='y', alpha=0.3)
    
    # Metric 2: Average Booking Lead Time
    lead_time = df.groupby('Semester_Label')['Booking_Lead_Time_Days'].mean()
    
    axes[0, 1].bar(range(len(lead_time)), lead_time.values, color=COLORS['warning'], alpha=0.8)
    axes[0, 1].set_xticks(range(len(lead_time)))
    axes[0, 1].set_xticklabels(lead_time.index, rotation=45, ha='right', fontsize=9)
    axes[0, 1].set_ylabel('Days in Advance')
    axes[0, 1].set_title('Avg Booking Lead Time')
    axes[0, 1].grid(axis='y', alpha=0.3)
    
    # Metric 3: Average Session Length
    session_len = df.groupby('Semester_Label')['Actual_Session_Length'].mean() * 60
    
    axes[1, 0].bar(range(len(session_len)), session_len.values, color=COLORS['primary'], alpha=0.8)
    axes[1, 0].set_xticks(range(len(session_len)))
    axes[1, 0].set_xticklabels(session_len.index, rotation=45, ha='right', fontsize=9)
    axes[1, 0].set_ylabel('Minutes')
    axes[1, 0].set_title('Avg Session Length')
    axes[1, 0].axhline(y=40, color='red', linestyle='--', linewidth=1, alpha=0.7)
    axes[1, 0].grid(axis='y', alpha=0.3)
    
    # Metric 4: Average Satisfaction (if available)
    if 'Overall_Satisfaction' in df.columns:
        satisfaction = df.groupby('Semester_Label')['Overall_Satisfaction'].mean()
        
        axes[1, 1].bar(range(len(satisfaction)), satisfaction.values, color=COLORS['success'], alpha=0.8)
        axes[1, 1].set_xticks(range(len(satisfaction)))
        axes[1, 1].set_xticklabels(satisfaction.index, rotation=45, ha='right', fontsize=9)
        axes[1, 1].set_ylabel('Score (1-7)')
        axes[1, 1].set_title('Avg Satisfaction')
        axes[1, 1].set_ylim(1, 7)
        axes[1, 1].grid(axis='y', alpha=0.3)
    else:
        # If no satisfaction data, show confidence change
        if 'Confidence_Change' in df.columns:
            conf_change = df.groupby('Semester_Label')['Confidence_Change'].mean()
            
            axes[1, 1].bar(range(len(conf_change)), conf_change.values, color=COLORS['secondary'], alpha=0.8)
            axes[1, 1].set_xticks(range(len(conf_change)))
            axes[1, 1].set_xticklabels(conf_change.index, rotation=45, ha='right', fontsize=9)
            axes[1, 1].set_ylabel('Change in Confidence')
            axes[1, 1].set_title('Avg Confidence Improvement')
            axes[1, 1].axhline(y=0, color='red', linestyle='--', linewidth=1, alpha=0.7)
            axes[1, 1].grid(axis='y', alpha=0.3)
    
    plt.tight_layout()
    
    return fig


# ============================================================================
# SECTION 8: DATA QUALITY
# ============================================================================

def plot_survey_response_rates(context):
    """
    Chart 8.1: Survey response rates (bar chart)
    """
    if 'surveys' not in context:
        return None
    
    ctx = context['surveys']
    
    labels = ['Pre-Survey', 'Post-Survey', 'Both Completed']
    rates = [ctx['pre_survey_completion_rate'], 
             ctx['post_survey_completion_rate'],
             ctx['both_surveys_completion_rate']]
    
    # Plot
    fig, ax = plt.subplots(figsize=(10, 6))
    
    bars = ax.bar(range(len(labels)), rates, color=COLORS['primary'], alpha=0.8)
    
    ax.set_xticks(range(len(labels)))
    ax.set_xticklabels(labels)
    ax.set_ylabel('Completion Rate (%)')
    ax.set_title('Survey Completion Rates')
    ax.set_ylim(0, 100)
    ax.grid(axis='y', alpha=0.3)
    
    # Add value labels
    for bar, rate in zip(bars, rates):
        ax.text(bar.get_x() + bar.get_width()/2., rate,
                f'{rate:.1f}%',
                ha='center', va='bottom', fontsize=11, fontweight='bold')
    
    plt.tight_layout()
    
    return fig


def plot_missing_data_concern(missing_report):
    """
    Chart 8.2: Missing data by column (only concerning columns)
    """
    # Filter to only concerning missing data (>20% and category is 'concerning')
    concerning = {k: v for k, v in missing_report.items() 
                  if v.get('category') == 'concerning' and v['percentage'] > 20}
    
    if not concerning:
        return None
    
    # Sort by percentage
    sorted_items = sorted(concerning.items(), key=lambda x: x[1]['percentage'], reverse=True)
    columns = [item[0] for item in sorted_items]
    percentages = [item[1]['percentage'] for item in sorted_items]
    
    # Plot
    fig, ax = plt.subplots(figsize=(10, 8))
    
    y_pos = range(len(columns))
    bars = ax.barh(y_pos, percentages, color=COLORS['warning'], alpha=0.8)
    
    ax.set_yticks(y_pos)
    ax.set_yticklabels(columns, fontsize=9)
    ax.set_xlabel('Missing Data (%)')
    ax.set_title('Data Quality Concerns (Missing Values >20%)')
    ax.grid(axis='x', alpha=0.3)
    
    # Add value labels
    for i, pct in enumerate(percentages):
        ax.text(pct, i, f' {pct:.1f}%', va='center', fontsize=9)
    
    plt.tight_layout()
    
    return fig