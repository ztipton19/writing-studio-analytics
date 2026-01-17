# src/core/data_cleaner.py

import pandas as pd
import numpy as np
from datetime import datetime
import warnings

warnings.filterwarnings('ignore')


# ============================================================================
# SESSION TYPE DETECTION
# ============================================================================

def detect_session_type(df):
    """
    Auto-detect whether this is scheduled sessions or walk-in data.
    
    Returns: 'scheduled', 'walkin', or 'unknown'
    """
    # Scheduled session indicators
    scheduled_indicators = [
        'Appointment Type',
        'Requested Length',
        'Student - On a scale of 1-5'
    ]
    
    # Walk-in indicators
    walkin_indicators = [
        'Duration Minutes',
        'Check In At Date',
        'Check In At Time'
    ]
    
    # Check for scheduled
    scheduled_score = sum(1 for col in scheduled_indicators if col in df.columns)
    walkin_score = sum(1 for col in walkin_indicators if col in df.columns)
    
    if scheduled_score >= 2:
        return 'scheduled'
    elif walkin_score >= 2:
        return 'walkin'
    else:
        return 'unknown'


# ============================================================================
# COLUMN CLEANUP
# ============================================================================

def clean_column_names(df):
    """
    Clean column names by stripping whitespace.
    Penji exports often have trailing spaces that break column matching.
    """
    df_clean = df.copy()
    df_clean.columns = df_clean.columns.str.strip()
    return df_clean


# ============================================================================
# DATETIME MERGING
# ============================================================================

def merge_datetime_columns(df):
    """
    Merge separate date and time columns into single datetime objects.
    Handles NaN gracefully.
    """
    df_merged = df.copy()
    
    # Define date/time pairs to merge
    datetime_pairs = [
        ('Requested At Date', 'Requested At Time', 'Booking_DateTime'),
        ('Requested Start At Date', 'Requested Start At Time', 'Appointment_DateTime'),
        ('Started At Date', 'Started At Time', 'Actual_Start_DateTime'),
        ('Ended At Date', 'Ended At Time', 'Actual_End_DateTime'),
        ('Cancelled At Date', 'Cancelled At Time', 'Cancelled_DateTime')
    ]
    
    for date_col, time_col, new_col in datetime_pairs:
        if date_col in df_merged.columns and time_col in df_merged.columns:
            # Combine date and time, handling NaN
            df_merged[new_col] = pd.to_datetime(
                df_merged[date_col].astype(str) + ' ' + df_merged[time_col].astype(str),
                errors='coerce'  # NaN if either is missing
            )
    
    return df_merged


# ============================================================================
# COLUMN RENAMING
# ============================================================================

def rename_columns(df):
    """
    Rename columns to be more concise and analysis-friendly.
    Only renames columns that exist in the dataframe.
    """
    rename_map = {
        # Core Session Info
        'Unique ID': 'Session_ID',
        'Status': 'Status',
        'Course': 'Document_Type',
        'Location': 'Location',

        # Session Length
        'Tutor Submitted Length': 'Actual_Session_Length',
        
        # Attendance
        'Student Attendance': 'Attendance_Status',
        'Session Feedback From Student': 'Student_Feedback',
        
        # Pre-Session (Agenda)
        'Agenda - For which course are you writing this document? (If not applicable, write "N/A")': 'Course_Subject',
        'Agenda - How confident do you feel about your writing assignment right now? (1="Not at all"; 5="Very")': 'Pre_Confidence',
        'Agenda - Is this your first appointment?': 'Is_First_Appointment',
        'Agenda - Please check one of the following boxes to help us determine the context of your visit.': 'Visit_Context',
        'Agenda - Roughly speaking, what stage of the writing process are you in right now?': 'Writing_Stage',
        'Agenda - What would you like to focus on during this appointment?': 'Focus_Area',
        'Agenda - When is your paper due?': 'Paper_Due_Date',
        
        # Post-Session (Student Feedback)
        'Student - How confident do you feel about your writing assignment now that your meeting is over? (1="Not at all"; 5="Very")': 'Post_Confidence',
        'Student - On a scale of 1-5 (1="not at all," 5="extremely well"), how well did you get along with your tutor?': 'Tutor_Rapport',
        'Student - On a scale of 1-5 (1="not easy at all", 5="extremely easy"), how easy was it to use our website and scheduling software to schedule and attend your appointment?': 'Platform_Ease',
        'Student - On a scale of 1-5 (1="very poorly", 5="very well"), how well would you say your your appointment went?': 'Session_Quality',
        'Student - On a scale of 1-7 (1="extremely dissatisfied," 7="extremely satisfied"), how satisfied are you with the help you received at the Writing Studio?': 'Overall_Satisfaction',
        
        # Tutor Feedback
        'Tutor - Overall, how well would you say that the consultation went?': 'Tutor_Session_Rating'
    }
    
    # Only rename columns that exist
    existing_renames = {old: new for old, new in rename_map.items() if old in df.columns}
    df_renamed = df.rename(columns=existing_renames)

    return df_renamed, len(existing_renames)


