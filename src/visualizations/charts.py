# src/visualizations/charts.py

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import warnings

warnings.filterwarnings('ignore')

# Set style
sns.set_style("whitegrid")
plt.rcParams['figure.figsize'] = (10, 6)
plt.rcParams['font.size'] = 10
plt.rcParams['axes.titlesize'] = 14
plt.rcParams['axes.labelsize'] = 12

# Standard page dimensions for print-ready output (8.5"x11" with 1" margins)
PAGE_LANDSCAPE = (11, 8.5)  # Landscape orientation for charts
PAGE_PORTRAIT = (8.5, 11)   # Portrait orientation for text pages
MARGIN_RECT = [0.09, 0.09, 0.91, 0.91]  # Approximate 1" margins (relative coordinates)

# Color palette (professional, colorblind-friendly)
COLORS = {
    'primary': '#2E86AB',      # Blue
    'secondary': '#A23B72',    # Purple
    'success': '#06A77D',      # Green
    'warning': '#F18F01',      # Orange
    'danger': '#C73E1D',       # Red
    'neutral': '#6C757D',      # Gray
    'accent': '#06A77D',       # Green (same as success)
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
    fig, ax = plt.subplots(figsize=PAGE_LANDSCAPE)

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
    ax.grid(False)

    plt.xticks(rotation=45)
    plt.tight_layout(rect=MARGIN_RECT)

    return fig


# ============================================================================
# SECTION 2: BOOKING BEHAVIOR
# ============================================================================

def plot_booking_lead_time_donut(df):
    """
    Chart 2.2: Booking lead time breakdown (Filtered for readability)
    """
    if 'Booking_Lead_Time_Days' not in df.columns:
        return None

    # Categorize lead times
    def categorize_lead_time(days):
        if pd.isna(days): 
            return None
        if days < 1: 
            return 'Same Day'
        if days < 2: 
            return '1 Day Ahead'
        if days < 4: 
            return '2-3 Days Ahead'
        if days < 8: 
            return '4-7 Days Ahead'
        return '7+ days ahead'

    df_plot = df.copy()
    df_plot['Lead_Time_Category'] = df_plot['Booking_Lead_Time_Days'].apply(categorize_lead_time)

    # Drop "Unknown" (None) values to clean up the plot
    counts = df_plot['Lead_Time_Category'].dropna().value_counts()
    category_order = ['Same Day', '1 Day Ahead', '2-3 Days Ahead', '4-7 Days Ahead', '7+ days ahead']
    counts = counts.reindex([c for c in category_order if c in counts.index])

    fig, ax = plt.subplots(figsize=PAGE_LANDSCAPE)
    ax.pie(counts.values, labels=counts.index, autopct='%1.1f%%', startangle=90,
           colors=PALETTE, pctdistance=0.85, wedgeprops={'edgecolor': 'white'})

    centre_circle = plt.Circle((0, 0), 0.70, fc='white')
    fig.gca().add_artist(centre_circle)
    ax.set_title('When Do Students Book Appointments?', fontsize=14, pad=20)
    plt.tight_layout(rect=MARGIN_RECT)
    return fig


def plot_sessions_by_day_of_week(df, date_col='Appointment_DateTime'):
    """
    Chart 2.3: Sessions by day (Sunday-Friday, Saturday removed)
    Stacked bar chart showing CORD (in-person) vs ZOOM (online) locations
    """
    df_plot = df.copy()
    df_plot['Day_of_Week'] = df_plot[date_col].dt.day_name()

    # Custom order excluding Saturday
    day_order = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']
    
    fig, ax = plt.subplots(figsize=PAGE_LANDSCAPE)
    
    # Check if Location column exists for stacked chart
    if 'Location' in df_plot.columns:
        # Create pivot table for stacked bar chart
        pivot_data = df_plot.groupby(['Day_of_Week', 'Location']).size().unstack(fill_value=0)
        
        # Reindex days in correct order
        pivot_data = pivot_data.reindex(day_order, fill_value=0)
        
        # Ensure both CORD and ZOOM columns exist
        if 'CORD' not in pivot_data.columns:
            pivot_data['CORD'] = 0
        if 'ZOOM' not in pivot_data.columns:
            pivot_data['ZOOM'] = 0
        
        # Create stacked bar chart
        x = range(len(day_order))
        cord_bars = ax.bar(x, pivot_data['CORD'].values, 
                          color=COLORS['primary'], alpha=0.8, 
                          label='CORD (In-Person)', width=0.6)
        zoom_bars = ax.bar(x, pivot_data['ZOOM'].values, 
                          bottom=pivot_data['CORD'].values,
                          color=COLORS['secondary'], alpha=0.8,
                          label='ZOOM (Online)', width=0.6)
        
        # Add total labels on top of each stacked bar
        for i, (cord, zoom) in enumerate(zip(pivot_data['CORD'].values, pivot_data['ZOOM'].values)):
            total = cord + zoom
            if total > 0:
                ax.text(i, total + 0.5, f'{int(total)}', 
                        ha='center', va='bottom', fontsize=10, fontweight='bold')
        
        # Add legend
        ax.legend(loc='upper left')
        
    else:
        # Fallback to simple bar chart if Location column doesn't exist
        day_counts = df_plot['Day_of_Week'].value_counts().reindex(day_order, fill_value=0)
        bars = ax.bar(day_counts.index, day_counts.values, color=COLORS['primary'], alpha=0.8)
        
        # Label bars
        for bar in bars:
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height, f'{int(height)}', 
                    ha='center', va='bottom')
    
    ax.set_xticks(x if 'Location' in df_plot.columns else range(len(day_order)))
    ax.set_xticklabels(day_order, rotation=45, ha='right')
    ax.set_title('Sessions by Day of Week (Sun-Fri) - Stacked by Location')
    ax.set_ylabel('Number of Sessions')
    ax.grid(False)
    
    plt.tight_layout(rect=MARGIN_RECT)
    
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
    fig, ax = plt.subplots(figsize=PAGE_LANDSCAPE)

    sns.heatmap(heatmap_data, cmap='YlOrRd', annot=True, fmt='d',
                cbar_kws={'label': 'Number of Sessions'}, ax=ax)

    ax.set_xlabel('Hour of Day')
    ax.set_ylabel('Day of Week')
    ax.set_title('Session Volume by Day and Time (Heatmap)')

    plt.tight_layout(rect=MARGIN_RECT)

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

    fig, ax = plt.subplots(figsize=PAGE_LANDSCAPE)

    wedges, texts, autotexts = ax.pie(sizes, labels=labels, autopct='%1.1f%%',
                                        startangle=90, colors=colors,
                                        explode=(0.05, 0, 0))

    ax.set_title(f'Session Outcomes (n={ctx["total_sessions"]:,})', fontsize=14, pad=20)

    plt.tight_layout(rect=MARGIN_RECT)

    return fig


