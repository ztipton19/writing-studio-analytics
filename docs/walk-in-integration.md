# Walk-In Data Analytics Guide

## Executive Summary

This document outlines the complete strategy for creating a **standalone walk-in analytics report** from the walk-in appointment data (`check_ins.csv`). Walk-ins are **separate from scheduled appointments** and will generate their own independent report. No data merging or cross-analysis with scheduled sessions is required.

**Key Decisions:**
- Walk-ins and scheduled sessions = **two separate reports**
- User uploads one CSV → gets one report
- Two session types within walk-ins: **"Completed"** (met with consultant) and **"Check In"** (used space independently)
- Focus on consultant workload distribution analysis
- All PII handled identically to scheduled sessions (SHA256 hashing + encrypted codebook)

---

## 1. Walk-In Data Overview

### 1.1 Dataset Structure (`check_ins.csv`)
- **Source**: Walk-in queue/check-in system
- **Rows**: ~2,478 check-ins
- **Data Richness**: Low - minimal student feedback, no surveys
- **Date Range**: December 2025 - Present

### 1.2 Two Session Types

#### Type 1: **Completed** (~2,300 sessions)
- **Definition**: Student met with a writing consultant for help
- **Has**: Tutor assigned, tutor feedback, actual start/end times, duration
- **Analysis Focus**: Consultant workload, duration, course distribution, temporal patterns

#### Type 2: **Check In** (~100 sessions)
- **Definition**: Student checked in to use the writing space independently (no consultant)
- **Has**: Check-in time, end time, duration, course
- **Missing**: No tutor assigned, no tutor feedback
- **Analysis Focus**: Space usage patterns, duration, course distribution
- **Purpose**: Answers "Are students using our space independently, and how much?"

### 1.3 Key Fields

| Field | Available For | Purpose |
|-------|---------------|---------|
| `Unique ID` | Both | Session identifier |
| `Status` | Both | Completed / Check In / Cancelled / In Progress |
| `Student Email` | Both | Primary identifier for anonymization |
| `Student SSO ID` | Both | Secondary identifier |
| `Student ID` | Both | Tertiary identifier |
| `Student Name` | Both | **DELETE after anonymization** |
| `Check In At Date/Time` | Both | When student arrived |
| `Started At Date/Time` | Both | When session/space usage began |
| `Ended At Date/Time` | Both | When session/space usage ended |
| `Duration Minutes` | Both | Pre-calculated duration |
| `Tutor Email` | Completed only | Primary tutor identifier |
| `Tutor SSO ID` | Completed only | Secondary tutor identifier |
| `Tutor Name` | Completed only | **DELETE after anonymization** |
| `Course` | Both | Writing type/topic |
| `Resource` | Both | Mostly empty, ignore for now |
| `Topic` | Both | Mostly empty |
| `Check In Feedback From Tutor` | Completed only | Brief notes |
| `Cancel Reason` | Cancelled only | Why cancelled |
| `Canceller Email` | Cancelled only | Who cancelled |
| ~~`Mode`~~ | Both | **IGNORE - Useless** |
| ~~`Location`~~ | Both | **IGNORE - Only one location** |
| ~~`Requested Tutor Name`~~ | Both | **IGNORE - Mostly empty** |

### 1.4 Course Field Cleanup

The `Course` field has **36 unique values**, many with duplicates/typos that need consolidation:

#### Issues Found:
1. **"Other" variations** (869 total):
   - "Other topic not listed" (835)
   - "Other topic not listed (please describe in intake form in "Is there anything else you'd like to share?")" (34)
   - **→ Consolidate to**: "Other"

2. **Duplicate entries with double text**:
   - "Speech outlineSpeech outline" (12) → "Speech outline"
   - "Scientific or lab reportScientific or lab report" (1) → "Scientific or lab report"
   - "Reflection or response paperReflection or response paper" (1) → "Reflection or response paper"

3. **Thesis/dissertation variations** (27 total):
   - "Thesis or dissertation" (22)
   - "Thesis or dissertation (Undergraduate/Graduate)" (4)
   - "Thesis or dissertation (Undergradaute/Graduate)" (1) - typo!
   - **→ Consolidate to**: "Thesis or dissertation"