# ============================================================================
# TEXT TO NUMERIC CONVERSION
# ============================================================================

def convert_text_ratings_to_numeric(df):
    """
    Convert text-based rating responses to numeric values.

    Handles two patterns:
    1. Tutor_Session_Rating: Full text responses like "It went very well"
    2. Student feedback fields: Numeric prefix format like "5 - Very well"
    """
    df_converted = df.copy()

    # Tutor Session Rating conversion map
    # Based on the question: "Overall, how well would you say that the consultation went?"
    # Actual values from Penji: "It went extremely well", "It went very well", etc.
    tutor_rating_map = {
        'It went extremely well': 5,
        'It went very well': 4,
        'It went moderately well': 3,
        'It went somewhat well': 2,
        "It didn't go well at all": 1,
        # Case-insensitive variants (lowercase)
        'it went extremely well': 5,
        'it went very well': 4,
        'it went moderately well': 3,
        'it went somewhat well': 2,
        "it didn't go well at all": 1
    }

    if 'Tutor_Session_Rating' in df_converted.columns:
        # Convert text to numeric using the mapping
        df_converted['Tutor_Session_Rating'] = df_converted['Tutor_Session_Rating'].map(tutor_rating_map)
        # Any unmapped values will become NaN (which is fine for data quality)

    # Extract numeric values from student feedback fields
    # These come in format: "5 - Very well" or "7 - Extremely satisfied"
    # We need to extract just the number at the beginning
    fields_to_extract = ['Tutor_Rapport', 'Platform_Ease', 'Session_Quality', 'Overall_Satisfaction']

    for field in fields_to_extract:
        if field in df_converted.columns:
            # Extract number from beginning of string (before the " - " separator)
            # Use regex to extract digits at the start, handling various formats
            df_converted[field] = df_converted[field].astype(str).str.extract(r'^(\d+)', expand=False)
            # Convert to numeric, any non-numeric becomes NaN
            df_converted[field] = pd.to_numeric(df_converted[field], errors='coerce')

    return df_converted


# ============================================================================
# COLUMN REMOVAL
# ============================================================================

def remove_useless_columns(df):
    """
    Remove columns that don't add value to analysis.
    """
    columns_to_remove = [
        # Always the same value (no variation)
        'Appointment Type',  # Always "40min 1-on-1"
        'Kind',              # Always "1-on-1"
        'Session_Kind',      # Duplicate of above

        # Redundant after datetime merge
        'Requested At Date',
        'Requested At Time',
        'Requested Start At Date',
        'Requested Start At Time',
        'Requested End At Date',
        'Requested End At Time',
        'Scheduled Start At Date',
        'Scheduled Start At Time',
        'Scheduled End At Date',
        'Scheduled End At Time',
        'Started At Date',
        'Started At Time',
        'Ended At Date',
        'Ended At Time',
        'Cancelled At Date',
        'Cancelled At Time',

        # Always 0.67 (40 minutes)
        'Requested Length',

        # Don't matter for analysis
        'Source Kind',
        'Booking Flow',
        'Booking_Source',
        'Booking_Method',

        # Not useful
        'Student Attendance Reason',
        'Attendance_Reason',

        # Useless columns
        'Recurrence',
        'Section',
        'Session Feedback From Tutor',  # Generated/blank column, duplicate of Session_Feedback_From_Tutor
        'Agenda - If you are meeting a Writing Consultant in-person, would you like to meet in a sensory-friendly, Low Distraction Room (LDR) if it is available?',
        'Agenda - If you have access to any rubrics or assignment sheets, please attach them here.',
        'Agenda - Please attach any assignment sheets, written directions, or rubrics for your paper.',
        'Agenda - Please upload your paper here.',
        'Tutor - Was this a mock or test consultation?',

        # Text feedback fields - can't run metrics on text data
        'Tutor - Please provide a brief overview of the topics discussed or issues addressed during your consultation.',  # Session_Feedback_From_Tutor
        'Agenda - Is there anything else you\'d like to share?',  # 52% filled but not useful
        'Cancel Reason',  # 12.9% - not useful
        'Student - Please share any comments that you\'d like your tutor to see.',  # 3.6% - Student_Comments_Public
        'Student - Please share any obstacles, disappointments, or problems that you encountered during your consultation at the Writing Studio.',  # Student_Issues - low fill
        'Student - Were you offered any of the following incentives for today\'s visit? Please select any that apply.'  # 90.6% null
    ]
    
    # Only remove columns that exist
    existing_removes = [col for col in columns_to_remove if col in df.columns]
    df_clean = df.drop(columns=existing_removes, errors='ignore')
    
    return df_clean, existing_removes


