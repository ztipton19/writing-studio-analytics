# src/visualizations/report_generator.py

import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
import pandas as pd
from datetime import datetime
import os

# Import all chart functions
from src.visualizations.charts import *


def generate_full_report(df, cleaning_log, output_path='report.pdf'):
    """
    Generate comprehensive PDF report with all visualizations.
    
    Parameters:
    - df: Cleaned dataframe
    - cleaning_log: Log from data cleaning (includes context)
    - output_path: Where to save PDF
    
    Returns:
    - Path to generated PDF
    """
    from src.core.metrics import calculate_all_metrics
    
    # Extract context from cleaning log
    context = cleaning_log.get('context', {})
    missing_report = cleaning_log.get('missing_values', {})
    
    # Calculate all metrics once
    print("\n📊 Calculating metrics...")
    metrics = calculate_all_metrics(df)
    
    # Create PDF
    with PdfPages(output_path) as pdf:
        
        print("📊 Generating Writing Studio Analytics Report...")
        print("="*80)
        
        # ====================================================================
        # COVER PAGE
        # ====================================================================
        print("\n📄 Creating cover page...")
        fig = create_cover_page(df, context)
        if fig:
            pdf.savefig(fig, bbox_inches='tight')
            plt.close(fig)
        
        # ====================================================================
        # SECTION 1: EXECUTIVE SUMMARY
        # ====================================================================
        print("\n📊 Section 1: Executive Summary")
        
        # Key metrics summary (text display)
        metrics = create_key_metrics_summary(df, context)
        fig = create_metrics_display_page(metrics)
        if fig:
            pdf.savefig(fig, bbox_inches='tight')
            plt.close(fig)
            print("   ✓ Key metrics summary")
        
        # Sessions over time
        fig = plot_sessions_over_time(df)
        if fig:
            pdf.savefig(fig, bbox_inches='tight')
            plt.close(fig)
            print("   ✓ Sessions over time")
        
        # ====================================================================
        # SECTION 2: BOOKING BEHAVIOR
        # ====================================================================
        print("\n📅 Section 2: Booking Behavior")
        
        # Booking lead time donut
        fig = plot_booking_lead_time_donut(df)
        if fig:
            pdf.savefig(fig, bbox_inches='tight')
            plt.close(fig)
            print("   ✓ Booking lead time breakdown")
        
        # Sessions by day of week
        fig = plot_sessions_by_day_of_week(df)
        if fig:
            pdf.savefig(fig, bbox_inches='tight')
            plt.close(fig)
            print("   ✓ Sessions by day of week")
        
        # Heatmap
        fig = plot_sessions_heatmap_day_time(df)
        if fig:
            pdf.savefig(fig, bbox_inches='tight')
            plt.close(fig)
            print("   ✓ Day/time heatmap")
        
        # ====================================================================
        # SECTION 3: ATTENDANCE & OUTCOMES
        # ====================================================================
        print("\n✅ Section 3: Attendance & Outcomes")
        
        # Session outcomes pie
        fig = plot_session_outcomes_pie(context)
        if fig:
            pdf.savefig(fig, bbox_inches='tight')
            plt.close(fig)
            print("   ✓ Session outcomes")
        
        # No-show by day
        fig = plot_no_show_by_day(df)
        if fig:
            pdf.savefig(fig, bbox_inches='tight')
            plt.close(fig)
            print("   ✓ No-show rate by day")
        
        # Trends over time
        fig = plot_outcomes_over_time(df)
        if fig:
            pdf.savefig(fig, bbox_inches='tight')
            plt.close(fig)
            print("   ✓ Outcome trends")
        
        # ====================================================================
        # SECTION 4: STUDENT SATISFACTION
        # ====================================================================
        print("\n😊 Section 4: Student Satisfaction")
        
        # Confidence comparison
        fig = plot_confidence_comparison(df)
        if fig:
            pdf.savefig(fig, bbox_inches='tight')
            plt.close(fig)
            print("   ✓ Pre vs post confidence")
        
        # Confidence change distribution
        fig = plot_confidence_change_distribution(df)
        if fig:
            pdf.savefig(fig, bbox_inches='tight')
            plt.close(fig)
            print("   ✓ Confidence change distribution")
        
        # Satisfaction distribution
        fig = plot_satisfaction_distribution(df)
        if fig:
            pdf.savefig(fig, bbox_inches='tight')
            plt.close(fig)
            print("   ✓ Satisfaction distribution")
        
        # Satisfaction trends
        fig = plot_satisfaction_trends(df)
        if fig:
            pdf.savefig(fig, bbox_inches='tight')
            plt.close(fig)
            print("   ✓ Satisfaction trends")
        
        # ====================================================================
        # SECTION 5: TUTOR ANALYTICS
        # ====================================================================
        print("\n👥 Section 5: Tutor Analytics")
        
        # Sessions per tutor
        fig = plot_sessions_per_tutor(df)
        if fig:
            pdf.savefig(fig, bbox_inches='tight')
            plt.close(fig)
            print("   ✓ Sessions per tutor")
        
        # Workload balance
        fig = plot_tutor_workload_balance(df)
        if fig:
            pdf.savefig(fig, bbox_inches='tight')
            plt.close(fig)
            print("   ✓ Workload balance")
        
        # Session length by tutor
        fig = plot_session_length_by_tutor(df)
        if fig:
            pdf.savefig(fig, bbox_inches='tight')
            plt.close(fig)
            print("   ✓ Session length by tutor")
        
        # ====================================================================
        # SECTION 6: SESSION CONTENT
        # ====================================================================
        print("\n📝 Section 6: Session Content")
        
        # Writing stages
        fig = plot_writing_stages(df)
        if fig:
            pdf.savefig(fig, bbox_inches='tight')
            plt.close(fig)
            print("   ✓ Writing stages")
        
        # Focus areas
        fig = plot_focus_areas(df)
        if fig:
            pdf.savefig(fig, bbox_inches='tight')
            plt.close(fig)
            print("   ✓ Focus areas")
        
        # First-time vs returning
        fig = plot_first_time_vs_returning(df)
        if fig:
            pdf.savefig(fig, bbox_inches='tight')
            plt.close(fig)
            print("   ✓ First-time vs returning")
        
        # ====================================================================
        # SECTION 7: SEMESTER COMPARISONS (only if multiple semesters)
        # ====================================================================
        num_semesters = df['Semester_Label'].nunique() if 'Semester_Label' in df.columns else 0
        
        if num_semesters >= 2:
            print("\n📊 Section 7: Semester Comparisons")
            
            # Semester growth
            fig = plot_semester_growth(df)
            if fig:
                pdf.savefig(fig, bbox_inches='tight')
                plt.close(fig)
                print("   ✓ Semester growth")
            
            # Small multiples comparison
            fig = plot_semester_metrics_comparison(df, context)
            if fig:
                pdf.savefig(fig, bbox_inches='tight')
                plt.close(fig)
                print("   ✓ Metrics comparison")
        else:
            print("\n⏭️  Section 7: Skipped (single semester data)")
        
        # ====================================================================
        # SECTION 8: DATA QUALITY
        # ====================================================================
        print("\n📋 Section 8: Data Quality")
        
        # Survey response rates
        fig = plot_survey_response_rates(context)
        if fig:
            pdf.savefig(fig, bbox_inches='tight')
            plt.close(fig)
            print("   ✓ Survey response rates")
        
        # Missing data concerns
        fig = plot_missing_data_concern(missing_report)
        if fig:
            pdf.savefig(fig, bbox_inches='tight')
            plt.close(fig)
            print("   ✓ Missing data analysis")
        
        # ====================================================================
        # METADATA PAGE
        # ====================================================================
        print("\n📄 Adding metadata page...")
        fig = create_metadata_page(df, cleaning_log)
        if fig:
            pdf.savefig(fig, bbox_inches='tight')
            plt.close(fig)
        
        # Set PDF metadata
        d = pdf.infodict()
        d['Title'] = 'Writing Studio Analytics Report'
        d['Author'] = 'Writing Studio Analytics Tool'
        d['Subject'] = f'Analysis of {len(df):,} tutoring sessions'
        d['Keywords'] = 'Tutoring, Analytics, Writing Studio'
        d['CreationDate'] = datetime.now()
    
    print("\n" + "="*80)
    print(f"✅ Report generated successfully: {output_path}")
    print("="*80 + "\n")
    
    return output_path