4. **Reflection paper variations** (129 total):
   - "Reflection or response paper" (78)
   - "Reflection paper" (51)
   - **→ Keep both or consolidate?** (User decision needed)

5. **Analysis paper variations**:
   - "Analysis Paper: Historical Sources" (86)
   - "Analysis Paper" (6)
   - **→ Keep separate or consolidate?** (User decision needed)

#### Full Course Distribution (After Basic Cleanup):
```
Other                                                     869
Custom essay                                             471
Research paper                                           284
Scientific or lab report                                 120
Speech outline                                           102
Analysis Paper: Historical Sources                       86
Reflection or response paper                             79
Synthesis paper                                          75
Reflection paper                                         51
Creative writing                                         48
Professional or technical writing assignment             35
Literature review                                        30
Rhetorical analysis                                      30
Summary                                                  23
Thesis or dissertation                                   27
Journalistic writing                                     19
Genre writing: Genre analysis or example of genre        18
Policy brief                                             16
Argumentative essay                                      11
Application essay (scholarship, graduate school, etc.)    9
Book or article review                                    9
Proposal                                                  6
Case study or case analysis                               6
Literary analysis                                         6
Annotated bibliography                                    4
Position paper                                            2
Professional writing                                      2
Response paper                                            1
Precis                                                    1
```

**Questions for User:**
- Consolidate "Reflection paper" + "Reflection or response paper"?
- Consolidate "Analysis Paper" + "Analysis Paper: Historical Sources"?
- Consolidate "Professional writing" + "Professional or technical writing assignment"?

---

## 2. Data Architecture

### 2.1 Walk-In Data Model

```python
WALKIN_SCHEMA = {
    # Core identifiers
    'Session_ID': 'Unique session identifier',
    'Session_Type': 'Completed | Check In | Cancelled | In Progress',

    # Temporal data
    'Check_In_DateTime': 'When student checked in',
    'Started_DateTime': 'When session/space usage began',
    'Ended_DateTime': 'When session/space usage ended',
    'Duration_Minutes': 'Actual duration',
    'Wait_Time_Minutes': 'Check-in to start time (if different)',

    # Student information (anonymized)
    'Student_Anon_ID': 'SHA256-hashed student identifier (from email)',
    'Is_One_Time_Visitor': 'Boolean - student only came once (Completed sessions only)',
    'Visit_Count': 'How many times this student came (Completed sessions only)',

    # Tutor information (anonymized, Completed only)
    'Tutor_Anon_ID': 'SHA256-hashed tutor identifier (from email)',

    # Session content
    'Course': 'Course or writing type (cleaned)',
    'Tutor_Feedback': 'Text notes from tutor (Completed only)',

    # Outcomes
    'Status': 'Completed | Check In | Cancelled | In Progress',
    'Cancel_Reason': 'Why cancelled (if applicable)',

    # Context
    'Semester_Label': 'e.g., Fall 2025',
    'Academic_Year': 'e.g., 2025-2026',
    'Day_of_Week': 'Monday, Tuesday, etc.',
    'Hour_of_Day': '0-23',
}
```

### 2.2 Data Processing Pipeline

```
┌─────────────────┐
│ check_ins.csv   │
│  (Raw Data)     │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Data Cleaning   │
│ - Parse dates   │
│ - Clean Course  │
│ - Validate dur. │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Anonymization  │
│ - Hash emails   │
│ - Create IDs    │
│ - Delete PII    │
│ - Save codebook │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Split by Status │
│ - Completed     │
│ - Check In      │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│Calculate Metrics│
│ - Per type      │
│ - Consultant    │
│ - Temporal      │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Generate Report │
│ - Completed     │
│ - Check In      │
│ - Combined      │
└─────────────────┘
```

---

## 3. Privacy & Anonymization

### 3.1 PII Handling Strategy

**Follow existing `privacy.py` implementation:**

```python
# Student anonymization
Student Email → SHA256 hash → Student_Anon_ID (e.g., "STU_04521")
Student SSO ID → DELETE
Student ID → DELETE
Student Name → DELETE

# Tutor anonymization (Completed sessions only)
Tutor Email → SHA256 hash → Tutor_Anon_ID (e.g., "TUT_0842")
Tutor SSO ID → DELETE
Tutor Name → DELETE

# Other PII
Canceller Email → DELETE (or hash if needed for analysis)
```

