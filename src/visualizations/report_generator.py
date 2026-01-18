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
            pdf.savefig(fig)
            plt.close(fig)
        
        # ====================================================================
        # SECTION 1: EXECUTIVE SUMMARY
        # ====================================================================
        print("\n📊 Section 1: Executive Summary")
        
        # Key metrics summary (text display)
        metrics = create_key_metrics_summary(df, context)
        fig = create_metrics_display_page(metrics)
        if fig:
            pdf.savefig(fig)
            plt.close(fig)
            print("   ✓ Key metrics summary")
        
        # Sessions over time
        fig = plot_sessions_over_time(df)
        if fig:
            pdf.savefig(fig)
            plt.close(fig)
            print("   ✓ Sessions over time")

         # Small multiples comparison
        fig = plot_semester_metrics_comparison(df, context)
        if fig:
            pdf.savefig(fig)
            plt.close(fig)
            print("   ✓ Metrics comparison")
        else:
            print("\n⏭️  Section 7: Skipped (single semester data)")
        
        # ====================================================================
        # SECTION 2: BOOKING BEHAVIOR
        # ====================================================================
        print("\n📅 Section 2: Booking Behavior")
        
        # Booking lead time donut
        fig = plot_booking_lead_time_donut(df)
        if fig:
            pdf.savefig(fig)
            plt.close(fig)
            print("   ✓ Booking lead time breakdown")
        
        # Sessions by day of week
        fig = plot_sessions_by_day_of_week(df)
        if fig:
            pdf.savefig(fig)
            plt.close(fig)
            print("   ✓ Sessions by day of week")
        
        # Heatmap
        fig = plot_sessions_heatmap_day_time(df)
        if fig:
            pdf.savefig(fig)
            plt.close(fig)
            print("   ✓ Day/time heatmap")
        
        # ====================================================================
        # SECTION 3: ATTENDANCE & OUTCOMES
        # ====================================================================
        print("\n✅ Section 3: Attendance & Outcomes")
        
        # Session outcomes pie
        fig = plot_session_outcomes_pie(context)
        if fig:
            pdf.savefig(fig)
            plt.close(fig)
            print("   ✓ Session outcomes")
        
        # No-show by day
        fig = plot_no_show_by_day(df)
        if fig:
            pdf.savefig(fig)
            plt.close(fig)
            print("   ✓ No-show rate by day")
        
        # Trends over time
        fig = plot_outcomes_over_time(df)
        if fig:
            pdf.savefig(fig)
            plt.close(fig)
            print("   ✓ Outcome trends")

        # ====================================================================
        # SECTION 7: SEMESTER COMPARISONS (only if multiple semesters)
        # ====================================================================
        num_semesters = df['Semester_Label'].nunique() if 'Semester_Label' in df.columns else 0

        if num_semesters >= 2:
            print("\n📊 Section 7: Semester Comparisons")

            # Semester growth
            fig = plot_semester_growth(df)
            if fig:
                pdf.savefig(fig)
                plt.close(fig)
                print("   ✓ Semester growth")


        # ====================================================================
        # TOP ACTIVE STUDENTS
        # ====================================================================
        print("\n⭐ Top Active Students")

        # Top 10 most active students
        fig = plot_top_active_students(df, top_n=10)
        if fig:
            pdf.savefig(fig)
            plt.close(fig)
            print("   ✓ Top 10 most active students")

        # ====================================================================
        # SECTION 4: STUDENT SATISFACTION
        # ====================================================================
        print("\n😊 Section 4: Student Satisfaction")
        
        # Confidence comparison
        fig = plot_confidence_comparison(df)
        if fig:
            pdf.savefig(fig)
            plt.close(fig)
            print("   ✓ Pre vs post confidence")
        
        # Confidence change distribution
        fig = plot_confidence_change_distribution(df)
        if fig:
            pdf.savefig(fig)
            plt.close(fig)
            print("   ✓ Confidence change distribution")
        
        # Satisfaction distribution
        fig = plot_satisfaction_distribution(df)
        if fig:
            pdf.savefig(fig)
            plt.close(fig)
            print("   ✓ Satisfaction distribution")
        
        # Satisfaction trends
        fig = plot_satisfaction_trends(df)
        if fig:
            pdf.savefig(fig)
            plt.close(fig)
            print("   ✓ Satisfaction trends")
        
        # ====================================================================
        # SECTION 5: TUTOR ANALYTICS
        # ====================================================================
        print("\n👥 Section 5: Tutor Analytics")
        
        # Sessions per tutor
        fig = plot_sessions_per_tutor(df)
        if fig:
            pdf.savefig(fig)
            plt.close(fig)
            print("   ✓ Sessions per tutor")
        
        # Workload balance
        fig = plot_tutor_workload_balance(df)
        if fig:
            pdf.savefig(fig)
            plt.close(fig)
            print("   ✓ Workload balance")
        
        # Session length by tutor
        fig = plot_session_length_by_tutor(df)
        if fig:
            pdf.savefig(fig)
            plt.close(fig)
            print("   ✓ Session length by tutor")
        
        # ====================================================================
        # SECTION 6: SESSION CONTENT
        # ====================================================================
        print("\n📝 Section 6: Session Content")
        
        # Writing stages
        fig = plot_writing_stages(df)
        if fig:
            pdf.savefig(fig)
            plt.close(fig)
            print("   ✓ Writing stages")
        
        # Focus areas
        fig = plot_focus_areas(df)
        if fig:
            pdf.savefig(fig)
            plt.close(fig)
            print("   ✓ Focus areas")
        
        # First-time vs returning
        fig = plot_first_time_vs_returning(df)
        if fig:
            pdf.savefig(fig)
            plt.close(fig)
            print("   ✓ First-time vs returning")

        # Student retention trends over time
        fig = plot_student_retention_trends(df)
        if fig:
            pdf.savefig(fig)
            plt.close(fig)
            print("   ✓ Student retention trends")

        # ====================================================================
        # SECTION 7: INCENTIVE ANALYSIS
        # ====================================================================
        print("\n🎯 Section 7: Incentive Analysis")

        # Check if we have incentive data
        if 'Incentivized' in df.columns and df['Incentivized'].notna().sum() > 0:
            # Recalculate metrics to get incentive data
            from src.core.metrics import calculate_all_metrics
            metrics_full = calculate_all_metrics(df)

            # Incentive breakdown bar chart (show distribution first)
            fig = plot_incentive_breakdown(metrics_full.get('incentives', {}))
            if fig:
                pdf.savefig(fig)
                plt.close(fig)
                print("   ✓ Incentive type distribution")

            # Tutor ratings by incentive type (then show the analysis)
            fig = plot_incentives_vs_tutor_rating(metrics_full.get('incentives', {}))
            if fig:
                pdf.savefig(fig)
                plt.close(fig)
                print("   ✓ Tutor ratings by incentive type")

            # Student satisfaction ratings by incentive type
            fig = plot_incentives_vs_satisfaction(metrics_full.get('incentives', {}))
            if fig:
                pdf.savefig(fig)
                plt.close(fig)
                print("   ✓ Student satisfaction by incentive type")
        else:
            print("   ⏭️  Skipped (no incentive data available)")

        # ====================================================================
        # SECTION 8: DATA QUALITY
        # ====================================================================
        print("\n📋 Section 8: Data Quality")
        
        # Survey response rates
        fig = plot_survey_response_rates(context)
        if fig:
            pdf.savefig(fig)
            plt.close(fig)
            print("   ✓ Survey response rates")
        
        # ====================================================================
        # METADATA PAGE
        # ====================================================================
        print("\n📄 Adding metadata page...")
        fig = create_metadata_page(df, cleaning_log)
        if fig:
            pdf.savefig(fig)
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
    from src.visualizations.charts import PAGE_PORTRAIT, MARGIN_RECT
    fig, ax = plt.subplots(figsize=PAGE_PORTRAIT)
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

    # Quick stats box - centered individual lines
    stats_y = 0.45
    ax.text(0.5, stats_y, 'Quick Statistics', ha='center', fontsize=16, fontweight='bold',
            transform=ax.transAxes)

    if 'cancellations' in context:
        ctx = context['cancellations']
        y = stats_y - 0.08

        ax.text(0.5, y, f"Total Sessions: {ctx['total_sessions']:,}",
                ha='center', fontsize=12, transform=ax.transAxes, family='monospace')
        y -= 0.04
        ax.text(0.5, y, f"Completion Rate: {ctx['completion_rate']:.1f}%",
                ha='center', fontsize=12, transform=ax.transAxes, family='monospace')
        y -= 0.04
        ax.text(0.5, y, f"Cancellation Rate: {ctx['cancellation_rate']:.1f}%",
                ha='center', fontsize=12, transform=ax.transAxes, family='monospace')
        y -= 0.04
        ax.text(0.5, y, f"No-Show Rate: {ctx['no_show_rate']:.1f}%",
                ha='center', fontsize=12, transform=ax.transAxes, family='monospace')

    # Generated date
    ax.text(0.5, 0.1, f'Generated: {datetime.now().strftime("%B %d, %Y at %I:%M %p")}',
            ha='center', fontsize=10, style='italic', transform=ax.transAxes,
            color='gray')

    plt.tight_layout(rect=MARGIN_RECT)
    return fig


