# src/core/privacy.py

import pandas as pd
import hashlib
import re
from datetime import datetime
import json
import base64
import os


# ============================================================================
# PII DETECTION
# ============================================================================

def detect_pii_columns(df):
    """
    Two-layer PII detection system:
    1. Exact column name matching
    2. Pattern-based detection for variations
    """
    pii_columns = set()
    
    # Layer 1: Known PII column names (exact match)
    known_pii = [
        'Student Email', 'Student SSO ID', 'Student - Student ID', 'Student ID',
        'Student Name', 'Tutor Name', 'Tutor Email',
        'Tutor - Email the session receipt to'
    ]
    
    for col in df.columns:
        if col in known_pii:
            pii_columns.add(col)
    
    # Layer 2: Pattern-based detection
    for col in df.columns:
        col_lower = col.lower()
        
        # Check for PII keywords
        pii_keywords = ['email', 'sso', 'student id', 'name']
        if any(keyword in col_lower for keyword in pii_keywords):
            # Validate with data pattern
            if _is_pii_data(df[col]):
                pii_columns.add(col)
    
    return list(pii_columns)


def _is_pii_data(series):
    """
    Check if column contains PII based on data patterns
    """
    sample = series.dropna().head(10)
    
    if len(sample) == 0:
        return False
    
    # Check for email patterns
    email_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
    if any(re.search(email_pattern, str(val)) for val in sample):
        return True
    
    # Check for SSO ID patterns (typically alphanumeric)
    sso_pattern = r'^[a-zA-Z0-9]{6,10}$'
    if any(re.match(sso_pattern, str(val)) for val in sample):
        return True
    
    # Check for name patterns (contains spaces, starts with capital)
    name_pattern = r'^[A-Z][a-z]+ [A-Z][a-z]+.*$'
    if any(re.match(name_pattern, str(val)) for val in sample):
        return True
    
    return False


# ============================================================================
# ANONYMIZATION WITH CODEBOOK
# ============================================================================

