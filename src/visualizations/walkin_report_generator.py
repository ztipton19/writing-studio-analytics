# src/visualizations/walkin_report_generator.py

import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
from datetime import datetime
import sys
import os

# Import walk-in specific functions
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
try:
    from core.walkin_metrics import calculate_all_metrics, generate_executive_summary
    from walkin_charts import create_all_walkin_charts
except ImportError:
    print("Warning: Could not import walkin modules from current directory")


def create_cover_page(df, date_range=None):
    """Create cover page for walk-in report"""
    fig, ax = plt.subplots(figsize=(8.5, 11))
    ax.axis('off')
    
    # Title
    ax.text(0.5, 0.7, 'Writing Studio\nWalk-In Analytics Report',
            ha='center', va='center', fontsize=32, weight='bold')
    
    # Stats
    total_sessions = len(df)
    if date_range:
        date_text = f"Period: {date_range}"
    else:
        date_text = "All Available Data"
    
    stats_text = f"{total_sessions:,} Walk-In Sessions\n{date_text}"
    ax.text(0.5, 0.4, stats_text,
            ha='center', va='center', fontsize=16)
    
    # Generated date
    gen_date = datetime.now().strftime('%B %d, %Y')
    ax.text(0.5, 0.2, f'Generated: {gen_date}',
            ha='center', va='center', fontsize=12, style='italic')
    
    plt.tight_layout()
    return fig


def create_executive_summary_page(summary):
    """Create executive summary text page"""
    fig, ax = plt.subplots(figsize=(8.5, 11))
    ax.axis('off')
    
    # Title
    ax.text(0.5, 0.95, 'Executive Summary',
            ha='center', va='top', fontsize=20, weight='bold')
    
    # Overview
    y_pos = 0.88
    ax.text(0.1, y_pos, 'Overview', fontsize=14, weight='bold')
    y_pos -= 0.03
    ax.text(0.1, y_pos, summary['overview'], fontsize=11, wrap=True)
    
    # Key Findings
    y_pos -= 0.08
    ax.text(0.1, y_pos, 'Key Findings', fontsize=14, weight='bold')
    y_pos -= 0.03
    for finding in summary['key_findings']:
        ax.text(0.12, y_pos, f"• {finding}", fontsize=10, wrap=True)
        y_pos -= 0.04
    
    # Concerns (if any)
    if summary['concerns']:
        y_pos -= 0.03
        ax.text(0.1, y_pos, 'Concerns', fontsize=14, weight='bold', color='#C73E1D')
        y_pos -= 0.03
        for concern in summary['concerns']:
            ax.text(0.12, y_pos, f"⚠ {concern}", fontsize=10, color='#C73E1D')
            y_pos -= 0.04
    
    # Recommendations (if any)
    if summary['recommendations']:
        y_pos -= 0.03
        ax.text(0.1, y_pos, 'Recommendations', fontsize=14, weight='bold', color='#06A77D')
        y_pos -= 0.03
        for rec in summary['recommendations']:
            ax.text(0.12, y_pos, f"💡 {rec}", fontsize=10, color='#06A77D')
            y_pos -= 0.04
    
    plt.tight_layout()
    return fig


def create_section_divider(title):
    """Create section divider page"""
    fig, ax = plt.subplots(figsize=(8.5, 11))
    ax.axis('off')
    
    ax.text(0.5, 0.5, title,
            ha='center', va='center', fontsize=28, weight='bold',
            bbox=dict(boxstyle='round', facecolor='#2E86AB', alpha=0.2, pad=1))
    
    plt.tight_layout()
    return fig