def create_metrics_display_page(metrics):
    """Create a visual display of key metrics"""
    from src.visualizations.charts import PAGE_PORTRAIT, MARGIN_RECT
    fig, ax = plt.subplots(figsize=PAGE_PORTRAIT)
    ax.axis('off')

    # Title
    ax.text(0.5, 0.95, 'Key Performance Metrics', ha='center', fontsize=20, fontweight='bold',
            transform=ax.transAxes)

    # Metrics grid
    y_start = 0.85
    y_step = 0.12

    metric_list = [
        ('Total Sessions', metrics.get('total_sessions', 'N/A')),
        ('Completion Rate', f"{metrics.get('completion_rate', 0):.1f}%"),
        ('Cancellation Rate', f"{metrics.get('cancellation_rate', 0):.1f}%"),
        ('No-Show Rate', f"{metrics.get('no_show_rate', 0):.1f}%"),
        ('Pre-Survey Response', f"{metrics.get('pre_survey_rate', 0):.1f}%"),
        ('Post-Survey Response', f"{metrics.get('post_survey_rate', 0):.1f}%"),
    ]

    for i, (label, value) in enumerate(metric_list):
        y = y_start - (i * y_step)

        # Label
        ax.text(0.25, y, label, ha='left', fontsize=14, transform=ax.transAxes,
                fontweight='bold')

        # Value
        ax.text(0.75, y, str(value), ha='right', fontsize=16, transform=ax.transAxes,
                color=COLORS['primary'], fontweight='bold')

    plt.tight_layout(rect=MARGIN_RECT)
    return fig