def anonymize_with_codebook(df, create_codebook=True, password=None, confirm_password=None):
    """
    Anonymize PII while optionally creating encrypted reverse-lookup codebook.
    
    Parameters:
    - df: DataFrame with PII
    - create_codebook: Whether to generate codebook
    - password: Password to encrypt codebook
    - confirm_password: Password confirmation
    
    Returns:
    - df_anon: Anonymized dataframe
    - codebook_path: Path to codebook (or None)
    - anonymization_log: Summary of what was anonymized
    """
    
    # Validate password if codebook requested
    if create_codebook:
        if not password:
            raise ValueError("Password required to create codebook")
        
        if password != confirm_password:
            raise ValueError("Passwords do not match! Please re-enter matching passwords.")
        
        if len(password) < 12:
            raise ValueError("Password must be at least 12 characters for security")
    
    # Initialize codebook and log
    codebook = {
        'students': {},
        'tutors': {},
        'metadata': {
            'created': datetime.now().isoformat(),
            'total_students': 0,
            'total_tutors': 0,
            'dataset_date_range': None
        }
    }
    
    anonymization_log = {
        'pii_columns_removed': [],
        'students_anonymized': 0,
        'tutors_anonymized': 0,
        'codebook_created': create_codebook
    }
    
    df_anon = df.copy()
    
    # Store date range for codebook metadata
    if 'Requested At Date' in df.columns:
        min_date = pd.to_datetime(df['Requested At Date']).min()
        max_date = pd.to_datetime(df['Requested At Date']).max()
        codebook['metadata']['dataset_date_range'] = f"{min_date.date()} to {max_date.date()}"
    
    # ========================================================================
    # ANONYMIZE STUDENTS
    # ========================================================================

    # Student email column in Penji exports - check both possible column names
    student_email_col = None
    if 'Student Email' in df.columns:
        student_email_col = 'Student Email'
    elif 'Student - Email' in df.columns:
        student_email_col = 'Student - Email'

    if student_email_col:
        student_map = {}
        used_student_ids = set()
        student_collisions = 0

        for email in df[student_email_col].unique():
            # Create consistent hash-based anonymous ID using SHA256 (deterministic)
            hash_hex = hashlib.sha256(str(email).encode()).hexdigest()
            hash_int = int(hash_hex[:8], 16)  # Use first 8 hex chars
            anon_id = f"STU_{hash_int % 100000:05d}"

            # Check for collision and handle with suffix
            if anon_id in used_student_ids:
                student_collisions += 1
                suffix = 'A'
                while f"{anon_id}_{suffix}" in used_student_ids:
                    suffix = chr(ord(suffix) + 1)  # A -> B -> C...
                anon_id = f"{anon_id}_{suffix}"

            used_student_ids.add(anon_id)
            student_map[email] = anon_id

            if create_codebook:
                codebook['students'][anon_id] = email

        df_anon['Student_Anon_ID'] = df[student_email_col].map(student_map)
        anonymization_log['students_anonymized'] = len(student_map)
        anonymization_log['student_collisions'] = student_collisions
        codebook['metadata']['total_students'] = len(student_map)
    
    # ========================================================================
    # ANONYMIZE TUTORS
    # ========================================================================

    # Tutor email column in Penji exports - check both possible column names
    tutor_email_col = None
    if 'Tutor Email' in df.columns:
        tutor_email_col = 'Tutor Email'
    elif 'Tutor - Email the session receipt to' in df.columns:
        tutor_email_col = 'Tutor - Email the session receipt to'

    if tutor_email_col:
        tutor_map = {}
        used_tutor_ids = set()
        tutor_collisions = 0

        for email in df[tutor_email_col].unique():
            # Create consistent hash-based anonymous ID using SHA256 (deterministic)
            hash_hex = hashlib.sha256(str(email).encode()).hexdigest()
            hash_int = int(hash_hex[:8], 16)  # Use first 8 hex chars
            anon_id = f"TUT_{hash_int % 10000:04d}"

            # Check for collision and handle with suffix
            if anon_id in used_tutor_ids:
                tutor_collisions += 1
                suffix = 'A'
                while f"{anon_id}_{suffix}" in used_tutor_ids:
                    suffix = chr(ord(suffix) + 1)  # A -> B -> C...
                anon_id = f"{anon_id}_{suffix}"

            used_tutor_ids.add(anon_id)
            tutor_map[email] = anon_id

            if create_codebook:
                codebook['tutors'][anon_id] = email

        df_anon['Tutor_Anon_ID'] = df[tutor_email_col].map(tutor_map)
        anonymization_log['tutors_anonymized'] = len(tutor_map)
        anonymization_log['tutor_collisions'] = tutor_collisions
        codebook['metadata']['total_tutors'] = len(tutor_map)
    
    # ========================================================================
    # REMOVE ALL PII COLUMNS
    # ========================================================================

    # Detect all PII columns using our two-layer detection system
    pii_columns = detect_pii_columns(df_anon)

    # Remove all detected PII columns
    for col in pii_columns:
        if col in df_anon.columns:
            df_anon = df_anon.drop(columns=[col])
            anonymization_log['pii_columns_removed'].append(col)

    # ========================================================================
    # SAVE CODEBOOK
    # ========================================================================
    
    codebook_path = None
    if create_codebook:
        timestamp = datetime.now().strftime('%Y-%m-%d_%H%M%S')
        codebook_path = f"codebook_{timestamp}.enc"
        
        try:
            save_encrypted_codebook(codebook, codebook_path, password)
        except Exception as e:
            raise ValueError(f"Failed to save codebook: {e}")
    
    return df_anon, codebook_path, anonymization_log


# ============================================================================
# CODEBOOK ENCRYPTION
# ============================================================================

def save_encrypted_codebook(codebook, filepath, password):
    """
    Encrypt and save codebook using password-based encryption.
    
    Uses PBKDF2 key derivation + Fernet symmetric encryption.
    """
    try:
        from cryptography.fernet import Fernet
        from cryptography.hazmat.primitives import hashes
        from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
    except ImportError:
        raise ImportError(
            "cryptography package required for codebook encryption.\n"
            "Install with: pip install cryptography"
        )
    
    # Derive encryption key from password
    salt = b'writing_studio_analytics_2025'  # Fixed salt for consistency
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=100000  # High iteration count for security
    )
    key = base64.urlsafe_b64encode(kdf.derive(password.encode()))
    
    # Encrypt codebook
    fernet = Fernet(key)
    codebook_json = json.dumps(codebook, indent=2).encode()
    encrypted = fernet.encrypt(codebook_json)
    
    # Save to file
    with open(filepath, 'wb') as f:
        f.write(encrypted)
    
    print(f"\n✅ Codebook encrypted and saved: {filepath}")
    print(f"   Students: {codebook['metadata']['total_students']}")
    print(f"   Tutors: {codebook['metadata']['total_tutors']}")
    print(f"   Date range: {codebook['metadata'].get('dataset_date_range', 'Unknown')}")
    print(f"\n⚠️  IMPORTANT: Give codebook + password to supervisor ONLY!")
    print(f"   Do NOT commit to GitHub or share insecurely.")