# ============================================================================
# DATA TYPE STANDARDIZATION
# ============================================================================

def standardize_data_types(df):
    """
    Convert columns to appropriate data types.
    Handles NaN gracefully throughout.
    """
    df_typed = df.copy()
    
    # Numeric columns (ratings, lengths)
    numeric_columns = [
        'Actual_Session_Length',
        'Pre_Confidence', 'Post_Confidence',
        'Tutor_Rapport', 'Platform_Ease',
        'Session_Quality', 'Overall_Satisfaction',
        'Tutor_Session_Rating'
    ]
    
    for col in numeric_columns:
        if col in df_typed.columns:
            df_typed[col] = pd.to_numeric(df_typed[col], errors='coerce')
    
    # Categorical columns (convert to category type for efficiency)
    categorical_columns = [
        'Status', 'Location', 'Attendance_Status',
        'Is_First_Appointment', 'Visit_Context', 'Writing_Stage'
    ]
    
    for col in categorical_columns:
        if col in df_typed.columns:
            df_typed[col] = df_typed[col].astype('category')
    
    # Text columns (ensure string type, replace NaN with empty string for text processing)
    text_columns = [
        'Document_Type', 'Course_Subject', 'Focus_Area',
        'Student_Comments_For_Tutor', 'Student_Comments_Public',
        'Student_Issues', 'Tutor_Feedback', 'Student_Feedback',
        'Cancellation_Reason', 'Incentives_Offered'
    ]
    
    for col in text_columns:
        if col in df_typed.columns:
            df_typed[col] = df_typed[col].fillna('').astype(str)
            # But mark truly empty as NaN for analysis purposes
            df_typed[col] = df_typed[col].replace('', np.nan)
    
    return df_typed


# ============================================================================
# CALCULATED FIELDS
# ============================================================================

def create_calculated_fields(df):
    """
    Create useful derived fields for analysis.
    """
    df_calc = df.copy()
    
    # Booking lead time (how far in advance they booked)
    if 'Booking_DateTime' in df_calc.columns and 'Appointment_DateTime' in df_calc.columns:
        df_calc['Booking_Lead_Time_Hours'] = (
            (df_calc['Appointment_DateTime'] - df_calc['Booking_DateTime'])
            .dt.total_seconds() / 3600
        )
        df_calc['Booking_Lead_Time_Days'] = df_calc['Booking_Lead_Time_Hours'] / 24
    
    # Confidence change (pre to post)
    if 'Pre_Confidence' in df_calc.columns and 'Post_Confidence' in df_calc.columns:
        df_calc['Confidence_Change'] = df_calc['Post_Confidence'] - df_calc['Pre_Confidence']
    
    # Actual session duration (if we have actual start/end times)
    if 'Actual_Start_DateTime' in df_calc.columns and 'Actual_End_DateTime' in df_calc.columns:
        df_calc['Calculated_Session_Length'] = (
            (df_calc['Actual_End_DateTime'] - df_calc['Actual_Start_DateTime'])
            .dt.total_seconds() / 3600
        )
    
    # Flag: First-time student (convert yes/no to boolean)
    if 'Is_First_Appointment' in df_calc.columns:
        df_calc['Is_First_Timer'] = df_calc['Is_First_Appointment'].str.lower().isin(['yes', 'y', 'true'])
    
    # Academic calendar fields (semester, academic year)
    if 'Appointment_DateTime' in df_calc.columns:
        # Import here to avoid circular imports
        from src.utils.academic_calendar import detect_semester, get_academic_year, get_semester_label
        
        df_calc['Semester'] = df_calc['Appointment_DateTime'].apply(detect_semester)
        df_calc['Academic_Year'] = df_calc['Appointment_DateTime'].apply(get_academic_year)
        df_calc['Semester_Label'] = df_calc['Appointment_DateTime'].apply(get_semester_label)
    
    return df_calc