### 3.2 Codebook Generation

- **Identical process to scheduled sessions**
- User provides password (12+ characters)
- Encrypted codebook saved as `codebook_YYYY-MM-DD_HHMMSS.enc`
- Codebook contains reverse lookup: `STU_04521 → original email`
- Codebook given to supervisor ONLY
- **Never commit to GitHub**

### 3.3 Fields to DELETE (No Anonymization Needed)

```python
DELETE_COLUMNS = [
    'Mode',  # Useless
    'Location',  # Only one location
    'Requested Tutor Name',  # Mostly empty
    'Resource',  # Mostly empty (can revisit if useful later)
    'Topic',  # Mostly empty
]
```

---

## 4. Report Structure

### 4.1 Walk-In Analytics Report Sections

```
WALK-IN ANALYTICS REPORT
━━━━━━━━━━━━━━━━━━━━━━━━━

COVER PAGE
- Date range
- Total sessions
- Completed vs Check In breakdown

SECTION 1: EXECUTIVE SUMMARY
├─ Total Walk-Ins (Combined)
├─ Sessions by Type (Completed vs Check In)
├─ Overall Metrics Summary
└─ Walk-In Volume Over Time (Line chart)

SECTION 2: CONSULTANT SESSIONS (Status = "Completed")
├─ 2.1 Volume & Temporal Patterns
│   ├─ Sessions over time (daily timeseries)
│   ├─ Sessions by day of week
│   ├─ Sessions by hour of day (peak hours)
│   └─ Day/time heatmap
│
├─ 2.2 Duration Analysis
│   ├─ Duration distribution (histogram)
│   ├─ Average duration over time
│   └─ Duration by course type (boxplot)
│
├─ 2.3 Consultant Workload Analysis ⭐ HIGH PRIORITY
│   ├─ Total sessions per consultant (bar chart, descending)
│   ├─ Sessions per consultant over time (line chart, multi-series)
│   ├─ Consultant workload distribution (boxplot + stats)
│   ├─ Average session duration by consultant
│   ├─ Workload balance metrics (Gini coefficient, std dev)
│   └─ Consultant coverage by day/time (who works when?)
│
├─ 2.4 Course/Topic Analysis
│   ├─ Top courses (bar chart, top 15)
│   ├─ Course distribution (donut chart)
│   └─ Course trends over time
│
└─ 2.5 Student Engagement
    ├─ One-time vs repeat visitors (pie chart)
    ├─ Visit frequency distribution
    └─ Top active students (bar chart, top 10)

SECTION 3: INDEPENDENT SPACE USAGE (Status = "Check In")
├─ 3.1 Volume Metrics
│   ├─ Check-ins over time (timeseries)
│   ├─ Check-ins by day of week
│   └─ Check-ins by hour (when do students use space?)
│
├─ 3.2 Duration Analysis
│   ├─ Duration distribution
│   └─ Average duration over time
│
└─ 3.3 Course Distribution
    └─ What courses do independent students work on?

SECTION 4: CANCELLATIONS & NO-SHOWS
├─ Cancellation rate
├─ Cancellation reasons
└─ Cancellation trends over time

SECTION 5: DATA QUALITY & METHODOLOGY
├─ Data coverage notes
├─ Outlier handling
└─ Methodology & assumptions

METADATA PAGE
- Dataset stats
- Date range
- Anonymization summary
- Generation timestamp
```

### 4.2 Charts by Priority

#### High Priority (Consultant Workload Focus)
1. ⭐ **Sessions per consultant** (bar, descending) - *Are some consultants slacking?*
2. ⭐ **Sessions per consultant over time** (line) - *Is slacking consistent or episodic?*
3. ⭐ **Workload distribution** (boxplot) - *How uneven is the distribution?*
4. **Average session duration by consultant** - *Are some rushing through sessions?*
5. **Consultant coverage heatmap** - *Who is available when?*

#### Medium Priority (Operations)
6. **Sessions over time** (timeseries)
7. **Peak hours** (bar chart)
8. **Day of week distribution** (bar chart)
9. **Duration distribution** (histogram)
10. **Top courses** (bar chart)

#### Low Priority (Student Behavior)
11. **One-time vs repeat visitors** (pie)
12. **Check-in volume** (timeseries)
13. **Check-in duration** (histogram)

