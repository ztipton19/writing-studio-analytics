# src/visualizations/walkin_charts.py

"""
Walk-In Charts Module

Chart generation functions for walk-in data analytics.
Matches existing charts.py style and standards.

Author: Writing Studio Analytics Team
Date: 2026-01-19
"""

import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import warnings

warnings.filterwarnings('ignore')

# Set style (matching charts.py)
sns.set_style("whitegrid")
plt.rcParams['figure.figsize'] = (10, 6)
plt.rcParams['font.size'] = 10
plt.rcParams['axes.titlesize'] = 14
plt.rcParams['axes.labelsize'] = 12

# Standard page dimensions for print-ready output (8.5"x11" with 1" margins)
PAGE_LANDSCAPE = (11, 8.5)  # Landscape orientation for charts
PAGE_PORTRAIT = (8.5, 11)   # Portrait orientation for text pages
MARGIN_RECT = [0.09, 0.09, 0.91, 0.91]  # Approximate 1" margins (relative coordinates)

# Color palette (professional, colorblind-friendly) - matching charts.py
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
# CHART 1: CONSULTANT WORKLOAD DISTRIBUTION
# ============================================================================

def create_consultant_workload_chart(metrics):
    """
    Chart: Consultant workload distribution

    Shows sessions per consultant with:
    - Bar chart sorted by workload (descending)
    - Mean line for reference
    - Neutral color coding

    NOTE: Lower counts may reflect GAs, supervisors, main email account,
    or scheduling patterns (not necessarily performance issues).

    Parameters:
    - metrics: Dictionary from walkin_metrics.calculate_consultant_workload()

    Returns:
    - matplotlib figure object
    """

    if 'error' in metrics:
        print(f"⚠️  Cannot create workload chart: {metrics['message']}")
        return None

    # Extract data
    sessions_data = metrics['raw_data']['sessions_per_consultant']
    mean_sessions = metrics['sessions_per_consultant']['mean']

    # Sort by sessions (ascending for better visual)
    sorted_data = sorted(sessions_data.items(), key=lambda x: x[1])
    consultants = [c for c, _ in sorted_data]
    sessions = [s for _, s in sorted_data]

    # Create figure
    fig, ax = plt.subplots(figsize=PAGE_LANDSCAPE)

    # Create bar chart with single neutral color
    bars = ax.barh(consultants, sessions, color=COLORS['primary'], alpha=0.8, edgecolor='white')

    # Add mean line only
    ax.axvline(mean_sessions, color=COLORS['neutral'], linestyle='-',
               linewidth=2, label=f'Mean ({mean_sessions:.1f})', alpha=0.7)

    # Add value labels on bars
    for bar in bars:
        width = bar.get_width()
        ax.text(width + 0.3, bar.get_y() + bar.get_height()/2,
                f'{int(width)}',
                ha='left', va='center', fontsize=9)

    # Add disclaimer note
    disclaimer = ('Note: Lower counts may reflect GAs, supervisors,\n'
                 'admin accounts, or scheduling patterns.')
    ax.text(0.98, 0.02, disclaimer,
            transform=ax.transAxes,
            fontsize=9,
            verticalalignment='bottom',
            horizontalalignment='right',
            style='italic',
            color='gray')

    # Labels and title
    ax.set_xlabel('Number of Sessions')
    ax.set_ylabel('Consultant (Anonymous ID)')
    ax.set_title('Consultant Workload Distribution', fontsize=14, pad=20)
    ax.legend(loc='lower right')
    ax.grid(False)

    plt.tight_layout(rect=MARGIN_RECT)

    return fig