# ============================================================================
# HELPER FUNCTIONS FOR SPECIAL PAGES
# ============================================================================

def create_cover_page(df, context):
    """Create cover page for report"""
    fig, ax = plt.subplots(figsize=(8.5, 11))
    ax.axis('off')
    
    # Title
    ax.text(0.5, 0.8, 'Writing Studio', ha='center', fontsize=36, fontweight='bold',
            transform=ax.transAxes)
    ax.text(0.5, 0.72, 'Analytics Report', ha='center', fontsize=28,
            transform=ax.transAxes, color=COLORS['primary'])
    
    # Date range
    if 'Appointment_DateTime' in df.columns:
        min_date = df['Appointment_DateTime'].min().strftime('%B %d, %Y')
        max_date = df['Appointment_DateTime'].max().strftime('%B %d, %Y')
        ax.text(0.5, 0.6, f'{min_date} - {max_date}', ha='center', fontsize=14,
                transform=ax.transAxes, style='italic')
    
    # Quick stats box
    stats_y = 0.45
    ax.text(0.5, stats_y, 'Quick Statistics', ha='center', fontsize=16, fontweight='bold',
            transform=ax.transAxes)
    
    if 'cancellations' in context:
        ctx = context['cancellations']
        stats_text = f"""
        Total Sessions: {ctx['total_sessions']:,}
        Completion Rate: {ctx['completion_rate']:.1f}%
        Cancellation Rate: {ctx['cancellation_rate']:.1f}%
        No-Show Rate: {ctx['no_show_rate']:.1f}%
        """
        ax.text(0.5, stats_y - 0.15, stats_text, ha='center', fontsize=12,
                transform=ax.transAxes, family='monospace')
    
    # Generated date
    ax.text(0.5, 0.1, f'Generated: {datetime.now().strftime("%B %d, %Y at %I:%M %p")}',
            ha='center', fontsize=10, style='italic', transform=ax.transAxes,
            color='gray')
    
    return fig