---

## 5. Code Architecture

### 5.1 New Files to Create

```
src/
├── core/
│   ├── data_cleaner.py              [EXISTING]
│   ├── data_cleaner_walkins.py      [NEW] ← Walk-in specific cleaning
│   ├── privacy.py                   [EXISTING] ← Already perfect, reuse
│   └── metrics.py                   [EXISTING - needs walkin functions]
│
├── visualizations/
│   ├── charts.py                    [EXISTING]
│   ├── charts_walkins.py            [NEW] ← Walk-in specific charts
│   └── report_generator_walkins.py  [NEW] ← Walk-in report builder
│
└── main.py                          [EXISTING - add walkin mode]
```

### 5.2 Module Responsibilities

#### **data_cleaner_walkins.py**
```python
def clean_walkin_data(df, remove_outliers=True, log_actions=True):
    """
    Clean walk-in check-in data.

    Tasks:
    1. Parse datetime columns (Check In At, Started At, Ended At)
    2. Validate/clean Duration Minutes field
    3. Handle Status field (Completed, Check In, Cancelled, In Progress)
    4. Clean Course field (consolidate duplicates/typos)
    5. Calculate wait time (Check In → Started)
    6. Extract semester labels from dates
    7. Handle duration outliers (cap at 3 hours or flag)
    8. Drop useless columns (Mode, Location, Requested Tutor Name)
    9. Validate tutor presence (Completed should have tutor, Check In should not)

    Returns: (cleaned_df, cleaning_log)
    """

def clean_course_field(df):
    """
    Consolidate Course field duplicates/typos.

    Mappings:
    - "Other topic not listed*" → "Other"
    - "Speech outlineSpeech outline" → "Speech outline"
    - Thesis variations → "Thesis or dissertation"
    - Remove leading/trailing whitespace

    Returns: df with cleaned Course column
    """
```

#### **metrics.py** (add walkin functions)
```python
def calculate_walkin_metrics(df):
    """
    Calculate walk-in specific metrics.

    Metrics:
    - Total sessions (by Status type)
    - Completion rate
    - Cancellation rate
    - Average duration (overall, by type, by consultant)
    - Sessions per consultant (mean, median, std, Gini)
    - Sessions per student (one-time vs repeat)
    - Peak hours/days
    - Wait time statistics

    Returns: metrics dict
    """

def calculate_consultant_workload_metrics(df):
    """
    Deep dive into consultant workload distribution.

    Metrics:
    - Sessions per consultant
    - Workload balance (Gini coefficient, std deviation)
    - Fairness score (0-100, where 100 = perfectly balanced)
    - Consultant utilization over time
    - Coverage gaps (times with no consultants)

    Returns: workload_metrics dict
    """

def detect_one_time_visitors(df):
    """
    Identify students who only came once (Completed sessions only).

    Returns:
    - one_time_pct: Percentage of one-time visitors
    - repeat_pct: Percentage of repeat visitors
    - visit_distribution: Distribution of visit counts
    """
```

#### **charts_walkins.py**
```python
# Consultant Workload Charts (HIGH PRIORITY)

def plot_sessions_per_consultant(df):
    """Bar chart: Sessions per consultant (descending order)"""

def plot_consultant_workload_over_time(df):
    """Line chart: Sessions per consultant over time (multiple lines)"""

def plot_consultant_workload_distribution(df):
    """Boxplot + stats: Distribution of consultant workloads"""

def plot_consultant_duration_comparison(df):
    """Boxplot: Average session duration by consultant"""

def plot_consultant_coverage_heatmap(df):
    """Heatmap: Which consultants work which days/times"""

# General Volume Charts

def plot_walkin_volume_over_time(df):
    """Line chart: Daily walk-in volume"""

def plot_walkin_by_day_of_week(df):
    """Bar chart: Sessions by day"""

def plot_walkin_by_hour(df):
    """Bar chart: Peak hours"""

def plot_walkin_heatmap_day_time(df):
    """Heatmap: Day x Time"""

# Duration Charts

def plot_duration_distribution(df):
    """Histogram: Session duration distribution"""

def plot_duration_by_course(df):
    """Boxplot: Duration by course type"""

# Course Charts

def plot_top_courses(df, top_n=15):
    """Bar chart: Most common courses"""

def plot_course_distribution_donut(df):
    """Donut chart: Course categories"""

# Student Engagement Charts

def plot_one_time_vs_repeat_visitors(df):
    """Pie chart: One-time vs repeat (Completed only)"""

def plot_visit_frequency_distribution(df):
    """Histogram: How many times do students visit?"""

def plot_top_active_students(df, top_n=10):
    """Bar chart: Most frequent visitors"""

# Check In Specific Charts

def plot_checkin_volume_over_time(df):
    """Line chart: Independent space usage over time"""

def plot_checkin_duration_distribution(df):
    """Histogram: How long do students stay?"""

def plot_checkin_course_distribution(df):
    """Bar chart: What do independent students work on?"""
```

