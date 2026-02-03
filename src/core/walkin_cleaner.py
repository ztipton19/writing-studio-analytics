# src/processing/walkin_cleaner.py

"""
Walk-In Data Cleaning Module

Handles data cleaning for walk-in check-in data from Penji exports.
Includes course consolidation, datetime parsing, outlier handling, and derived fields.

Author: Writing Studio Analytics Team
Date: 2026-01-19
"""

import pandas as pd
import numpy as np
from datetime import datetime

# Import academic calendar utilities
try:
    from src.utils.academic_calendar import add_semester_columns
except ImportError:
    try:
        from src.utils.academic_calendar import add_semester_columns
    except ImportError:
        print("Warning: academic_calendar.py not found. Semester columns will not be added.")
        add_semester_columns = None


# ============================================================================
# MAIN CLEANING PIPELINE
# ============================================================================

def clean_walkin_data(df):
    """
    Main cleaning pipeline for walk-in data.
    
    Steps:
    1. Parse datetime columns
    2. Consolidate course field
    3. Handle duration outliers (IQR method)
    4. Add derived fields (semester, day_of_week, hour, etc.)
    5. Drop useless columns
    6. Validate data quality
    
    Parameters:
    - df: Raw walk-in DataFrame from Penji CSV
    
    Returns:
    - Cleaned DataFrame ready for anonymization and analysis
    - Dictionary with cleaning log (including outlier stats)
    """
    
    print("\n" + "="*70)
    print("WALK-IN DATA CLEANING PIPELINE")
    print("="*70)
    
    cleaning_log = {
        'mode': 'walkin',
        'original_rows': len(df),
        'original_cols': len(df.columns),
        'final_rows': 0,
        'final_cols': 0
    }
    
    df_clean = df.copy()
    
    # Step 1: Parse datetimes
    print("\n[1/6] Parsing datetime columns...")
    df_clean = parse_walkin_datetimes(df_clean)
    
    # Step 2: Consolidate courses
    print("[2/6] Consolidating course categories...")
    df_clean = consolidate_courses(df_clean)
    
    # Step 3: Handle duration outliers
    print("[3/6] Handling duration outliers...")
    df_clean, outlier_stats = handle_duration_outliers(df_clean)
    cleaning_log['outliers_removed'] = outlier_stats
    
    # Step 4: Add derived fields
    print("[4/6] Adding derived fields...")
    df_clean = add_derived_fields(df_clean)
    
    # Step 5: Drop useless columns
    print("[5/6] Dropping useless columns...")
    df_clean = drop_useless_columns(df_clean)
    
    # Step 6: Validate data quality
    print("[6/6] Validating data quality...")
    quality_report = validate_data_quality(df_clean)
    cleaning_log['quality_report'] = quality_report
    
    # Update final counts
    cleaning_log['final_rows'] = len(df_clean)
    cleaning_log['final_cols'] = len(df_clean.columns)
    
    # Summary
    print("\n" + "="*70)
    print("CLEANING SUMMARY")
    print("="*70)
    print(f"Original rows: {len(df)}")
    print(f"Cleaned rows: {len(df_clean)}")
    print(f"Columns: {len(df.columns)} → {len(df_clean.columns)}")
    if outlier_stats['removed_count'] > 0:
        print(f"Outliers removed: {outlier_stats['removed_count']} ({outlier_stats['removed_pct']:.1f}%)")
        print(f"Valid range: {outlier_stats['lower_bound']:.2f} - {outlier_stats['upper_bound']:.2f} minutes")
    else:
        print(f"Outliers removed: 0")
    print(f"Missing data issues: {quality_report['total_issues']}")
    print("="*70 + "\n")
    
    return df_clean, cleaning_log


# ============================================================================
# DATETIME PARSING
# ============================================================================

