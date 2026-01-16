# src/core/privacy.py

import pandas as pd
import re

def detect_pii_columns(df):
    """
    Detect columns containing PII using both exact matches and patterns.
    Returns list of column names to remove.
    """
    pii_columns = []
    
    # Layer 1: Known exact column names
    known_pii = [
        'Student Email',
        'Student SSO ID',
        'Student ID',
        'Student Name',
        'Source User Email',
        'Tutor Email',
        'Tutor SSO ID',
        'Tutor Name',
        'Agenda - Please enter your UARK email here.',
        'Tutor - Email the session receipt to'
    ]
    
    for col in known_pii:
        if col in df.columns:
            pii_columns.append(col)
    
    # Layer 2: Pattern-based detection
    for col in df.columns:
        col_lower = col.lower()
        
        # Skip if already caught
        if col in pii_columns:
            continue
        
        # Check column name patterns
        pii_keywords = [
            'email', 'sso', 'student id', 'tutor id',
            'name', 'first name', 'last name',
            'phone', 'address', 'ssn'
        ]
        
        if any(keyword in col_lower for keyword in pii_keywords):
            # Additional check: look at actual data
            if is_pii_data(df[col]):
                pii_columns.append(col)
    
    return list(set(pii_columns))  # Remove duplicates


def is_pii_data(series):
    """
    Check if a column's data looks like PII.
    Returns True if it appears to contain sensitive info.
    """
    # Skip if mostly empty
    if series.isna().sum() / len(series) > 0.9:
        return False
    
    sample = series.dropna().head(100).astype(str)
    
    # Email pattern
    email_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
    if sample.str.match(email_pattern).any():
        return True
    
    # SSO ID pattern (usually alphanumeric, 6-12 chars)
    sso_pattern = r'^[a-zA-Z0-9]{6,12}$'
    if sample.str.match(sso_pattern).sum() > len(sample) * 0.5:
        return True
    
    # Student ID pattern (usually numeric, 7-10 digits)
    id_pattern = r'^\d{7,10}$'
    if sample.str.match(id_pattern).sum() > len(sample) * 0.5:
        return True
    
    # Name pattern (2+ words, capitalized)
    name_pattern = r'^[A-Z][a-z]+ [A-Z][a-z]+'
    if sample.str.match(name_pattern).sum() > len(sample) * 0.3:
        return True
    
    return False


def get_essential_columns():
    """
    Define which columns we actually need for analytics.
    This is the WHITELIST - only keep these (plus anonymized IDs).
    """
    essential = [
        # Session Identifiers
        'Unique ID',
        
        # Session Metadata
        'Status',
        'Source Kind',
        'Booking Flow',
        'Appointment Type',
        'Kind',
        'Course',
        'Location',
        
        # Booking Times
        'Requested At Date',
        'Requested At Time',
        
        # Appointment Times (we'll rename these during cleaning)
        'Requested Start At Date',
        'Requested Start At Time',
        'Requested End At Time',
        'Requested Length',
        
        # Actual Session Times
        'Started At Date',
        'Started At Time',
        'Ended At Date',
        'Ended At Time',
        'Tutor Submitted Length',
        
        # Attendance & Outcomes
        'Student Attendance',
        'Student Attendance Reason',
        'Cancel Reason',
        'Session Feedback From Student',
        
        # Agenda Questions (Pre-session)
        'Agenda - For which course are you writing this document? (If not applicable, write "N/A")',
        'Agenda - How confident do you feel about your writing assignment right now? (1="Not at all"; 5="Very")',
        'Agenda - Is this your first appointment?',
        'Agenda - Please check one of the following boxes to help us determine the context of your visit.',
        'Agenda - Roughly speaking, what stage of the writing process are you in right now?',
        'Agenda - What would you like to focus on during this appointment?',
        'Agenda - When is your paper due?',
        
        # Student Feedback (Post-session)
        'Student - How confident do you feel about your writing assignment now that your meeting is over? (1="Not at all"; 5="Very")',
        'Student - On a scale of 1-5 (1="not at all," 5="extremely well"), how well did you get along with your tutor?',
        'Student - On a scale of 1-5 (1="not easy at all", 5="extremely easy"), how easy was it to use our website and scheduling software to schedule and attend your appointment?',
        'Student - On a scale of 1-5 (1="very poorly", 5="very well"), how well would you say your your appointment went?',
        'Student - On a scale of 1-7 (1="extremely dissatisfied," 7="extremely satisfied"), how satisfied are you with the help you received at the Writing Studio?',
        'Student - Please share any comments that you would like us to share with your tutor.',
        'Student - Please share any comments that you\'d like your tutor to see.',
        'Student - Please share any obstacles, disappointments, or problems that you encountered during your consultation at the Writing Studio.',
        'Student - Were you offered any of the following incentives for today\'s visit? Please select any that apply.',
        
        # Tutor Feedback
        'Tutor - Overall, how well would you say that the consultation went?',
        'Tutor - Please provide a brief overview of the topics discussed or issues addressed during your consultation.'
    ]
    
    return essential