# ============================================================================
# EXCEL FORMULA ESCAPING
# ============================================================================

def escape_excel_formulas(df):
    """
    Prevent Excel from treating text as formulas.
    Prepends single quote to cells starting with - or =
    """
    df_escaped = df.copy()
    
    # Apply to all object/string columns
    for col in df_escaped.select_dtypes(include=['object']).columns:
        df_escaped[col] = df_escaped[col].apply(
            lambda x: f"'{x}" if isinstance(x, str) and len(x) > 0 and x[0] in ('-', '=') else x
        )
    
    return df_escaped


# ============================================================================
# OUTLIER REMOVAL
# ============================================================================

def remove_outliers(df, column='Actual_Session_Length', method='iqr'):
    """
    Remove statistical outliers from session length data.
    
    Parameters:
    - column: Column to check for outliers
    - method: 'iqr' (default), 'percentile', or 'cap'
    
    Returns: (cleaned_df, outlier_stats)
    """
    if column not in df.columns:
        return df, {'removed_count': 0, 'method': 'column_not_found'}
    
    original_count = len(df)
    values = df[column].dropna()
    
    if len(values) == 0:
        return df, {'removed_count': 0, 'method': 'no_data'}
    
    if method == 'iqr':
        Q1 = values.quantile(0.25)
        Q3 = values.quantile(0.75)
        IQR = Q3 - Q1
        lower_bound = max(0.05, Q1 - 1.5 * IQR)  # At least 3 minutes
        upper_bound = Q3 + 1.5 * IQR
        
    elif method == 'percentile':
        lower_bound = values.quantile(0.05)
        upper_bound = values.quantile(0.95)
        
    elif method == 'cap':
        lower_bound = 0.05  # 3 minutes
        upper_bound = 2.0   # 2 hours
    
    else:
        raise ValueError(f"Unknown method: {method}")
    
    # Filter data
    df_clean = df[
        (df[column].isna()) |  # Keep NaN values
        ((df[column] >= lower_bound) & (df[column] <= upper_bound))
    ].copy()
    
    removed_count = original_count - len(df_clean)
    removed_pct = (removed_count / original_count) * 100 if original_count > 0 else 0
    
    outlier_stats = {
        'removed_count': removed_count,
        'removed_pct': removed_pct,
        'lower_bound': round(lower_bound, 2),
        'upper_bound': round(upper_bound, 2),
        'method': method,
        'original_count': original_count,
        'final_count': len(df_clean)
    }
    
    return df_clean, outlier_stats


# ============================================================================
# DATA QUALITY VALIDATION
# ============================================================================

def validate_data_quality(df):
    """
    Check for data quality issues and return warnings.
    Handles NaN gracefully - doesn't flag missing data as errors.
    """
    issues = []
    warnings_list = []
    
    # Check session lengths (only non-NaN values)
    if 'Actual_Session_Length' in df.columns:
        valid_lengths = df['Actual_Session_Length'].dropna()
        
        if len(valid_lengths) > 0:
            long_sessions = valid_lengths[valid_lengths > 3]
            if len(long_sessions) > 0:
                issues.append(f"⚠️ Found {len(long_sessions)} sessions longer than 3 hours (possible data error)")
            
            short_sessions = valid_lengths[valid_lengths < 0.05]  # Less than 3 minutes
            if len(short_sessions) > 0:
                issues.append(f"⚠️ Found {len(short_sessions)} sessions shorter than 3 minutes (possible data error)")
    
    # Check satisfaction scores are in valid ranges
    score_checks = [
        ('Pre_Confidence', 1, 5),
        ('Post_Confidence', 1, 5),
        ('Tutor_Rapport', 1, 5),
        ('Platform_Ease', 1, 5),
        ('Session_Quality', 1, 5),
        ('Overall_Satisfaction', 1, 7),
        ('Tutor_Session_Rating', 1, 5)
    ]
    
    for col, min_val, max_val in score_checks:
        if col in df.columns:
            valid_scores = df[col].dropna()
            invalid = valid_scores[(valid_scores < min_val) | (valid_scores > max_val)]
            
            if len(invalid) > 0:
                issues.append(f"⚠️ Found {len(invalid)} {col} scores outside {min_val}-{max_val} range")
    
    # Check for future appointments (might be scheduled sessions, not errors)
    if 'Appointment_DateTime' in df.columns:
        future_appts = df[df['Appointment_DateTime'] > pd.Timestamp.now()]
        if len(future_appts) > 0:
            warnings_list.append(f"ℹ️ Found {len(future_appts)} future appointments (likely scheduled sessions)")
    
    # Report on missing critical data (informational, not errors)
    critical_cols = ['Attendance_Status', 'Document_Type', 'Actual_Session_Length']
    for col in critical_cols:
        if col in df.columns:
            missing_count = df[col].isna().sum()
            missing_pct = (missing_count / len(df)) * 100
            
            if missing_pct > 20:
                warnings_list.append(f"ℹ️ {col}: {missing_pct:.1f}% missing data ({missing_count} rows)")
    
    return issues, warnings_list