def parse_walkin_datetimes(df):
    """
    Parse walk-in datetime columns.
    
    Walk-in CSV has separate date/time columns:
    - Check In At Date + Check In At Time
    - Started At Date + Started At Time  
    - Ended At Date + Ended At Time
    - Cancelled At Date + Cancelled At Time
    
    Combines them into proper datetime objects.
    """
    df_clean = df.copy()
    
    # Parse Check In datetime
    if 'Check In At Date' in df.columns and 'Check In At Time' in df.columns:
        df_clean['Check_In_DateTime'] = pd.to_datetime(
            df_clean['Check In At Date'] + ' ' + df_clean['Check In At Time'],
            errors='coerce'
        )
        parsed = df_clean['Check_In_DateTime'].notna().sum()
        print(f"  ✓ Parsed Check In DateTime: {parsed} records")
    
    # Parse Started At datetime
    if 'Started At Date' in df.columns and 'Started At Time' in df.columns:
        df_clean['Started_DateTime'] = pd.to_datetime(
            df_clean['Started At Date'] + ' ' + df_clean['Started At Time'],
            errors='coerce'
        )
        parsed = df_clean['Started_DateTime'].notna().sum()
        print(f"  ✓ Parsed Started DateTime: {parsed} records")
    
    # Parse Ended At datetime
    if 'Ended At Date' in df.columns and 'Ended At Time' in df.columns:
        df_clean['Ended_DateTime'] = pd.to_datetime(
            df_clean['Ended At Date'] + ' ' + df_clean['Ended At Time'],
            errors='coerce'
        )
        parsed = df_clean['Ended_DateTime'].notna().sum()
        print(f"  ✓ Parsed Ended DateTime: {parsed} records")
    
    # Parse Cancelled At datetime
    if 'Cancelled At Date' in df.columns and 'Cancelled At Time' in df.columns:
        df_clean['Cancelled_DateTime'] = pd.to_datetime(
            df_clean['Cancelled At Date'] + ' ' + df_clean['Cancelled At Time'],
            errors='coerce'
        )
        parsed = df_clean['Cancelled_DateTime'].notna().sum()
        if parsed > 0:
            print(f"  ✓ Parsed Cancelled DateTime: {parsed} records")
    
    return df_clean


# ============================================================================
# COURSE CONSOLIDATION
# ============================================================================

def consolidate_courses(df):
    """
    Consolidate course field variations into consistent categories.
    
    Applies 4 approved consolidation rules:
    1. "Other topic not listed..." → "Other"
    2. Duplicate text (e.g., "Speech outlineSpeech outline") → single text
    3. Thesis/dissertation variations → "Thesis or dissertation"
    4. Reflection paper variations → "Reflection or response paper"
    
    Plus additional cleaning rules from analysis.
    """
    df_clean = df.copy()
    
    if 'Course' not in df.columns:
        print("  ⚠️  No 'Course' column found - skipping consolidation")
        return df_clean
    
    # Track changes
    original_unique = df_clean['Course'].nunique()
    
    # Create mapping dictionary
    course_mapping = {}
    
    # Rule 1: "Other" variations
    course_mapping.update({
        'Other topic not listed': 'Other',
        'Other topic not listed (please describe in intake form in "Is there anything else you\'d like to share?")': 'Other',
    })
    
    # Rule 2: Duplicate text patterns
    course_mapping.update({
        'Speech outlineSpeech outline': 'Speech outline',
        'Scientific or lab reportScientific or lab report': 'Scientific or lab report',
        'Reflection or response paperReflection or response paper': 'Reflection or response paper',
    })
    
    # Rule 3: Thesis/dissertation variations
    course_mapping.update({
        'Thesis or dissertation (Undergraduate/Graduate)': 'Thesis or dissertation',
        'Thesis or dissertation (Undergradaute/Graduate)': 'Thesis or dissertation',  # Typo in data
    })
    
    # Rule 0: XXXX to N/A recode
    course_mapping.update({
        'XXXX': 'N/A',
    })

    # Rule 4: Reflection paper variations (APPROVED: consolidate all)
    course_mapping.update({
        'Reflection paper': 'Reflection or response paper',
        'Response paper': 'Reflection or response paper',
    })
    
    # Additional approved consolidations
    course_mapping.update({
        # Analysis papers (APPROVED: consolidate)
        'Analysis Paper': 'Analysis Paper: Historical Sources',
        
        # Professional writing (APPROVED: consolidate)
        'Professional writing': 'Professional or technical writing assignment',
        
        # Application essays (APPROVED: shorten)
        'Application essay (scholarship, graduate school, SOP, etc.)': 'Application essay',
    })
    
    # Apply mapping
    df_clean['Course'] = df_clean['Course'].replace(course_mapping)
    
    # Additional cleaning: strip whitespace
    df_clean['Course'] = df_clean['Course'].str.strip()
    
    # Classify real course codes vs document types
    # Note: Always creates Course_Code column for backward compatibility with older data
    import os
    valid_codes = set()
    try:
        courses_path = os.path.join(os.path.dirname(__file__), '..', '..', 'courses.csv')
        courses_df = pd.read_csv(courses_path)
        for _, row in courses_df.iterrows():
            abbrev = str(row['Subject Abbreviation']).strip()
            number = str(row['Course Number']).strip()
            code = abbrev + number
            valid_codes.add(code)
    except FileNotFoundError:
        print("  ⚠️  courses.csv not found - skipping course classification")
    
    if valid_codes:
        def classify(value):
            if pd.isna(value):
                return np.nan
            value_clean = str(value).strip()
            if value_clean == 'N/A':
                return 'N/A'
            if value_clean in valid_codes:
                return value_clean
            return np.nan  # It's an old document type, not a course
        
        df_clean['Course_Code'] = df_clean['Course'].apply(classify)
        code_count = df_clean['Course_Code'].notna().sum()
        print(f"  ✓ Course codes identified: {code_count}")
    else:
        # Create empty Course_Code column if no valid codes available
        df_clean['Course_Code'] = np.nan
    
    # Summary
    final_unique = df_clean['Course'].nunique()
    consolidated = original_unique - final_unique
    
    print(f"  ✓ Course categories: {original_unique} → {final_unique} ({consolidated} consolidated)")
    
    return df_clean


