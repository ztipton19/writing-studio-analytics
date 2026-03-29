/**
 * privacy.test.js
 *
 * Phase 3 exit criterion:
 *   - codebook encrypt/decrypt passes round-trip tests
 *   - wrong password fails with a handled user-facing error
 *
 * Also covers:
 *   - SHA-256 ID parity (deterministic, matches Python logic)
 *   - detectPiiColumns two-layer detection
 *   - lookupInCodebook / getCodebookInfo
 */

import { describe, it, expect } from 'vitest';
import {
  sha256Hex,
  studentAnonId,
  tutorAnonId,
  detectPiiColumns,
  encryptCodebook,
  decryptCodebook,
  lookupInCodebook,
  getCodebookInfo,
  anonymizeWithCodebook,
} from '../src/core/privacy.js';

// ---------------------------------------------------------------------------
// sha256Hex
// ---------------------------------------------------------------------------

describe('sha256Hex', () => {
  it('returns 64-char lowercase hex', async () => {
    const h = await sha256Hex('hello');
    expect(h).toHaveLength(64);
    expect(h).toMatch(/^[0-9a-f]+$/);
  });

  it('is deterministic for the same input', async () => {
    const h1 = await sha256Hex('test@example.com');
    const h2 = await sha256Hex('test@example.com');
    expect(h1).toBe(h2);
  });

  it('differs for different inputs', async () => {
    const h1 = await sha256Hex('alice@example.com');
    const h2 = await sha256Hex('bob@example.com');
    expect(h1).not.toBe(h2);
  });

  // Golden value computed with Python:
  //   import hashlib; hashlib.sha256(b"hello").hexdigest()
  it('matches known SHA-256 of "hello"', async () => {
    const h = await sha256Hex('hello');
    expect(h).toBe('2cf24dba5fb0a30e26e83b2ac5b9e29e1b161e5c1fa7425e73043362938b9824');
  });
});

// ---------------------------------------------------------------------------
// studentAnonId / tutorAnonId
// ---------------------------------------------------------------------------

describe('studentAnonId', () => {
  it('returns STU_ prefix with 5-digit zero-padded number', async () => {
    const id = await studentAnonId('alice@example.com');
    expect(id).toMatch(/^STU_\d{5}$/);
  });

  it('is deterministic', async () => {
    const id1 = await studentAnonId('alice@example.com');
    const id2 = await studentAnonId('alice@example.com');
    expect(id1).toBe(id2);
  });

  it('differs for different emails', async () => {
    const id1 = await studentAnonId('alice@example.com');
    const id2 = await studentAnonId('bob@example.com');
    expect(id1).not.toBe(id2);
  });

  it('matches Python formula: STU_ + (int(hex[:8],16) % 100000) zero-padded', async () => {
    // Python: hashlib.sha256("alice@example.com".encode()).hexdigest()
    // Then: int(hex[:8], 16) % 100000
    const hex = await sha256Hex('alice@example.com');
    const n   = parseInt(hex.slice(0, 8), 16) % 100_000;
    const expected = `STU_${String(n).padStart(5, '0')}`;
    const actual   = await studentAnonId('alice@example.com');
    expect(actual).toBe(expected);
  });
});

describe('tutorAnonId', () => {
  it('returns TUT_ prefix with 4-digit zero-padded number', async () => {
    const id = await tutorAnonId('tutor@example.com');
    expect(id).toMatch(/^TUT_\d{4}$/);
  });

  it('is deterministic', async () => {
    const id1 = await tutorAnonId('tutor@example.com');
    const id2 = await tutorAnonId('tutor@example.com');
    expect(id1).toBe(id2);
  });

  it('matches Python formula: TUT_ + (int(hex[:8],16) % 10000) zero-padded', async () => {
    const hex = await sha256Hex('tutor@example.com');
    const n   = parseInt(hex.slice(0, 8), 16) % 10_000;
    const expected = `TUT_${String(n).padStart(4, '0')}`;
    const actual   = await tutorAnonId('tutor@example.com');
    expect(actual).toBe(expected);
  });
});

// ---------------------------------------------------------------------------
// detectPiiColumns
// ---------------------------------------------------------------------------