def create_anonymous_ids(df):
    """
    Create anonymized student and tutor IDs before removing PII.
    """
    df_copy = df.copy()
    
    # Student anonymization - try multiple possible ID columns
    student_id_cols = ['Student SSO ID', 'Student ID', 'Student Email']
    for col in student_id_cols:
        if col in df_copy.columns:
            df_copy['Student_Anon_ID'] = df_copy[col].apply(
                lambda x: f"STU_{abs(hash(str(x))) % 100000:05d}" if pd.notna(x) else None
            )
            break
    
    # Tutor anonymization - try multiple possible ID columns
    tutor_id_cols = ['Tutor SSO ID', 'Tutor Email', 'Tutor Name']
    for col in tutor_id_cols:
        if col in df_copy.columns:
            df_copy['Tutor_Anon_ID'] = df_copy[col].apply(
                lambda x: f"TUT_{abs(hash(str(x))) % 10000:04d}" if pd.notna(x) else None
            )
            break
    
    return df_copy


def anonymize_and_clean(df, log_actions=True):
    """
    Main privacy function:
    1. Create anonymous IDs (before removing PII)
    2. Remove PII columns
    3. Keep only essential columns
    4. Return cleaned dataframe + logs
    """
    original_cols = len(df.columns)
    
    if log_actions:
        print("="*80)
        print("🔒 PRIVACY & DATA CLEANING")
        print("="*80)
        print(f"\nOriginal dataset: {len(df)} rows × {original_cols} columns")
    
    # Step 1: Create anonymized IDs BEFORE removing PII
    df_anon = create_anonymous_ids(df)
    
    if log_actions:
        if 'Student_Anon_ID' in df_anon.columns:
            unique_students = df_anon['Student_Anon_ID'].nunique()
            print(f"✓ Created {unique_students} anonymized student IDs")
        if 'Tutor_Anon_ID' in df_anon.columns:
            unique_tutors = df_anon['Tutor_Anon_ID'].nunique()
            print(f"✓ Created {unique_tutors} anonymized tutor IDs")
    
    # Step 2: Detect and remove PII columns
    pii_columns = detect_pii_columns(df_anon)
    
    if log_actions and pii_columns:
        print(f"\n🔒 Removing {len(pii_columns)} PII columns:")
        for col in sorted(pii_columns):
            print(f"   - {col}")
    
    # Step 3: Get essential columns + our anonymized IDs
    essential = get_essential_columns()
    essential_in_df = [c for c in essential if c in df_anon.columns]
    
    # Add anonymized IDs to keep list
    anon_cols = [c for c in df_anon.columns if c.startswith('Student_Anon') or c.startswith('Tutor_Anon')]
    keep_columns = essential_in_df + anon_cols
    
    # Step 4: Keep only essential columns
    df_clean = df_anon[keep_columns].copy()
    
    # Calculate what was removed
    removed_pii = set(pii_columns)
    removed_excess = set(df_anon.columns) - set(keep_columns) - removed_pii
    
    if log_actions:
        print(f"\n🧹 Removing {len(removed_excess)} excess/duplicate columns:")
        for col in sorted(list(removed_excess)[:10]):  # Show first 10
            print(f"   - {col}")
        if len(removed_excess) > 10:
            print(f"   ... and {len(removed_excess) - 10} more")
        
        print(f"\n✅ Clean dataset: {len(df_clean)} rows × {len(df_clean.columns)} columns")
        print(f"   Removed: {original_cols - len(df_clean.columns)} columns total")
        print(f"   - {len(removed_pii)} PII columns")
        print(f"   - {len(removed_excess)} excess columns")
    
    # Step 5: Final validation
    validation_passed = validate_no_pii(df_clean, log_actions)
    
    # Create detailed log
    cleanup_log = {
        'original_rows': len(df),
        'original_cols': original_cols,
        'final_rows': len(df_clean),
        'final_cols': len(df_clean.columns),
        'pii_removed': list(removed_pii),
        'excess_removed': list(removed_excess),
        'anonymous_students': df_clean['Student_Anon_ID'].nunique() if 'Student_Anon_ID' in df_clean.columns else 0,
        'anonymous_tutors': df_clean['Tutor_Anon_ID'].nunique() if 'Tutor_Anon_ID' in df_clean.columns else 0,
        'validation_passed': validation_passed
    }
    
    return df_clean, cleanup_log


def validate_no_pii(df, log_actions=True):
    """
    Final sanity check - scan for any remaining PII.
    Returns True if clean, False if PII detected.
    """
    issues = []
    
    for col in df.columns:
        # Skip our anonymous IDs
        if col.startswith('Student_Anon') or col.startswith('Tutor_Anon'):
            continue
        
        sample = df[col].dropna().head(100).astype(str)
        
        # Check for email addresses
        if sample.str.contains('@', na=False).any():
            issues.append(f"Possible email found in column '{col}'")
        
        # Check for column names that suggest PII
        col_lower = col.lower()
        if any(keyword in col_lower for keyword in ['email', 'sso', 'phone', 'address']):
            issues.append(f"Column name suggests PII: '{col}'")
    
    if issues:
        if log_actions:
            print("\n⚠️ PRIVACY VALIDATION WARNINGS:")
            for issue in issues:
                print(f"   - {issue}")
        return False
    else:
        if log_actions:
            print("\n✅ Privacy validation passed - no PII detected")
        return True


# Convenience function for simple use
def clean_data(csv_path, log_actions=True):
    """
    One-step function: Load CSV → Clean → Return anonymized data
    """
    df = pd.read_csv(csv_path)
    df_clean, log = anonymize_and_clean(df, log_actions)
    return df_clean, log