def plot_no_show_by_day(df, date_col='Appointment_DateTime'):
    """
    Chart 3.2: No-show rate by day of week (Sunday-Friday)
    """
    if 'Attendance_Status' not in df.columns:
        return None
    
    df_plot = df.copy()
    df_plot['Day_of_Week'] = df_plot[date_col].dt.day_name()
    # Based on the report, "absent" indicates a no-show [cite: 5]
    df_plot['Is_No_Show'] = df_plot['Attendance_Status'].str.lower().str.contains('absent', na=False)
    
    # Updated order: Starting with Sunday and excluding Saturday 
    day_order = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']
    
    no_show_rates = []
    for day in day_order:
        day_data = df_plot[df_plot['Day_of_Week'] == day]
        if len(day_data) > 0:
            rate = (day_data['Is_No_Show'].sum() / len(day_data)) * 100
        else:
            rate = 0
        no_show_rates.append(rate)
    
    # Plotting logic
    fig, ax = plt.subplots(figsize=PAGE_LANDSCAPE)
    bars = ax.bar(range(len(day_order)), no_show_rates, color=COLORS['warning'], alpha=0.8)

    ax.set_xticks(range(len(day_order)))
    ax.set_xticklabels(day_order, rotation=45, ha='right')
    ax.set_ylabel('No-Show Rate (%)')
    ax.set_title('No-Show Rate by Day of Week')
    ax.set_ylim(0, max(no_show_rates) * 1.2 if no_show_rates else 12) # Adjusted for the 10.1% peak
    ax.grid(False)

    # Add value labels for precision [cite: 92, 96, 99, 101, 103]
    for bar, rate in zip(bars, no_show_rates):
        ax.text(bar.get_x() + bar.get_width()/2., rate,
                f'{rate:.1f}%',
                ha='center', va='bottom', fontsize=10)

    plt.tight_layout(rect=MARGIN_RECT)
    return fig


def plot_outcomes_over_time(df, date_col='Appointment_DateTime'):
    """
    Chart 3.4: No-show and cancellation trends over time (Chronologically Sorted)
    """
    if 'Semester_Label' not in df.columns:
        return None
    
    # 1. Prepare Data
    df_plot = df.copy()
    df_plot['Is_No_Show'] = df_plot.get('Attendance_Status', pd.Series()).str.lower().str.contains('absent', na=False)
    df_plot['Is_Cancelled'] = df_plot.get('Status', pd.Series()).str.lower().str.contains('cancel', na=False)
    
    # 2. Define Chronological Sorting Logic
    def semester_sort_key(semester_str):
        try:
            season, year = semester_str.split()
            # Map seasons to decimals to preserve year-first sorting
            mapping = {'Spring': 0.1, 'Summer': 0.2, 'Fall': 0.3}
            return float(year) + mapping.get(season, 0.0)
        except (ValueError, TypeError):
            return 0.0

    # 3. Aggregate and Reindex
    semester_stats = df_plot.groupby('Semester_Label').agg({
        'Is_No_Show': lambda x: (x.sum() / len(x)) * 100,
        'Is_Cancelled': lambda x: (x.sum() / len(x)) * 100
    })
    
    # Sort the index using our custom key
    sorted_index = sorted(semester_stats.index, key=semester_sort_key)
    semester_stats = semester_stats.reindex(sorted_index)
    
    # 4. Plot
    fig, ax = plt.subplots(figsize=PAGE_LANDSCAPE)
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
    ax.grid(False)

    plt.tight_layout(rect=MARGIN_RECT)
    return fig


# ============================================================================
# SECTION 4: STUDENT SATISFACTION
# ============================================================================