describe('detectPiiColumns', () => {
  it('detects known PII column names (Layer 1)', () => {
    const headers = ['Unique ID', 'Student Email', 'Course', 'Tutor Name'];
    const pii = detectPiiColumns(headers, []);
    expect(pii).toContain('Student Email');
    expect(pii).toContain('Tutor Name');
    expect(pii).not.toContain('Unique ID');
    expect(pii).not.toContain('Course');
  });

  it('detects email-patterned columns via Layer 2 (keyword + email pattern)', () => {
    // Column name contains 'email' keyword and value matches EMAIL_RE
    const headers = ['Session_ID', 'student_email_address'];
    const rows = [{ student_email_address: 'alice@uark.edu' }];
    const pii = detectPiiColumns(headers, rows);
    expect(pii).toContain('student_email_address');
  });

  it('does not flag columns with no matching data', () => {
    const headers = ['some_email_field'];
    const rows = [{ some_email_field: 'no-email-here-123' }];
    const pii = detectPiiColumns(headers, rows);
    // Column contains "email" keyword but value doesn't match patterns
    // Depends on whether "no-email-here-123" matches SSO or Name patterns
    // SSO_RE: /^[a-zA-Z0-9]{6,10}$/ — "no-email-here-123" has hyphens → no match
    // EMAIL_RE won't match, NAME_RE won't match
    expect(pii).not.toContain('some_email_field');
  });

  it('returns empty array when no PII found', () => {
    const headers = ['Semester', 'Course', 'Duration_Minutes'];
    const pii = detectPiiColumns(headers, []);
    expect(pii).toHaveLength(0);
  });

  it('handles empty rows array without error', () => {
    const headers = ['Student Email'];
    const pii = detectPiiColumns(headers, []);
    expect(pii).toContain('Student Email');
  });
});

// ---------------------------------------------------------------------------
// encryptCodebook / decryptCodebook — round-trip (Phase 3 exit criterion)
// ---------------------------------------------------------------------------

describe('encryptCodebook / decryptCodebook round-trip', () => {
  const password = 'SuperSecret1234!';
  const codebook = {
    students: { 'STU_00042': 'alice@example.com' },
    tutors:   { 'TUT_0007':  'bob@example.com' },
    metadata: {
      created: '2025-01-01T00:00:00.000Z',
      session_type: 'scheduled',
      total_students: 1,
      total_tutors: 1,
      dataset_date_range: '2025-01-01 to 2025-05-31',
    },
  };

  it('round-trip preserves codebook content', async () => {
    const payload  = await encryptCodebook(codebook, password);
    const decoded  = await decryptCodebook(payload, password);
    expect(decoded.students).toEqual(codebook.students);
    expect(decoded.tutors).toEqual(codebook.tutors);
    expect(decoded.metadata.session_type).toBe('scheduled');
    expect(decoded.metadata.total_students).toBe(1);
  });

  it('payload is a valid JSON string with version, iv, ciphertext', async () => {
    const payload = await encryptCodebook(codebook, password);
    const obj     = JSON.parse(payload);
    expect(obj.version).toBe(2);
    expect(typeof obj.iv).toBe('string');
    expect(typeof obj.ciphertext).toBe('string');
  });

  it('two encryptions of the same data produce different ciphertext (random IV)', async () => {
    const p1 = await encryptCodebook(codebook, password);
    const p2 = await encryptCodebook(codebook, password);
    // IVs differ, so ciphertexts differ
    expect(JSON.parse(p1).ciphertext).not.toBe(JSON.parse(p2).ciphertext);
  });

  // Phase 3 exit criterion: wrong password fails with user-facing error
  it('wrong password throws user-facing INCORRECT PASSWORD error', async () => {
    const payload = await encryptCodebook(codebook, password);
    await expect(decryptCodebook(payload, 'wrong-password-xyz')).rejects.toThrow(
      /INCORRECT PASSWORD/
    );
  });

  it('corrupt payload throws CORRUPTED CODEBOOK error', async () => {
    await expect(decryptCodebook('not-valid-json!!!', password)).rejects.toThrow(
      /CORRUPTED CODEBOOK/
    );
  });

  it('unsupported version throws informative error', async () => {
    const fakePayload = JSON.stringify({ version: 1, iv: 'abc', ciphertext: 'xyz' });
    await expect(decryptCodebook(fakePayload, password)).rejects.toThrow(
      /Unsupported codebook version/
    );
  });
});

// ---------------------------------------------------------------------------
// lookupInCodebook
// ---------------------------------------------------------------------------

describe('lookupInCodebook', () => {
  const password = 'lookup-test-pass-99!';
  const codebook = {
    students: { 'STU_00001': 'alice@example.com' },
    tutors:   { 'TUT_0002':  'bob@example.com' },
    metadata: { created: '2025-01-01T00:00:00.000Z', session_type: 'scheduled',
                total_students: 1, total_tutors: 1, dataset_date_range: null },
  };

  it('resolves a student ID to email', async () => {
    const payload = await encryptCodebook(codebook, password);
    const email   = await lookupInCodebook('STU_00001', payload, password);
    expect(email).toBe('alice@example.com');
  });

  it('resolves a tutor ID to email', async () => {
    const payload = await encryptCodebook(codebook, password);
    const email   = await lookupInCodebook('TUT_0002', payload, password);
    expect(email).toBe('bob@example.com');
  });

  it('throws if ID not found in codebook', async () => {
    const payload = await encryptCodebook(codebook, password);
    await expect(lookupInCodebook('STU_99999', payload, password)).rejects.toThrow(
      /not found in codebook/
    );
  });

  it('throws on invalid ID format', async () => {
    const payload = await encryptCodebook(codebook, password);
    await expect(lookupInCodebook('INVALID_001', payload, password)).rejects.toThrow(
      /Invalid ID format/
    );
  });
});

