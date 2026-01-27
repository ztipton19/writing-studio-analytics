# Writing Studio Analytics

A comprehensive, privacy-first analytics tool for university writing centers. Built for the University of Arkansas Writing Studio to generate FERPA-compliant reports from Penji export data.

## ✨ What Makes This Cool

### 🎯 Privacy-First by Design

-   **Automatic PII Detection**: Two-layer system identifies emails, names, and student IDs
-   **Federated Anonymization**: SHA256 hashing creates consistent anonymous IDs (e.g., `STU_04521`)
-   **Encrypted Codebook**: Optional reverse-lookup capability for supervisors (PBKDF2 + Fernet encryption)
-   **FERPA-Compliant**: Share reports publicly without revealing student/tutor identities

### 📊 Dual Mode Support

Supports **two distinct session types** from Penji:

1.  **Scheduled Sessions** (40-minute appointments)
    -   Full pre/post session surveys
    -   Confidence metrics (before/after)
    -   Satisfaction ratings (1-7 scale)
    -   Tutor quality assessments
    -   Incentive tracking (extra credit, class requirements)
2.  **Walk-In Sessions** (drop-in visits)
    -   Variable duration sessions
    -   Consultant workload analysis
    -   Independent space usage tracking
    -   Temporal pattern analysis
    -   Course distribution metrics

### 🔬 Advanced Analytics

-   **Booking Behavior**: Lead time analysis, booking patterns, peak times
-   **Attendance Metrics**: Completion rates, no-shows, cancellations by day/semester
-   **Session Quality**: Duration statistics, outlier detection (IQR method)
-   **Student Satisfaction**: Pre/post confidence changes, satisfaction trends
-   **Tutor Performance**: Workload distribution, session lengths, balance analysis
-   **Incentive Research**: Statistical analysis of incentivized vs. non-incentivized sessions
-   **Temporal Patterns**: Heatmaps, day-of-week trends, peak hours
-   **Academic Calendar**: Semester-based analysis (Spring/Summer/Fall)

### 📈 Professional Visualizations

-   **PDF Reports**: Multi-page reports with executive summaries
-   **Interactive Charts**: Bar charts, pie charts, line graphs, heatmaps
-   **Small Multiples**: Semester comparisons side-by-side
-   **Custom Styling**: Professional color scheme and layout

### 🤖 AI Chat Assistant

-   **Natural Language Queries**: Ask questions about your data in plain English
-   **Local-Only Inference**: Uses Gemma 3 4B model running entirely on your machine
-   **Privacy-First**: No cloud APIs or external services - your data never leaves your computer
-   **Code Execution**: Can run Python code to analyze data on-the-fly
-   **Optional Feature**: Works perfectly without AI - model download is optional

To use the AI Chat, download the model (~3 GB) from:
```
https://ws-analytics-chatbot.s3.us-east-2.amazonaws.com/gemma-3-4b-it-q4_0.gguf
```
Place it in the `models/` folder. The app includes a built-in downloader interface for convenience.

## 🚀 Quick Start

### Installation

``` bash
# Clone the repository
git clone https://github.com/ztipton19/writing-studio-analytics.git
cd writing-studio-analytics

# Install dependencies
pip install -r requirements.txt
```

### Running the Application

**Option 1: Windows (Recommended)**
``` bash
# Double-click launch.bat to start the application
# The launcher automatically finds Python and starts Streamlit
```

**Option 2: Command Line**
``` bash
# Start the Streamlit app
streamlit run app.py
```

The app will open in your browser at `http://localhost:8501`

## � How to Use

### Step 1: Select Session Type

Choose the type of data you're analyzing: - **40-Minute Sessions (Scheduled)**: Pre-booked appointments with full survey data - **Walk-In Sessions**: Drop-in visits with variable duration, minimal survey data

The tool will auto-detect the file type and warn you if there's a mismatch.

### Step 2: Upload Your Data

Export your data from Penji as CSV or Excel file and upload it through the interface. The tool will display: - File dimensions (rows × columns) - Date range covered - Session statistics (completed, cancelled, no-shows) - Unique participants (tutors/students)

### Step 3: Configure Options

**Remove Statistical Outliers**: - Uses IQR method to remove extreme session lengths - Filters out data errors (e.g., 23-hour sessions from forgot-to-close) - Recommended: Enable for accurate statistics

**Generate Codebook**: - Creates encrypted lookup table for supervisor access - Enables investigation of specific anonymous IDs - **Important**: Requires password (12+ characters)