def decrypt_codebook(filepath, password):
    """
    Decrypt and load codebook using password.
    
    Returns:
    - codebook dict on success
    - Raises exception with descriptive error on failure
    """
    try:
        from cryptography.fernet import Fernet
        from cryptography.hazmat.primitives import hashes
        from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
    except ImportError:
        raise ImportError(
            "cryptography package required for codebook decryption.\n"
            "Install with: pip install cryptography"
        )
    
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Codebook file not found: {filepath}")
    
    # Derive decryption key from password
    salt = b'writing_studio_analytics_2025'
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=100000
    )
    
    try:
        key = base64.urlsafe_b64encode(kdf.derive(password.encode()))
        fernet = Fernet(key)
        
        # Read and decrypt
        with open(filepath, 'rb') as f:
            encrypted = f.read()
        
        decrypted = fernet.decrypt(encrypted)
        codebook = json.loads(decrypted)
        
        return codebook
        
    except Exception as e:
        # More specific error messages
        if 'Invalid' in str(e) or 'token' in str(e):
            raise ValueError(
                "❌ INCORRECT PASSWORD\n"
                "The password you entered does not match the codebook encryption.\n"
                "Please try again with the correct password."
            )
        elif 'JSON' in str(e):
            raise ValueError(
                "❌ CORRUPTED CODEBOOK\n"
                "The codebook file appears to be corrupted or invalid.\n"
                "You may need to regenerate the report."
            )
        else:
            raise ValueError(f"❌ ERROR: {e}")


# ============================================================================
# CODEBOOK LOOKUP
# ============================================================================

def lookup_in_codebook(anon_id, codebook_path, password):
    """
    Reverse-lookup: Anonymous ID → Email/Name
    
    Parameters:
    - anon_id: Anonymous ID (e.g., "STU_04521" or "TUT_0842")
    - codebook_path: Path to encrypted codebook file
    - password: Decryption password
    
    Returns:
    - Email/name string on success
    - Error message string on failure
    """
    try:
        # Decrypt codebook
        codebook = decrypt_codebook(codebook_path, password)
        
        # Validate ID format
        if not (anon_id.startswith('STU_') or anon_id.startswith('TUT_')):
            return "❌ Invalid ID format. Must start with 'STU_' or 'TUT_'"
        
        # Lookup in appropriate section
        if anon_id.startswith('STU_'):
            result = codebook['students'].get(anon_id)
            if result:
                return result
            else:
                return f"❌ Student ID '{anon_id}' not found in codebook"
        
        elif anon_id.startswith('TUT_'):
            result = codebook['tutors'].get(anon_id)
            if result:
                return result
            else:
                return f"❌ Tutor ID '{anon_id}' not found in codebook"
    
    except ValueError as e:
        # Password error or corrupted file (already has nice error message)
        return str(e)
    
    except FileNotFoundError as e:
        return f"❌ Codebook file not found: {codebook_path}"
    
    except Exception as e:
        return f"❌ Unexpected error: {e}"


def get_codebook_info(codebook_path, password):
    """
    Get metadata about codebook without looking up specific IDs.
    
    Useful for displaying codebook stats to user.
    """
    try:
        codebook = decrypt_codebook(codebook_path, password)
        
        info = {
            'total_students': codebook['metadata']['total_students'],
            'total_tutors': codebook['metadata']['total_tutors'],
            'created': codebook['metadata']['created'],
            'date_range': codebook['metadata'].get('dataset_date_range', 'Unknown')
        }
        
        return info
    
    except Exception as e:
        return {'error': str(e)}


# ============================================================================
# LEGACY FUNCTION (for backward compatibility)
# ============================================================================

def anonymize_data(df):
    """
    Simple anonymization without codebook (legacy function).
    
    For new code, use anonymize_with_codebook() instead.
    """
    df_anon, _, log = anonymize_with_codebook(df, create_codebook=False)
    return df_anon