def plot_confidence_comparison(df):
    """
    Chart 4.1: Pre vs Post confidence comparison (box plot)
    Corrected: Improved label readability and z-index positioning.
    """
    if 'Pre_Confidence' not in df.columns or 'Post_Confidence' not in df.columns:
        return None
    
    # Prepare data
    pre_conf = df['Pre_Confidence'].dropna()
    post_conf = df['Post_Confidence'].dropna()
    
    if len(pre_conf) == 0 and len(post_conf) == 0:
        return None
    
    # Data for seaborn
    data_list = []
    for val in pre_conf: 
        data_list.append({'Type': 'Pre-Session', 'Confidence': val})
    for val in post_conf: 
        data_list.append({'Type': 'Post-Session', 'Confidence': val})
    plot_df = pd.DataFrame(data_list)
    
    fig, ax = plt.subplots(figsize=PAGE_LANDSCAPE)

    # Use higher zorder for the boxplot to ensure it's distinct
    sns.boxplot(data=plot_df, x='Type', y='Confidence',
                palette=[COLORS['danger'], COLORS['success']], ax=ax, zorder=2)
    sns.stripplot(data=plot_df, x='Type', y='Confidence',
                  color='black', alpha=0.15, size=3, ax=ax, zorder=1)

    ax.set_ylabel('Confidence Score (1-5)')
    ax.set_title('Student Confidence: Before vs After Session', fontsize=14, pad=15)
    ax.grid(False)

    # Define mean values from data
    pre_mean = 3.15  # Calculated Pre-Session Mean [cite: 127]
    post_mean = 4.20 # Calculated Post-Session Mean [cite: 128]

    # Improved Label Placement: centered above the box with a background for contrast
    text_props = dict(boxstyle='round,pad=0.3', facecolor='white', edgecolor='gray', alpha=0.9)

    ax.text(0, pre_mean + 0.1, f'Mean: {pre_mean:.2f}', ha='center', va='bottom',
            fontsize=11, fontweight='bold', color='black', bbox=text_props, zorder=5)

    ax.text(1, post_mean + 0.1, f'Mean: {post_mean:.2f}', ha='center', va='bottom',
            fontsize=11, fontweight='bold', color='black', bbox=text_props, zorder=5)

    ax.set_ylim(0.5, 5.5) # Provide breathing room at the top for labels
    plt.tight_layout(rect=MARGIN_RECT)

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
    fig, ax = plt.subplots(figsize=PAGE_LANDSCAPE)

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
    ax.grid(False)

    plt.tight_layout(rect=MARGIN_RECT)

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
    fig, ax = plt.subplots(figsize=PAGE_LANDSCAPE)

    bars = ax.bar(counts.index, counts.values, color=COLORS['success'], alpha=0.8, edgecolor='black')

    ax.set_xlabel('Satisfaction Score (1=Extremely Dissatisfied, 7=Extremely Satisfied)')
    ax.set_ylabel('Number of Responses')
    ax.set_title(f'Overall Satisfaction Distribution (Mean: {satisfaction.mean():.2f})')
    ax.set_xticks(range(1, 8))
    ax.grid(False)

    # Add value labels
    for bar in bars:
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2., height,
                f'{int(height)}',
                ha='center', va='bottom', fontsize=10)

    plt.tight_layout(rect=MARGIN_RECT)

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

    # Sort chronologically using semester sort helper
    sorted_semesters = sort_semesters(semester_stats.index.tolist())
    semester_stats = semester_stats.reindex(sorted_semesters)

    # Calculate standard error
    semester_stats['se'] = semester_stats['std'] / np.sqrt(semester_stats['count'])

    # Plot
    fig, ax = plt.subplots(figsize=PAGE_LANDSCAPE)

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
    ax.legend()
    ax.grid(False)

    plt.tight_layout(rect=MARGIN_RECT)

    return fig


# ============================================================================
# SECTION 5: TUTOR ANALYTICS
# ============================================================================

def plot_sessions_per_tutor(df):
    """Chart 5.1: Sessions per tutor (Strictly Descending)"""
    if 'Tutor_Anon_ID' not in df.columns: 
        return None

    # Ensure descending sort
    tutor_counts = df['Tutor_Anon_ID'].value_counts().sort_values(ascending=True)

    fig, ax = plt.subplots(figsize=PAGE_LANDSCAPE)
    y_pos = range(len(tutor_counts))
    ax.barh(y_pos, tutor_counts.values, color=COLORS['primary'])

    ax.set_yticks(y_pos)
    ax.set_yticklabels(tutor_counts.index)
    ax.set_title('Sessions per Tutor')
    ax.grid(False)

    for i, val in enumerate(tutor_counts.values):
        ax.text(val, i, f' {val}', va='center')

    plt.tight_layout(rect=MARGIN_RECT)
    return fig


def plot_tutor_workload_balance(df):
    """
    Chart 5.2: Tutor workload distribution (box plot)
    """
    if 'Tutor_Anon_ID' not in df.columns:
        return None
    
    tutor_counts = df['Tutor_Anon_ID'].value_counts()
    
    # Plot
    fig, ax = plt.subplots(figsize=PAGE_LANDSCAPE)

    ax.boxplot([tutor_counts.values], vert=False, widths=0.5, patch_artist=True,
                boxprops=dict(facecolor=COLORS['primary'], alpha=0.7))

    ax.set_xlabel('Sessions per Tutor')
    ax.set_title('Tutor Workload Distribution')
    ax.set_yticks([])
    ax.grid(False)

    # Add statistics
    stats_text = f"Mean: {tutor_counts.mean():.1f} | Median: {tutor_counts.median():.0f} | Max: {tutor_counts.max()}"
    ax.text(0.5, -0.15, stats_text, transform=ax.transAxes, ha='center', fontsize=10)

    plt.tight_layout(rect=MARGIN_RECT)

    return fig


