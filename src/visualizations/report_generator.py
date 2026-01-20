# src/visualizations/report_generator.py

import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
from datetime import datetime

# Import all chart functions
import src.visualizations.charts as charts


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
    from src.core.metrics import calculate_all_metrics, generate_executive_summary
    
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
        # METADATA PAGE
        # ====================================================================
        print("\n📄 Adding metadata page...")
        fig = create_metadata_page(df, cleaning_log)
        if fig:
            pdf.savefig(fig)
            plt.close(fig)
        
        # ====================================================================
        # SECTION 1: EXECUTIVE SUMMARY
        # ====================================================================
        print("\n📊 Section 1: Executive Summary")
        
        # Generate executive summary from metrics
        print("   Generating executive summary...")
        summary = generate_executive_summary(metrics)
        fig = create_executive_summary_page(summary)
        if fig:
            pdf.savefig(fig)
            plt.close(fig)
            print("   ✓ Executive summary")
        
        # Sessions over time
        fig = charts.plot_sessions_over_time(df)
        if fig:
            pdf.savefig(fig)
            plt.close(fig)
            print("   ✓ Sessions over time")

         # Small multiples comparison
        fig = charts.plot_semester_metrics_comparison(df, context)
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
        fig = charts.plot_booking_lead_time_donut(df)
        if fig:
            pdf.savefig(fig)
            plt.close(fig)
            print("   ✓ Booking lead time breakdown")
        
        # Sessions by day of week
        fig = charts.plot_sessions_by_day_of_week(df)
        if fig:
            pdf.savefig(fig)
            plt.close(fig)
            print("   ✓ Sessions by day of week")
        
        # Heatmap
        fig = charts.plot_sessions_heatmap_day_time(df)
        if fig:
            pdf.savefig(fig)
            plt.close(fig)
            print("   ✓ Day/time heatmap")
        
        # ====================================================================
        # SECTION 3: ATTENDANCE & OUTCOMES
        # ====================================================================
        print("\n✅ Section 3: Attendance & Outcomes")
        
        # Session outcomes pie
        fig = charts.plot_session_outcomes_pie(context)
        if fig:
            pdf.savefig(fig)
            plt.close(fig)
            print("   ✓ Session outcomes")
        
        # No-show by day
        fig = charts.plot_no_show_by_day(df)
        if fig:
            pdf.savefig(fig)
            plt.close(fig)
            print("   ✓ No-show rate by day")
        
        # Trends over time
        fig = charts.plot_outcomes_over_time(df)
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
            fig = charts.plot_semester_growth(df)
            if fig:
                pdf.savefig(fig)
                plt.close(fig)
                print("   ✓ Semester growth")


        # ====================================================================
        # TOP ACTIVE STUDENTS
        # ====================================================================
        print("\n⭐ Top Active Students")

        # Top 10 most active students
        fig = charts.plot_top_active_students(df, top_n=10)
        if fig:
            pdf.savefig(fig)
            plt.close(fig)
            print("   ✓ Top 10 most active students")

        # ====================================================================
        # SECTION 4: STUDENT SATISFACTION
        # ====================================================================
        print("\n😊 Section 4: Student Satisfaction")
        
        # Confidence comparison
        fig = charts.plot_confidence_comparison(df)
        if fig:
            pdf.savefig(fig)
            plt.close(fig)
            print("   ✓ Pre vs post confidence")
        
        # Confidence change distribution
        fig = charts.plot_confidence_change_distribution(df)
        if fig:
            pdf.savefig(fig)
            plt.close(fig)
            print("   ✓ Confidence change distribution")
        
        # Satisfaction distribution
        fig = charts.plot_satisfaction_distribution(df)
        if fig:
            pdf.savefig(fig)
            plt.close(fig)
            print("   ✓ Satisfaction distribution")
        
        # Satisfaction trends
        fig = charts.plot_satisfaction_trends(df)
        if fig:
            pdf.savefig(fig)
            plt.close(fig)
            print("   ✓ Satisfaction trends")
        
        # ====================================================================
        # SECTION 5: TUTOR ANALYTICS
        # ====================================================================
        print("\n👥 Section 5: Tutor Analytics")
        
        # Sessions per tutor
        fig = charts.plot_sessions_per_tutor(df)
        if fig:
            pdf.savefig(fig)
            plt.close(fig)
            print("   ✓ Sessions per tutor")
        
        # Workload balance
        fig = charts.plot_tutor_workload_balance(df)
        if fig:
            pdf.savefig(fig)
            plt.close(fig)
            print("   ✓ Workload balance")
        
        # Session length by tutor
        fig = charts.plot_session_length_by_tutor(df)
        if fig:
            pdf.savefig(fig)
            plt.close(fig)
            print("   ✓ Session length by tutor")
        
        # ====================================================================
        # SECTION 6: SESSION CONTENT
        # ====================================================================
        print("\n📝 Section 6: Session Content")
        
        # Writing stages
        fig = charts.plot_writing_stages(df)
        if fig:
            pdf.savefig(fig)
            plt.close(fig)
            print("   ✓ Writing stages")
        
        # Focus areas
        fig = charts.plot_focus_areas(df)
        if fig:
            pdf.savefig(fig)
            plt.close(fig)
            print("   ✓ Focus areas")
        
        # First-time vs returning
        fig = charts.plot_first_time_vs_returning(df)
        if fig:
            pdf.savefig(fig)
            plt.close(fig)
            print("   ✓ First-time vs returning")

        # Student retention trends over time
        fig = charts.plot_student_retention_trends(df)
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
            fig = charts.plot_incentive_breakdown(metrics_full.get('incentives', {}))
            if fig:
                pdf.savefig(fig)
                plt.close(fig)
                print("   ✓ Incentive type distribution")

            # Tutor ratings by incentive type (then show the analysis)
            fig = charts.plot_incentives_vs_tutor_rating(metrics_full.get('incentives', {}))
            if fig:
                pdf.savefig(fig)
                plt.close(fig)
                print("   ✓ Tutor ratings by incentive type")

            # Student satisfaction ratings by incentive type
            fig = charts.plot_incentives_vs_satisfaction(metrics_full.get('incentives', {}))
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
        fig = charts.plot_survey_response_rates(context)
        if fig:
            pdf.savefig(fig)
            plt.close(fig)
            print("   ✓ Survey response rates")
        
        # Set PDF metadata
        d = pdf.infodict()
        d['Title'] = 'Writing Studio Sessions Analytics Report'
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
    ax.text(0.5, 0.7, 'Writing Studio', ha='center', va='center', fontsize=36, fontweight='bold',
            transform=ax.transAxes)
    ax.text(0.5, 0.62, 'Analytics Report', ha='center', va='center', fontsize=28,
            transform=ax.transAxes, color=charts.COLORS['primary'])

    # Stats
    total_sessions = len(df)
    if 'Appointment_DateTime' in df.columns:
        min_date = df['Appointment_DateTime'].min().date()
        max_date = df['Appointment_DateTime'].max().date()
        date_text = f"Period: {min_date} to {max_date}"
    else:
        date_text = "All Available Data"

    stats_text = f"{total_sessions:,} Sessions\n{date_text}"
    ax.text(0.5, 0.4, stats_text,
            ha='center', va='center', fontsize=16,
            transform=ax.transAxes)

    # Generated date
    gen_date = datetime.now().strftime('%B %d, %Y')
    ax.text(0.5, 0.2, f'Generated: {gen_date}',
            ha='center', va='center', fontsize=12, style='italic',
            transform=ax.transAxes)

    plt.tight_layout(rect=MARGIN_RECT)
    return fig