def create_consultant_hours_chart(metrics):
    """
    Chart: Consultant hours distribution
    
    Shows total hours per consultant (if duration data available).
    
    Parameters:
    - metrics: Dictionary from walkin_metrics.calculate_consultant_workload()
    
    Returns:
    - matplotlib figure object or None
    """
    
    if 'error' in metrics:
        return None
    
    if 'hours_per_consultant' not in metrics.get('raw_data', {}):
        return None
    
    # Extract data
    hours_data = metrics['raw_data']['hours_per_consultant']
    mean_hours = metrics['hours_per_consultant']['mean']
    
    # Sort by hours
    sorted_data = sorted(hours_data.items(), key=lambda x: x[1])
    consultants = [c for c, _ in sorted_data]
    hours = [h for _, h in sorted_data]
    
    # Create figure
    fig, ax = plt.subplots(figsize=PAGE_LANDSCAPE)
    
    # Create bar chart
    bars = ax.barh(consultants, hours, color=COLORS['secondary'], alpha=0.8, edgecolor='white')
    
    # Add mean line
    ax.axvline(mean_hours, color=COLORS['success'], linestyle='-', 
               linewidth=2, label=f'Mean ({mean_hours:.1f} hrs)', alpha=0.7)
    
    # Add value labels on bars
    for bar in bars:
        width = bar.get_width()
        ax.text(width + 0.1, bar.get_y() + bar.get_height()/2, 
                f'{width:.1f}', 
                ha='left', va='center', fontsize=9)
    
    # Labels and title
    ax.set_xlabel('Total Hours')
    ax.set_ylabel('Consultant (Anonymous ID)')
    ax.set_title('Total Consulting Hours per Consultant', fontsize=14, pad=20)
    ax.legend(loc='lower right')
    ax.grid(False)
    
    plt.tight_layout(rect=MARGIN_RECT)
    
    return fig


# ============================================================================
# CHART 2: TEMPORAL PATTERNS
# ============================================================================

def create_sessions_by_hour_chart(metrics):
    """
    Chart: Sessions by hour of day
    
    Bar chart showing session volume throughout the day.
    Highlights peak hours.
    
    Parameters:
    - metrics: Dictionary from walkin_metrics.calculate_temporal_patterns()
    
    Returns:
    - matplotlib figure object
    """
    
    if 'by_hour' not in metrics:
        print("⚠️  Cannot create hourly chart: missing hour data")
        return None
    
    # Extract data
    hourly_data = metrics['by_hour']['distribution']
    peak_hour = metrics['by_hour']['peak_hour']
    peak_hours = metrics.get('peak_periods', {}).get('hours', [peak_hour])
    
    # Create full 24-hour range
    hours = list(range(min(hourly_data.keys()), max(hourly_data.keys()) + 1))
    sessions = [hourly_data.get(h, 0) for h in hours]
    
    # Color bars (peak hours in orange, others in blue)
    colors_list = [COLORS['warning'] if h in peak_hours else COLORS['primary'] 
                   for h in hours]
    
    # Create figure
    fig, ax = plt.subplots(figsize=PAGE_LANDSCAPE)
    
    # Create bar chart
    ax.bar(hours, sessions, color=colors_list, alpha=0.8, edgecolor='white')
    
    # Add value labels on bars
    for i, (hour, count) in enumerate(zip(hours, sessions)):
        if count > 0:
            ax.text(hour, count + 0.3, str(count), 
                    ha='center', va='bottom', fontsize=9)
    
    # Add average line
    avg_sessions = np.mean(sessions)
    ax.axhline(avg_sessions, color=COLORS['neutral'], linestyle='--', 
               linewidth=1.5, label=f'Average ({avg_sessions:.1f})', alpha=0.6)
    
    # Labels and title
    ax.set_xlabel('Hour of Day')
    ax.set_ylabel('Number of Sessions')
    ax.set_title('Walk-In Session Volume by Hour', fontsize=14, pad=20)
    ax.set_xticks(hours)
    ax.set_xticklabels([f'{h}:00' for h in hours], rotation=45, ha='right')
    ax.legend()
    ax.grid(False)
    
    plt.tight_layout(rect=MARGIN_RECT)
    
    return fig