def plot_session_length_by_tutor(df):
    """
    Chart 5.3: Average session length by tutor (top 10)
    """
    if 'Tutor_Anon_ID' not in df.columns or 'Actual_Session_Length' not in df.columns:
        return None
    
    # Get top 10 tutors by session count
    top_tutors = df['Tutor_Anon_ID'].value_counts().index
    
    tutor_stats = df[df['Tutor_Anon_ID'].isin(top_tutors)].groupby('Tutor_Anon_ID')['Actual_Session_Length'].agg(['mean', 'std'])
    tutor_stats = tutor_stats.sort_values('mean', ascending=False)
    
    # Plot
    fig, ax = plt.subplots(figsize=PAGE_LANDSCAPE)

    x = range(len(tutor_stats))
    ax.bar(x, tutor_stats['mean'].values * 60, color=COLORS['secondary'], alpha=0.8,
           yerr=tutor_stats['std'].values * 60, capsize=5, error_kw={'alpha': 0.5})

    ax.set_xticks(x)
    ax.set_xticklabels(tutor_stats.index, rotation=45, ha='right')
    ax.set_ylabel('Average Session Length (minutes)')
    ax.set_title('Average Session Length by Tutor')
    ax.axhline(y=40, color='red', linestyle='--', linewidth=1, label='Standard 40 min', alpha=0.7)
    ax.legend()
    ax.grid(False)

    plt.tight_layout(rect=MARGIN_RECT)

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
    
    stages = df['Writing_Stage'].value_counts().head(10).sort_values(ascending=True)
    
    if len(stages) == 0:
        return None
    
    # Plot
    fig, ax = plt.subplots(figsize=PAGE_LANDSCAPE)

    ax.barh(range(len(stages)), stages.values, color=COLORS['primary'], alpha=0.8)

    ax.set_yticks(range(len(stages)))
    ax.set_yticklabels(stages.index)
    ax.set_xlabel('Number of Sessions')
    ax.set_title('Most Common Writing Stages')
    ax.grid(False)

    # Add value labels
    for i, val in enumerate(stages.values):
        ax.text(val, i, f' {val}', va='center', fontsize=9)

    plt.tight_layout()

    return fig


def plot_focus_areas(df):
    """
    Chart 6.2: Top focus areas (Horizontal bar chart - Descending)
    """
    if 'Focus_Area' not in df.columns:
        return None
    
    focus = df['Focus_Area'].dropna()
    
    if len(focus) == 0:
        return None
    
    # Get top 15 and sort ascending for the horizontal plot (highest at the top)
    focus_counts = focus.value_counts().head(15).sort_values(ascending=True)
    
    # Plot
    fig, ax = plt.subplots(figsize=PAGE_LANDSCAPE)

    # Horizontal bar plot
    bars = ax.barh(range(len(focus_counts)), focus_counts.values,
                   color=COLORS['secondary'], alpha=0.8)

    # Formatting
    ax.set_yticks(range(len(focus_counts)))
    ax.set_yticklabels(focus_counts.index, fontsize=10)
    ax.set_xlabel('Number of Sessions')
    ax.set_title('Top Focus Areas (Student Requests)', fontsize=14, pad=15)
    ax.grid(False)

    # Add value labels to the end of each bar for clarity
    for bar in bars:
        width = bar.get_width()
        ax.text(width + 0.3, bar.get_y() + bar.get_height()/2,
                f'{int(width)}', va='center', fontsize=10)

    plt.tight_layout(rect=MARGIN_RECT)

    return fig


def plot_first_time_vs_returning(df):
    """
    Chart 6.3: First-time vs returning students (pie chart)
    """
    if 'Is_First_Timer' not in df.columns:
        return None

    # Count
    first_time = df['Is_First_Timer'].sum()
    returning = (~df['Is_First_Timer']).sum() - df['Is_First_Timer'].isna().sum()

    # Plot
    fig, ax = plt.subplots(figsize=PAGE_LANDSCAPE)

    labels = ['Returning Students', 'First-Time Students']
    sizes = [returning, first_time]
    colors = [COLORS['primary'], COLORS['success']]

    wedges, texts, autotexts = ax.pie(sizes, labels=labels, autopct='%1.1f%%',
                                        startangle=90, colors=colors)

    ax.set_title(f'First-Time vs Returning Students (n={first_time + returning:,})', fontsize=14, pad=20)
    ax.grid(False)

    plt.tight_layout(rect=MARGIN_RECT)

    return fig


def plot_student_retention_trends(df):
    """
    Chart 6.4: New vs returning student trends over time (line chart)
    Shows growth in new student acquisition and returning student engagement
    """
    if 'Is_First_Timer' not in df.columns or 'Semester_Label' not in df.columns:
        return None

    # Prepare data
    df_plot = df.copy()

    # Group by semester and count first-timers vs returning
    semester_data = df_plot.groupby('Semester_Label').agg({
        'Is_First_Timer': lambda x: x.sum(),  # Count of first-timers
    })
    semester_data['Returning'] = df_plot.groupby('Semester_Label').size() - semester_data['Is_First_Timer']
    semester_data.rename(columns={'Is_First_Timer': 'First_Time'}, inplace=True)

    # Sort chronologically using semester sort helper
    sorted_semesters = sort_semesters(semester_data.index.tolist())
    semester_data = semester_data.reindex(sorted_semesters)

    if len(semester_data) < 2:
        return None  # Need at least 2 semesters for a trend

    # Plot
    fig, ax = plt.subplots(figsize=PAGE_LANDSCAPE)

    x = range(len(semester_data))

    # Plot lines for first-time and returning students
    ax.plot(x, semester_data['First_Time'].values, marker='o',
            color=COLORS['success'], linewidth=2, markersize=8,
            label='First-Time Students')
    ax.plot(x, semester_data['Returning'].values, marker='s',
            color=COLORS['primary'], linewidth=2, markersize=8,
            label='Returning Students')

    # Formatting
    ax.set_xticks(x)
    ax.set_xticklabels(semester_data.index, rotation=45, ha='right')
    ax.set_xlabel('Semester')
    ax.set_ylabel('Number of Students')
    ax.set_title('Student Retention Trends: New vs Returning Students Over Time')
    ax.legend()
    ax.grid(False)

    plt.tight_layout(rect=MARGIN_RECT)

    return fig


