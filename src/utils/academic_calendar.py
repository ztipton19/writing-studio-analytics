# src/utils/academic_calendar.py

import pandas as pd
from datetime import datetime


def detect_semester(date):
    """
    Dead simple semester detection based on month.
    
    Rules:
    - Spring: January - May (includes May intersession)
    - Summer: June - August (includes all summer sessions + August intersession)
    - Fall: September - December
    
    Parameters:
    - date: datetime object or pandas Timestamp
    
    Returns:
    - "Spring", "Summer", or "Fall"
    """
    if pd.isna(date):
        return None
    
    month = date.month
    
    if 1 <= month <= 5:
        return "Spring"
    elif 6 <= month <= 8:
        return "Summer"
    else:  # 9-12
        return "Fall"


def get_academic_year(date):
    """
    Returns academic year as string: '2024-2025'
    
    Academic year runs from Fall (Aug) to Summer (July).
    - Fall 2024 = Academic Year 2024-2025
    - Spring 2025 = Academic Year 2024-2025
    - Summer 2025 = Academic Year 2024-2025
    - Fall 2025 = Academic Year 2025-2026
    
    Parameters:
    - date: datetime object or pandas Timestamp
    
    Returns:
    - String like "2024-2025"
    """
    if pd.isna(date):
        return None
    
    if date.month >= 8:  # Fall semester starts academic year
        return f"{date.year}-{date.year + 1}"
    else:  # Spring/Summer are second half of academic year
        return f"{date.year - 1}-{date.year}"


def get_semester_label(date):
    """
    Returns full semester label: "Spring 2025", "Fall 2024", etc.
    
    Useful for chart labels and grouping.
    
    Parameters:
    - date: datetime object or pandas Timestamp
    
    Returns:
    - String like "Spring 2025" or "Fall 2024"
    """
    if pd.isna(date):
        return None
    
    semester = detect_semester(date)
    year = date.year
    
    return f"{semester} {year}"


def add_semester_columns(df, date_column='Appointment_DateTime'):
    """
    Add semester-related columns to a dataframe.
    
    Adds three columns:
    - Semester: "Spring", "Summer", or "Fall"
    - Academic_Year: "2024-2025"
    - Semester_Label: "Spring 2025"
    
    Parameters:
    - df: pandas DataFrame
    - date_column: name of column containing datetime values
    
    Returns:
    - DataFrame with new columns added
    """
    df = df.copy()
    
    if date_column not in df.columns:
        raise ValueError(f"Column '{date_column}' not found in dataframe")
    
    # Add semester columns
    df['Semester'] = df[date_column].apply(detect_semester)
    df['Academic_Year'] = df[date_column].apply(get_academic_year)
    df['Semester_Label'] = df[date_column].apply(get_semester_label)
    
    return df


def get_semester_order():
    """
    Returns the natural ordering of semesters for sorting/plotting.
    
    Use this for categorical ordering in pandas/seaborn:
    df['Semester'] = pd.Categorical(df['Semester'], categories=get_semester_order(), ordered=True)
    
    Returns:
    - List: ["Spring", "Summer", "Fall"]
    """
    return ["Spring", "Summer", "Fall"]


def get_semester_stats(df, date_column='Appointment_DateTime'):
    """
    Get basic statistics about sessions by semester.
    
    Returns count of sessions for each semester in the dataset.
    
    Parameters:
    - df: pandas DataFrame
    - date_column: name of column containing datetime values
    
    Returns:
    - Dictionary with semester counts
    """
    if date_column not in df.columns:
        raise ValueError(f"Column '{date_column}' not found in dataframe")
    
    df_temp = df.copy()
    df_temp['Semester_Label'] = df_temp[date_column].apply(get_semester_label)
    
    semester_counts = df_temp['Semester_Label'].value_counts().to_dict()
    
    return semester_counts


# ============================================================================
# CONVENIENCE FUNCTIONS FOR COMMON OPERATIONS
# ============================================================================

def is_fall_semester(date):
    """Check if date falls in Fall semester"""
    return detect_semester(date) == "Fall"


def is_spring_semester(date):
    """Check if date falls in Spring semester"""
    return detect_semester(date) == "Spring"


def is_summer_semester(date):
    """Check if date falls in Summer semester"""
    return detect_semester(date) == "Summer"


def filter_by_semester(df, semester, date_column='Appointment_DateTime'):
    """
    Filter dataframe to only include rows from specified semester(s).
    
    Parameters:
    - df: pandas DataFrame
    - semester: "Spring", "Summer", "Fall", or list of these
    - date_column: name of column containing datetime values
    
    Returns:
    - Filtered DataFrame
    
    Example:
        spring_data = filter_by_semester(df, "Spring")
        spring_fall = filter_by_semester(df, ["Spring", "Fall"])
    """
    if date_column not in df.columns:
        raise ValueError(f"Column '{date_column}' not found in dataframe")
    
    df_temp = df.copy()
    df_temp['_temp_semester'] = df_temp[date_column].apply(detect_semester)
    
    if isinstance(semester, str):
        semester = [semester]
    
    filtered_df = df_temp[df_temp['_temp_semester'].isin(semester)].copy()
    filtered_df = filtered_df.drop(columns=['_temp_semester'])
    
    return filtered_df


def filter_by_academic_year(df, academic_year, date_column='Appointment_DateTime'):
    """
    Filter dataframe to only include rows from specified academic year.
    
    Parameters:
    - df: pandas DataFrame
    - academic_year: "2024-2025" or list of academic years
    - date_column: name of column containing datetime values
    
    Returns:
    - Filtered DataFrame
    
    Example:
        ay_2024 = filter_by_academic_year(df, "2024-2025")
        recent = filter_by_academic_year(df, ["2023-2024", "2024-2025"])
    """
    if date_column not in df.columns:
        raise ValueError(f"Column '{date_column}' not found in dataframe")
    
    df_temp = df.copy()
    df_temp['_temp_ay'] = df_temp[date_column].apply(get_academic_year)
    
    if isinstance(academic_year, str):
        academic_year = [academic_year]
    
    filtered_df = df_temp[df_temp['_temp_ay'].isin(academic_year)].copy()
    filtered_df = filtered_df.drop(columns=['_temp_ay'])
    
    return filtered_df