#### **report_generator_walkins.py**
```python
def generate_walkin_report(df, cleaning_log, output_path='walkin_report.pdf'):
    """
    Generate comprehensive walk-in analytics PDF report.

    Parameters:
    - df: Cleaned walkin dataframe
    - cleaning_log: Log from data cleaning
    - output_path: Where to save PDF

    Returns:
    - Path to generated PDF
    """
    # Split by Status
    completed_df = df[df['Status'] == 'Completed']
    checkin_df = df[df['Status'] == 'Check In']

    # Generate report sections...

def quick_walkin_report(file_path, output_path='walkin_report.pdf'):
    """
    One-liner: Load CSV, clean, anonymize, generate report.

    Usage:
        quick_walkin_report('check_ins.csv', 'walkin_report.pdf')
    """
```

---

## 6. Metrics Strategy

### 6.1 Metrics for Completed Sessions

| Metric | Calculation | Purpose |
|--------|-------------|---------|
| **Total Sessions** | Count where `Status == 'Completed'` | Volume tracking |
| **Average Duration** | Mean of `Duration Minutes` | Session efficiency |
| **Sessions per Consultant** | Count per `Tutor_Anon_ID` | Workload distribution |
| **Workload Gini Coefficient** | Gini of sessions per consultant | Inequality measure (0=equal, 1=unequal) |
| **Workload Std Dev** | Std deviation of sessions per consultant | Variability measure |
| **Peak Hour** | Mode of `Hour_of_Day` | Staffing decisions |
| **Peak Day** | Mode of `Day_of_Week` | Scheduling optimization |
| **One-Time Visitor %** | Students with 1 visit / total students | Engagement depth |
| **Repeat Visitor %** | Students with 2+ visits / total students | Retention |
| **Top Course** | Mode of `Course` | Curriculum insights |

### 6.2 Metrics for Check In Sessions

| Metric | Calculation | Purpose |
|--------|-------------|---------|
| **Total Check-Ins** | Count where `Status == 'Check In'` | Space usage tracking |
| **Average Duration** | Mean of `Duration Minutes` | Space usage patterns |
| **Peak Hour** | Mode of `Hour_of_Day` | Space demand patterns |
| **Top Course** | Mode of `Course` | What students work on independently |

### 6.3 Combined Metrics

| Metric | Calculation | Purpose |
|--------|-------------|---------|
| **Total Walk-Ins** | Count of all sessions | Overall demand |
| **Completed %** | Completed / Total | Consultant utilization |
| **Check In %** | Check In / Total | Independent usage rate |
| **Cancellation Rate** | Cancelled / Total | Reliability |

---

## 7. Key Technical Challenges

### 7.1 Challenge: Duration Outliers
**Problem**: Some sessions show unrealistic durations (e.g., 1142 minutes = 19 hours).

**Root Cause**: Likely unclosed sessions or system errors.

**Solution**:
- Flag sessions >180 minutes (3 hours) as outliers
- Option 1: Cap at 180 minutes
- Option 2: Remove from duration analysis
- Option 3: Mark as "data quality issue" in report
- **Recommended**: Cap at 180 minutes with footnote

### 7.2 Challenge: Missing Tutor for "Completed" Sessions
**Problem**: Some "Completed" sessions have no tutor assigned.

**Solution**:
- Flag as data quality issue
- Exclude from consultant workload analysis
- Include in overall session counts
- Report count in data quality section

### 7.3 Challenge: "In Progress" Sessions
**Problem**: Sessions marked "In Progress" (not yet ended).