### Step 4: Generate Report

Click "Generate Report" to create: 1. **PDF Report**: Comprehensive analytics with visualizations 2. **Cleaned CSV**: Anonymized dataset ready for analysis 3. **Codebook**: Encrypted mapping file (if enabled)

### Step 5: Download Results

Download your files directly from the interface: - PDF reports are safe to share publicly - Cleaned CSV contains anonymous IDs only - Codebook must be given to supervisor ONLY (with password)

### Codebook Lookup

If you generated a codebook, use the "Codebook Lookup" tab to: - Upload the encrypted codebook file - Enter the password - Reverse-lookup anonymous IDs (e.g., `STU_04521` → `student@email.com`) - Investigate specific cases flagged in reports

## 📁 Project Structure

```         
writing-studio-analytics/
├── app.py                          # Streamlit application entry point
├── requirements.txt                 # Python dependencies
├── README.md                       # This file
├── src/
│   ├── core/
│   │   ├── data_cleaner.py         # Scheduled sessions data cleaning
│   │   ├── walkin_cleaner.py       # Walk-in data cleaning
│   │   ├── metrics.py              # Scheduled sessions metrics
│   │   ├── walkin_metrics.py       # Walk-in metrics
│   │   └── privacy.py             # PII detection & anonymization
│   ├── utils/
│   │   └── academic_calendar.py    # Semester detection & utilities
│   └── visualizations/
│       ├── charts.py               # Chart functions (scheduled)
│       ├── walkin_charts.py       # Chart functions (walk-in)
│       ├── report_generator.py     # PDF report generator (scheduled)
│       └── walkin_report_generator.py  # PDF report generator (walk-in)
└── docs/
    ├── build-guide.md              # Developer documentation
    └── claude_context.md          # AI assistant context
```

## 🛠️ Technical Details

### Data Cleaning Pipeline

**Scheduled Sessions:** 1. Clean column names (strip whitespace) 2. Merge datetime columns (date + time → datetime) 3. Rename columns for consistency 4. Convert text ratings to numeric 5. Remove useless/redundant columns 6. Standardize data types 7. Create calculated fields (lead time, confidence change) 8. Remove outliers (optional, IQR method) 9. Escape Excel formulas 10. Validate data quality

**Walk-In Sessions:** 1. Parse datetime columns 2. Consolidate course categories 3. Handle duration outliers (IQR method) 4. Add derived fields (semester, day_of_week, hour_of_day) 5. Drop useless columns 6. Validate data quality

### Privacy & Security

**Anonymization:** - SHA256 hashing for deterministic anonymous IDs - Collision detection and handling - Supports both student and tutor anonymization - Graceful handling of missing data (walk-in sessions with no tutor)

**Encryption:** - PBKDF2 key derivation (100,000 iterations) - Fernet symmetric encryption (AES-128) - Password-based encryption for codebooks - Fixed salt for consistency

**PII Detection:** - Layer 1: Exact column name matching - Layer 2: Pattern-based detection (regex) - Supports both session types (scheduled + walk-in)

### Metrics & Analysis

**Scheduled Sessions Metrics:** - Booking behavior (lead time, patterns) - Attendance & outcomes (completion, no-show, cancellation) - Session length statistics - Student satisfaction & confidence - Tutor workload & performance - Student engagement (repeat vs. first-time) - Semester comparisons - Incentive analysis (with statistical t-tests)

**Walk-In Sessions Metrics:** - Consultant workload (sessions/hours per consultant) - Gini coefficient (workload inequality measure) - Temporal patterns (hour/day analysis) - Duration statistics (by session type, by course) - Check-in usage (independent space usage) - Course distribution

## 📊 Report Contents

### Scheduled Sessions Report

1.  **Cover Page**: Title, session count, date range
2.  **Metadata**: Data cleaning summary, date range, semester breakdown
3.  **Executive Summary**: Overview, key findings, concerns, recommendations
4.  **Booking Behavior**: Lead time breakdown, day of week, heatmap
5.  **Attendance & Outcomes**: Outcomes pie chart, no-show by day, trends
6.  **Student Satisfaction**: Pre/post confidence, satisfaction distribution, trends
7.  **Tutor Analytics**: Sessions per tutor, workload balance, session lengths
8.  **Session Content**: Writing stages, focus areas, first-time vs. returning
9.  **Incentive Analysis**: Incentive distribution, ratings by type (if data available)
10. **Data Quality**: Survey response rates, missing value analysis
11. **Semester Comparisons**: Growth trends, metrics comparison (if multiple semesters)