def create_sessions_by_day_chart(metrics):
    """
    Chart: Sessions by day of week
    
    Bar chart showing session volume by day.
    
    Parameters:
    - metrics: Dictionary from walkin_metrics.calculate_temporal_patterns()
    
    Returns:
    - matplotlib figure object
    """
    
    if 'by_day' not in metrics:
        print("⚠️  Cannot create daily chart: missing day data")
        return None
    
    # Extract data
    daily_data = metrics['by_day']['distribution']
    peak_day = metrics['by_day']['peak_day']
    
    # Order days properly
    day_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    days = [d for d in day_order if d in daily_data]
    sessions = [daily_data[d] for d in days]
    
    # Color bars (peak day in orange, others in blue)
    colors_list = [COLORS['warning'] if d == peak_day else COLORS['primary'] 
                   for d in days]
    
    # Create figure
    fig, ax = plt.subplots(figsize=PAGE_LANDSCAPE)
    
    # Create bar chart
    bars = ax.bar(days, sessions, color=colors_list, alpha=0.8, edgecolor='white')
    
    # Add value labels on bars
    for bar in bars:
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2., height + 0.3, 
                f'{int(height)}', 
                ha='center', va='bottom', fontsize=10)
    
    # Labels and title
    ax.set_xlabel('Day of Week')
    ax.set_ylabel('Number of Sessions')
    ax.set_title('Walk-In Session Volume by Day', fontsize=14, pad=20)
    ax.grid(False)
    
    plt.tight_layout(rect=MARGIN_RECT)
    
    return fig


def create_sessions_heatmap(df):
    """
    Chart: Sessions heatmap (day x hour)
    
    Heatmap showing session volume by day of week and hour of day.
    
    Parameters:
    - df: DataFrame with 'Day_of_Week' and 'Hour_of_Day' columns
    
    Returns:
    - matplotlib figure object
    """
    
    if 'Day_of_Week' not in df.columns or 'Hour_of_Day' not in df.columns:
        print("⚠️  Cannot create heatmap: missing Day_of_Week or Hour_of_Day columns")
        return None
    
    # Create pivot table
    day_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    heatmap_data = df.groupby(['Day_of_Week', 'Hour_of_Day']).size().unstack(fill_value=0)
    
    # Reorder days
    days_present = [d for d in day_order if d in heatmap_data.index]
    heatmap_data = heatmap_data.reindex(days_present, fill_value=0)
    
    # Create figure
    fig, ax = plt.subplots(figsize=PAGE_LANDSCAPE)
    
    # Create heatmap
    sns.heatmap(heatmap_data, cmap='YlOrRd', annot=True, fmt='d',
                cbar_kws={'label': 'Number of Sessions'}, ax=ax,
                linewidths=0.5, linecolor='white')
    
    # Labels and title
    ax.set_xlabel('Hour of Day')
    ax.set_ylabel('Day of Week')
    ax.set_title('Walk-In Session Volume Heatmap (Day × Hour)', fontsize=14, pad=20)
    
    plt.tight_layout(rect=MARGIN_RECT)
    
    return fig


# ============================================================================
# CHART 3: DURATION ANALYSIS
# ============================================================================

def create_duration_distribution_chart(metrics):
    """
    Chart: Duration distribution (overall)
    
    Simple histogram showing overall duration distribution.
    
    Parameters:
    - metrics: Dictionary from walkin_metrics.calculate_duration_stats()
    
    Returns:
    - matplotlib figure object
    """
    
    if 'error' in metrics:
        print(f"⚠️  Cannot create duration chart: {metrics['message']}")
        return None
    
    # Create figure
    fig, ax = plt.subplots(figsize=PAGE_LANDSCAPE)
    
    # Get overall statistics
    mean_dur = metrics['overall']['mean']
    median_dur = metrics['overall']['median']
    std_dur = metrics['overall']['std']
    
    # Create simple histogram with summary statistics as text
    # Note: We can't create histogram from aggregated metrics alone
    # This chart shows summary statistics instead
    
    # Create bar chart for summary statistics
    stats_names = ['Mean', 'Median', 'Std Dev', 'Min', 'Max']
    stats_values = [
        metrics['overall']['mean'],
        metrics['overall']['median'],
        metrics['overall']['std'],
        metrics['overall']['min'],
        metrics['overall']['max']
    ]
    
    colors = [COLORS['primary'], COLORS['secondary'], COLORS['neutral'], 
              COLORS['success'], COLORS['warning']]
    
    bars = ax.bar(stats_names, stats_values, color=colors, alpha=0.8, edgecolor='white')
    
    # Add value labels on bars
    for bar, value in zip(bars, stats_values):
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2., height + 2,
                f'{value:.1f} min',
                ha='center', va='bottom', fontsize=10, weight='bold')
    
    # Labels and title
    ax.set_ylabel('Duration (minutes)')
    ax.set_title('Overall Session Duration Statistics', fontsize=14, pad=20)
    ax.grid(axis='y', alpha=0.3)
    
    # Add total hours annotation
    total_hours = metrics['overall']['total_hours']
    ax.annotate(f'Total: {total_hours:.1f} hours',
                xy=(0.5, 0.95), xycoords='axes fraction',
                ha='center', va='top', fontsize=11,
                bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.3))
    
    plt.tight_layout(rect=MARGIN_RECT)
    
    return fig