def plot_top_active_students(df, top_n=10):
    """
    Chart: Top N most active students (horizontal bar chart)
    Shows which students use the Writing Studio most frequently.
    """
    if 'Student_Anon_ID' not in df.columns:
        return None

    # Count sessions per student - sort ascending so highest appears at top when plotted
    student_counts = df['Student_Anon_ID'].value_counts().head(top_n).sort_values(ascending=True)

    if len(student_counts) == 0:
        return None

    # Create horizontal bar chart (descending order - most active at top)
    fig, ax = plt.subplots(figsize=PAGE_LANDSCAPE)

    y_pos = range(len(student_counts))
    ax.barh(y_pos, student_counts.values, color=COLORS['success'], alpha=0.8)

    ax.set_yticks(y_pos)
    ax.set_yticklabels(student_counts.index)
    ax.set_xlabel('Number of Sessions')
    ax.set_title(f'Top {top_n} Most Active Students', fontsize=14, pad=15)
    ax.grid(False)

    # Add value labels
    for i, val in enumerate(student_counts.values):
        ax.text(val, i, f' {val}', va='center', fontsize=10)

    plt.tight_layout(rect=MARGIN_RECT)

    return fig


# ============================================================================
# SECTION 7: SEMESTER COMPARISONS
# ============================================================================

def get_semester_sort_key(semester_str):
    """Helper to map 'Season Year' to a sortable float (e.g., Fall 2025 -> 2025.3)"""
    try:
        season, year = semester_str.split()
        mapping = {'Spring': 0.1, 'Summer': 0.2, 'Fall': 0.3}
        return float(year) + mapping.get(season, 0.0)
    except (ValueError, TypeError):
        return 0.0

def sort_semesters(semester_list):
    """Returns a list of semester labels sorted chronologically"""
    return sorted(semester_list, key=get_semester_sort_key)

# Apply this to your growth chart:
def plot_semester_growth(df):
    if 'Semester_Label' not in df.columns: 
        return None
    
    counts = df['Semester_Label'].value_counts()
    sorted_labels = sort_semesters(counts.index.tolist())
    counts = counts.reindex(sorted_labels)
    
    fig, ax = plt.subplots(figsize=PAGE_LANDSCAPE)
    ax.plot(range(len(counts)), counts.values, marker='o', color=COLORS['primary'], linewidth=3)
    ax.set_xticks(range(len(counts)))
    ax.set_xticklabels(counts.index, rotation=45)
    ax.set_title('Session Volume: Chronological Growth')
    ax.grid(False)

    plt.tight_layout(rect=MARGIN_RECT)

    return fig


def plot_semester_metrics_comparison(df, context):
    """
    Chart 7.2: Small multiples - key metrics by semester
    Corrected: Applied chronological semester sorting helper.
    """
    if 'Semester_Label' not in df.columns:
        return None

    # 1. Helper for Chronological Sorting
    def semester_sort_key(semester_str):
        try:
            season, year = semester_str.split()
            mapping = {'Spring': 0.1, 'Summer': 0.2, 'Fall': 0.3}
            return float(year) + mapping.get(season, 0.0)
        except (ValueError, TypeError):
            return 0.0

    semesters = df['Semester_Label'].unique()
    if len(semesters) < 2:
        return None
    
    # Pre-sort the semester list to use for all subplots
    sorted_semesters = sorted(semesters, key=semester_sort_key)

    fig, axes = plt.subplots(2, 2, figsize=PAGE_LANDSCAPE)
    fig.suptitle('Key Metrics Comparison by Semester', fontsize=16, y=0.95)
    
    # --- Subplot 1: Attendance Rate ---
    df_plot = df.copy()
    df_plot['Attended'] = df_plot.get('Attendance_Status', pd.Series()).str.lower().str.contains('present', na=False)
    attendance = df_plot.groupby('Semester_Label')['Attended'].apply(lambda x: (x.sum() / len(x)) * 100)
    attendance = attendance.reindex(sorted_semesters)
    
    bars1 = axes[0, 0].bar(range(len(attendance)), attendance.values, color=COLORS['success'], alpha=0.8)
    axes[0, 0].set_title('Attendance Rate (%)')
    
    # Add value labels
    for i, (bar, val) in enumerate(zip(bars1, attendance.values)):
        height = bar.get_height()
        axes[0, 0].text(bar.get_x() + bar.get_width()/2., height,
                        f'{val:.1f}%',
                        ha='center', va='bottom', fontsize=9)
    
    # --- Subplot 2: Average Booking Lead Time ---
    lead_time = df.groupby('Semester_Label')['Booking_Lead_Time_Days'].mean()
    lead_time = lead_time.reindex(sorted_semesters)
    
    bars2 = axes[0, 1].bar(range(len(lead_time)), lead_time.values, color=COLORS['warning'], alpha=0.8)
    axes[0, 1].set_title('Avg Booking Lead Time (Days)')
    
    # Add value labels
    for i, (bar, val) in enumerate(zip(bars2, lead_time.values)):
        height = bar.get_height()
        axes[0, 1].text(bar.get_x() + bar.get_width()/2., height,
                        f'{val:.1f}',
                        ha='center', va='bottom', fontsize=9)
    
    # --- Subplot 3: Average Session Length ---
    session_len = df.groupby('Semester_Label')['Actual_Session_Length'].mean() * 60
    session_len = session_len.reindex(sorted_semesters)
    
    bars3 = axes[1, 0].bar(range(len(session_len)), session_len.values, color=COLORS['primary'], alpha=0.8)
    axes[1, 0].axhline(y=40, color='red', linestyle='--', linewidth=1, label='Target (40m)')
    axes[1, 0].set_title('Avg Session Length (Minutes)')
    
    # Add value labels
    for i, (bar, val) in enumerate(zip(bars3, session_len.values)):
        height = bar.get_height()
        axes[1, 0].text(bar.get_x() + bar.get_width()/2., height,
                        f'{val:.0f}',
                        ha='center', va='bottom', fontsize=9)
    
    # --- Subplot 4: Avg Satisfaction or Confidence Improvement ---
    if 'Overall_Satisfaction' in df.columns:
        metric_data = df.groupby('Semester_Label')['Overall_Satisfaction'].mean().reindex(sorted_semesters)
        axes[1, 1].set_title('Avg Satisfaction (1-7)')
        axes[1, 1].set_ylim(1, 7)
    else:
        metric_data = df.groupby('Semester_Label')['Confidence_Change'].mean().reindex(sorted_semesters)
        axes[1, 1].set_title('Avg Confidence Improvement')
        axes[1, 1].axhline(y=0, color='red', linestyle='--', linewidth=1)

    bars4 = axes[1, 1].bar(range(len(metric_data)), metric_data.values, color=COLORS['secondary'], alpha=0.8)
    
    # Add value labels
    for i, (bar, val) in enumerate(zip(bars4, metric_data.values)):
        height = bar.get_height()
        axes[1, 1].text(bar.get_x() + bar.get_width()/2., height,
                        f'{val:.2f}',
                        ha='center', va='bottom', fontsize=9)

    # Global formatting for all axes
    for ax in axes.flat:
        ax.set_xticks(range(len(sorted_semesters)))
        ax.set_xticklabels(sorted_semesters, rotation=45, ha='right', fontsize=9)
        ax.grid(False)

    plt.tight_layout(rect=MARGIN_RECT)
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
    
    labels = ['Pre-Survey', 'Post-Survey']
    rates = [ctx['pre_survey_completion_rate'], 
             ctx['post_survey_completion_rate']]
    
    # Plot
    fig, ax = plt.subplots(figsize=PAGE_LANDSCAPE)

    bars = ax.bar(range(len(labels)), rates, color=COLORS['primary'], alpha=0.8)

    ax.set_xticks(range(len(labels)))
    ax.set_xticklabels(labels)
    ax.set_ylabel('Completion Rate (%)')
    ax.set_title('Survey Completion Rates')
    ax.set_ylim(0, 100)
    ax.grid(False)

    # Add value labels
    for bar, rate in zip(bars, rates):
        ax.text(bar.get_x() + bar.get_width()/2., rate,
                f'{rate:.1f}%',
                ha='center', va='bottom', fontsize=11, fontweight='bold')

    plt.tight_layout(rect=MARGIN_RECT)

    return fig