def create_metadata_page(df, cleaning_log):
    """Create metadata/technical details page"""
    from src.visualizations.charts import PAGE_PORTRAIT, MARGIN_RECT
    fig, ax = plt.subplots(figsize=PAGE_PORTRAIT)
    ax.axis('off')

    # Title
    ax.text(0.5, 0.95, 'Report Metadata', ha='center', fontsize=18, fontweight='bold',
            transform=ax.transAxes)

    # Data summary - centered
    y = 0.88
    ax.text(0.5, y, 'DATA SUMMARY', ha='center', fontsize=12, fontweight='bold',
            transform=ax.transAxes)

    y -= 0.04
    ax.text(0.5, y, '─' * 30, ha='center', fontsize=10, transform=ax.transAxes,
            family='monospace')

    y -= 0.04
    ax.text(0.5, y, f"Original Rows: {cleaning_log.get('original_rows', 'N/A'):,}",
            ha='center', fontsize=10, transform=ax.transAxes, family='monospace')

    y -= 0.03
    ax.text(0.5, y, f"Original Columns: {cleaning_log.get('original_cols', 'N/A')}",
            ha='center', fontsize=10, transform=ax.transAxes, family='monospace')

    y -= 0.03
    ax.text(0.5, y, f"Final Rows: {cleaning_log.get('final_rows', 'N/A'):,}",
            ha='center', fontsize=10, transform=ax.transAxes, family='monospace')

    y -= 0.03
    ax.text(0.5, y, f"Final Columns: {cleaning_log.get('final_cols', 'N/A')}",
            ha='center', fontsize=10, transform=ax.transAxes, family='monospace')

    y -= 0.03
    ax.text(0.5, y, f"Columns Removed: {cleaning_log.get('original_cols', 0) - cleaning_log.get('final_cols', 0)}",
            ha='center', fontsize=10, transform=ax.transAxes, family='monospace')

    if 'outliers_removed' in cleaning_log:
        outliers = cleaning_log['outliers_removed']
        y -= 0.04
        ax.text(0.5, y, f"Outliers Removed: {outliers.get('removed_count', 0)} ({outliers.get('removed_pct', 0):.1f}%)",
                ha='center', fontsize=10, transform=ax.transAxes, family='monospace')
        y -= 0.03
        ax.text(0.5, y, f"Outlier Method: {outliers.get('method', 'N/A').upper()}",
                ha='center', fontsize=10, transform=ax.transAxes, family='monospace')

    # Date range - centered
    if 'Appointment_DateTime' in df.columns:
        y -= 0.08
        min_date = df['Appointment_DateTime'].min()
        max_date = df['Appointment_DateTime'].max()
        days_span = (max_date - min_date).days

        ax.text(0.5, y, 'DATE RANGE', ha='center', fontsize=12, fontweight='bold',
                transform=ax.transAxes)

        y -= 0.04
        ax.text(0.5, y, '─' * 30, ha='center', fontsize=10, transform=ax.transAxes,
                family='monospace')

        y -= 0.04
        ax.text(0.5, y, f"Start: {min_date.strftime('%B %d, %Y')}",
                ha='center', fontsize=10, transform=ax.transAxes, family='monospace')

        y -= 0.03
        ax.text(0.5, y, f"End: {max_date.strftime('%B %d, %Y')}",
                ha='center', fontsize=10, transform=ax.transAxes, family='monospace')

        y -= 0.03
        ax.text(0.5, y, f"Days Covered: {days_span:,} days",
                ha='center', fontsize=10, transform=ax.transAxes, family='monospace')

    # Semester breakdown - centered
    if 'Semester_Label' in df.columns:
        y -= 0.08
        semester_counts = df['Semester_Label'].value_counts().sort_index()

        ax.text(0.5, y, 'SEMESTER BREAKDOWN', ha='center', fontsize=12, fontweight='bold',
                transform=ax.transAxes)

        y -= 0.04
        ax.text(0.5, y, '─' * 30, ha='center', fontsize=10, transform=ax.transAxes,
                family='monospace')

        for sem, count in semester_counts.items():
            y -= 0.04
            ax.text(0.5, y, f"{sem}: {count:,} sessions",
                    ha='center', fontsize=10, transform=ax.transAxes, family='monospace')

    # Generation info
    ax.text(0.5, 0.05, f'Generated by Writing Studio Analytics Tool',
            ha='center', fontsize=9, style='italic', transform=ax.transAxes,
            color='gray')
    ax.text(0.5, 0.02, f'{datetime.now().strftime("%B %d, %Y at %I:%M %p")}',
            ha='center', fontsize=9, style='italic', transform=ax.transAxes,
            color='gray')

    plt.tight_layout(rect=MARGIN_RECT)
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