def create_duration_by_course_chart(metrics):
    """
    Chart: Average duration by course type
    
    Horizontal bar chart showing average duration for each course type.
    
    Parameters:
    - metrics: Dictionary from walkin_metrics.calculate_duration_stats()
    
    Returns:
    - matplotlib figure object
    """
    
    if 'error' in metrics:
        return None
    
    if 'by_course' not in metrics:
        return None
    
    # Extract data (top 10)
    course_data = metrics['by_course']
    
    # Sort by mean duration (descending, then reverse for barh top-to-bottom)
    try:
        sorted_courses = sorted(course_data.items(), 
                               key=lambda x: x[1]['mean'], 
                               reverse=True)[:10]
        sorted_courses = sorted_courses[::-1]  # Reverse for descending top-to-bottom
        
        courses = [c for c, _ in sorted_courses]
        durations = [d['mean'] for _, d in sorted_courses]
        counts = [d['count'] for _, d in sorted_courses]
    except KeyError as e:
        print(f"⚠️  Cannot create duration by course chart: missing key {e}")
        return None
    
    # Create figure
    fig, ax = plt.subplots(figsize=PAGE_LANDSCAPE)
    
    # Create horizontal bar chart
    bars = ax.barh(courses, durations, color=COLORS['primary'], alpha=0.8, edgecolor='white')
    
    # Add value labels with counts
    for i, (bar, count) in enumerate(zip(bars, counts)):
        width = bar.get_width()
        ax.text(width + 1, bar.get_y() + bar.get_height()/2, 
                f'{width:.1f} min (n={count})', 
                ha='left', va='center', fontsize=9)
    
    # Labels and title
    ax.set_xlabel('Average Duration (minutes)')
    ax.set_ylabel('Course Type')
    ax.set_title('Average Session Duration by Course Type (Top 10)', fontsize=14, pad=20)
    ax.grid(False)
    
    plt.tight_layout(rect=MARGIN_RECT)
    
    return fig


# ============================================================================
# CHART 4: CHECK-IN USAGE PATTERNS
# ============================================================================

def create_checkin_usage_chart(metrics):
    """
    Chart: Check-in (independent space usage) overview
    
    Shows percentage breakdown of session types.
    
    Parameters:
    - metrics: Dictionary from walkin_metrics.calculate_checkin_usage()
    
    Returns:
    - matplotlib figure object
    """
    
    if metrics.get('total_checkin_sessions', 0) == 0:
        print("ℹ️  No check-in sessions to visualize")
        return None
    
    # Create figure (single subplot now)
    fig, ax = plt.subplots(figsize=PAGE_LANDSCAPE)
    
    # Pie chart showing percentage of sessions
    labels = ['Check In\n(Independent)', 'Completed\n(With Consultant)']
    sizes = [metrics['percentage_of_all'], 100 - metrics['percentage_of_all']]
    colors = [COLORS['warning'], COLORS['primary']]
    
    wedges, texts, autotexts = ax.pie(sizes, labels=labels, autopct='%1.1f%%',
                                       startangle=90, colors=colors,
                                       explode=(0.05, 0))
    
    ax.set_title('Independent Space Usage Analysis', fontsize=14, pad=20)
    
    plt.tight_layout(rect=MARGIN_RECT)
    
    return fig