# ============================================================================
# DURATION OUTLIER HANDLING
# ============================================================================

def handle_duration_outliers(df, method='iqr'):
    """
    Handle extreme duration outliers using IQR method (same as scheduled sessions).
    
    Strategy: Remove rows beyond Q3 + 1.5*IQR (statistical outlier removal)
    
    Rationale:
    - Uses statistical method to identify outliers (same as scheduled sessions)
    - Removes outlier rows entirely (not just capping)
    - Consistent with user-facing "Remove statistical outliers" checkbox
    
    Parameters:
    - df: DataFrame with 'Duration Minutes' column
    - method: Outlier detection method (default: 'iqr')
    
    Returns:
    - DataFrame with outliers removed
    - Dictionary with outlier statistics
    """
    df_clean = df.copy()
    
    stats = {
        'removed_count': 0,
        'removed_pct': 0,
        'lower_bound': 0,
        'upper_bound': 0,
        'method': method,
        'original_count': len(df),
        'final_count': len(df)
    }
    
    if 'Duration Minutes' not in df.columns:
        print("  ⚠️  No 'Duration Minutes' column found - skipping outlier handling")
        return df_clean, stats
    
    original_count = len(df_clean)
    values = df_clean['Duration Minutes'].dropna()
    
    if len(values) == 0:
        print("  ⚠️  No valid duration values - skipping outlier handling")
        return df_clean, stats
    
    if method == 'iqr':
        # Calculate IQR bounds
        Q1 = values.quantile(0.25)
        Q3 = values.quantile(0.75)
        IQR = Q3 - Q1
        lower_bound = max(3, Q1 - 1.5 * IQR)  # At least 3 minutes
        upper_bound = Q3 + 1.5 * IQR
        
        stats['lower_bound'] = round(lower_bound, 2)
        stats['upper_bound'] = round(upper_bound, 2)
        
        # Remove outliers (keep NaN values)
        df_clean = df_clean[
            (df_clean['Duration Minutes'].isna()) |
            ((df_clean['Duration Minutes'] >= lower_bound) & 
             (df_clean['Duration Minutes'] <= upper_bound))
        ].copy()
        
        removed_count = original_count - len(df_clean)
        stats['removed_count'] = removed_count
        stats['removed_pct'] = (removed_count / original_count) * 100 if original_count > 0 else 0
        stats['final_count'] = len(df_clean)
        
        if removed_count > 0:
            print(f"  ⚠️  Removed {removed_count} outliers ({stats['removed_pct']:.1f}%)")
            print(f"      Valid range: {stats['lower_bound']:.2f} - {stats['upper_bound']:.2f} minutes")
        else:
            print(f"  ✓ No outliers found (all within {stats['lower_bound']:.2f}-{stats['upper_bound']:.2f} min)")
    else:
        print(f"  ⚠️  Unknown method: {method} - skipping outlier handling")
    
    return df_clean, stats


