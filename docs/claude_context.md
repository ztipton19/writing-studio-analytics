# Claude Context: Writing Studio Analytics Report

## Project Overview
This project generates comprehensive PDF analytics reports for a university writing studio, analyzing tutoring session data including attendance, student satisfaction, tutor performance, and booking behavior.

## Recent Major Update: Print-Ready Report Format

### Objective
Convert all report pages to print-ready 8.5"x11" format with consistent 1" margins for easy printing.

### Implementation Details

#### Page Dimensions & Margins
Added standard constants to `src/visualizations/charts.py`:
```python
PAGE_LANDSCAPE = (11, 8.5)  # Landscape orientation for charts
PAGE_PORTRAIT = (8.5, 11)   # Portrait orientation for text pages
MARGIN_RECT = [0.09, 0.09, 0.91, 0.91]  # Approximate 1" margins
```

#### Page Orientation Rules
- **Landscape (11"x8.5")**: All data visualization charts
- **Portrait (8.5"x11")**: Cover page, key metrics summary page, metadata page

#### Chart Updates
All 26+ chart functions in `charts.py` updated to:
1. Use `figsize=PAGE_LANDSCAPE` for landscape charts
2. Use `plt.tight_layout(rect=MARGIN_RECT)` for consistent margins
3. Include `ax.grid(False)` to remove gridlines
4. Implement chronological semester sorting where applicable

#### Report Generator Changes
Updated `src/visualizations/report_generator.py`:
- Removed `bbox_inches='tight'` from all `pdf.savefig()` calls
- Updated special pages (cover, metrics, metadata) to use `PAGE_PORTRAIT`
- Added student retention trends chart after first-time vs returning pie chart

### Key Features Implemented

#### 1. Chronological Semester Sorting
Created `sort_semesters()` helper function to properly order semesters:
- Extracts year and season from semester labels
- Maps seasons: Spring=0.1, Summer=0.2, Fall=0.3
- Returns chronologically sorted list (e.g., Spring 2024 → Summer 2024 → Fall 2024 → Spring 2025)

Applied to charts:
- Sessions over time
- Satisfaction trends
- Outcome trends
- Semester growth
- Semester metrics comparison
- Student retention trends

#### 2. Descending Order for Rankings
Charts showing "top N" items display highest values at the top:
- Top active students (chart at [charts.py:754-786](src/visualizations/charts.py#L754-L786))
- Sessions per tutor (chart at [charts.py:517-537](src/visualizations/charts.py#L517-L537))
- Top focus areas (chart at [charts.py:633-670](src/visualizations/charts.py#L633-L670))
- Missing data concerns (chart at [charts.py:887-925](src/visualizations/charts.py#L887-L925))

Implementation: Use `.sort_values(ascending=True)` for horizontal bar charts to flip display order.

#### 3. New Visualization: Student Retention Trends
Added `plot_student_retention_trends()` function ([charts.py:702-751](src/visualizations/charts.py#L702-L751)):
- Time-series line chart showing new vs returning students per semester
- Two lines: first-time students (green) and returning students (blue)
- Chronologically sorted semesters
- Helps identify student acquisition and retention patterns
- Located in report after first-time vs returning pie chart

### Report Structure

The report is organized into sections:
1. **Cover Page** (portrait)
2. **Executive Summary**: Key metrics (portrait), sessions over time, metrics comparison
3. **Booking Behavior**: Lead time, day of week, time heatmap
4. **Attendance & Outcomes**: Outcomes pie, no-show rates, trends
5. **Semester Comparisons**: Growth chart (only if multiple semesters)
6. **Top Active Students**: Top 10 bar chart
7. **Student Satisfaction**: Confidence comparison, satisfaction distribution, trends
8. **Tutor Analytics**: Sessions per tutor, workload balance, session length
9. **Session Content**: Writing stages, focus areas, first-time vs returning, retention trends
10. **Data Quality**: Survey response rates, missing data
11. **Metadata Page** (portrait)

### Technical Patterns

#### Standard Chart Template
```python
def plot_chart_name(df):
    fig, ax = plt.subplots(figsize=PAGE_LANDSCAPE)

    # Chart-specific plotting code

    ax.set_title('Chart Title')
    ax.grid(False)
    plt.tight_layout(rect=MARGIN_RECT)

    return fig
```

#### Semester Sorting Pattern
```python
# Sort chronologically using semester sort helper
sorted_semesters = sort_semesters(semester_data.index.tolist())
semester_data = semester_data.reindex(sorted_semesters)
```

#### Descending Bar Chart Pattern
```python
# For horizontal bars - sort ascending so highest appears at top
data = df['column'].value_counts().head(n).sort_values(ascending=True)
```

### Files Modified

1. **src/visualizations/charts.py** (Main visualization file)
   - Added PAGE_LANDSCAPE, PAGE_PORTRAIT, MARGIN_RECT constants
   - Updated all 26+ chart functions for landscape orientation
   - Added `plot_student_retention_trends()` function
   - Implemented chronological semester sorting across multiple charts
   - Fixed descending order for ranking charts
   - Adjusted title positioning to respect margins

2. **src/visualizations/report_generator.py** (Report orchestrator)
   - Removed `bbox_inches='tight'` from all PDF saves
   - Updated cover, metrics, and metadata pages to portrait orientation
   - Added student retention trends to report flow
   - Organized report into clear sections with print statements

### Common Issues & Solutions

| Issue | Solution | Location |
|-------|----------|----------|
| Charts not fitting on page | Use PAGE_LANDSCAPE constant | All chart functions |
| Margins inconsistent | Apply MARGIN_RECT to all tight_layout() | All chart functions |
| Semesters out of order | Use sort_semesters() helper | Time-series charts |
| Rankings not descending | Use .sort_values(ascending=True) for horizontal bars | Ranking charts |
| Title outside margins | Adjust y parameter (e.g., y=0.95) | Subplot titles |

### Color Palette
```python
COLORS = {
    'primary': '#2E86AB',    # Blue
    'secondary': '#A23B72',  # Purple
    'success': '#06A77D',    # Green
    'warning': '#F18F01',    # Orange
    'danger': '#C73E1D',     # Red
    'neutral': '#6C757D',    # Gray
}
```

### Dependencies
- matplotlib (plotting and PDF generation)
- seaborn (enhanced visualizations)
- pandas (data manipulation)
- numpy (numerical operations)

### Usage
Generate report: `python -m src.visualizations.report_generator`

The report outputs to `writing_studio_report.pdf` with all pages formatted for standard 8.5"x11" printing.

### Git Status
Repository is clean with all changes committed. Latest commits focus on report formatting improvements, encryption updates, and privacy enhancements.

---

**Last Updated**: January 2026
**Current State**: All requested formatting complete, report is print-ready