def create_checkin_courses_chart(metrics):
    """
    Chart: Course types for check-in sessions
    
    Bar chart showing what students work on independently.
    
    Parameters:
    - metrics: Dictionary from walkin_metrics.calculate_checkin_usage()
    
    Returns:
    - matplotlib figure object or None
    """
    
    if 'courses' not in metrics:
        return None
    
    course_data = metrics['courses']['distribution']
    
    if not course_data:
        return None
    
    # Sort by count (descending, then reverse for barh top-to-bottom)
    sorted_courses = sorted(course_data.items(), key=lambda x: x[1], reverse=True)
    sorted_courses = sorted_courses[::-1]  # Reverse for descending top-to-bottom
    courses = [c for c, _ in sorted_courses]
    counts = [cnt for _, cnt in sorted_courses]
    
    # Create figure
    fig, ax = plt.subplots(figsize=PAGE_LANDSCAPE)
    
    # Create bar chart
    bars = ax.barh(courses, counts, color=COLORS['warning'], alpha=0.8, edgecolor='white')
    
    # Add value labels
    for bar in bars:
        width = bar.get_width()
        ax.text(width + 0.1, bar.get_y() + bar.get_height()/2, 
                f'{int(width)}', 
                ha='left', va='center', fontsize=9)
    
    # Labels and title
    ax.set_xlabel('Number of Sessions')
    ax.set_ylabel('Course Type')
    ax.set_title('Course Types for Independent Work (Check In)', fontsize=14, pad=20)
    ax.grid(False)
    
    plt.tight_layout(rect=MARGIN_RECT)
    
    return fig


# ============================================================================
# CHART 5: COURSE DISTRIBUTION
# ============================================================================

def create_course_distribution_chart(metrics):
    """
    Chart: Overall course distribution
    
    Horizontal bar chart showing all course types.
    
    Parameters:
    - metrics: Dictionary from walkin_metrics.calculate_course_distribution()
    
    Returns:
    - matplotlib figure object
    """
    
    if 'error' in metrics:
        print(f"⚠️  Cannot create course chart: {metrics['message']}")
        return None
    
    # Extract data
    course_data = metrics['distribution']
    
    # Sort by count (descending, then reverse for barh top-to-bottom)
    sorted_courses = sorted(course_data.items(), key=lambda x: x[1], reverse=True)
    sorted_courses = sorted_courses[::-1]  # Reverse for descending top-to-bottom
    courses = [c for c, _ in sorted_courses]
    counts = [cnt for _, cnt in sorted_courses]
    percentages = [metrics['percentages'][c] for c in courses]
    
    # Create figure
    fig, ax = plt.subplots(figsize=PAGE_LANDSCAPE)
    
    # Create horizontal bar chart
    bars = ax.barh(courses, counts, color=COLORS['primary'], alpha=0.8, edgecolor='white')
    
    # Add value labels with percentages
    for bar, pct in zip(bars, percentages):
        width = bar.get_width()
        ax.text(width + 0.3, bar.get_y() + bar.get_height()/2, 
                f'{int(width)} ({pct:.1f}%)', 
                ha='left', va='center', fontsize=9)
    
    # Highlight "Other" category if present
    if 'other_category' in metrics:
        other_index = courses.index('Other')
        bars[other_index].set_color(COLORS['neutral'])
    
    # Labels and title
    ax.set_xlabel('Number of Sessions')
    ax.set_ylabel('Course Type')
    ax.set_title('Course/Writing Type Distribution', fontsize=14, pad=20)
    ax.grid(False)
    
    plt.tight_layout(rect=MARGIN_RECT)
    
    return fig