# ============================================================================
# DERIVED FIELDS
# ============================================================================

def add_derived_fields(df):
    """
    Add derived fields for analysis.
    
    Derived fields:
    - Semester (Spring/Summer/Fall)
    - Academic_Year (2024-2025)
    - Semester_Label (Spring 2025)
    - Day_of_Week (Monday, Tuesday, etc.)
    - Hour_of_Day (0-23)
    - Wait_Time_Minutes (Check-in to start time)
    """
    df_clean = df.copy()
    
    # Add semester columns using academic_calendar.py
    if add_semester_columns and 'Check_In_DateTime' in df_clean.columns:
        try:
            df_clean = add_semester_columns(df_clean, date_column='Check_In_DateTime')
            print("  ✓ Added semester columns (Semester, Academic_Year, Semester_Label)")
        except Exception as e:
            print(f"  ⚠️  Could not add semester columns: {e}")
    
    # Add day of week
    if 'Check_In_DateTime' in df_clean.columns:
        df_clean['Day_of_Week'] = df_clean['Check_In_DateTime'].dt.day_name()
        print("  ✓ Added Day_of_Week")
    
    # Add hour of day
    if 'Check_In_DateTime' in df_clean.columns:
        df_clean['Hour_of_Day'] = df_clean['Check_In_DateTime'].dt.hour
        print("  ✓ Added Hour_of_Day")
    
    # Calculate wait time (check-in to start)
    if 'Check_In_DateTime' in df_clean.columns and 'Started_DateTime' in df_clean.columns:
        wait_time = (df_clean['Started_DateTime'] - df_clean['Check_In_DateTime']).dt.total_seconds() / 60
        df_clean['Wait_Time_Minutes'] = wait_time
        
        # Only show stats for positive wait times
        valid_waits = wait_time[wait_time > 0]
        if len(valid_waits) > 0:
            print(f"  ✓ Added Wait_Time_Minutes (avg: {valid_waits.mean():.1f} min)")
    
    return df_clean


# ============================================================================
# DROP USELESS COLUMNS
# ============================================================================

def drop_useless_columns(df):
    """
    Drop columns that aren't useful for analysis.
    
    Columns to drop:
    - Mode: Useless (always "Queue" or "Log")
    - Location: Only one location
    - Requested Tutor Name: Mostly empty (and is PII)
    - Resource: Mostly empty
    - Topic: Mostly empty
    - Original date/time columns (we have parsed datetimes now)
    """
    df_clean = df.copy()
    
    columns_to_drop = [
        # Useless columns per spec
        'Mode',
        'Location',
        'Resource',
        'Topic',
        
        # Original date/time columns (we have parsed versions now)
        'Check In At Date',
        'Check In At Time',
        'Started At Date',
        'Started At Time',
        'Ended At Date',
        'Ended At Time',
        'Cancelled At Date',
        'Cancelled At Time',
    ]
    
    dropped = []
    for col in columns_to_drop:
        if col in df_clean.columns:
            df_clean = df_clean.drop(columns=[col])
            dropped.append(col)
    
    if dropped:
        print(f"  ✓ Dropped {len(dropped)} useless columns")
        for col in dropped[:5]:  # Show first 5
            print(f"      - {col}")
        if len(dropped) > 5:
            print(f"      ... and {len(dropped)-5} more")
    
    return df_clean


# ============================================================================
# DATA QUALITY VALIDATION
# ============================================================================

