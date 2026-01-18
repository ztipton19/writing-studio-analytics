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

## Incentive Analysis Feature (January 2026)

### Research Question
Do incentivized students (required class visits or extra credit) have lower-quality sessions as perceived by tutors? This addresses tutor complaints about students being "checked out" during required visits, which contradicts findings in the literature.

### Implementation Summary

#### 1. Data Processing ([data_cleaner.py](../src/core/data_cleaner.py))
**Column Renaming** (Line 135):
- Added `'Student - Were you offered any of the following incentives...'` → `'Incentives_Offered'`
- Removed incentives column from deletion list (previously removed at line 255)

**Boolean Columns Creation** (Lines 358-370):
```python
df['Extra_Credit'] = df['Incentives_Offered'].str.contains('extra credit', case=False, na=False)
df['Class_Required'] = df['Incentives_Offered'].str.contains('entire class was required', case=False, na=False)
df['Incentivized'] = df['Extra_Credit'] | df['Class_Required']
```

#### 2. Statistical Analysis ([metrics.py](../src/core/metrics.py))
**New Function**: `calculate_incentive_metrics()` (Lines 462-728)

Calculates:
- **Incentive breakdown**: Counts and percentages for each type
- **Tutor ratings by group**: Mean, median, std, count for:
  - Extra Credit vs No Extra Credit
  - Class Required vs Not Required
  - Any Incentive vs No Incentive
- **Student satisfaction ratings by group** (Lines 588-655): Same structure as tutor ratings
  - Uses `Overall_Satisfaction` column (1-7 scale)
  - Filters to sessions with satisfaction data available
  - Same four-group comparison structure
- **Statistical tests**: Welch's t-tests for all comparisons
  - Tutor ratings tests: `statistical_tests` (Lines 657-692)
  - Satisfaction ratings tests: `satisfaction_statistical_tests` (Lines 694-728)
  - t-statistic, p-value, significance flags (p<0.05, p<0.01)
- **Mean difference**: Quantifies rating gap between groups
- **Rating distribution**: Full distribution by incentive status

**Integration**:
- Added to `calculate_all_metrics()` return dictionary as `'incentives'` key

#### 3. Visualizations ([charts.py](../src/visualizations/charts.py))

**Chart 1: Distribution of Student Incentive Types** (Lines 1168-1226)
- Horizontal bar chart showing session counts by incentive type
- Labels include both count and percentage (e.g., "914 sessions (97.8%)")
- No gridlines for clean appearance
- Color-coded: Green (No Incentive), Blue (Class Required), Purple (Extra Credit)

**Chart 2: Tutor Session Ratings by Incentive Type** (Lines 991-1077)
- Vertical bar chart with **error bars** (±1 SEM)
- Shows mean ratings (1-5 scale) for four groups:
  - No Incentive
  - Any Incentive
  - Class Required
  - Extra Credit
- **Error bars**: Standard Error of Mean (SEM = std / √n)
  - Positioned above bars to avoid overlap (text_y = height + sem + 0.15)
- Statistical significance annotation if p<0.05
- Reference line at 4.0 for context

**Chart 3: Student Satisfaction Ratings by Incentive Type** (Lines 1080-1165)
- Vertical bar chart with **error bars** (±1 SEM)
- Shows mean self-reported satisfaction (1-7 scale) for same four groups
- Uses `Overall_Satisfaction` column from student survey
- Design mirrors tutor ratings chart for easy comparison
- Error bars positioned above bars (text_y = height + sem + 0.2)
- Statistical significance annotation if p<0.05
- Reference line at 6.0 for context

#### 4. Report Integration ([report_generator.py](../src/visualizations/report_generator.py))

**Section 7: Incentive Analysis** (Lines 251-283)
- **Page 1**: Distribution chart (context - what data do we have?)
- **Page 2**: Tutor ratings chart (analysis - tutor perspective)
- **Page 3**: Student satisfaction chart (analysis - student perspective)
- Only appears if incentive data exists (`df['Incentivized'].notna().sum() > 0`)
- Gracefully skips if no data available

### Incentive Categories

From sessions.csv analysis:
1. **No Incentive**: 84 responses (majority of non-null)
2. **Class Required**: "My entire class was required to visit" - 17 responses
3. **Extra Credit**: "I was offered extra credit to visit" - 4 responses
4. **Professor Referral**: "My professor referred me" - 15 responses (not categorized as incentive)
5. **NaN**: 1,151 responses (field added recently)

### Statistical Approach

**Welch's t-test** (`equal_var=False`):
- Appropriate when group variances may differ
- More robust than standard t-test
- Tests null hypothesis: no difference in mean ratings between groups

**Standard Error of Mean (SEM)**:
- Formula: `std / √n`
- Shows precision of the mean estimate
- Smaller n → larger error bars → less confidence
- Non-overlapping error bars suggest significant difference

### Key Technical Details

**Error Bar Positioning**:
- Text labels positioned dynamically: `text_y = height + sem + 0.15`
- Ensures no overlap between labels and error bar caps
- Buffer value (0.15) provides visual separation

**Chart Order Rationale**:
1. Show distribution first (what data do we have?)
2. Show ratings analysis second (what does it mean?)

**Color Scheme**:
- `accent` color (#06A77D, green) for "No Incentive" baseline
- `primary` color (#2E86AB, blue) for incentivized groups
- Provides visual distinction between comparison groups

### Files Modified

1. **src/core/data_cleaner.py**: Boolean column creation, incentive field preservation
2. **src/core/metrics.py**: Statistical analysis function with both tutor and satisfaction metrics
3. **src/visualizations/charts.py**: Three chart functions (distribution, tutor ratings, satisfaction ratings)
4. **src/visualizations/report_generator.py**: Section 7 with three-page incentive analysis

### Usage Notes

The incentive analysis:
- Automatically runs when data is available
- Provides both descriptive (charts) and inferential (t-tests) statistics
- **Dual perspective**: Compares both tutor perceptions AND student self-reported satisfaction
- Enables evidence-based discussion about incentive effects
- Can inform policy decisions about required visits and extra credit

### Example Interpretation

Comparing tutor ratings vs student satisfaction can reveal:
- **Agreement**: Both metrics show similar patterns (validates findings)
- **Disagreement**: Tutors rate sessions lower but students are satisfied (or vice versa)
- **Statistical significance**: p < 0.05 indicates reliable difference, p < 0.01 very strong evidence

If results show:
- **p > 0.05**: No statistically significant difference (literature may be correct)
- **p < 0.05 & higher ratings**: Incentivized students actually perform better
- **p < 0.05 & lower ratings**: Tutor concerns may be valid

---

**Last Updated**: January 17, 2026
**Current State**: Incentive analysis complete with dual perspective (tutor ratings + student satisfaction), statistical testing, and three-page visualization section