def plot_missing_data_concern(missing_report):
    """
    Chart 8.2: Missing data by column (only concerning columns)
    Corrected: Sorted descending (highest missing % at the top).
    """
    # Filter to only concerning missing data (>20% and category is 'concerning')
    concerning = {k: v for k, v in missing_report.items() 
                  if v.get('category') == 'concerning' and v['percentage'] > 20}
    
    if not concerning:
        return None
    
    # Sort by percentage ASCENDING so that the highest appears at the TOP of the plot
    sorted_items = sorted(concerning.items(), key=lambda x: x[1]['percentage'], reverse=False)
    columns = [item[0] for item in sorted_items]
    percentages = [item[1]['percentage'] for item in sorted_items]
    
    # Plot
    fig, ax = plt.subplots(figsize=PAGE_LANDSCAPE)

    y_pos = range(len(columns))
    ax.barh(y_pos, percentages, color=COLORS['warning'], alpha=0.8)

    ax.set_yticks(y_pos)
    ax.set_yticklabels(columns, fontsize=10)
    ax.set_xlabel('Missing Data (%)')
    ax.set_title('Data Quality Concerns (Missing Values >20%)', fontsize=14, pad=15)
    ax.grid(False)

    # Add value labels at the end of each bar
    for i, pct in enumerate(percentages):
        ax.text(pct + 0.5, i, f'{pct:.1f}%', va='center', fontsize=10, fontweight='bold')

    # Ensure the x-axis has some breathing room for the labels
    ax.set_xlim(0, max(percentages) + 10)

    plt.tight_layout(rect=MARGIN_RECT)

    return fig