def create_top_courses_pie_chart(metrics):
    """
    Chart: Top 5 courses pie chart
    
    Pie chart showing top 5 course types.
    
    Parameters:
    - metrics: Dictionary from walkin_metrics.calculate_course_distribution()
    
    Returns:
    - matplotlib figure object
    """
    
    if 'error' in metrics:
        return None
    
    # Extract top 5
    top5 = metrics['top_5']
    
    # Create figure
    fig, ax = plt.subplots(figsize=PAGE_LANDSCAPE)
    
    # Create pie chart
    wedges, texts, autotexts = ax.pie(top5.values(), labels=top5.keys(), 
                                        autopct='%1.1f%%', startangle=90,
                                        colors=PALETTE, pctdistance=0.85)
    
    # Make percentage text bold
    for autotext in autotexts:
        autotext.set_color('white')
        autotext.set_weight('bold')
    
    ax.set_title('Top 5 Course Types', fontsize=14, pad=20)
    
    plt.tight_layout(rect=MARGIN_RECT)
    
    return fig


# ============================================================================
# CONVENIENCE FUNCTION: CREATE ALL CHARTS
# ============================================================================

def create_all_walkin_charts(df, metrics):
    """
    Create all walk-in charts at once.
    
    Convenience function to generate all charts from cleaned data and metrics.
    
    Parameters:
    - df: Cleaned walk-in DataFrame
    - metrics: Dictionary from walkin_metrics.calculate_all_metrics()
    
    Returns:
    - Dictionary of figure objects
    """
    
    charts = {}
    
    print("\nGenerating walk-in charts...")
    
    # Consultant workload charts
    print("  [1/12] Consultant workload distribution...")
    charts['consultant_workload'] = create_consultant_workload_chart(
        metrics['consultant_workload']
    )
    
    print("  [2/12] Consultant hours...")
    charts['consultant_hours'] = create_consultant_hours_chart(
        metrics['consultant_workload']
    )
    
    # Temporal pattern charts
    print("  [3/12] Sessions by hour...")
    charts['sessions_by_hour'] = create_sessions_by_hour_chart(
        metrics['temporal_patterns']
    )
    
    print("  [4/12] Sessions by day...")
    charts['sessions_by_day'] = create_sessions_by_day_chart(
        metrics['temporal_patterns']
    )
    
    print("  [5/12] Sessions heatmap...")
    charts['sessions_heatmap'] = create_sessions_heatmap(df)
    
    # Duration charts
    print("  [6/12] Duration distribution...")
    charts['duration_distribution'] = create_duration_distribution_chart(
        metrics['duration_stats']
    )
    
    print("  [7/12] Duration by course...")
    charts['duration_by_course'] = create_duration_by_course_chart(
        metrics['duration_stats']
    )
    
    # Check-in charts
    print("  [8/12] Check-in usage overview...")
    charts['checkin_usage'] = create_checkin_usage_chart(
        metrics['checkin_usage']
    )
    
    print("  [9/12] Check-in courses...")
    charts['checkin_courses'] = create_checkin_courses_chart(
        metrics['checkin_usage']
    )
    
    # Course distribution charts
    print("  [10/12] Course distribution...")
    charts['course_distribution'] = create_course_distribution_chart(
        metrics['course_distribution']
    )
    
    print("  [11/12] Top courses pie...")
    charts['top_courses_pie'] = create_top_courses_pie_chart(
        metrics['course_distribution']
    )
    
    print("  [12/12] Done!")
    
    # Remove None values (charts that couldn't be created)
    charts = {k: v for k, v in charts.items() if v is not None}
    
    print(f"\n✓ Generated {len(charts)} charts successfully")
    
    return charts


# ============================================================================
# MAIN FUNCTION FOR TESTING
# ============================================================================

if __name__ == "__main__":
    print("Walk-In Charts Module")
    print("=" * 70)
    print("\nThis module provides chart generation for walk-in data.")
    print("\nMain function: create_all_walkin_charts(df, metrics)")
    print("\nIndividual chart functions:")
    print("  - create_consultant_workload_chart(metrics)")
    print("  - create_sessions_by_hour_chart(metrics)")
    print("  - create_sessions_by_day_chart(metrics)")
    print("  - create_duration_distribution_chart(metrics)")
    print("  - create_checkin_usage_chart(metrics)")
    print("  - create_course_distribution_chart(metrics)")
    print("=" * 70)