**Solution**:
- Exclude from all analysis (temporary state)
- Report count in data quality section
- User should re-export data after sessions complete

### 7.4 Challenge: Wait Time Calculation
**Problem**: Check-in time vs start time may differ (students in queue).

**Solution**:
```python
Wait_Time = Started_DateTime - Check_In_DateTime

# Handle edge cases:
- If wait time < 0: Data error, set to 0
- If wait time > 60 min: Likely error, cap or flag
- If Status == "Check In": Wait time irrelevant (no queue)
```

### 7.5 Challenge: One-Time Visitor Detection
**Problem**: Can only detect based on current dataset window.

**Limitation**:
- Student may have visited before/after dataset window
- Not as accurate as self-reported "Is this your first visit?"

**Solution**:
- Label as "One-Time Visitor (in this dataset)"
- Add footnote about limitation
- Only calculate for Completed sessions (Check In irrelevant)

---

## 8. Implementation Phases

### Phase 1: Data Cleaning (Priority 1) - **3-4 days**

#### Tasks:
1. Create `data_cleaner_walkins.py`
   - Parse datetime fields (Check In At, Started At, Ended At)
   - Clean Status field
   - Clean Course field (consolidate "Other" variations, fix typos)
   - Calculate wait time
   - Validate duration (flag >180 min outliers)
   - Extract semester labels
   - Drop useless columns (Mode, Location, Requested Tutor Name)

2. Test data cleaning
   - Verify datetime parsing
   - Check Course consolidation
   - Validate outlier detection

**Deliverable**:
```python
from src.core.data_cleaner_walkins import clean_walkin_data

df_clean, log = clean_walkin_data(df_raw, remove_outliers=True)
# Result: Clean DataFrame ready for anonymization
```

### Phase 2: Anonymization (Priority 1) - **1-2 days**

#### Tasks:
1. Integrate `privacy.py` with walk-in data
   - Map Student Email → Student_Anon_ID
   - Map Tutor Email → Tutor_Anon_ID (Completed only)
   - Delete all PII columns
   - Generate encrypted codebook

2. Test anonymization
   - Verify SHA256 hashing
   - Test codebook encryption/decryption
   - Ensure no PII leakage

**Deliverable**:
```python
from src.core.privacy import anonymize_with_codebook

df_anon, codebook_path, log = anonymize_with_codebook(
    df_clean,
    create_codebook=True,
    password=user_password
)
# Result: Anonymized DataFrame + encrypted codebook
```

### Phase 3: Consultant Workload Charts (Priority 1) - **3-4 days**

#### Tasks:
1. Create consultant-focused charts in `charts_walkins.py`
   - Sessions per consultant (bar, descending)
   - Sessions per consultant over time (line)
   - Workload distribution (boxplot + Gini)
   - Duration by consultant (boxplot)
   - Coverage heatmap

2. Add workload metrics to `metrics.py`

**Deliverable**: All high-priority workload charts rendering correctly

### Phase 4: General Volume & Duration Charts (Priority 2) - **2-3 days**

#### Tasks:
1. Create volume charts
   - Sessions over time
   - By day of week
   - By hour of day
   - Day/time heatmap

2. Create duration charts
   - Duration distribution
   - Duration by course
   - Duration over time

**Deliverable**: All volume/duration charts working

### Phase 5: Course & Student Engagement Charts (Priority 2) - **2-3 days**

#### Tasks:
1. Create course charts
   - Top courses (bar)
   - Course distribution (donut)
   - Course trends over time

2. Create student engagement charts
   - One-time vs repeat (pie)
   - Visit frequency distribution
   - Top active students

**Deliverable**: All course/engagement charts working

### Phase 6: Check In Charts (Priority 3) - **1-2 days**

#### Tasks:
1. Create Check In specific charts
   - Volume over time
   - Duration distribution
   - Course distribution

**Deliverable**: Check In section complete

### Phase 7: Report Assembly (Priority 1) - **3-4 days**

#### Tasks:
1. Create `report_generator_walkins.py`
   - Cover page
   - Section 1: Executive Summary
   - Section 2: Consultant Sessions (Completed)
   - Section 3: Independent Space Usage (Check In)
   - Section 4: Cancellations
   - Section 5: Data Quality
   - Metadata page

2. Test full report generation

**Deliverable**: Complete walk-in report PDF