# ============================================================================
# MISSING VALUE ANALYSIS (CONTEXT-AWARE)
# ============================================================================

def analyze_missing_values(df):
    """
    Smart missing value analysis that understands context.
    Distinguishes between "expected empty" vs "data quality issue"
    
    Returns: {
        'missing_data': {...},
        'context': {...}
    }
    """
    missing_report = {}
    
    # Define field categories and expectations
    conditional_fields = {
        'Cancellation_Reason': 'Only applies to cancelled sessions',
        'Student_Issues': 'Optional - students only fill if they had problems',
        'Student_Comments_For_Tutor': 'Optional feedback field',
        'Student_Comments_Public': 'Optional feedback field',
        'Incentives_Offered': 'Only applies if incentives were offered',
        'Paper_Due_Date': 'Optional - not all assignments have fixed deadlines',
    }
    
    critical_fields = {
        'Session_ID': 'Required - should never be missing',
        'Appointment_DateTime': 'Required - should never be missing',
        'Attendance_Status': 'Should be filled for all sessions',
        'Actual_Session_Length': 'Should be filled by tutor',
        'Status': 'Required - session status',
    }
    
    important_fields = {
        'Course_Subject': 'Important but often skipped by students',
        'Pre_Confidence': 'Pre-session survey - not always completed',
        'Post_Confidence': 'Post-session survey - not always completed',
        'Focus_Area': 'Important for understanding session goals',
        'Writing_Stage': 'Helpful for tracking student progress',
        'Visit_Context': 'Useful for categorizing sessions',
    }
    
    # Analyze each column
    for col in df.columns:
        missing_count = df[col].isna().sum()
        if missing_count > 0:
            missing_pct = (missing_count / len(df)) * 100
            
            # Categorize the missing data
            if col in conditional_fields:
                category = 'expected'
                explanation = conditional_fields[col]
                severity = 'ok'
            elif col in critical_fields:
                category = 'critical'
                explanation = critical_fields[col]
                severity = 'high'
            elif col in important_fields:
                category = 'concerning'
                explanation = important_fields[col]
                severity = 'medium' if missing_pct > 30 else 'low'
            else:
                category = 'optional'
                explanation = 'Optional field'
                severity = 'low'
            
            missing_report[col] = {
                'count': missing_count,
                'percentage': round(missing_pct, 1),
                'category': category,
                'severity': severity,
                'explanation': explanation
            }
    
    # Calculate contextual information
    context = {}
    
    # Cancellation context
    if 'Status' in df.columns:
        total_sessions = len(df)
        
        # Count cancelled sessions
        cancelled = df['Status'].str.lower().str.contains('cancel', na=False).sum()
        
        # No-shows are marked as "Absent" in Attendance_Status (different from cancelled)
        if 'Attendance_Status' in df.columns:
            no_show = df['Attendance_Status'].str.lower().str.contains('absent', na=False).sum()
            # Completed = marked as Present in Attendance_Status
            completed = df['Attendance_Status'].str.lower().str.contains('present', na=False).sum()
        else:
            # Fallback to Status column if Attendance_Status doesn't exist
            no_show = df['Status'].str.lower().str.contains('no.?show', na=False, regex=True).sum()
            completed = df['Status'].str.lower().str.contains('complete|attended', na=False, regex=True).sum()
        
        context['cancellations'] = {
            'total_sessions': total_sessions,
            'cancelled': cancelled,
            'no_show': no_show,
            'completed': completed,
            'cancellation_rate': round((cancelled / total_sessions) * 100, 1) if total_sessions > 0 else 0,
            'no_show_rate': round((no_show / total_sessions) * 100, 1) if total_sessions > 0 else 0,
            'completion_rate': round((completed / total_sessions) * 100, 1) if total_sessions > 0 else 0,
        }
    
    # Student issues context
    if 'Student_Issues' in df.columns:
        has_issues = df['Student_Issues'].notna().sum()
        context['student_issues'] = {
            'sessions_with_issues': has_issues,
            'sessions_without_issues': len(df) - has_issues,
            'issue_rate': round((has_issues / len(df)) * 100, 1)
        }
    
    # Survey completion context
    if 'Pre_Confidence' in df.columns and 'Post_Confidence' in df.columns:
        pre_completed = df['Pre_Confidence'].notna().sum()
        post_completed = df['Post_Confidence'].notna().sum()
        both_completed = df[df['Pre_Confidence'].notna() & df['Post_Confidence'].notna()].shape[0]
        
        context['surveys'] = {
            'pre_survey_completion_rate': round((pre_completed / len(df)) * 100, 1),
            'post_survey_completion_rate': round((post_completed / len(df)) * 100, 1),
            'both_surveys_completion_rate': round((both_completed / len(df)) * 100, 1)
        }
    
    return {
        'missing_data': missing_report,
        'context': context
    }