def create_metrics_display_page(metrics):
    """Create a visual display of key metrics"""
    fig, ax = plt.subplots(figsize=(11, 8.5))
    ax.axis('off')
    
    # Title
    ax.text(0.5, 0.95, 'Key Performance Metrics', ha='center', fontsize=20, fontweight='bold',
            transform=ax.transAxes)
    
    # Metrics grid
    y_start = 0.85
    y_step = 0.12
    
    metric_list = [
        ('Total Sessions', metrics.get('total_sessions', 'N/A'), '📊'),
        ('Completion Rate', f"{metrics.get('completion_rate', 0):.1f}%", '✅'),
        ('Cancellation Rate', f"{metrics.get('cancellation_rate', 0):.1f}%", '📅'),
        ('No-Show Rate', f"{metrics.get('no_show_rate', 0):.1f}%", '⚠️'),
        ('Pre-Survey Response', f"{metrics.get('pre_survey_rate', 0):.1f}%", '📝'),
        ('Post-Survey Response', f"{metrics.get('post_survey_rate', 0):.1f}%", '📝'),
    ]
    
    for i, (label, value, emoji) in enumerate(metric_list):
        y = y_start - (i * y_step)
        
        # Emoji
        ax.text(0.2, y, emoji, ha='center', fontsize=24, transform=ax.transAxes)
        
        # Label
        ax.text(0.3, y, label, ha='left', fontsize=14, transform=ax.transAxes,
                fontweight='bold')
        
        # Value
        ax.text(0.8, y, str(value), ha='right', fontsize=16, transform=ax.transAxes,
                color=COLORS['primary'], fontweight='bold')
    
    # Power users section
    if 'power_users' in metrics:
        y_power = y_start - (len(metric_list) * y_step) - 0.08
        ax.text(0.5, y_power, 'Top 5 Most Active Students', ha='center', fontsize=14,
                fontweight='bold', transform=ax.transAxes)
        
        power_users = metrics['power_users']
        for i, (student_id, count) in enumerate(list(power_users.items())[:5]):
            y = y_power - 0.06 - (i * 0.04)
            ax.text(0.3, y, f'{student_id}', ha='left', fontsize=11,
                    transform=ax.transAxes, family='monospace')
            ax.text(0.7, y, f'{count} sessions', ha='right', fontsize=11,
                    transform=ax.transAxes, color=COLORS['success'])
    
    return fig