### Phase 8: CLI Integration (Priority 2) - **1-2 days**

#### Tasks:
1. Update `main.py` to support walk-in mode
   ```bash
   python main.py --walkins check_ins.csv --output walkin_report.pdf
   ```

2. Test end-to-end workflow

**Deliverable**: User can generate walk-in report via command line

### Phase 9: Testing & Edge Cases (Priority 1) - **2-3 days**

#### Tasks:
1. Handle edge cases
   - Duration outliers
   - Missing tutor for Completed sessions
   - In Progress sessions
   - Cancelled sessions
   - Empty Check In sessions

2. Data quality checks
3. Visual regression testing

**Deliverable**: Robust error handling

---

## 9. Timeline Estimate

| Phase | Duration | Priority | Deliverable |
|-------|----------|----------|-------------|
| **Phase 1** | 3-4 days | P1 | Data cleaning working |
| **Phase 2** | 1-2 days | P1 | Anonymization + codebook |
| **Phase 3** | 3-4 days | P1 | Consultant workload charts |
| **Phase 4** | 2-3 days | P2 | Volume/duration charts |
| **Phase 5** | 2-3 days | P2 | Course/engagement charts |
| **Phase 6** | 1-2 days | P3 | Check In charts |
| **Phase 7** | 3-4 days | P1 | Full report generation |
| **Phase 8** | 1-2 days | P2 | CLI integration |
| **Phase 9** | 2-3 days | P1 | Testing & edge cases |
| **Total** | **18-27 days** | | Fully functional walk-in analytics |

---

## 10. Success Criteria

### 10.1 Phase Completion Criteria

#### Phase 1 Success:
- ✅ Walk-in CSV loads without errors
- ✅ Datetimes parsed correctly
- ✅ Course field cleaned (duplicates consolidated)
- ✅ Outliers flagged/capped
- ✅ Useless columns dropped

#### Phase 2 Success:
- ✅ Student emails hashed to anonymous IDs
- ✅ Tutor emails hashed to anonymous IDs
- ✅ All PII columns deleted
- ✅ Encrypted codebook generated
- ✅ Codebook can be decrypted with password

#### Phase 3 Success:
- ✅ Consultant workload charts render correctly
- ✅ Charts clearly show workload distribution
- ✅ Gini coefficient calculated
- ✅ Charts identify "slacking" consultants (if any)

#### Phase 7 Success:
- ✅ Walk-in report generates without errors
- ✅ Report clearly separates Completed vs Check In
- ✅ All charts properly labeled
- ✅ Report is under 40 pages
- ✅ Executive summary accurate

### 10.2 Final Success:
- ✅ User can upload `check_ins.csv` and get report
- ✅ Report answers key questions:
  - Are consultants fairly distributing workload?
  - When are peak walk-in hours?
  - How long do sessions typically last?
  - Are students using the space independently?
  - Which courses are most common?
- ✅ Code is modular and maintainable
- ✅ Documentation complete

---

## 11. Key Questions for User

### 11.1 Course Field Consolidation

**Recommendation needed for these categories:**

1. **Reflection papers** (129 total):
   - "Reflection or response paper" (78)
   - "Reflection paper" (51)
   - "Response paper" (1)
   - **→ Consolidate all to "Reflection or response paper"**

2. **Analysis papers** (92 total):
   - "Analysis Paper: Historical Sources" (86)
   - "Analysis Paper" (6)
   - **→ Keep separate or consolidate to "Analysis Paper"**

3. **Professional writing** (37 total):
   - "Professional or technical writing assignment" (35)
   - "Professional writing" (2)
   - **→ Consolidate to "Professional or technical writing"**

4. **Application essays** (9):
   - "Application essay (scholarship, graduate school, SOP, etc.)" (9)
   - **→ Shorten to "Application essay"?**

**Please advise on consolidation strategy.**

---

## 12. Workload Analysis - Key Metrics

### 12.1 Gini Coefficient (Workload Inequality)

**Definition**: Measure of inequality (0 = perfectly equal, 1 = perfectly unequal)