# ============================================================================
# MAIN CLEANING FUNCTION: SCHEDULED SESSIONS
# ============================================================================

def clean_scheduled_sessions(df, remove_outliers_flag=True, log_actions=True):
    """
    Complete cleaning pipeline for scheduled 40-minute sessions.
    Handles NaN values gracefully throughout.
    
    Parameters:
    - df: Raw dataframe from Penji export
    - remove_outliers_flag: Whether to remove statistical outliers
    - log_actions: Print progress/results
    
    Returns: (cleaned_df, cleaning_log)
    """
    if log_actions:
        print("\n" + "="*80)
        print("🧹 DATA CLEANING - SCHEDULED SESSIONS")
        print("="*80)
        print(f"\nOriginal dataset: {len(df):,} rows × {len(df.columns)} columns")
    
    cleaning_log = {
        'original_rows': len(df),
        'original_cols': len(df.columns)
    }

    # Step 0: Clean column names (strip whitespace)
    df_clean = clean_column_names(df)
    if log_actions:
        print("\n✓ Step 0: Cleaned column names (stripped whitespace)")

    # Step 1: Merge date/time columns
    df_clean = merge_datetime_columns(df_clean)
    if log_actions:
        print("✓ Step 1: Merged date/time columns into datetime objects")
    
    # Step 2: Rename columns
    df_clean, rename_count = rename_columns(df_clean)
    cleaning_log['renamed_columns'] = rename_count
    if log_actions:
        print(f"✓ Step 2: Renamed {rename_count} columns for clarity")

    # Step 2.5: Convert text ratings to numeric
    df_clean = convert_text_ratings_to_numeric(df_clean)
    if log_actions:
        print("✓ Step 2.5: Converted text ratings to numeric values")

    # Step 3: Remove useless columns
    df_clean, removed_cols = remove_useless_columns(df_clean)
    cleaning_log['removed_columns'] = removed_cols
    if log_actions:
        print(f"✓ Step 3: Removed {len(removed_cols)} unnecessary columns")
    
    # Step 4: Standardize data types
    df_clean = standardize_data_types(df_clean)
    if log_actions:
        print("✓ Step 4: Standardized data types (dates, numbers, categories, text)")
    
    # Step 5: Create calculated fields
    df_clean = create_calculated_fields(df_clean)
    if log_actions:
        print("✓ Step 5: Created calculated fields (lead time, confidence change, etc.)")
    
    # Step 6: Remove outliers (optional)
    if remove_outliers_flag and 'Actual_Session_Length' in df_clean.columns:
        df_clean, outlier_stats = remove_outliers(df_clean, 'Actual_Session_Length', method='iqr')
        cleaning_log['outliers_removed'] = outlier_stats
        
        if log_actions and outlier_stats['removed_count'] > 0:
            print(f"\n✓ Step 6: Removed {outlier_stats['removed_count']} outliers ({outlier_stats['removed_pct']:.1f}%)")
            print(f"   Valid range: {outlier_stats['lower_bound']:.2f} - {outlier_stats['upper_bound']:.2f} hours")
    elif log_actions:
        print("✓ Step 6: Skipped outlier removal (disabled)")
    
    # Step 7: Escape Excel formulas
    df_clean = escape_excel_formulas(df_clean)
    if log_actions:
        print("✓ Step 7: Escaped Excel formula characters (-, =)")
    
    # Step 8: Validate data quality
    issues, warnings_list = validate_data_quality(df_clean)
    cleaning_log['quality_issues'] = issues
    cleaning_log['quality_warnings'] = warnings_list
    
    if log_actions:
        print("\n" + "="*80)
        print("📊 DATA QUALITY REPORT")
        print("="*80)
        
        if issues:
            for issue in issues:
                print(f"   {issue}")
        
        if warnings_list:
            for warning in warnings_list:
                print(f"   {warning}")
        
        if not issues and not warnings_list:
            print("   ✅ No data quality issues detected!")
    
    # Step 9: Analyze missing values
    missing_analysis = analyze_missing_values(df_clean)
    missing_report = missing_analysis['missing_data']
    context = missing_analysis['context']
    
    cleaning_log['missing_values'] = missing_report
    cleaning_log['context'] = context
    
    if log_actions and missing_report:
        print("\n" + "="*80)
        print("📋 MISSING VALUE REPORT")
        print("="*80)
        
        # Separate by category
        critical = {k: v for k, v in missing_report.items() if v['category'] == 'critical'}
        concerning = {k: v for k, v in missing_report.items() if v['category'] == 'concerning'}
        expected = {k: v for k, v in missing_report.items() if v['category'] == 'expected'}
        optional = {k: v for k, v in missing_report.items() if v['category'] == 'optional'}
        
        # Critical missing data
        if critical:
            print("\n🔴 CRITICAL MISSING DATA (should be filled):")
            for col, stats in sorted(critical.items(), key=lambda x: x[1]['percentage'], reverse=True):
                print(f"   ⚠️ {col}: {stats['percentage']:.1f}% missing ({stats['count']:,} rows)")
                print(f"      → {stats['explanation']}")
        
        # Concerning missing data
        if concerning:
            print("\n🟡 IMPORTANT BUT OFTEN MISSING (affects analysis quality):")
            for col, stats in sorted(concerning.items(), key=lambda x: x[1]['percentage'], reverse=True):
                print(f"   - {col}: {stats['percentage']:.1f}% missing ({stats['count']:,} rows)")
                print(f"     → {stats['explanation']}")
        
        # Expected missing data (with context)
        if expected:
            print("\n✅ EXPECTED MISSING DATA (not a problem):")
            for col, stats in sorted(expected.items(), key=lambda x: x[1]['percentage'], reverse=True):
                print(f"   - {col}: {stats['percentage']:.1f}% missing ({stats['count']:,} rows)")
                print(f"     → {stats['explanation']}")
        
        # Optional fields (only show if significant)
        if optional:
            high_missing_optional = {k: v for k, v in optional.items() if v['percentage'] > 50}
            if high_missing_optional:
                print("\nℹ️ OPTIONAL FIELDS (low priority):")
                for col, stats in sorted(high_missing_optional.items(), key=lambda x: x[1]['percentage'], reverse=True)[:5]:
                    print(f"   - {col}: {stats['percentage']:.1f}% missing")
        
        # Show context information
        if context:
            print("\n" + "="*80)
            print("📊 SESSION STATISTICS")
            print("="*80)
            
            # Cancellation stats
            if 'cancellations' in context:
                cancel_ctx = context['cancellations']
                print(f"\n📅 Session Outcomes:")
                print(f"   Total sessions: {cancel_ctx['total_sessions']:,}")
                print(f"   Completed: {cancel_ctx['completed']:,} ({cancel_ctx['completion_rate']:.1f}%)")
                print(f"   Cancelled: {cancel_ctx['cancelled']:,} ({cancel_ctx['cancellation_rate']:.1f}%)")
                print(f"   No-shows: {cancel_ctx['no_show']:,} ({cancel_ctx['no_show_rate']:.1f}%)")
            
            # Student issues stats
            if 'student_issues' in context:
                issues_ctx = context['student_issues']
                print(f"\n💬 Student Feedback:")
                print(f"   Sessions with issues reported: {issues_ctx['sessions_with_issues']:,} ({issues_ctx['issue_rate']:.1f}%)")
                print(f"   Sessions without issues: {issues_ctx['sessions_without_issues']:,}")
                print(f"   → Low issue rate is a positive indicator!")
            
            # Survey completion stats
            if 'surveys' in context:
                survey_ctx = context['surveys']
                print(f"\n📝 Survey Completion Rates:")
                print(f"   Pre-session survey: {survey_ctx['pre_survey_completion_rate']:.1f}%")
                print(f"   Post-session survey: {survey_ctx['post_survey_completion_rate']:.1f}%")
                print(f"   Both surveys completed: {survey_ctx['both_surveys_completion_rate']:.1f}%")
    
    # Final summary
    cleaning_log['final_rows'] = len(df_clean)
    cleaning_log['final_cols'] = len(df_clean.columns)
    
    if log_actions:
        print("\n" + "="*80)
        print("✅ CLEANING COMPLETE")
        print("="*80)
        print(f"   Final dataset: {len(df_clean):,} rows × {len(df_clean.columns)} columns")
        print(f"   Removed: {cleaning_log['original_cols'] - cleaning_log['final_cols']} columns")
        if remove_outliers_flag and 'outliers_removed' in cleaning_log:
            print(f"   Removed: {cleaning_log['outliers_removed']['removed_count']} outlier rows")
        print(f"   Missing data handled gracefully in {len(missing_report)} columns")
        
        # Add cancellation rate to final summary
        if 'context' in cleaning_log and 'cancellations' in cleaning_log['context']:
            cancel_rate = cleaning_log['context']['cancellations']['cancellation_rate']
            print(f"   Cancellation rate: {cancel_rate}%")
        
        print("="*80 + "\n")
    
    return df_clean, cleaning_log