// ---------------------------------------------------------------------------
// getCodebookInfo
// ---------------------------------------------------------------------------

describe('getCodebookInfo', () => {
  const password = 'info-test-pass-77!';
  const codebook = {
    students: { 'STU_00001': 'a@example.com', 'STU_00002': 'b@example.com' },
    tutors:   {},
    metadata: {
      created: '2025-03-01T12:00:00.000Z',
      session_type: 'walkin',
      total_students: 2,
      total_tutors: 0,
      dataset_date_range: '2025-01-01 to 2025-03-01',
    },
  };

  it('returns correct metadata without individual entries', async () => {
    const payload = await encryptCodebook(codebook, password);
    const info    = await getCodebookInfo(payload, password);
    expect(info.session_type).toBe('walkin');
    expect(info.total_students).toBe(2);
    expect(info.total_tutors).toBe(0);
    expect(info.created).toBe('2025-03-01T12:00:00.000Z');
    expect(info.date_range).toBe('2025-01-01 to 2025-03-01');
  });

  it('does not include individual student or tutor entries in the return', async () => {
    const payload = await encryptCodebook(codebook, password);
    const info    = await getCodebookInfo(payload, password);
    expect(info).not.toHaveProperty('students');
    expect(info).not.toHaveProperty('tutors');
  });
});

// ---------------------------------------------------------------------------
// anonymizeWithCodebook — integration
// ---------------------------------------------------------------------------

describe('anonymizeWithCodebook', () => {
  const rows = [
    {
      'Student Email': 'alice@example.com',
      'Tutor Email':   'tutor1@example.com',
      'Course':        'ENGL1013',
      'Status':        'Completed',
    },
    {
      'Student Email': 'bob@example.com',
      'Tutor Email':   'tutor1@example.com',
      'Course':        'ENGL1023',
      'Status':        'Completed',
    },
  ];

  const opts = {
    createCodebook:  true,
    password:        'MySecure_Pass_2025!',
    confirmPassword: 'MySecure_Pass_2025!',
    sessionType:     'scheduled',
  };

  it('removes PII columns', async () => {
    const { rows: out } = await anonymizeWithCodebook(rows, opts);
    for (const row of out) {
      expect(row).not.toHaveProperty('Student Email');
      expect(row).not.toHaveProperty('Tutor Email');
    }
  });

  it('adds Student_Anon_ID and Tutor_Anon_ID', async () => {
    const { rows: out } = await anonymizeWithCodebook(rows, opts);
    for (const row of out) {
      expect(row).toHaveProperty('Student_Anon_ID');
      expect(row).toHaveProperty('Tutor_Anon_ID');
    }
  });

  it('Student_Anon_ID matches studentAnonId', async () => {
    const { rows: out } = await anonymizeWithCodebook(rows, opts);
    const expectedAlice = await studentAnonId('alice@example.com');
    const row = out.find(r => r.Course === 'ENGL1013');
    expect(row.Student_Anon_ID).toBe(expectedAlice);
  });

  it('log.piiColumnsRemoved lists removed columns', async () => {
    const { log } = await anonymizeWithCodebook(rows, opts);
    expect(log.piiColumnsRemoved).toContain('Student Email');
    expect(log.piiColumnsRemoved).toContain('Tutor Email');
  });

  it('preserves non-PII columns', async () => {
    const { rows: out } = await anonymizeWithCodebook(rows, opts);
    for (const row of out) {
      expect(row).toHaveProperty('Course');
      expect(row).toHaveProperty('Status');
    }
  });

  it('codebookPayload is a non-empty string', async () => {
    const { codebookPayload } = await anonymizeWithCodebook(rows, opts);
    expect(typeof codebookPayload).toBe('string');
    expect(codebookPayload.length).toBeGreaterThan(0);
  });

  it('throws when password is too short', async () => {
    await expect(anonymizeWithCodebook(rows, {
      ...opts,
      password: 'short',
      confirmPassword: 'short',
    })).rejects.toThrow(/at least 12 characters/);
  });

  it('throws when passwords do not match', async () => {
    await expect(anonymizeWithCodebook(rows, {
      ...opts,
      password:        'MySecure_Pass_2025!',
      confirmPassword: 'different_pass_2025!',
    })).rejects.toThrow(/Passwords do not match/);
  });

  it('codebook can be decrypted and used for lookup', async () => {
    const { codebookPayload } = await anonymizeWithCodebook(rows, opts);
    const aliceId = await studentAnonId('alice@example.com');
    const email   = await lookupInCodebook(aliceId, codebookPayload, opts.password);
    expect(email).toBe('alice@example.com');
  });
});