**Calculation**:
```python
def calculate_gini(values):
    """
    Calculate Gini coefficient for workload distribution.

    Interpretation:
    - 0.0-0.2: Very equal distribution
    - 0.2-0.3: Moderately equal
    - 0.3-0.4: Moderately unequal
    - 0.4+: Very unequal (CONCERN)
    """
    sorted_values = sorted(values)
    n = len(sorted_values)
    cumsum = 0

    for i, val in enumerate(sorted_values):
        cumsum += (2 * (i + 1) - n - 1) * val

    return cumsum / (n * sum(sorted_values))
```

**Usage in Report**:
- Calculate Gini for sessions per consultant
- If Gini > 0.4: Flag as "Unequal workload distribution - investigate further"
- Include Gini on workload distribution chart

### 12.2 Workload Distribution Stats

```python
workload_stats = {
    'mean': sessions_per_consultant.mean(),
    'median': sessions_per_consultant.median(),
    'std': sessions_per_consultant.std(),
    'min': sessions_per_consultant.min(),
    'max': sessions_per_consultant.max(),
    'gini': calculate_gini(sessions_per_consultant),
    'range': sessions_per_consultant.max() - sessions_per_consultant.min(),
}
```

### 12.3 Identifying "Slacking"

**Define "slacking" as**:
- Sessions < (Mean - 1 × Std Dev)
- Or: Sessions < 50th percentile

**Visualization**:
- Highlight low-performing consultants in red on bar chart
- Add reference line for mean sessions
- Add reference line for acceptable minimum (e.g., mean - 1 std)

---

## 13. User Interface

### 13.1 Command-Line Interface

```bash
# Walk-in report only
python main.py --walkins check_ins.csv --output walkin_report.pdf

# With anonymization + codebook
python main.py --walkins check_ins.csv --output walkin_report.pdf --codebook --password

# Without codebook (simple anonymization)
python main.py --walkins check_ins.csv --output walkin_report.pdf --no-codebook

# Scheduled report (existing functionality)
python main.py --scheduled sessions.csv --output scheduled_report.pdf
```

### 13.2 Configuration

```yaml
# config.yaml

data:
  walkins: "check_ins.csv"
  scheduled: "sessions.csv"  # Separate reports

processing:
  remove_outliers: true
  outlier_method: "cap"  # Options: cap | remove
  duration_cap_minutes: 180  # Cap at 3 hours
  anonymize: true
  create_codebook: true

walkin_report:
  include_sections:
    - executive_summary
    - consultant_sessions  # Status = Completed
    - independent_usage    # Status = Check In
    - cancellations
    - data_quality

  charts:
    consultant_workload_priority: high  # Generate first
    include_check_in_charts: true
```

---

## 14. Data Quality Tracking

### 14.1 Known Issues to Track

| Issue | Expected Frequency | Impact | Handling |
|-------|-------------------|--------|----------|
| **Duration Outliers** | ~5 sessions >500 min | Skews averages | Cap at 180 min + footnote |
| **Missing Tutor (Completed)** | Small number | Can't attribute workload | Exclude from consultant metrics |
| **In Progress** | Small number | Incomplete data | Exclude entirely |
| **Cancelled** | ~50-100 | No duration data | Separate analysis |
| **Check In (no tutor)** | ~100 | Expected behavior | Separate section |
| **Course = "Other"** | ~869 (35%) | Low specificity | Accept, note in report |

### 14.2 Data Quality Metrics Page

```python
quality_metrics = {
    'total_rows': len(df),
    'completed_sessions': len(df[df['Status'] == 'Completed']),
    'check_in_sessions': len(df[df['Status'] == 'Check In']),
    'cancelled_sessions': len(df[df['Status'] == 'Cancelled']),
    'in_progress_sessions': len(df[df['Status'] == 'In Progress']),
    'missing_tutor_for_completed': len(completed_df[completed_df['Tutor_Anon_ID'].isna()]),
    'duration_outliers': len(df[df['Duration Minutes'] > 180]),
    'duration_outliers_capped': True,  # or False
    'course_other_pct': (df['Course'] == 'Other').mean() * 100,
}
```

---

## 15. Next Steps

1. **Get user decisions on Course consolidation** (Section 11.1)
2. **Review and approve this plan**
3. **Begin Phase 1: Data Cleaning** (3-4 days)
4. **Set up testing environment**
5. **Start coding!**

---

*Document Version: 2.0 (Walk-In Only)*
*Last Updated: 2026-01-17*
*Author: Writing Studio Analytics Team*