# ============================================================================
# WALK-IN SESSIONS CLEANING (PLACEHOLDER)
# ============================================================================

def clean_walkin_sessions(df, remove_outliers_flag=True, log_actions=True):
    """
    TODO: Complete cleaning pipeline for walk-in sessions.
    
    Walk-in sessions have different schema:
    - Duration Minutes (not Tutor Submitted Length)
    - Check In At Date/Time (not Requested At Date/Time)
    - No pre/post surveys
    - Simpler data structure (19 columns vs 48)
    
    This will be implemented after scheduled sessions pipeline is complete.
    """
    if log_actions:
        print("\n" + "="*80)
        print("🚶 WALK-IN SESSIONS CLEANING")
        print("="*80)
        print("⚠️ Walk-in pipeline not yet implemented")
        print("   Returning data as-is for now")
        print("="*80 + "\n")
    
    # Placeholder: return data unchanged with basic log
    cleaning_log = {
        'pipeline': 'walkin',
        'status': 'not_implemented',
        'original_rows': len(df),
        'original_cols': len(df.columns),
        'final_rows': len(df),
        'final_cols': len(df.columns)
    }
    
    return df, cleaning_log


# ============================================================================
# MAIN DISPATCHER
# ============================================================================

def clean_data(df, mode='auto', remove_outliers=True, log_actions=True):
    """
    Main entry point for data cleaning.
    Auto-detects session type or uses specified mode.
    
    Parameters:
    - df: Raw dataframe
    - mode: 'auto', 'scheduled', or 'walkin'
    - remove_outliers: Whether to remove statistical outliers
    - log_actions: Print progress/results
    
    Returns: (cleaned_df, cleaning_log)
    """
    # Auto-detect if needed
    if mode == 'auto':
        detected_mode = detect_session_type(df)
        if log_actions:
            print(f"🔍 Auto-detected session type: {detected_mode}")
        mode = detected_mode
    
    # Dispatch to appropriate pipeline
    if mode == 'scheduled':
        return clean_scheduled_sessions(df, remove_outliers, log_actions)
    
    elif mode == 'walkin':
        return clean_walkin_sessions(df, remove_outliers, log_actions)
    
    else:
        raise ValueError(
            f"Unknown session type: {mode}\n"
            "Unable to auto-detect. Please specify mode='scheduled' or mode='walkin'"
        )


# ============================================================================
# CONVENIENCE FUNCTION
# ============================================================================

def quick_clean(csv_path, mode='auto', remove_outliers=True):
    """
    One-liner: Load CSV and clean in one step.
    
    Usage:
        df_clean, log = quick_clean('penji_export.csv')
    """
    df = pd.read_csv(csv_path)
    return clean_data(df, mode=mode, remove_outliers=remove_outliers, log_actions=True)