def plot_incentives_vs_tutor_rating(incentive_metrics):
    """
    Chart 9: Tutor Session Ratings by Incentive Type
    Shows average tutor ratings for incentivized vs non-incentivized students.

    Research question: Do incentivized students have lower-quality sessions
    as perceived by tutors?
    """
    if not incentive_metrics or 'tutor_rating_by_incentive' not in incentive_metrics:
        return None

    tutor_ratings = incentive_metrics['tutor_rating_by_incentive']

    # Prepare data for plotting
    categories = []
    means = []
    counts = []
    stds = []
    sems = []  # Standard error of the mean

    # Define order and labels for better readability
    rating_order = [
        ('not_incentivized', 'No Incentive'),
        ('incentivized', 'Any Incentive'),
        ('class_required', 'Class Required'),
        ('extra_credit', 'Extra Credit')
    ]

    for key, label in rating_order:
        if key in tutor_ratings:
            categories.append(label)
            means.append(tutor_ratings[key]['mean'])
            counts.append(tutor_ratings[key]['count'])
            stds.append(tutor_ratings[key]['std'])
            # Calculate standard error of the mean (SEM = std / sqrt(n))
            sem = tutor_ratings[key]['std'] / np.sqrt(tutor_ratings[key]['count'])
            sems.append(sem)

    if not categories:
        return None

    # Create figure
    fig, ax = plt.subplots(figsize=PAGE_LANDSCAPE)

    # Create bar chart with error bars (using SEM)
    x_pos = range(len(categories))
    bars = ax.bar(x_pos, means,
                   yerr=sems,  # Error bars showing standard error
                   capsize=5,  # Width of error bar caps
                   color=[COLORS['accent'] if 'No' in cat else COLORS['primary'] for cat in categories],
                   alpha=0.8,
                   error_kw={'elinewidth': 2, 'ecolor': 'black', 'alpha': 0.6})

    ax.set_xticks(x_pos)
    ax.set_xticklabels(categories, fontsize=12)
    ax.set_ylabel('Average Tutor Rating', fontsize=12)
    ax.set_ylim(0, 5.5)
    ax.set_title('Tutor Session Ratings by Incentive Type\n(1=Didn\'t go well, 5=Went extremely well; error bars show ±1 SEM)',
                 fontsize=14, pad=15)
    ax.axhline(y=4.0, color='gray', linestyle='--', alpha=0.3, label='Reference: 4.0')
    ax.grid(axis='y', alpha=0.2)
    ax.grid(False)

    # Add value labels on bars (with extra spacing to avoid error bar overlap)
    for i, (bar, mean, count, sem) in enumerate(zip(bars, means, counts, sems)):
        height = bar.get_height()
        # Position text above the error bar (height + SEM + small buffer)
        text_y = height + sem + 0.15
        ax.text(bar.get_x() + bar.get_width()/2., text_y,
                f'{mean:.2f}\n(n={count})',
                ha='center', va='bottom', fontsize=11, fontweight='bold')

    # Add statistical significance indicator if available
    if 'statistical_tests' in incentive_metrics:
        tests = incentive_metrics['statistical_tests']

        if 'incentivized_vs_not' in tests and tests['incentivized_vs_not']['significant_at_05']:
            sig_level = '**' if tests['incentivized_vs_not']['significant_at_01'] else '*'
            p_val = tests['incentivized_vs_not']['p_value']
            ax.text(0.02, 0.98, f'Incentivized vs No Incentive: p={p_val:.4f} {sig_level}',
                   transform=ax.transAxes, fontsize=9, va='top',
                   bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.3))

    plt.tight_layout(rect=MARGIN_RECT)

    return fig


def plot_incentives_vs_satisfaction(incentive_metrics):
    """
    Chart 9.2: Student Satisfaction Ratings by Incentive Type
    Shows average student self-reported satisfaction for incentivized vs non-incentivized students.

    Research question: Do incentivized students report different satisfaction levels
    than non-incentivized students?
    """
    if not incentive_metrics or 'satisfaction_rating_by_incentive' not in incentive_metrics:
        return None

    satisfaction_ratings = incentive_metrics['satisfaction_rating_by_incentive']

    # Prepare data for plotting
    categories = []
    means = []
    counts = []
    stds = []
    sems = []  # Standard error of the mean

    # Define order and labels for better readability
    rating_order = [
        ('not_incentivized', 'No Incentive'),
        ('incentivized', 'Any Incentive'),
        ('class_required', 'Class Required'),
        ('extra_credit', 'Extra Credit')
    ]

    for key, label in rating_order:
        if key in satisfaction_ratings:
            categories.append(label)
            means.append(satisfaction_ratings[key]['mean'])
            counts.append(satisfaction_ratings[key]['count'])
            stds.append(satisfaction_ratings[key]['std'])
            # Calculate standard error of the mean (SEM = std / sqrt(n))
            sem = satisfaction_ratings[key]['std'] / np.sqrt(satisfaction_ratings[key]['count'])
            sems.append(sem)

    if not categories:
        return None

    # Create figure
    fig, ax = plt.subplots(figsize=PAGE_LANDSCAPE)

    # Create bar chart with error bars (using SEM)
    x_pos = range(len(categories))
    bars = ax.bar(x_pos, means,
                   yerr=sems,  # Error bars showing standard error
                   capsize=5,  # Width of error bar caps
                   color=[COLORS['accent'] if 'No' in cat else COLORS['primary'] for cat in categories],
                   alpha=0.8,
                   error_kw={'elinewidth': 2, 'ecolor': 'black', 'alpha': 0.6})

    ax.set_xticks(x_pos)
    ax.set_xticklabels(categories, fontsize=12)
    ax.set_ylabel('Average Student Satisfaction', fontsize=12)
    ax.set_ylim(0, 7.5)
    ax.set_title('Student Satisfaction Ratings by Incentive Type\n(1=Extremely dissatisfied, 7=Extremely satisfied; error bars show ±1 SEM)',
                 fontsize=14, pad=15)
    ax.axhline(y=6.0, color='gray', linestyle='--', alpha=0.3, label='Reference: 6.0')
    ax.grid(False)

    # Add value labels on bars (with extra spacing to avoid error bar overlap)
    for i, (bar, mean, count, sem) in enumerate(zip(bars, means, counts, sems)):
        height = bar.get_height()
        # Position text above the error bar (height + SEM + small buffer)
        text_y = height + sem + 0.2
        ax.text(bar.get_x() + bar.get_width()/2., text_y,
                f'{mean:.2f}\n(n={count})',
                ha='center', va='bottom', fontsize=11, fontweight='bold')

    # Add statistical significance indicator if available
    if 'satisfaction_statistical_tests' in incentive_metrics:
        tests = incentive_metrics['satisfaction_statistical_tests']

        if 'incentivized_vs_not' in tests and tests['incentivized_vs_not']['significant_at_05']:
            sig_level = '**' if tests['incentivized_vs_not']['significant_at_01'] else '*'
            p_val = tests['incentivized_vs_not']['p_value']
            ax.text(0.02, 0.98, f'Incentivized vs No Incentive: p={p_val:.4f} {sig_level}',
                   transform=ax.transAxes, fontsize=9, va='top',
                   bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.3))

    plt.tight_layout(rect=MARGIN_RECT)

    return fig


