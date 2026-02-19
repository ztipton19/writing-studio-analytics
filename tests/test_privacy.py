import base64
import json

import pytest
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

from src.core.privacy import decrypt_codebook, save_encrypted_codebook


def test_codebook_roundtrip_v2(tmp_path):
    payload = {
        'students': {'STU_00001': 'student@example.edu'},
        'tutors': {'TUT_0001': 'tutor@example.edu'},
        'metadata': {
            'created': '2026-02-19T00:00:00',
            'session_type': 'scheduled',
            'total_students': 1,
            'total_tutors': 1,
            'dataset_date_range': '2026-01-01 to 2026-01-31',
        },
    }
    out = tmp_path / 'codebook.enc'

    save_encrypted_codebook(payload, str(out), 'strong-password-123')
    loaded = decrypt_codebook(str(out), 'strong-password-123')

    assert loaded['students']['STU_00001'] == 'student@example.edu'
    assert loaded['metadata']['session_type'] == 'scheduled'


def test_codebook_legacy_decrypt_support(tmp_path):
    payload = {
        'students': {'STU_00001': 'legacy@example.edu'},
        'tutors': {},
        'metadata': {
            'created': '2025-01-01T00:00:00',
            'session_type': 'scheduled',
            'total_students': 1,
            'total_tutors': 0,
            'dataset_date_range': '2025-01-01 to 2025-01-31',
        },
    }

    password = 'legacy-pass-123'
    salt = b'writing_studio_analytics_2025'
    kdf = PBKDF2HMAC(algorithm=hashes.SHA256(), length=32, salt=salt, iterations=100000)
    key = base64.urlsafe_b64encode(kdf.derive(password.encode()))
    token = Fernet(key).encrypt(json.dumps(payload).encode('utf-8'))

    out = tmp_path / 'legacy.enc'
    out.write_bytes(token)

    loaded = decrypt_codebook(str(out), password)
    assert loaded['students']['STU_00001'] == 'legacy@example.edu'


def test_codebook_wrong_password_raises(tmp_path):
    payload = {
        'students': {'STU_00001': 'student@example.edu'},
        'tutors': {},
        'metadata': {
            'created': '2026-02-19T00:00:00',
            'session_type': 'scheduled',
            'total_students': 1,
            'total_tutors': 0,
            'dataset_date_range': '2026-01-01 to 2026-01-31',
        },
    }
    out = tmp_path / 'codebook.enc'

    save_encrypted_codebook(payload, str(out), 'correct-pass-123')

    with pytest.raises(ValueError):
        decrypt_codebook(str(out), 'wrong-pass')