def create_metadata_page(df, cleaning_log):
    """Create metadata/technical details page"""
    fig, ax = plt.subplots(figsize=(8.5, 11))
    ax.axis('off')
    
    # Title
    ax.text(0.5, 0.95, 'Report Metadata', ha='center', fontsize=18, fontweight='bold',
            transform=ax.transAxes)
    
    # Data summary
    y = 0.88
    info_text = f"""
    DATA SUMMARY
    ────────────────────────────────
    Original Rows:        {cleaning_log.get('original_rows', 'N/A'):,}
    Original Columns:     {cleaning_log.get('original_cols', 'N/A')}
    Final Rows:           {cleaning_log.get('final_rows', 'N/A'):,}
    Final Columns:        {cleaning_log.get('final_cols', 'N/A')}
    Columns Removed:      {cleaning_log.get('original_cols', 0) - cleaning_log.get('final_cols', 0)}
    """
    
    if 'outliers_removed' in cleaning_log:
        outliers = cleaning_log['outliers_removed']
        info_text += f"""
    Outliers Removed:     {outliers.get('removed_count', 0)} ({outliers.get('removed_pct', 0):.1f}%)
    Outlier Method:       {outliers.get('method', 'N/A').upper()}
    """
    
    ax.text(0.1, y, info_text, ha='left', fontsize=10, transform=ax.transAxes,
            family='monospace', verticalalignment='top')
    
    # Date range
    if 'Appointment_DateTime' in df.columns:
        y -= 0.25
        min_date = df['Appointment_DateTime'].min()
        max_date = df['Appointment_DateTime'].max()
        days_span = (max_date - min_date).days
        
        date_text = f"""
    DATE RANGE
    ────────────────────────────────
    Start:                {min_date.strftime('%B %d, %Y')}
    End:                  {max_date.strftime('%B %d, %Y')}
    Days Covered:         {days_span:,} days
        """
        
        ax.text(0.1, y, date_text, ha='left', fontsize=10, transform=ax.transAxes,
                family='monospace', verticalalignment='top')
    
    # Semester breakdown
    if 'Semester_Label' in df.columns:
        y -= 0.2
        semester_counts = df['Semester_Label'].value_counts().sort_index()
        
        semester_text = "SEMESTER BREAKDOWN\n────────────────────────────────\n"
        for sem, count in semester_counts.items():
            semester_text += f"{sem:20s}: {count:>6,} sessions\n"
        
        ax.text(0.1, y, semester_text, ha='left', fontsize=10, transform=ax.transAxes,
                family='monospace', verticalalignment='top')
    
    # Generation info
    ax.text(0.5, 0.05, f'Generated by Writing Studio Analytics Tool',
            ha='center', fontsize=9, style='italic', transform=ax.transAxes,
            color='gray')
    ax.text(0.5, 0.02, f'{datetime.now().strftime("%B %d, %Y at %I:%M %p")}',
            ha='center', fontsize=9, style='italic', transform=ax.transAxes,
            color='gray')
    
    return fig


# ============================================================================
# CONVENIENCE FUNCTION
# ============================================================================

def quick_report(file_path, output_path='writing_studio_report.pdf'):
    """
    One-liner: Load file, clean, and generate full report.
    
    Supports CSV and Excel files.
    
    Usage:
        quick_report('penji_export.csv', 'report.pdf')
        quick_report('penji_export.xlsx', 'report.pdf')
    """
    from src.core.data_cleaner import clean_data
    import pandas as pd
    
    # Load data (detect file type)
    if file_path.endswith('.xlsx') or file_path.endswith('.xls'):
        df = pd.read_excel(file_path)
    else:
        df = pd.read_csv(file_path)
    
    df_clean, log = clean_data(df, mode='scheduled', remove_outliers=True, log_actions=True)
    
    # Generate report
    report_path = generate_full_report(df_clean, log, output_path)
    
    return report_path