def validate_data_quality(df):
    """
    Validate data quality and report issues.
    
    Checks:
    - Missing required fields
    - Invalid status values
    - Negative durations
    - Missing tutors for "Completed" sessions
    - Date range sanity
    
    Returns:
    - Dictionary with quality metrics
    """
    issues = []
    
    # Check 1: Required fields present
    required_fields = ['Unique ID', 'Status', 'Course']
    for field in required_fields:
        if field not in df.columns:
            issues.append(f"Missing required field: {field}")
    
    # Check 2: Valid status values
    if 'Status' in df.columns:
        valid_statuses = ['Completed', 'Check In', 'Cancelled', 'In Progress']
        invalid_statuses = df[~df['Status'].isin(valid_statuses)]
        if len(invalid_statuses) > 0:
            issues.append(f"Invalid status values: {len(invalid_statuses)} records")
    
    # Check 3: Negative durations
    if 'Duration Minutes' in df.columns:
        negative = df[df['Duration Minutes'] < 0]
        if len(negative) > 0:
            issues.append(f"Negative durations: {len(negative)} records")
    
    # Check 4: Missing tutors for Completed sessions
    if 'Status' in df.columns:
        completed = df[df['Status'] == 'Completed']
        if len(completed) > 0:
            # Check if we have anonymized tutor IDs (post-anonymization check)
            if 'Tutor_Anon_ID' in df.columns:
                missing_tutors = completed[completed['Tutor_Anon_ID'].isna()]
            # Or check original tutor email (pre-anonymization check)
            elif 'Tutor Email' in df.columns:
                missing_tutors = completed[completed['Tutor Email'].isna()]
            else:
                missing_tutors = pd.DataFrame()  # Can't check
            
            if len(missing_tutors) > 0:
                issues.append(f"Completed sessions missing tutor: {len(missing_tutors)} records")
    
    # Check 5: Date range sanity
    if 'Check_In_DateTime' in df.columns:
        min_date = df['Check_In_DateTime'].min()
        max_date = df['Check_In_DateTime'].max()
        
        # Check if dates are in reasonable range (not in future, not too old)
        if pd.notna(max_date) and max_date > datetime.now():
            issues.append("Future dates detected in dataset")
        
        if pd.notna(min_date) and min_date.year < 2020:
            issues.append("Very old dates detected (pre-2020)")
    
    # Build report
    report = {
        'total_issues': len(issues),
        'issues': issues,
        'total_records': len(df),
        'status_distribution': df['Status'].value_counts().to_dict() if 'Status' in df.columns else {},
        'date_range': f"{df['Check_In_DateTime'].min().date()} to {df['Check_In_DateTime'].max().date()}" if 'Check_In_DateTime' in df.columns else 'Unknown'
    }
    
    # Print summary
    if issues:
        print(f"  ⚠️  Found {len(issues)} data quality issues:")
        for issue in issues:
            print(f"      - {issue}")
    else:
        print("  ✓ No data quality issues found")
    
    print("\n  Status distribution:")
    for status, count in report['status_distribution'].items():
        print(f"      {status}: {count}")
    
    return report


# ============================================================================
# CONVENIENCE FUNCTIONS
# ============================================================================

def get_completed_sessions(df):
    """
    Filter to only Completed sessions (met with consultant).
    
    Use for consultant workload analysis.
    """
    if 'Status' not in df.columns:
        raise ValueError("No 'Status' column found in dataframe")
    
    return df[df['Status'] == 'Completed'].copy()


def get_checkin_sessions(df):
    """
    Filter to only Check In sessions (used space independently).
    
    Use for independent space usage analysis.
    """
    if 'Status' not in df.columns:
        raise ValueError("No 'Status' column found in dataframe")
    
    return df[df['Status'] == 'Check In'].copy()


def get_cancelled_sessions(df):
    """
    Filter to only Cancelled sessions.
    
    Use for cancellation analysis.
    """
    if 'Status' not in df.columns:
        raise ValueError("No 'Status' column found in dataframe")
    
    return df[df['Status'] == 'Cancelled'].copy()


# ============================================================================
# MAIN FUNCTION FOR TESTING
# ============================================================================

if __name__ == "__main__":
    print("Walk-In Data Cleaner Module")
    print("=" * 70)
    print("\nThis module provides data cleaning functions for walk-in data.")
    print("\nMain function: clean_walkin_data(df)")
    print("\nUsage:")
    print("  from walkin_cleaner import clean_walkin_data")
    print("  df_clean = clean_walkin_data(df_raw)")
    print("\nHelper functions:")
    print("  - get_completed_sessions(df)")
    print("  - get_checkin_sessions(df)")
    print("  - get_cancelled_sessions(df)")
    print("=" * 70)