### Walk-In Sessions Report

1.  **Cover Page**: Title, session count, date range
2.  **Metadata**: Data summary, outlier info, date range, peak hours/days
3.  **Executive Summary**: Overview, key findings, concerns, recommendations
4.  **Consultant Workload**: Session distribution, hours per consultant
5.  **Temporal Patterns**: Sessions by day, heatmap of usage
6.  **Duration Analysis**: Completed vs. check-in durations, by course
7.  **Independent Space Usage**: Check-in patterns, courses for independent work
8.  **Course Distribution**: All courses, top courses pie chart

## 🔧 Advanced Usage

### Programmatic Usage

``` python
from src.core.data_cleaner import clean_data
from src.core.privacy import anonymize_with_codebook
from src.visualizations.report_generator import generate_full_report
import pandas as pd

# Load data
df = pd.read_csv('penji_export.csv')

# Clean data
df_clean, cleaning_log = clean_data(df, mode='scheduled', remove_outliers=True)

# Anonymize (optional codebook)
df_anon, codebook_path, anon_log = anonymize_with_codebook(
    df_clean, 
    create_codebook=True,
    password='your_secure_password_here',
    confirm_password='your_secure_password_here'
)

# Generate report
report_path = generate_full_report(df_anon, cleaning_log, 'report.pdf')
```

### Command Line (Quick Report)

``` python
from src.visualizations.report_generator import quick_report

# One-liner: load, clean, generate report
report_path = quick_report('penji_export.csv', 'report.pdf')
```

## 🐛 Troubleshooting

**Issue: "Walk-in modules not installed"** - Ensure all files are present in `src/core/` and `src/visualizations/` - Check imports in `app.py` are not raising exceptions

**Issue: "Password incorrect" during codebook lookup** - Verify password matches exactly (case-sensitive) - Ensure you're using the correct codebook file - Regenerate report if password is lost

**Issue: "Type mismatch detected"** - Check that you selected the correct session type - Verify your Penji export contains the expected columns - Export again if data structure seems incorrect

**Issue: Charts not displaying** - Check that `matplotlib` and `seaborn` are installed - Verify data has required columns for specific charts - Check console for error messages

## 🔧 For Future Developers

### Updating Data Processing Logic

If Penji changes their export format or adds/removes columns, you'll need to update these files:

**For Scheduled Sessions:**
- `src/core/data_cleaner.py` - Column mapping, data type conversions, outlier detection
- `src/core/metrics.py` - Metric calculations, new analyses
- `src/visualizations/charts.py` - Chart functions
- `src/visualizations/report_generator.py` - PDF report sections

**For Walk-In Sessions:**
- `src/core/walkin_cleaner.py` - Column mapping, data type conversions, outlier detection
- `src/core/walkin_metrics.py` - Metric calculations, new analyses
- `src/visualizations/walkin_charts.py` - Chart functions
- `src/visualizations/walkin_report_generator.py` - PDF report sections

### Critical: Privacy System

**NEVER remove or bypass the anonymization layer:**
- `src/core/privacy.py` contains the PII detection and anonymization logic
- Always anonymize before any analysis or reporting
- The codebook system allows supervisor access while maintaining FERPA compliance

### Adding New Features

1. **New metrics:** Add to `metrics.py` or `walkin_metrics.py`, then update report generators
2. **New charts:** Add to `charts.py` or `walkin_charts.py`, include in report generators
3. **New data cleaning:** Update `data_cleaner.py` or `walkin_cleaner.py`, test with real Penji exports

### Testing Changes

1. Export fresh data from Penji (both session types if applicable)
2. Test the full pipeline: upload → clean → anonymize → generate report
3. Verify no PII leaks in anonymized data or reports
4. Check codebook lookup functionality if enabled
5. Test with both outlier removal on and off

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 👤 Author

Created by Zachary Tipton (Graduate Assistant) University of Arkansas Writing Studio

## 🙏 Acknowledgments

-   Built for the University of Arkansas Writing Studio
-   Uses Penji export data format
-   Privacy-first design prioritizes student and tutor confidentiality
-   FERPA-compliant analytics approach

## 📞 Support

For questions or issues: - Review error messages in the Streamlit interface - Contact the Writing Studio administration team

------------------------------------------------------------------------

**Note**: This tool is designed to help writing centers understand their usage patterns while maintaining strict privacy standards. All student and tutor data is anonymized before analysis, and the encrypted codebook should only be shared with authorized supervisors.