def create_executive_summary_page(summary):
    """Create executive summary text page"""
    from src.visualizations.charts import PAGE_PORTRAIT, MARGIN_RECT
    fig, ax = plt.subplots(figsize=PAGE_PORTRAIT)
    ax.axis('off')
    
    # Title
    ax.text(0.5, 0.95, 'Executive Summary',
            ha='center', va='top', fontsize=20, weight='bold',
            transform=ax.transAxes)
    
    # Overview
    y_pos = 0.88
    ax.text(0.12, y_pos, 'Overview', fontsize=14, weight='bold',
            transform=ax.transAxes)
    y_pos -= 0.03
    ax.text(0.12, y_pos, summary['overview'], fontsize=11, wrap=True,
            transform=ax.transAxes, ha='left')
    
    # Add extra space after overview for better visual separation
    y_pos -= 0.05
    
    # Key Findings
    y_pos -= 0.03
    ax.text(0.12, y_pos, 'Key Findings', fontsize=14, weight='bold',
            transform=ax.transAxes, ha='left')
    y_pos -= 0.03
    for finding in summary['key_findings']:
        ax.text(0.14, y_pos, f"• {finding}", fontsize=10, wrap=True,
                transform=ax.transAxes, ha='left')
        y_pos -= 0.04
    
    # Concerns (if any)
    if summary['concerns']:
        y_pos -= 0.03
        ax.text(0.12, y_pos, 'Concerns', fontsize=14, weight='bold', 
                color='#C73E1D', transform=ax.transAxes, ha='left')
        y_pos -= 0.03
        for concern in summary['concerns']:
            ax.text(0.14, y_pos, f"• {concern}", fontsize=10, color='#C73E1D',
                    wrap=True, transform=ax.transAxes, ha='left')
            y_pos -= 0.04
    
    # Recommendations (if any)
    if summary['recommendations']:
        y_pos -= 0.03
        ax.text(0.12, y_pos, 'Recommendations', fontsize=14, weight='bold',
                color='#06A77D', transform=ax.transAxes, ha='left')
        y_pos -= 0.03
        for rec in summary['recommendations']:
            ax.text(0.14, y_pos, f"• {rec}", fontsize=10, color='#06A77D',
                    wrap=True, transform=ax.transAxes, ha='left')
            y_pos -= 0.04
    
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
    ax.text(0.5, 0.05, 'Generated by Writing Studio Analytics Tool',
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