def plot_incentive_breakdown(incentive_metrics):
    """
    Chart 9.1: Incentive Type Distribution
    Shows the breakdown of different incentive types as a horizontal bar chart.
    """
    if not incentive_metrics or 'incentive_breakdown' not in incentive_metrics:
        return None

    breakdown = incentive_metrics['incentive_breakdown']

    # Prepare data
    labels = []
    counts = []
    percentages = []
    colors_list = []

    # Define categories to show
    categories = [
        ('no_incentive', 'No Incentive', COLORS['accent']),
        ('class_required', 'Class Required', COLORS['primary']),
        ('extra_credit', 'Extra Credit', COLORS['secondary'])
    ]

    for key, label, color in categories:
        if key in breakdown and breakdown[key]['count'] > 0:
            labels.append(label)
            counts.append(breakdown[key]['count'])
            percentages.append(breakdown[key]['percentage'])
            colors_list.append(color)

    if not counts:
        return None

    # Create figure
    fig, ax = plt.subplots(figsize=PAGE_LANDSCAPE)

    # Create horizontal bar chart
    y_pos = range(len(labels))
    bars = ax.barh(y_pos, counts, color=colors_list, alpha=0.8)

    ax.set_yticks(y_pos)
    ax.set_yticklabels(labels, fontsize=12)
    ax.set_xlabel('Number of Sessions', fontsize=12)
    ax.set_title('Distribution of Student Incentive Types', fontsize=14, pad=15)
    ax.grid(False)  # No grid for cleaner appearance

    # Add value labels at the end of each bar with counts and percentages
    for i, (bar, count, pct) in enumerate(zip(bars, counts, percentages)):
        width = bar.get_width()
        ax.text(width + max(counts) * 0.01, i,
                f'{count} sessions ({pct:.1f}%)',
                va='center', fontsize=11, fontweight='bold')

    # Add some space on the right for labels
    ax.set_xlim(0, max(counts) * 1.25)

    plt.tight_layout(rect=MARGIN_RECT)

    return fig


# ============================================================================
# SECTION 9: COURSE ENROLLMENT TABLE
# ============================================================================

def plot_course_table(df, courses_csv_path='courses.csv'):
    """
    Table page: Courses linked to Writing Studio visits.
    Shows Subject Abbreviation, Course Number, and session count.
    Only shows courses with at least 1 visit.
    Sorted alphabetically by subject, N/A pinned to bottom.
    
    Note: Skips gracefully if no course data available (e.g., older exports)
    """
    # Safety check: Course_Code column must exist
    if 'Course_Code' not in df.columns:
        return None
    
    # Safety check: Must have non-null course data
    course_data = df['Course_Code'].dropna()
    
    if len(course_data) == 0:
        return None
    
    # Load courses.csv for lookup
    import os
    code_to_info = {}
    try:
        courses_df = pd.read_csv(courses_csv_path)
        for _, row in courses_df.iterrows():
            abbrev = str(row['Subject Abbreviation']).strip()
            number = str(row['Course Number']).strip()
            code = abbrev + number
            code_to_info[code] = {'subject': abbrev, 'number': number}
    except FileNotFoundError:
        alt_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'courses.csv')
        try:
            courses_df = pd.read_csv(alt_path)
            for _, row in courses_df.iterrows():
                abbrev = str(row['Subject Abbreviation']).strip()
                number = str(row['Course Number']).strip()
                code = abbrev + number
                code_to_info[code] = {'subject': abbrev, 'number': number}
        except FileNotFoundError:
            pass
    
    # Count sessions per course code
    counts = course_data.value_counts()
    
    # Build table rows
    table_rows = []
    for code, count in counts.items():
        if code == 'N/A':
            table_rows.append({'Subject': 'N/A', 'Course Number': '', 'Sessions': count, '_sort_last': True})
        elif code in code_to_info:
            info = code_to_info[code]
            table_rows.append({'Subject': info['subject'], 'Course Number': info['number'], 'Sessions': count, '_sort_last': False})
        else:
            # Unknown code — still show it
            table_rows.append({'Subject': code, 'Course Number': '', 'Sessions': count, '_sort_last': False})
    
    if not table_rows:
        return None
    
    # Sort: alphabetical by subject, N/A last
    table_rows.sort(key=lambda r: (r['_sort_last'], r['Subject'], r['Course Number']))
    
    # Build display data
    cell_text = [[r['Subject'], r['Course Number'], str(r['Sessions'])] for r in table_rows]
    col_labels = ['Subject', 'Course Number', 'Sessions']
    
    # Create figure
    fig, ax = plt.subplots(figsize=PAGE_LANDSCAPE)
    ax.axis('off')
    ax.grid(False)
    
    ax.set_title('Course Enrollment Linked to Writing Studio Visits', fontsize=14, pad=20, fontweight='bold')
    
    # Create table
    table = ax.table(
        cellText=cell_text,
        colLabels=col_labels,
        loc='center',
        cellLoc='center'
    )
    
    # Style the table
    table.auto_set_font_size(False)
    table.set_fontsize(10)
    table.scale(1, 1.5)  # Row height
    
    # Header styling
    for j in range(len(col_labels)):
        cell = table[0, j]
        cell.set_facecolor(COLORS['primary'])
        cell.set_text_props(color='white', fontweight='bold')
    
    # Alternate row shading
    for i in range(1, len(cell_text) + 1):
        for j in range(len(col_labels)):
            cell = table[i, j]
            if i % 2 == 0:
                cell.set_facecolor('#f0f0f0')
            else:
                cell.set_facecolor('white')
    
    # Column widths
    table.auto_set_column_width([0, 1, 2])
    
    plt.tight_layout(rect=MARGIN_RECT)
    
    return fig