def generate_walkin_report(df, output_path='walkin_report.pdf'):
    """
    Generate comprehensive PDF report for walk-in data.
    
    Parameters:
    - df: Cleaned walk-in DataFrame
    - output_path: Where to save PDF
    
    Returns:
    - Path to generated PDF
    """
    
    print("\n📊 Generating Walk-In Analytics Report...")
    print("="*80)
    
    # Calculate all metrics
    print("\n📊 Calculating metrics...")
    metrics = calculate_all_metrics(df)
    
    # Generate executive summary
    print("📝 Generating executive summary...")
    summary = generate_executive_summary(metrics)
    
    # Generate all charts
    print("📈 Generating charts...")
    charts = create_all_walkin_charts(df, metrics)
    
    # Get date range
    if 'Check_In_DateTime' in df.columns:
        min_date = df['Check_In_DateTime'].min().date()
        max_date = df['Check_In_DateTime'].max().date()
        date_range = f"{min_date} to {max_date}"
    else:
        date_range = None
    
    # Create PDF
    with PdfPages(output_path) as pdf:
        
        # Cover Page
        print("\n📄 Creating cover page...")
        fig = create_cover_page(df, date_range)
        pdf.savefig(fig)
        plt.close(fig)
        
        # Executive Summary
        print("📄 Creating executive summary...")
        fig = create_executive_summary_page(summary)
        pdf.savefig(fig)
        plt.close(fig)
        
        # SECTION 1: CONSULTANT WORKLOAD
        print("\n👥 Section 1: Consultant Workload")
        fig = create_section_divider("Consultant Workload Analysis")
        pdf.savefig(fig)
        plt.close(fig)
        
        if 'consultant_workload' in charts:
            pdf.savefig(charts['consultant_workload'])
            plt.close(charts['consultant_workload'])
            print("   ✓ Workload distribution")
        
        if 'consultant_hours' in charts:
            pdf.savefig(charts['consultant_hours'])
            plt.close(charts['consultant_hours'])
            print("   ✓ Consultant hours")
        
        # SECTION 2: TEMPORAL PATTERNS
        print("\n⏰ Section 2: Temporal Patterns")
        fig = create_section_divider("Temporal Usage Patterns")
        pdf.savefig(fig)
        plt.close(fig)
        
        if 'sessions_by_hour' in charts:
            pdf.savefig(charts['sessions_by_hour'])
            plt.close(charts['sessions_by_hour'])
            print("   ✓ Sessions by hour")
        
        if 'sessions_by_day' in charts:
            pdf.savefig(charts['sessions_by_day'])
            plt.close(charts['sessions_by_day'])
            print("   ✓ Sessions by day")
        
        if 'sessions_heatmap' in charts:
            pdf.savefig(charts['sessions_heatmap'])
            plt.close(charts['sessions_heatmap'])
            print("   ✓ Sessions heatmap")
        
        # SECTION 3: DURATION ANALYSIS
        print("\n⏱️  Section 3: Duration Analysis")
        fig = create_section_divider("Session Duration Analysis")
        pdf.savefig(fig)
        plt.close(fig)
        
        if 'duration_distribution' in charts:
            pdf.savefig(charts['duration_distribution'])
            plt.close(charts['duration_distribution'])
            print("   ✓ Duration distribution")
        
        if 'duration_by_course' in charts:
            pdf.savefig(charts['duration_by_course'])
            plt.close(charts['duration_by_course'])
            print("   ✓ Duration by course")
        
        # SECTION 4: INDEPENDENT SPACE USAGE
        print("\n🏢 Section 4: Independent Space Usage")
        fig = create_section_divider("Check-In Space Usage")
        pdf.savefig(fig)
        plt.close(fig)
        
        if 'checkin_usage' in charts:
            pdf.savefig(charts['checkin_usage'])
            plt.close(charts['checkin_usage'])
            print("   ✓ Check-in usage")
        
        if 'checkin_courses' in charts:
            pdf.savefig(charts['checkin_courses'])
            plt.close(charts['checkin_courses'])
            print("   ✓ Check-in courses")
        
        # SECTION 5: COURSE DISTRIBUTION
        print("\n📚 Section 5: Course Distribution")
        fig = create_section_divider("Course & Writing Types")
        pdf.savefig(fig)
        plt.close(fig)
        
        if 'course_distribution' in charts:
            pdf.savefig(charts['course_distribution'])
            plt.close(charts['course_distribution'])
            print("   ✓ Course distribution")
        
        if 'top_courses_pie' in charts:
            pdf.savefig(charts['top_courses_pie'])
            plt.close(charts['top_courses_pie'])
            print("   ✓ Top courses pie")
        
        # Metadata
        d = pdf.infodict()
        d['Title'] = 'Writing Studio Walk-In Analytics Report'
        d['Author'] = 'Writing Studio Analytics Team'
        d['Subject'] = 'Walk-In Session Analysis'
        d['Keywords'] = 'Walk-In, Analytics, Writing Studio'
        d['CreationDate'] = datetime.now()
    
    print("\n" + "="*80)
    print(f"✅ Report generated: {output_path}")
    print(f"   Total pages: ~{5 + len(charts)}")
    print("="*80 + "\n")
    
    return output_path


if __name__ == "__main__":
    print("Walk-In Report Generator Module")
    print("=" * 70)
    print("\nUsage:")
    print("  from walkin_report_generator import generate_walkin_report")
    print("  generate_walkin_report(df_clean, 'report.pdf')")
    print("=" * 70)
